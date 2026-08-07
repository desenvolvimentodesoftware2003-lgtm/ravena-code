import json
import time
import threading

connected_clients = {}
desktop_connection = None
message_queue = []
lock = threading.Lock()


def handle_connect(client):
    with lock:
        connected_clients[client['id']] = client
    print(f"[WS] Cliente conectado: {client['id']}")


def handle_disconnect(client_id):
    with lock:
        connected_clients.pop(client_id, None)
    print(f"[WS] Cliente desconectado: {client_id}")


def handle_desktop_connect(client):
    global desktop_connection
    with lock:
        desktop_connection = client
    print(f"[WS] Desktop conectado: {client['id']}")
    broadcast({'type': 'status', 'desktop': 'online'})


def handle_desktop_disconnect():
    global desktop_connection
    with lock:
        desktop_connection = None
    broadcast({'type': 'status', 'desktop': 'offline'})


def send_to_desktop(message: dict):
    global desktop_connection
    if desktop_connection:
        try:
            desktop_connection['socket'].send(json.dumps(message))
            return True
        except Exception:
            handle_desktop_disconnect()
    with lock:
        message_queue.append({
            'message': message,
            'timestamp': time.time()
        })
    return False


def broadcast(message: dict):
    with lock:
        clients = list(connected_clients.values())
    for client in clients:
        try:
            client['socket'].send(json.dumps(message))
        except Exception:
            handle_disconnect(client['id'])


def get_desktop_status() -> dict:
    return {
        'connected': desktop_connection is not None,
        'client_id': desktop_connection['id'] if desktop_connection else None
    }


def process_command(command: str, target: str = None) -> dict:
    message = {
        'type': 'command',
        'action': command,
        'target': target,
        'timestamp': time.time()
    }
    sent = send_to_desktop(message)
    return {
        'sent': sent,
        'queued': not sent,
        'message': 'Comando enviado ao desktop' if sent else 'Desktop offline, comando na fila'
    }
