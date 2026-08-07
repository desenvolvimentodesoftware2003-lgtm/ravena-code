import os
import secrets


class Config:
    SECRET_KEY = os.environ.get('RAVENA_SECRET_KEY', secrets.token_hex(32))

    JWT_EXPIRATION_DAYS = 90
    JWT_ALGORITHM = 'HS256'

    DATABASE_URL = os.environ.get(
        'DATABASE_URL',
        'postgresql://ravena:password@localhost:5432/ravena'
    )
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

    TLS_CERT = os.environ.get('RAVENA_TLS_CERT', '/etc/ravena/ssl/cert.pem')
    TLS_KEY = os.environ.get('RAVENA_TLS_KEY', '/etc/ravena/ssl/key.pem')

    PORT = int(os.environ.get('RAVENA_WEB_PORT', 443))
    HOST = os.environ.get('RAVENA_WEB_HOST', '0.0.0.0')

    RATE_LIMIT = 100
    RATE_WINDOW = 60

    DB_POOL_MIN = 2
    DB_POOL_MAX = 10

    WS_PING_INTERVAL = 25
    WS_PING_TIMEOUT = 10
