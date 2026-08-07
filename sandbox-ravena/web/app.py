import ssl
import eventlet
eventlet.monkey_patch()

from flask import Flask
from flask_socketio import SocketIO

from config import Config
from routes import api
from websocket import handle_connect, handle_disconnect, handle_desktop_connect, handle_desktop_disconnect, send_to_desktop, broadcast
from auth import close_db

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY

socketio = SocketIO(
    app,
    cors_allowed_origins='*',
    async_mode='eventlet',
    ping_interval=Config.WS_PING_INTERVAL,
    ping_timeout=Config.WS_PING_TIMEOUT
)

app.register_blueprint(api)


@app.teardown_appcontext
def teardown(exception):
    close_db(exception)


@socketio.on('connect')
def on_connect():
    from flask import request
    client_id = request.sid
    handle_connect({'id': client_id, 'socket': None})


@socketio.on('disconnect')
def on_disconnect():
    from flask import request
    handle_disconnect(request.sid)


@socketio.on('desktop_connect')
def on_desktop_connect():
    from flask import request
    client_id = request.sid
    handle_desktop_connect({'id': client_id, 'socket': None})


@socketio.on('desktop_disconnect')
def on_desktop_disconnect():
    handle_desktop_disconnect()


@socketio.on('command')
def on_command(data):
    from flask import request
    command = data.get('command', '')
    target = data.get('target', '')
    result = send_to_desktop({
        'type': 'command',
        'action': command,
        'target': target
    })
    return {'sent': result}


@socketio.on('result')
def on_result(data):
    broadcast({
        'type': 'result',
        'data': data
    })


@socketio.on('status_update')
def on_status_update(data):
    broadcast({
        'type': 'status_update',
        'data': data
    })


def create_ssl_context():
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_3
    ctx.load_cert_chain(Config.TLS_CERT, Config.TLS_KEY)
    return ctx


if __name__ == '__main__':
    ssl_ctx = create_ssl_context()
    socketio.run(
        app,
        host=Config.HOST,
        port=Config.PORT,
        ssl_context=ssl_ctx,
        debug=False
    )
