"""
Servidor Principal - Sandbox Ravena
Ambiente isolado para testes de segurança
"""

import os
import sys
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, request, jsonify, g
import psycopg2
import psycopg2.extras
import jwt
import redis

# Adicionar skills ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'skills'))

# Importar skills de segurança
from sqli_detector import SQLInjectionDetector
from brute_force_protector import BruteForceProtector
from input_validator import InputValidator
from rate_limiter import RateLimiter
from audit_logger import AuditLogger

app = Flask(__name__)

# Configurações
app.config['SECRET_KEY'] = os.getenv('JWT_SECRET', 'sandbox_jwt_secret_key')
app.config['DATABASE_URL'] = os.getenv('DATABASE_URL', 
    'postgresql://ravena_test:sandbox_password_123@ravena-db:5432/ravena_sandbox')

# ============================================
# CONEXÃO COM REDIS
# ============================================

redis_url = os.getenv('REDIS_URL', 'redis://ravena-redis:6379')
redis_client = redis.from_url(redis_url, decode_responses=True)

def cache_get(key):
    """Obtém valor do cache Redis"""
    try:
        value = redis_client.get(key)
        return json.loads(value) if value else None
    except Exception:
        return None

def cache_set(key, value, ttl=300):
    """Define valor no cache Redis (TTL em segundos)"""
    try:
        redis_client.setex(key, ttl, json.dumps(value))
    except Exception:
        pass

def cache_delete(key):
    """Remove valor do cache Redis"""
    try:
        redis_client.delete(key)
    except Exception:
        pass

def increment_counter(key, ttl=60):
    """Incrementa contador no Redis (para rate limiting)"""
    try:
        pipe = redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, ttl)
        result = pipe.execute()
        return result[0]
    except Exception:
        return 0

# ============================================
# INICIALIZAR SKILLS DE SEGURANÇA
# ============================================

sqli_detector = SQLInjectionDetector()
brute_force_protector = BruteForceProtector()
input_validator = InputValidator()
rate_limiter = RateLimiter()
audit_logger = AuditLogger()

# ============================================
# CONEXÃO COM BANCO DE DADOS
# ============================================

def get_db():
    """Obtém conexão com o banco de dados"""
    if 'db' not in g:
        g.db = psycopg2.connect(app.config['DATABASE_URL'])
    return g.db

@app.teardown_appcontext
def close_db(exception):
    """Fecha conexão com o banco ao final da requisição"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

# ============================================
# MIDDLEWARE DE SEGURANÇA
# ============================================

def log_attack(attack_type, endpoint, payload=None):
    """Registra tentativa de ataque"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO attack_log (attack_type, endpoint, payload, ip_address, user_agent, blocked)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            attack_type,
            endpoint,
            str(payload)[:1000] if payload else None,
            request.remote_addr,
            request.user_agent.string,
            True
        ))
        db.commit()
    except Exception as e:
        print(f"[ERRO] Falha ao registrar ataque: {e}")

def detect_sql_injection(data):
    """Detecta tentativas de SQL Injection"""
    if not data:
        return False
    
    sql_patterns = [
        "' OR 1=1",
        "' OR '1'='1",
        "UNION SELECT",
        "DROP TABLE",
        "INSERT INTO",
        "DELETE FROM",
        "--",
        ";",
        "/*",
        "EXEC(",
        "CHAR(",
        "0x",
        "BENCHMARK("
    ]
    
    data_str = str(data).upper()
    for pattern in sql_patterns:
        if pattern.upper() in data_str:
            return True
    return False

def detect_xss(data):
    """Detecta tentativas de XSS"""
    if not data:
        return False
    
    xss_patterns = [
        '<script>',
        'javascript:',
        'onload=',
        'onerror=',
        'alert(',
        'document.cookie',
        'eval('
    ]
    
    data_str = str(data).lower()
    for pattern in xss_patterns:
        if pattern.lower() in data_str:
            return True
    return False

def security_check(f):
    """Decorador de verificação de segurança"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Rate limiting via Redis
        ip_address = request.remote_addr
        rate_limit_key = f"rate_limit:{ip_address}"
        request_count = increment_counter(rate_limit_key, 60)
        
        if request_count > 100:  # 100 requests por minuto
            return jsonify({'error': 'Rate limit excedido'}), 429
        
        # Verificar SQL Injection em todos os dados
        all_data = json.dumps(request.get_json(silent=True) or {})
        all_data += request.url
        all_data += str(request.args)
        
        # Usar skill de detecção de SQL injection
        is_sqli, sqli_pattern = sqli_detector.detect(all_data)
        if is_sqli:
            log_attack('sql_injection', request.endpoint, all_data)
            audit_logger.log_event('sql_injection_detected', {
                'pattern': sqli_pattern,
                'ip': ip_address
            })
            return jsonify({'error': 'Rejeitado por segurança'}), 403
        
        if detect_xss(all_data):
            log_attack('xss', request.endpoint, all_data)
            audit_logger.log_event('xss_detected', {'ip': ip_address})
            return jsonify({'error': 'Rejeitado por segurança'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

# ============================================
# ROTAS DA API
# ============================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check da aplicação"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/metrics', methods=['GET'])
def metrics():
    """Endpoint para Prometheus - métricas da aplicação"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Contar usuários
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        # Contar ataques hoje
        cursor.execute("""
            SELECT COUNT(*) FROM attack_log 
            WHERE timestamp > CURRENT_DATE
        """)
        attacks_today = cursor.fetchone()[0]
        
        # Contar ataques bloqueados
        cursor.execute("""
            SELECT COUNT(*) FROM attack_log 
            WHERE blocked = true AND timestamp > CURRENT_DATE
        """)
        blocked_today = cursor.fetchone()[0]
        
        # Contar sessões ativas
        cursor.execute("""
            SELECT COUNT(*) FROM sessions 
            WHERE expires_at > NOW()
        """)
        active_sessions = cursor.fetchone()[0]
        
        # Status do Redis
        redis_status = "connected" if redis_client.ping() else "disconnected"
        
        # Métricas no formato Prometheus
        metrics_output = f"""# HELP ravena_users_total Total de usuários
# TYPE ravena_users_total counter
ravena_users_total {total_users}

# HELP ravena_attacks_today Total de ataques hoje
# TYPE ravena_attacks_today counter
ravena_attacks_today {attacks_today}

# HELP ravena_blocked_today Total de ataques bloqueados hoje
# TYPE ravena_blocked_today counter
ravena_blocked_today {blocked_today}

# HELP ravena_sessions_active Sessões ativas
# TYPE ravena_sessions_active gauge
ravena_sessions_active {active_sessions}

# HELP ravena_redis_status Status do Redis (1=conectado, 0=desconectado)
# TYPE ravena_redis_status gauge
ravena_redis_status {1 if redis_status == 'connected' else 0}

# HELP ravena_app_info Informações da aplicação
# TYPE ravena_app_info info
ravena_app_info{{version="1.0.0",environment="sandbox"}} 1
"""
        return metrics_output, 200, {'Content-Type': 'text/plain'}
    except Exception as e:
        return f"# HELP ravena_error Erro ao obter métricas\nravena_error 1\n", 500, {'Content-Type': 'text/plain'}

@app.route('/api/auth/login', methods=['POST'])
@security_check
def login():
    """Autenticação de usuário"""
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Credenciais inválidas'}), 400
    
    username = data['username']
    password = data['password']
    
    # Validar inputs usando skill
    is_valid, error_msg, _ = input_validator.validate(username, 'username')
    if not is_valid:
        audit_logger.log_event('validation_failed', {'field': 'username', 'error': error_msg})
        return jsonify({'error': 'Credenciais inválidas'}), 400
    
    # Verificar força bruta usando skill
    ip_address = request.remote_addr
    is_allowed, block_message = brute_force_protector.check_attempt(ip_address, username)
    if not is_allowed:
        audit_logger.log_event('brute_force_blocked', {'ip': ip_address, 'username': username})
        return jsonify({'error': block_message}), 429
    
    db = get_db()
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Buscar usuário
    cursor.execute("""
        SELECT id, username, email, balance, status, role, password_hash 
        FROM users 
        WHERE username = %s
    """, (username,))
    
    user = cursor.fetchone()
    
    if not user:
        brute_force_protector.record_failed_attempt(ip_address, username)
        audit_logger.log_event('login_failed', {'username': username, 'reason': 'user_not_found'})
        return jsonify({'error': 'Credenciais inválidas'}), 401
    
    # Verificar senha usando pgcrypto do PostgreSQL
    cursor.execute("""
        SELECT password_hash = crypt(%s, password_hash) as password_valid
        FROM users WHERE username = %s
    """, (password, username))
    
    password_check = cursor.fetchone()
    
    if not password_check or not password_check['password_valid']:
        brute_force_protector.record_failed_attempt(ip_address, username)
        audit_logger.log_event('login_failed', {'username': username, 'reason': 'invalid_password'})
        return jsonify({'error': 'Credenciais inválidas'}), 401
    
    # Login bem-sucedido - resetar contador
    brute_force_protector.reset_lockout(ip_address, username)
    
    # Verificar senha usando pgcrypto do PostgreSQL
    cursor.execute("""
        SELECT password_hash = crypt(%s, password_hash) as password_valid
        FROM users WHERE username = %s
    """, (password, username))
    
    password_check = cursor.fetchone()
    
    if not password_check or not password_check['password_valid']:
        log_attack('brute_force', 'login', username)
        return jsonify({'error': 'Credenciais inválidas'}), 401
    
    # Gerar token JWT
    token = jwt.encode({
        'user_id': str(user['id']),
        'username': user['username'],
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm='HS256')
    
    # Registrar sessão
    cursor.execute("""
        INSERT INTO sessions (user_id, token, ip_address, user_agent, expires_at)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        user['id'],
        token,
        request.remote_addr,
        request.user_agent.string,
        datetime.utcnow() + timedelta(hours=24)
    ))
    db.commit()
    
    return jsonify({
        'token': token,
        'user': {
            'id': str(user['id']),
            'username': user['username'],
            'balance': float(user['balance'])
        }
    })

@app.route('/api/auth/me', methods=['GET'])
@security_check
def get_current_user():
    """Obtém dados do usuário atual"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({'error': 'Token não fornecido'}), 401
    
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Token inválido'}), 401
    
    db = get_db()
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cursor.execute("""
        SELECT id, username, email, balance, status 
        FROM users 
        WHERE id = %s
    """, (data['user_id'],))
    
    user = cursor.fetchone()
    
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    return jsonify({
        'id': str(user['id']),
        'username': user['username'],
        'email': user['email'],
        'balance': float(user['balance']),
        'status': user['status']
    })

@app.route('/api/slots/spin', methods=['POST'])
@security_check
def slot_spin():
    """Realiza aposta em slot"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({'error': 'Token não fornecido'}), 401
    
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Token inválido'}), 401
    
    bet_data = request.get_json()
    bet_amount = bet_data.get('amount', 0)
    
    # Validações
    if bet_amount <= 0:
        return jsonify({'error': 'Valor da aposta inválido'}), 400
    
    if bet_amount > 1000:
        return jsonify({'error': 'Valor máximo de aposta: R$ 1.000,00'}), 400
    
    db = get_db()
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Verificar saldo
    cursor.execute("SELECT balance FROM users WHERE id = %s", (data['user_id'],))
    user = cursor.fetchone()
    
    if not user or user['balance'] < bet_amount:
        return jsonify({'error': 'Saldo insuficiente'}), 400
    
    # Simular resultado (RNG)
    import random
    win = random.random() < 0.3  # 30% de chance de ganhar
    win_amount = bet_amount * random.uniform(1.5, 5.0) if win else 0
    
    # Atualizar saldo
    new_balance = float(user['balance']) - bet_amount + win_amount
    cursor.execute("UPDATE users SET balance = %s WHERE id = %s", 
                   (new_balance, data['user_id']))
    
    # Registrar aposta
    cursor.execute("""
        INSERT INTO slot_bets (user_id, game_id, bet_amount, win_amount, result, status)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        data['user_id'],
        'slots_default',
        bet_amount,
        win_amount,
        json.dumps({'win': win, 'multiplier': win_amount / bet_amount if win else 0}),
        'completed'
    ))
    
    db.commit()
    
    return jsonify({
        'win': win,
        'win_amount': win_amount,
        'new_balance': new_balance
    })

@app.route('/api/withdrawals/request', methods=['POST'])
@security_check
def request_withdrawal():
    """Solicita saque"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({'error': 'Token não fornecido'}), 401
    
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Token inválido'}), 401
    
    withdrawal_data = request.get_json()
    amount = withdrawal_data.get('amount', 0)
    pix_key = withdrawal_data.get('pix_key', '')
    
    # Validações básicas
    if amount <= 0:
        return jsonify({'error': 'Valor inválido'}), 400
    
    if amount < 10:
        return jsonify({'error': 'Valor mínimo: R$ 10,00'}), 400
    
    if amount > 5000:
        return jsonify({'error': 'Valor máximo: R$ 5.000,00'}), 400
    
    if not pix_key or len(pix_key) < 10:
        return jsonify({'error': 'Chave PIX inválida'}), 400
    
    db = get_db()
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Verificar saldo
    cursor.execute("SELECT balance FROM users WHERE id = %s", (data['user_id'],))
    user = cursor.fetchone()
    
    if not user or user['balance'] < amount:
        return jsonify({'error': 'Saldo insuficiente'}), 400
    
    # Verificar transações pendentes
    cursor.execute("""
        SELECT COUNT(*) as pending 
        FROM transactions 
        WHERE user_id = %s 
        AND status = 'pending'
    """, (data['user_id'],))
    
    pending = cursor.fetchone()
    if pending and pending['pending'] > 0:
        return jsonify({'error': 'Já existe um saque pendente'}), 400
    
    # Criar transação
    cursor.execute("""
        INSERT INTO transactions (user_id, type, amount, status, payment_method, pix_key)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        data['user_id'],
        'withdrawal',
        amount,
        'pending',
        'pix',
        pix_key
    ))
    
    db.commit()
    
    return jsonify({
        'message': 'Saque solicitado com sucesso',
        'status': 'pending'
    }), 201

@app.route('/api/withdrawals/history', methods=['GET'])
@security_check
def withdrawal_history():
    """Histórico de saques"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({'error': 'Token não fornecido'}), 401
    
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Token inválido'}), 401
    
    db = get_db()
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cursor.execute("""
        SELECT id, type, amount, status, payment_method, created_at
        FROM transactions
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 50
    """, (data['user_id'],))
    
    transactions = cursor.fetchall()
    
    return jsonify({
        'transactions': [
            {
                'id': str(t['id']),
                'type': t['type'],
                'amount': float(t['amount']),
                'status': t['status'],
                'payment_method': t['payment_method'],
                'created_at': t['created_at'].isoformat()
            }
            for t in transactions
        ]
    })

@app.route('/api/admin/attacks', methods=['GET'])
@security_check
def get_attacks():
    """Obtém log de ataques (apenas admin)"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({'error': 'Token não fornecido'}), 401
    
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Token inválido'}), 401
    
    db = get_db()
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Verificar se é admin
    cursor.execute("SELECT status, role FROM users WHERE id = %s", (data['user_id'],))
    user = cursor.fetchone()
    
    if not user or user['status'] != 'active' or user.get('role') != 'admin':
        return jsonify({'error': 'Acesso negado - apenas administradores'}), 403
    
    cursor.execute("""
        SELECT id, attack_type, endpoint, payload, blocked, ip_address, timestamp
        FROM attack_log
        ORDER BY timestamp DESC
        LIMIT 100
    """)
    
    attacks = cursor.fetchall()
    
    return jsonify({
        'attacks': [
            {
                'id': a['id'],
                'type': a['attack_type'],
                'endpoint': a['endpoint'],
                'payload': a['payload'][:200] if a['payload'] else None,
                'blocked': a['blocked'],
                'ip_address': str(a['ip_address']) if a['ip_address'] else None,
                'timestamp': a['timestamp'].isoformat()
            }
            for a in attacks
        ]
    })

# ============================================
# INICIALIZAÇÃO
# ============================================

if __name__ == '__main__':
    print("[INFO] Iniciando Servidor Sandbox Ravena...")
    print("[INFO] Ambiente: SANDBOX ISOLADO")
    print("[INFO] Porta: 8080")
    
    app.run(host='0.0.0.0', port=8080, debug=True)
