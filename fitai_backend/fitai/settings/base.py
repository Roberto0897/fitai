# settings/base.py - CONFIGURAÇÕES COMPLETAS CORRIGIDAS

# Importações necessárias
import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-sua-chave-secreta-aqui-mude-depois')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost').split(',')

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',           
    'rest_framework.authtoken', 
    'corsheaders',              
]

LOCAL_APPS = [
    'apps.users',
    'apps.exercises', 
    'apps.workouts',
    'apps.recommendations',
    'apps.core',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',        
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'fitai.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'fitai.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files (uploads de usuários)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# CORS settings para Flutter
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

CORS_ALLOW_ALL_ORIGINS = DEBUG  # Só em desenvolvimento

# =============================================================================
# 🤖 CONFIGURAÇÕES DE IA E OPENAI
# =============================================================================

# OpenAI API Configuration
OPENAI_API_KEY = config('OPENAI_API_KEY', default='')
OPENAI_MODEL = config('OPENAI_MODEL', default='gpt-3.5-turbo')
OPENAI_MAX_TOKENS = config('OPENAI_MAX_TOKENS', default=800, cast=int)
OPENAI_TEMPERATURE = config('OPENAI_TEMPERATURE', default=0.7, cast=float)

# AI Features Control
AI_FEATURES_ENABLED = bool(OPENAI_API_KEY.strip())  # Só ativa se tiver API key válida
AI_FALLBACK_TO_RULES = True  # Sempre usar fallbacks quando IA indisponível

# Rate Limiting Configuration
OPENAI_RATE_LIMIT_PER_HOUR = config('OPENAI_RATE_LIMIT_PER_HOUR', default=50, cast=int)
OPENAI_RATE_LIMIT_PER_DAY = config('OPENAI_RATE_LIMIT_PER_DAY', default=500, cast=int)

# AI Quality & Monitoring
AI_QUALITY_THRESHOLD = config('AI_QUALITY_THRESHOLD', default=70.0, cast=float)
AI_ENABLE_METRICS = config('AI_ENABLE_METRICS', default=True, cast=bool)
AI_CACHE_TIMEOUT = config('AI_CACHE_TIMEOUT', default=3600, cast=int)  # 1 hora

# OpenAI Timeout & Retry Configuration
OPENAI_TIMEOUT_SECONDS = config('OPENAI_TIMEOUT_SECONDS', default=30, cast=int)
OPENAI_MAX_RETRIES = config('OPENAI_MAX_RETRIES', default=3, cast=int)
OPENAI_RETRY_DELAY = config('OPENAI_RETRY_DELAY', default=1.0, cast=float)

# AI Content Safety
AI_CONTENT_FILTERING = config('AI_CONTENT_FILTERING', default=True, cast=bool)
AI_MAX_RESPONSE_LENGTH = config('AI_MAX_RESPONSE_LENGTH', default=2000, cast=int)

# =============================================================================
# 📊 CACHE CONFIGURATION (MELHORADA PARA IA)
# =============================================================================

# Cache para desenvolvimento com Redis se disponível
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/1'),
        'TIMEOUT': 300,  # 5 minutos default
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'fitai_cache',
        'VERSION': 1,
    } if config('REDIS_URL', default='') else {
        # Fallback para cache em memória se Redis não disponível
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'fitai_cache',
        'TIMEOUT': 300,
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
            'CULL_FREQUENCY': 3,
        }
    }
}

# Cache específico para IA com timeout maior
CACHE_TIMEOUTS = {
    'ai_user_context': 3600,        # 1 hora
    'ai_recommendations': 1800,     # 30 minutos
    'ai_rate_limits': 3600,         # 1 hora
    'ai_metrics_daily': 86400,      # 24 horas
    'ai_quality_scores': 7200,      # 2 horas
}

# =============================================================================
# 🔐 LOGGING CONFIGURATION (MELHORADA)
# =============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'ai_formatter': {
            'format': '[AI] {asctime} {levelname} {module}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'ai_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'ai_service.log',
            'maxBytes': 1024*1024*5,  # 5 MB
            'backupCount': 5,
            'formatter': 'ai_formatter',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'apps.recommendations.services.ai_service': {
            'handlers': ['console', 'ai_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.recommendations': {
            'handlers': ['console'],
            'level': 'DEBUG' if config('DEBUG', default=False, cast=bool) else 'INFO',
            'propagate': False,
        },
    },
}

# Criar diretório de logs se não existir
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

# =============================================================================
# ⚙️ CELERY CONFIGURATION (PARA TAREFAS ASSÍNCRONAS DE IA)
# =============================================================================

# Celery Configuration (para processamento assíncrono de IA no futuro)
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/2')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/2')

CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TIMEZONE = 'America/Sao_Paulo'
CELERY_ENABLE_UTC = True

# Tarefas específicas de IA
CELERY_ROUTES = {
    'apps.recommendations.tasks.generate_ai_recommendations': {'queue': 'ai_tasks'},
    'apps.recommendations.tasks.analyze_user_progress': {'queue': 'ai_tasks'},
}

# =============================================================================
# 🎯 CONFIGURAÇÕES ESPECÍFICAS DE RECOMENDAÇÕES
# =============================================================================

# Algoritmos de recomendação disponíveis
RECOMMENDATION_ALGORITHMS = {
    'ai_personalized': {
        'name': 'IA Personalizada',
        'description': 'Recomendações geradas por inteligência artificial',
        'requires_ai': True,
        'weight': 0.4
    },
    'content_based': {
        'name': 'Baseado em Conteúdo',
        'description': 'Baseado no perfil e histórico do usuário',
        'requires_ai': False,
        'weight': 0.3
    },
    'collaborative': {
        'name': 'Filtragem Colaborativa',
        'description': 'Baseado em usuários similares',
        'requires_ai': False,
        'weight': 0.2
    },
    'hybrid': {
        'name': 'Híbrido',
        'description': 'Combina todos os algoritmos disponíveis',
        'requires_ai': False,
        'weight': 0.1
    }
}

# Configurações de qualidade das recomendações
RECOMMENDATION_CONFIG = {
    'min_confidence_score': 0.6,
    'max_recommendations_per_request': 10,
    'enable_learning': True,
    'enable_feedback_collection': True,
    'cache_recommendations': True,
}

# =============================================================================
# 🚨 MONITORAMENTO E ALERTAS
# =============================================================================

# Configurações de monitoramento
AI_MONITORING = {
    'enable_performance_tracking': True,
    'enable_error_tracking': True,
    'enable_usage_tracking': True,
    'alert_on_high_error_rate': True,
    'alert_threshold_errors_per_hour': 10,
    'alert_threshold_response_time_ms': 5000,
}

# Webhooks para alertas (opcional)
AI_ALERT_WEBHOOKS = {
    'slack_webhook': config('SLACK_WEBHOOK_URL', default=''),
    'email_alerts': config('AI_ALERT_EMAILS', default='').split(','),
    'enable_webhooks': config('ENABLE_AI_ALERTS', default=False, cast=bool),
}

# =============================================================================
# 🔒 SEGURANÇA ESPECÍFICA PARA IA
# =============================================================================

# Rate limiting para endpoints de IA
AI_RATE_LIMITS = {
    'generate_workout': '10/hour',
    'analyze_progress': '20/hour',
    'motivational_message': '30/hour',
    'personalized_recommendations': '50/hour',
}

# Validação de entrada para IA
AI_INPUT_VALIDATION = {
    'max_prompt_length': 2000,
    'allowed_contexts': ['workout_start', 'workout_complete', 'weekly_review', 'goal_reminder'],
    'sanitize_user_input': True,
    'block_suspicious_prompts': True,
}

# =============================================================================
# 📈 MÉTRICAS E ANALYTICS
# =============================================================================

# Configurações de métricas
METRICS_CONFIG = {
    'track_ai_usage': True,
    'track_recommendation_acceptance': True,
    'track_workout_completion': True,
    'track_user_engagement': True,
    'retention_days': 90,  # Manter métricas por 90 dias
}

# Configurações de analytics
ANALYTICS_CONFIG = {
    'enable_user_journey_tracking': True,
    'enable_ab_testing': False,  # Para futuras implementações
    'enable_cohort_analysis': True,
    'daily_reports': True,
}

# =============================================================================
# 🌍 CONFIGURAÇÕES ESPECÍFICAS DO BRASIL
# =============================================================================

# Localização brasileira
USE_L10N = True
USE_TZ = True
TIME_ZONE = 'America/Sao_Paulo'
LANGUAGE_CODE = 'pt-br'

# Formatação brasileira
DATE_FORMAT = 'd/m/Y'
TIME_FORMAT = 'H:i'
DATETIME_FORMAT = 'd/m/Y H:i'

# Moeda brasileira para futuros recursos premium
CURRENCY_CODE = 'BRL'
CURRENCY_SYMBOL = 'R$'

# =============================================================================
# 🔧 CONFIGURAÇÕES PARA DIFERENTES AMBIENTES
# =============================================================================

# Configurações que podem variar por ambiente
if config('ENVIRONMENT', default='development') == 'production':
    # Produção: mais restritivo
    AI_RATE_LIMIT_PER_HOUR = 30
    OPENAI_MAX_TOKENS = 600
    AI_CACHE_TIMEOUT = 7200  # 2 horas
    
elif config('ENVIRONMENT', default='development') == 'staging':
    # Staging: configurações intermediárias
    AI_RATE_LIMIT_PER_HOUR = 40
    OPENAI_MAX_TOKENS = 700
    
else:
    # Desenvolvimento: mais permissivo
    AI_RATE_LIMIT_PER_HOUR = 100
    OPENAI_MAX_TOKENS = 1000
    AI_ENABLE_METRICS = True

# =============================================================================
# ✅ VALIDAÇÕES DE CONFIGURAÇÃO
# =============================================================================

# Validar configurações críticas
def validate_ai_configuration():
    """Valida configurações de IA no startup"""
    errors = []
    
    if AI_FEATURES_ENABLED and not OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY é obrigatória quando AI_FEATURES_ENABLED=True")
    
    if OPENAI_MAX_TOKENS > 4000:
        errors.append("OPENAI_MAX_TOKENS não pode exceder 4000")
    
    if not (0.0 <= OPENAI_TEMPERATURE <= 2.0):
        errors.append("OPENAI_TEMPERATURE deve estar entre 0.0 e 2.0")
    
    if errors:
        import sys
        print("❌ ERROS DE CONFIGURAÇÃO DE IA:")
        for error in errors:
            print(f"  • {error}")
        if config('STRICT_VALIDATION', default=False, cast=bool):
            sys.exit(1)
    else:
        print("✅ Configurações de IA validadas com sucesso")

# Executar validação se não estiver em testes
import sys
if 'test' not in sys.argv and 'migrate' not in sys.argv:
    validate_ai_configuration()

# =============================================================================
# 📝 EXEMPLO DE ARQUIVO .env PARA REFERÊNCIA
# =============================================================================

"""
# Adicione estas variáveis ao seu arquivo .env:

# OpenAI Configuration
OPENAI_API_KEY=sk-sua_chave_openai_aqui
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_MAX_TOKENS=800
OPENAI_TEMPERATURE=0.7

# Environment
ENVIRONMENT=development  # development, staging, production

# Cache & Performance
REDIS_URL=redis://127.0.0.1:6379/1
CELERY_BROKER_URL=redis://localhost:6379/2

# Rate Limiting
OPENAI_RATE_LIMIT_PER_HOUR=50

# Monitoring (opcional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
ENABLE_AI_ALERTS=False
AI_ALERT_EMAILS=admin@fitai.com,dev@fitai.com

# Security
STRICT_VALIDATION=False
"""