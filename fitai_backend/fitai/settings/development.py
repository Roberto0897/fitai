"""
Configurações para quando você está DESENVOLVENDO
(seu computador, testando, etc.)
"""
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Database para desenvolvimento (SQLite é mais fácil)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# 🆕 CORS - Deixa o Flutter conversar com nosso backend
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",      # React (se usar depois)
    "http://127.0.0.1:3000",      # React
    "http://localhost:8080",      # Flutter web
    "http://127.0.0.1:8080",      # Flutter web
]

# Durante desenvolvimento, pode ser mais liberal
CORS_ALLOW_ALL_ORIGINS = True  # ⚠️ APENAS para desenvolvimento!

# Para ver melhor os erros
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}