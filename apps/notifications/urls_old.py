# apps/notifications/urls.py - MAPEAMENTO COMPLETO DAS 12 APIs
from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # =============================================================================
    # APIs BÁSICAS
    # =============================================================================
    path('test/', views.test_notifications_api, name='test'),
    path('health/', views.health_check, name='health_check'),
    path('list/', views.list_notifications, name='list'),
    path('preferences/', views.manage_preferences, name='preferences'),
    
    # =============================================================================
    # APIs DE ENGAJAMENTO
    # =============================================================================
    path('mark_as_read/', views.mark_as_read, name='mark_as_read'),
    path('mark_as_clicked/', views.mark_as_clicked, name='mark_as_clicked'),
    path('mark_all_as_read/', views.mark_all_as_read, name='mark_all_as_read'),
    
    # =============================================================================
    # APIs INTELIGENTES
    # =============================================================================
    path('send_test_notification/', views.send_test_notification, name='send_test_notification'),
    path('trigger_smart_reminder/', views.trigger_smart_reminder, name='trigger_smart_reminder'),
    path('schedule_smart_reminders/', views.schedule_smart_reminders, name='schedule_smart_reminders'),
    
    # =============================================================================
    # APIs DE ANALYTICS
    # =============================================================================
    path('notification_stats/', views.notification_stats, name='notification_stats'),
    
    # =============================================================================
    # APIs DE TEMPLATES (BONUS)
    # =============================================================================
    path('templates/', views.list_templates, name='list_templates'),
]

"""
=============================================================================
ENDPOINTS FINAIS DISPONÍVEIS:
=============================================================================

1. /api/v1/notifications/test/                    - GET  - Teste da API
2. /api/v1/notifications/health/                  - GET  - Health check
3. /api/v1/notifications/list/                    - GET  - Listar notificações (paginado)
4. /api/v1/notifications/preferences/             - GET/POST - Gerenciar preferências
5. /api/v1/notifications/mark_as_read/             - POST - Marcar como lida
6. /api/v1/notifications/mark_as_clicked/          - POST - Marcar como clicada
7. /api/v1/notifications/mark_all_as_read/         - POST - Marcar todas como lidas
8. /api/v1/notifications/send_test_notification/   - POST - Enviar teste
9. /api/v1/notifications/trigger_smart_reminder/   - POST - Lembrete inteligente
10. /api/v1/notifications/schedule_smart_reminders/ - POST - Agendar lembretes
11. /api/v1/notifications/notification_stats/       - GET  - Estatísticas completas
12. /api/v1/notifications/templates/                - GET  - Listar templates

=============================================================================
RATE LIMITING CONFIGURADO:
=============================================================================

- notifications: 100/hour (endpoints básicos)
- ai_notifications: 20/hour (endpoints com IA)
- notification_stats: 50/hour (endpoints de analytics)

=============================================================================
EXEMPLOS DE USO:
=============================================================================

# Listar notificações com filtros:
GET /api/v1/notifications/list/?page=1&per_page=10&unread_only=true&type=workout_reminder

# Marcar como lida:
POST /api/v1/notifications/mark_as_read/
{
    "notification_id": 123
}

# Enviar lembrete inteligente:
POST /api/v1/notifications/trigger_smart_reminder/
{
    "type": "workout_reminder",
    "context_data": {
        "suggested_workout": "Full Body Beginner"
    }
}

# Configurar preferências:
POST /api/v1/notifications/preferences/
{
    "notification_type": "workout_reminder",
    "enabled": true,
    "frequency": "daily",
    "preferred_time": "08:00"
}

# Estatísticas detalhadas:
GET /api/v1/notifications/notification_stats/?period_days=30
"""