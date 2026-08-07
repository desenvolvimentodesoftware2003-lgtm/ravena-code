from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
import psycopg2
import psycopg2.extras
from flask import request, jsonify, g

from config import Config


def get_db():
    if 'db' not in g:
        g.db = psycopg2.connect(Config.DATABASE_URL)
        g.db.autocommit = True
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def login(username: str, password: str) -> dict | None:
    db = get_db()
    with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT id, username, password_hash, role FROM users WHERE username = %s",
            (username,)
        )
        user = cur.fetchone()

    if not user:
        return None

    with db.cursor() as cur:
        cur.execute(
            "SELECT (password_hash = crypt(%s, password_hash)) AS match FROM users WHERE id = %s",
            (password, user['id'])
        )
        result = cur.fetchone()
        if not result or not result[0]:
            return None

    return {
        'id': user['id'],
        'username': user['username'],
        'role': user['role']
    }


def generate_token(user_id: int, username: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        'sub': user_id,
        'username': username,
        'role': role,
        'iat': now,
        'exp': now + timedelta(days=Config.JWT_EXPIRATION_DAYS)
    }
    return jwt.encode(payload, Config.SECRET_KEY, algorithm=Config.JWT_ALGORITHM)


def verify_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token, Config.SECRET_KEY, algorithms=[Config.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token ausente'}), 401

        token = auth_header.split(' ', 1)[1]
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Token inválido ou expirado'}), 401

        g.user = payload
        return f(*args, **kwargs)
    return decorated


def require_admin(f):
    @wraps(f)
    @require_auth
    def decorated(*args, **kwargs):
        if g.user.get('role') != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        return f(*args, **kwargs)
    return decorated
