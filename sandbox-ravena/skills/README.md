# ============================================
# SKILLS NATIVAS - SANDBOX RAVENA
# ============================================

## Visão Geral

As **Skills Nativas** são módulos de segurança desenvolvidos especificamente para a Sandbox Ravena. Elas funcionam **exclusivamente no ambiente isolado** e são projetadas para testes de segurança controlados.

> ⚠️ **AVISO:** Estas skills NÃO devem ser usadas em ambientes de produção ou com dados reais.

---

## Skills Disponíveis

### 1. SQLiDetector (Detector de SQL Injection)

**Arquivo:** `sqli_detector.py`

**Função:** Detecta e bloqueia tentativas de SQL Injection

**Funcionalidades:**
- Detecta UNION SELECT, comentários, Always True, etc.
- Calcula confiança da detecção
- Registra tentativas bloqueadas
- Fornece estatísticas de detecção

**Uso:**
```python
from skills import sqli_detector

# Analisar input
is_malicious, attack_type, confidence = sqli_detector.analyze("' OR 1=1--")

# Bloquear e registrar
result = sqli_detector.block_and_log(
    input_data="' OR 1=1--",
    endpoint="/api/login",
    ip_address="192.168.1.100"
)

# Obter estatísticas
stats = sqli_detector.get_stats()
```

**Padrões Detectados:**
- UNION SELECT
- Comentários SQL (--, /*, #)
- Always True (' OR 1=1)
- Stacked Queries (;)
- Information Gathering
- Blind SQLi
- Dangerous Functions

---

### 2. BruteForceProtector (Protetor contra Força Bruta)

**Arquivo:** `brute_force_protector.py`

**Função:** Protege contra ataques de força bruta

**Funcionalidades:**
- Limita tentativas de login
- Bloqueia IP após múltiplas falhas
- Bloqueia usuários específicos
- Janela de tempo configurável

**Uso:**
```python
from skills import brute_force_protector

# Verificar tentativa
allowed, message = brute_force_protector.check_attempt(
    ip_address="192.168.1.100",
    username="admin"
)

# Obter tentativas falhas
failed = brute_force_protector.get_failed_attempts("192.168.1.100")

# Resetar bloqueio (para testes)
brute_force_protector.reset_lockout(ip_address="192.168.1.100")
```

**Configurações:**
- `max_attempts`: Máximo de tentativas (padrão: 5)
- `window_minutes`: Janela de tempo em minutos (padrão: 5)
- `lockout_minutes`: Duração do bloqueio (padrão: 15)

---

### 3. SessionManager (Gerenciador de Sessões)

**Arquivo:** `session_manager.py`

**Função:** Gerencia sessões de forma segura

**Funcionalidades:**
- Cria tokens seguros (SHA-256)
- Valida sessões
- Invalida sessões
- Limite de sessões por usuário
- Limpeza automática de sessões expiradas

**Uso:**
```python
from skills import session_manager

# Criar sessão
session = session_manager.create_session(
    user_id="user_001",
    ip_address="192.168.1.100",
    user_agent="Mozilla/5.0"
)

# Validar sessão
is_valid, data = session_manager.validate_session(
    token=session['token'],
    ip_address="192.168.1.100"
)

# Invalidar todas as sessões de um usuário
count = session_manager.invalidate_all_user_sessions("user_001")
```

**Configurações:**
- `session_timeout_minutes`: Timeout da sessão (padrão: 30)
- `max_sessions_per_user`: Máximo de sessões por usuário (padrão: 3)

---

### 4. InputValidator (Validador de Entradas)

**Arquivo:** `input_validator.py`

**Função:** Valida e sanitiza entradas

**Funcionalidades:**
- Validação por tipo (username, email, password, etc.)
- Sanitização de HTML
- Detecção de padrões bloqueados
- Validação de força de senha
- Validação em lote

**Uso:**
```python
from skills import input_validator

# Validar campo
is_valid, error, sanitized = input_validator.validate(
    value="admin",
    field_type="username"
)

# Validar força de senha
strength = input_validator.validate_password_strength("Abc@1234")

# Validar múltiplos campos
results = input_validator.validate_batch({
    'username': ('admin', 'username'),
    'email': ('user@example.com', 'email'),
    'amount': ('100.50', 'amount')
})
```

**Tipos Disponíveis:**
- `username`: Nome de usuário
- `email`: E-mail
- `password`: Senha
- `amount`: Valor monetário
- `pix_key`: Chave PIX
- `text`: Texto genérico
- `sql_safe`: Seguro para SQL

---

### 5. RateLimiter (Limitador de Taxa)

**Arquivo:** `rate_limiter.py`

**Função:** Limita taxa de requisições

**Funcionalidades:**
- Limites por endpoint
- Bloqueio automático
- Contadores por IP/chave
- Limite personalizável

**Uso:**
```python
from skills import rate_limiter

# Verificar limite
allowed, info = rate_limiter.check_rate_limit(
    key="192.168.1.100",
    endpoint="login"
)

# Definir limite personalizado
rate_limiter.set_custom_limit(
    endpoint="custom",
    requests=10,
    window=60
)

# Usar decorator
from skills import rate_limit

@rate_limit('login')
def login():
    # Lógica de login
    pass
```

**Endpoints Padrão:**
- `login`: 5 requisições/5 minutos
- `api`: 100 requisições/minuto
- `withdrawal`: 3 requisições/hora
- `slot_spin`: 50 requisições/minuto

---

### 6. AuditLogger (Logger de Auditoria)

**Arquivo:** `audit_logger.py`

**Função:** Registra todas as ações para auditoria

**Funcionalidades:**
- Log de ações com timestamp
- Hash de integridade (SHA-256)
- Logs por usuário e tipo
- Sanitização de dados sensíveis
- Exportação em JSON/CSV

**Uso:**
```python
from skills import audit_logger

# Log genérico
audit_logger.log(
    action="data_access",
    user_id="user_001",
    details={"resource": "users"},
    ip_address="192.168.1.100"
)

# Log de login
audit_logger.log_login("user_001", "192.168.1.100", success=True)

# Log de saque
audit_logger.log_withdrawal("user_001", 500.00, "success")

# Verificar integridade
is_valid = audit_logger.verify_integrity(log_entry)

# Exportar logs
json_logs = audit_logger.export_logs('json')
```

---

## Uso Combinado das Skills

### Exemplo: Proteção Completa de Login

```python
from skills import (
    sqli_detector,
    brute_force_protector,
    session_manager,
    input_validator,
    rate_limiter,
    audit_logger
)

def secure_login(username, password, ip_address):
    # 1. Verificar rate limit
    allowed, info = rate_limiter.check_rate_limit(ip_address, 'login')
    if not allowed:
        return {'error': 'Rate limit excedido'}, 429
    
    # 2. Verificar brute force
    allowed, message = brute_force_protector.check_attempt(ip_address, username)
    if not allowed:
        return {'error': message}, 429
    
    # 3. Validar inputs
    is_valid, error, _ = input_validator.validate(username, 'username')
    if not is_valid:
        return {'error': error}, 400
    
    # 4. Verificar SQL Injection
    is_malicious, _, _ = sqli_detector.analyze(username)
    if is_malicious:
        audit_logger.log_security_event('sql_injection', ip_address, {'input': username})
        return {'error': 'Entrada inválida'}, 400
    
    # 5. Autenticar (simulado)
    success = authenticate(username, password)
    
    # 6. Registrar tentativa
    audit_logger.log_login(username, ip_address, success)
    
    if success:
        # 7. Criar sessão
        session = session_manager.create_session(username, ip_address, 'Mozilla/5.0')
        return {'token': session['token']}, 200
    else:
        return {'error': 'Credenciais inválidas'}, 401
```

---

## Estatísticas Globais

Para obter estatísticas de todas as skills:

```python
from skills import get_all_stats

stats = get_all_stats()
print(stats)
```

**Saída exemplo:**
```json
{
  "SQLiDetector": {
    "total_blocked": 47,
    "by_type": {"always_true": 23, "union": 15, "comment": 9},
    "by_ip": {"192.168.1.100": 30, "10.0.0.1": 17}
  },
  "BruteForceProtector": {
    "total_attempts": 156,
    "blocked_ips": {"192.168.1.100": 5},
    "active_lockouts": 2
  },
  "SessionManager": {
    "total_sessions": 89,
    "active_sessions": 12,
    "invalidated_tokens": 77
  },
  "InputValidator": {
    "available_rules": ["username", "email", "password", "amount", "pix_key", "text", "sql_safe"],
    "blocked_patterns_count": 25
  },
  "RateLimiter": {
    "active_counters": 45,
    "blocked_keys": 3,
    "total_requests_tracked": 1234
  },
  "AuditLogger": {
    "total_logs": 567,
    "unique_users": 23,
    "action_types": ["login", "logout", "withdrawal", "slot_spin", "security_sql_injection"]
  }
}
```

---

## Configuração

### Variáveis de Ambiente

As skills usam configurações padrão que podem ser ajustadas:

```python
# SQLiDetector
sqli_detector.patterns  # Padrões de detecção

# BruteForceProtector
brute_force_protector.max_attempts = 5
brute_force_protector.window_minutes = 5
brute_force_protector.lockout_minutes = 15

# SessionManager
session_manager.session_timeout = 30
session_manager.max_sessions = 3

# RateLimiter
rate_limiter.default_limits['login'] = {'requests': 5, 'window': 300}
```

---

## Segurança

### Restrições

1. **Ambiente Isolado:** Estas skills só funcionam na sandbox
2. **Dados Fictícios:** Não use com dados reais
3. **Sem Produção:** Nunca use em ambiente de produção
4. **Logs Locais:** Todos os logs ficam na sandbox

### Boas Práticas

1. Use sempre `input_validator` para validar entradas
2. Configure `rate_limiter` para endpoints sensíveis
3. Use `audit_logger` para todas as ações críticas
4. Verifique `sqli_detector` em todos os inputs
5. Use `session_manager` para gerenciar sessões

---

## Troubleshooting

### Skill não importa

```python
# Verificar se o diretório skills existe
import os
print(os.path.exists('skills'))

# Verificar arquivos
print(os.listdir('skills'))
```

### Erro de dependência

```bash
# Instalar dependências
pip install -r requirements.txt
```

### Logs não aparecem

```python
# Configurar logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## Desenvolvimento

### Adicionar Nova Skill

1. Crie um arquivo em `skills/`
2. Implemente a classe com `get_stats()`
3. Crie uma instância global
4. Importe em `__init__.py`
5. Adicione em `AVAILABLE_SKILLS`

### Testar Skill

```bash
# Executar teste da skill
python -m skills.sqli_detector
```

---

## Referências

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE/SANS Top 25](https://cwe.mitre.org/top25/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

---

## Licença

Estas skills são para fins educacionais e de testes de segurança. O uso inadequado é de inteira responsabilidade do usuário.
