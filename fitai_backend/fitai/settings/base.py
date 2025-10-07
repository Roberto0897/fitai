# fitai/settings/base.py - CONFIGURAÇÕES COMPLETAS COM CHATBOT INTEGRADO

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
    'apps.notifications', 
    'apps.core',
    'apps.chatbot',  # 👈 CHATBOT INTEGRADO
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
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.AnonRateThrottle'
    ],
}

# CORS settings para Flutter
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

CORS_ALLOW_ALL_ORIGINS = DEBUG  # Só em desenvolvimento

"""""
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

"""
# =============================================================================
# 🤖 CONFIGURAÇÕES DE IA - GOOGLE GEMINI (substituiu OpenAI)
# =============================================================================

# Google Gemini API Configuration
GEMINI_API_KEY = config('GEMINI_API_KEY', default='')
GEMINI_MODEL = config('GEMINI_MODEL', default='gemini-2.0-flash-exp')  # Modelo mais rápido e gratuito
GEMINI_MAX_TOKENS = config('GEMINI_MAX_TOKENS', default=1000, cast=int)
GEMINI_TEMPERATURE = config('GEMINI_TEMPERATURE', default=0.7, cast=float)

# AI Features Control
AI_FEATURES_ENABLED = bool(GEMINI_API_KEY.strip())  # Só ativa se tiver API key válida
AI_FALLBACK_TO_RULES = True  # Sempre usar fallbacks quando IA indisponível

# Rate Limiting Configuration (Gemini tem limites mais generosos)
GEMINI_RATE_LIMIT_PER_MINUTE = config('GEMINI_RATE_LIMIT_PER_MINUTE', default=15, cast=int)
GEMINI_RATE_LIMIT_PER_DAY = config('GEMINI_RATE_LIMIT_PER_DAY', default=1500, cast=int)

# AI Quality & Monitoring
AI_QUALITY_THRESHOLD = config('AI_QUALITY_THRESHOLD', default=70.0, cast=float)
AI_ENABLE_METRICS = config('AI_ENABLE_METRICS', default=True, cast=bool)
AI_CACHE_TIMEOUT = config('AI_CACHE_TIMEOUT', default=3600, cast=int)

# Gemini Timeout & Retry Configuration
GEMINI_TIMEOUT_SECONDS = config('GEMINI_TIMEOUT_SECONDS', default=30, cast=int)
GEMINI_MAX_RETRIES = config('GEMINI_MAX_RETRIES', default=3, cast=int)
GEMINI_RETRY_DELAY = config('GEMINI_RETRY_DELAY', default=1.0, cast=float)

# AI Content Safety (Gemini tem filtros nativos)
AI_CONTENT_FILTERING = config('AI_CONTENT_FILTERING', default=True, cast=bool)
AI_MAX_RESPONSE_LENGTH = config('AI_MAX_RESPONSE_LENGTH', default=2000, cast=int)

# Safety Settings para Gemini
GEMINI_SAFETY_SETTINGS = {
    'HARM_CATEGORY_HARASSMENT': 'BLOCK_MEDIUM_AND_ABOVE',
    'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_MEDIUM_AND_ABOVE',
    'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_MEDIUM_AND_ABOVE',
    'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_MEDIUM_AND_ABOVE',
}


# =============================================================================
# 📊 CACHE CONFIGURATION (MELHORADA PARA IA)
# =============================================================================
"""
# Cache para desenvolvimento com Redis se disponível / implementar posteriomente caso necessario
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
"""

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'fitai_dev_cache',
    }
}

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Cache específico para IA com timeout maior
CACHE_TIMEOUTS = {
    'ai_user_context': 3600,        # 1 hora
    'ai_recommendations': 1800,     # 30 minutos
    'ai_rate_limits': 3600,         # 1 hora
    'ai_metrics_daily': 86400,      # 24 horas
    'ai_quality_scores': 7200,      # 2 horas
    'chatbot_context': 3600,        # 1 hora - contexto do chatbot
    'chatbot_analytics': 1800,      # 30 minutos - analytics do chat
}

# =============================================================================
# 🔐 LOGGING CONFIGURATION (MELHORADA COM CHATBOT)
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
        'chat_formatter': {
            'format': '[CHAT] {asctime} {levelname} {module}: {message}',
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
        'notification_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'notifications.log',
            'maxBytes': 1024*1024*5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'chatbot_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'chatbot.log',
            'maxBytes': 1024*1024*5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'chat_ai_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'chatbot_ai.log',
            'maxBytes': 1024*1024*3,  # 3 MB
            'backupCount': 3,
            'formatter': 'chat_formatter',
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
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'apps.notifications': {
            'handlers': ['console', 'notification_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.notifications.services.notification_service': {
            'handlers': ['console', 'notification_file'], 
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'apps.chatbot': {
            'handlers': ['console', 'chatbot_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.chatbot.services.chat_service': {
            'handlers': ['console', 'chatbot_file', 'chat_ai_file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
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
    'apps.chatbot.tasks.process_chat_message': {'queue': 'chat_tasks'},  # Futuras tarefas assíncronas de chat
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
# 🚦 RATE LIMITING CONFIGURATION
# =============================================================================

# Rate limiting para APIs gerais
REST_FRAMEWORK_THROTTLE_RATES = {
    'notifications': '100/hour',         # APIs básicas de notificações
    'ai_notifications': '20/hour',       # APIs que usam IA
    'notification_stats': '50/hour',     # APIs de estatísticas
    'user': '1000/hour',                 # Limite geral por usuário
    'anon': '100/hour',                  # Usuários anônimos
    
    # Rate limits específicos do chatbot
    'chatbot_start': '100/hour',          # Iniciar conversas
    'chatbot_message': '150/hour',        # Enviar mensagens
    'chatbot_history': '50/hour',        # Ver histórico
    'chatbot_analytics': '10/hour',      # Analytics do chat
}

# Atualizar REST_FRAMEWORK com throttling
REST_FRAMEWORK.update({
    'DEFAULT_THROTTLE_RATES': REST_FRAMEWORK_THROTTLE_RATES
})

# =============================================================================
# 💬 CONFIGURAÇÕES ESPECÍFICAS DO CHATBOT
# =============================================================================

# Configurações do sistema de chatbot
CHATBOT_SETTINGS = {
    'MAX_CONVERSATIONS_PER_USER': config('CHATBOT_MAX_CONVERSATIONS_PER_USER', default=10, cast=int),
    'MESSAGE_MAX_LENGTH': config('CHATBOT_MESSAGE_MAX_LENGTH', default=500, cast=int),
    'CONVERSATION_TIMEOUT_HOURS': config('CHATBOT_CONVERSATION_TIMEOUT_HOURS', default=24, cast=int),
    'MAX_CONTEXT_MESSAGES': config('CHATBOT_MAX_CONTEXT_MESSAGES', default=10, cast=int),
    'ENABLE_ANALYTICS': config('CHATBOT_ENABLE_ANALYTICS', default=True, cast=bool),
    'ENABLE_INTENT_DETECTION': True,
    'FALLBACK_TO_RULES': True,
    'AUTO_CLEANUP_DAYS': 30,  # Limpar conversas antigas automaticamente
}

# Rate limiting específico para chatbot (mais detalhado)
CHATBOT_RATE_LIMITS = {
    'start_conversation': '70/hour',       # Criar conversas
    'send_message': '200/hour',             # Enviar mensagens
    'conversation_history': '50/hour',     # Ver histórico
    'user_conversations': '20/hour',       # Listar conversas
    'end_conversation': '20/hour',         # Finalizar conversas
    'message_feedback': '40/hour',         # Dar feedback
    'chat_analytics': '10/hour',           # Ver analytics
    
    # Limites diários
    'daily_messages': '300/day',           # Mensagens por dia
    'daily_conversations': '50/day',       # Conversas por dia
}

# Tipos de conversa suportados
CHATBOT_CONVERSATION_TYPES = [
    ('workout_consultation', 'Consultoria de Treino'),
    ('technique_guidance', 'Orientação Técnica'),
    ('progress_analysis', 'Análise de Progresso'),
    ('motivation_chat', 'Chat Motivacional'),
    ('nutrition_advice', 'Orientação Nutricional'),
    ('general_fitness', 'Fitness Geral'),
]

# Configurações de qualidade das respostas
CHATBOT_QUALITY_SETTINGS = {
    'MIN_CONFIDENCE_SCORE': 0.6,
    'ENABLE_RESPONSE_VALIDATION': True,
    'MAX_RESPONSE_TIME_MS': 30000,  # 30 segundos
    'ENABLE_CONTENT_FILTERING': True,
    'LOG_LOW_CONFIDENCE_RESPONSES': True,
    'REQUIRE_USER_PROFILE_FOR_PERSONALIZATION': False,  # Funciona sem perfil completo
}

# Configurações de contexto e personalização
CHATBOT_CONTEXT_SETTINGS = {
    'ENABLE_USER_CONTEXT': True,
    'ENABLE_WORKOUT_HISTORY_CONTEXT': True,
    'ENABLE_PREFERENCE_LEARNING': True,
    'CONTEXT_RELEVANCE_THRESHOLD': 0.5,
    'MAX_CONTEXT_AGE_HOURS': 72,  # 3 dias
    'AUTO_UPDATE_USER_PREFERENCES': True,
}

# Prompts especializados por tipo de conversa
CHATBOT_SPECIALIZED_PROMPTS = {
    'workout_consultation': {
        'system_focus': 'Especialista em prescrição de exercícios baseada em evidência científica',
        'response_style': 'Técnico mas acessível, sempre priorizando segurança',
        'safety_emphasis': 'Alto',
        'max_tokens': 600,
    },
    'technique_guidance': {
        'system_focus': 'Instrutor técnico especialista em biomecânica e execução correta',
        'response_style': 'Detalhado com instruções passo-a-passo claras',
        'safety_emphasis': 'Máximo',
        'max_tokens': 700,
    },
    'progress_analysis': {
        'system_focus': 'Analista de performance e dados fitness com visão holística',
        'response_style': 'Analítico com insights motivadores e práticos',
        'safety_emphasis': 'Médio',
        'max_tokens': 500,
    },
    'motivation_chat': {
        'system_focus': 'Coach motivacional e psicólogo esportivo empático',
        'response_style': 'Encorajador, empático e genuinamente motivador',
        'safety_emphasis': 'Alto - saúde mental',
        'max_tokens': 400,
    },
    'nutrition_advice': {
        'system_focus': 'Orientações gerais, sempre recomendar nutricionista para especificidades',
        'response_style': 'Informativo com disclaimers apropriados',
        'safety_emphasis': 'Máximo - questões de saúde',
        'max_tokens': 500,
    },
    'general_fitness': {
        'system_focus': 'Personal trainer virtual completo e versátil',
        'response_style': 'Adaptativo baseado na pergunta e contexto do usuário',
        'safety_emphasis': 'Alto',
        'max_tokens': 500,
    }
}

# =============================================================================
# 📊 CONFIGURAÇÕES DE NOTIFICAÇÕES
# =============================================================================

# Configurações específicas do sistema de notificações
NOTIFICATION_SETTINGS = {
    'MAX_NOTIFICATIONS_PER_PAGE': 50,
    'DEFAULT_PAGE_SIZE': 20,
    'MAX_SCHEDULE_DAYS_AHEAD': 14,
    'MAX_STATS_PERIOD_DAYS': 90,
    'ENABLE_AI_PERSONALIZATION': True,
    'DEFAULT_NOTIFICATION_PRIORITY': 'normal',
    'AUTO_MARK_READ_AFTER_DAYS': 30,
    'CLEANUP_OLD_NOTIFICATIONS_DAYS': 90,
}

# Templates padrão que serão criados automaticamente
DEFAULT_NOTIFICATION_TEMPLATES = {
    'workout_reminder': {
        'title': 'Hora do treino, {{user_name}}!',
        'message': 'Seu corpo está pronto para mais um treino incrível. Vamos lá?',
        'variables': ['user_name', 'suggested_workout', 'last_workout_days']
    },
    'achievement': {
        'title': 'Parabéns, {{user_name}}! 🎉',
        'message': 'Você acabou de conquistar: {{achievement_name}}. Continue assim!',
        'variables': ['user_name', 'achievement_name', 'achievement_description']
    },
    'motivation': {
        'title': 'Motivação do dia, {{user_name}}',
        'message': 'Lembre-se: cada treino te deixa mais forte. Você está no caminho certo!',
        'variables': ['user_name', 'progress_percentage', 'days_active']
    },
    'progress': {
        'title': 'Seu progresso semanal, {{user_name}}',
        'message': 'Esta semana você treinou {{workouts_count}} vezes e queimou {{calories}} calorias!',
        'variables': ['user_name', 'workouts_count', 'calories', 'improvement_areas']
    },
    'chat_summary': {
        'title': 'Resumo das suas conversas fitness, {{user_name}}',
        'message': 'Esta semana você teve {{conversation_count}} conversas no chatbot. Continue explorando!',
        'variables': ['user_name', 'conversation_count', 'favorite_topic', 'satisfaction_rating']
    }
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

# Monitoramento específico do chatbot
CHATBOT_MONITORING = {
    'enable_conversation_analytics': True,
    'enable_quality_tracking': True,
    'enable_user_satisfaction_tracking': True,
    'alert_on_low_satisfaction': True,
    'satisfaction_threshold': 3.0,  # Alertar se satisfação média cair abaixo de 3.0
    'enable_intent_accuracy_tracking': True,
}

# Webhooks para alertas (opcional)
AI_ALERT_WEBHOOKS = {
    'slack_webhook': config('SLACK_WEBHOOK_URL', default=''),
    'email_alerts': config('AI_ALERT_EMAILS', default='').split(','),
    'enable_webhooks': config('ENABLE_AI_ALERTS', default=False, cast=bool),
}

# =============================================================================
# 🔒 SEGURANÇA ESPECÍFICA PARA IA E CHATBOT
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

# Validações específicas do chatbot
CHATBOT_INPUT_VALIDATION = {
    'max_message_length': 500,
    'min_message_length': 1,
    'blocked_patterns': [
        r'<script.*?>.*?</script>',  # Scripts maliciosos
        r'javascript:',  # JavaScript URLs
        r'on\w+\s*=',   # Event handlers
    ],
    'sanitize_html': True,
    'rate_limit_duplicate_messages': True,
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
    'track_chatbot_usage': True,  # Nova métrica para chatbot
    'retention_days': 90,  # Manter métricas por 90 dias
}

# Configurações de analytics
ANALYTICS_CONFIG = {
    'enable_user_journey_tracking': True,
    'enable_ab_testing': False,  # Para futuras implementações
    'enable_cohort_analysis': True,
    'enable_chatbot_conversation_analytics': True,  # Analytics específico do chat
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
    CHATBOT_SETTINGS['MAX_CONVERSATIONS_PER_USER'] = 5
    CHATBOT_RATE_LIMITS['send_message'] = '20/hour'
    
elif config('ENVIRONMENT', default='development') == 'staging':
    # Staging: configurações intermediárias
    AI_RATE_LIMIT_PER_HOUR = 40
    OPENAI_MAX_TOKENS = 700
    CHATBOT_SETTINGS['MAX_CONVERSATIONS_PER_USER'] = 8
    
else:
    # Desenvolvimento: mais permissivo
    AI_RATE_LIMIT_PER_HOUR = 100
    OPENAI_MAX_TOKENS = 1000
    AI_ENABLE_METRICS = True
    CHATBOT_SETTINGS['MAX_CONVERSATIONS_PER_USER'] = 15

# =============================================================================
# ✅ VALIDAÇÕES DE CONFIGURAÇÃO (atualizado para Gemini)
# =============================================================================

def validate_ai_configuration():
    """Valida configurações de IA no startup"""
    errors = []
    
    if AI_FEATURES_ENABLED and not GEMINI_API_KEY:
        errors.append("GEMINI_API_KEY é obrigatória quando AI_FEATURES_ENABLED=True")
    
    if GEMINI_MAX_TOKENS > 8000:
        errors.append("GEMINI_MAX_TOKENS não pode exceder 8000")
    
    if not (0.0 <= GEMINI_TEMPERATURE <= 2.0):
        errors.append("GEMINI_TEMPERATURE deve estar entre 0.0 e 2.0")
    
    if CHATBOT_SETTINGS['MESSAGE_MAX_LENGTH'] > 1000:
        errors.append("CHATBOT_MESSAGE_MAX_LENGTH não pode exceder 1000 caracteres")
    
    if errors:
        import sys
        print("❌ ERROS DE CONFIGURAÇÃO:")
        for error in errors:
            print(f"  • {error}")
        if config('STRICT_VALIDATION', default=False, cast=bool):
            sys.exit(1)
    else:
        print("✅ Configurações validadas com sucesso (Gemini + Chatbot)")

# Executar validação
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

# Chatbot Configuration
CHATBOT_MAX_CONVERSATIONS_PER_USER=10
CHATBOT_MESSAGE_MAX_LENGTH=500
CHATBOT_CONVERSATION_TIMEOUT_HOURS=24
CHATBOT_ENABLE_ANALYTICS=True

# Monitoring (opcional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
ENABLE_AI_ALERTS=False
AI_ALERT_EMAILS=admin@fitai.com,dev@fitai.com

# Security
STRICT_VALIDATION=False
"""