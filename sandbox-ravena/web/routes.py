import time
import subprocess
import psutil
from flask import Blueprint, request, jsonify, render_template, g, redirect, url_for

from auth import login, generate_token, require_auth, require_admin, get_db
from websocket import process_command, get_desktop_status, broadcast

api = Blueprint('api', __name__)


@api.route('/')
def index():
    return redirect(url_for('api.login_page'))


@api.route('/login')
def login_page():
    return render_template('login.html')


@api.route('/dashboard')
@require_auth
def dashboard_page():
    return render_template('dashboard.html')


@api.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': 'Usuário e senha obrigatórios'}), 400

    user = login(username, password)
    if not user:
        return jsonify({'error': 'Credenciais inválidas'}), 401

    token = generate_token(user['id'], user['username'], user['role'])

    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "UPDATE users SET last_login = NOW() WHERE id = %s",
            (user['id'],)
        )

    return jsonify({
        'token': token,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'role': user['role']
        }
    })


@api.route('/api/status')
@require_auth
def api_status():
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    net = psutil.net_io_counters()

    return jsonify({
        'cpu': {'percent': cpu, 'count': psutil.cpu_count()},
        'memory': {
            'percent': mem.percent,
            'used_gb': round(mem.used / (1024**3), 2),
            'total_gb': round(mem.total / (1024**3), 2)
        },
        'disk': {
            'percent': disk.percent,
            'used_gb': round(disk.used / (1024**3), 2),
            'total_gb': round(disk.total / (1024**3), 2)
        },
        'network': {
            'bytes_sent': net.bytes_sent,
            'bytes_recv': net.bytes_recv
        },
        'desktop': get_desktop_status(),
        'timestamp': time.time()
    })


@api.route('/api/command', methods=['POST'])
@require_auth
def api_command():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    command = data.get('command', '').strip()
    target = data.get('target', '').strip()

    if not command:
        return jsonify({'error': 'Comando obrigatório'}), 400

    allowed_commands = [
        'scan', 'nmap', 'test', 'status', 'report',
        'backup', 'restore', 'clean', 'update'
    ]

    cmd_base = command.split()[0].lower()
    if cmd_base not in allowed_commands:
        return jsonify({'error': f'Comando não permitido: {cmd_base}'}), 403

    result = process_command(command, target)
    return jsonify(result)


@api.route('/api/tasks')
@require_auth
def api_tasks():
    return jsonify({
        'tasks': [],
        'message': 'Nenhuma tarefa em execução'
    })


@api.route('/api/logs')
@require_auth
def api_logs():
    try:
        result = subprocess.run(
            ['tail', '-n', '50', '/var/log/ravena/app.log'],
            capture_output=True, text=True, timeout=5
        )
        logs = result.stdout.strip().split('\n') if result.stdout else []
    except Exception:
        logs = ['Log não disponível']

    return jsonify({'logs': logs})


@api.route('/api/report', methods=['POST'])
@require_auth
def api_report():
    data = request.get_json() or {}
    report_type = data.get('type', 'status')

    result = process_command('report', report_type)
    return jsonify(result)


@api.route('/api/desktop/command', methods=['POST'])
@require_admin
def api_desktop_command():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    command = data.get('command', '')
    result = process_command(command)
    return jsonify(result)
