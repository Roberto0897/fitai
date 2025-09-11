"""
Configurações para quando colocar ONLINE
(servidor real, usuários reais)
"""
from .base import *
import os

DEBUG = False

ALLOWED_HOSTS = ['seu-dominio.com', 'www.seu-dominio.com']

# Database para produção (PostgreSQL é mais robusto)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# CORS mais restritivo para produção
CORS_ALLOWED_ORIGINS = [
    "https://seuapp.com",
    "https://www.seuapp.com",
]

# Segurança adicional
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True