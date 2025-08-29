# apps/notifications/views.py - TODAS AS 12 APIs IMPLEMENTADAS
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework import status
from django.utils import timezone
from django.db.models import Count, Q, Avg
from django.core.paginator import Paginator
from datetime import datetime, timedelta
import json

from .models import NotificationPreference, NotificationLog, NotificationTemplate, UserNotificationStats
from .services.notification_service import NotificationService


# =============================================================================
# RATE LIMITING CLASSES
# =============================================================================

class NotificationRateThrottle(UserRateThrottle):
    scope = 'notifications'
    rate = '100/hour'

class AINotificationRateThrottle(UserRateThrottle):
    scope = 'ai_notifications' 
    rate = '20/hour'

class StatsRateThrottle(UserRateThrottle):
    scope = 'notification_stats'
    rate = '50/hour'


# =============================================================================
# APIs BÁSICAS (JÁ EXISTENTES - MANTIDAS)
# =============================================================================

@api_view(['GET'])
def test_notifications_api(request):
    """Teste básico da API de notificações"""
    return Response({
        "api_status": "funcionando",
        "timestamp": timezone.now().isoformat(),
        "message": "Sistema de notificações completo funcionando",
        "version": "2.0 - Expandido",
        "available_endpoints": {
            "basic": ["test/", "list/", "preferences/"],
            "advanced": ["mark_as_read/", "mark_as_clicked/", "mark_all_as_read/"],
            "smart": ["send_test_notification/", "trigger_smart_reminder/", "schedule_smart_reminders/"],
            "analytics": ["notification_stats/"]
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([NotificationRateThrottle])
def list_notifications(request):
    """Lista notificações do usuário com paginação e filtros"""
    # Parâmetros de query
    page = int(request.GET.get('page', 1))
    per_page = min(int(request.GET.get('per_page', 20)), 50)  # Máximo 50 por página
    status_filter = request.GET.get('status', 'all')
    type_filter = request.GET.get('type', 'all')
    unread_only = request.GET.get('unread_only', 'false').lower() == 'true'
    
    # Query base
    notifications = NotificationLog.objects.filter(user=request.user)
    
    # Aplicar filtros
    if status_filter != 'all':
        notifications = notifications.filter(status=status_filter)
    
    if type_filter != 'all':
        notifications = notifications.filter(notification_type=type_filter)
    
    if unread_only:
        notifications = notifications.filter(read_at__isnull=True)
    
    # Ordenação
    notifications = notifications.order_by('-created_at')
    
    # Paginação
    paginator = Paginator(notifications, per_page)
    page_obj = paginator.get_page(page)
    
    # Serializar dados
    data = []
    for notification in page_obj:
        data.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'notification_type': notification.notification_type,
            'status': notification.status,
            'priority': notification.priority,
            'is_read': notification.read_at is not None,
            'is_clicked': notification.clicked_at is not None,
            'created_at': notification.created_at.isoformat(),
            'read_at': notification.read_at.isoformat() if notification.read_at else None,
            'metadata': notification.metadata
        })
    
    return Response({
        'notifications': data,
        'pagination': {
            'current_page': page,
            'total_pages': paginator.num_pages,
            'total_items': paginator.count,
            'per_page': per_page,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous()
        },
        'summary': {
            'total_unread': NotificationLog.objects.filter(user=request.user, read_at__isnull=True).count(),
            'total_notifications': NotificationLog.objects.filter(user=request.user).count()
        }
    })


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([NotificationRateThrottle])
def manage_preferences(request):
    """Gerenciar preferências completas do usuário"""
    if request.method == 'GET':
        preferences = NotificationPreference.objects.filter(user=request.user)
        data = []
        
        for pref in preferences:
            data.append({
                'id': pref.id,
                'notification_type': pref.notification_type,
                'notification_type_display': pref.get_notification_type_display(),
                'enabled': pref.enabled,
                'frequency': pref.frequency,
                'preferred_time': pref.preferred_time.strftime('%H:%M') if pref.preferred_time else None,
                'custom_settings': pref.custom_settings,
                'created_at': pref.created_at.isoformat(),
                'updated_at': pref.updated_at.isoformat()
            })
        
        return Response({
            'preferences': data,
            'available_types': NotificationPreference.NOTIFICATION_TYPES,
            'frequency_options': [
                ('instant', 'Instantâneo'),
                ('daily', 'Diário'), 
                ('weekly', 'Semanal'),
                ('never', 'Nunca')
            ]
        })
    
    elif request.method == 'POST':
        notification_type = request.data.get('notification_type', 'general')
        enabled = request.data.get('enabled', True)
        frequency = request.data.get('frequency', 'daily')
        preferred_time = request.data.get('preferred_time')
        custom_settings = request.data.get('custom_settings', {})
        
        # Validar preferred_time se fornecido
        time_obj = None
        if preferred_time:
            try:
                time_obj = datetime.strptime(preferred_time, '%H:%M').time()
            except ValueError:
                return Response({
                    'error': 'Formato de horário inválido. Use HH:MM'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Criar ou atualizar preferência
        pref, created = NotificationPreference.objects.update_or_create(
            user=request.user,
            notification_type=notification_type,
            defaults={
                'enabled': enabled,
                'frequency': frequency,
                'preferred_time': time_obj,
                'custom_settings': custom_settings
            }
        )
        
        return Response({
            'message': 'Preferência salva com sucesso',
            'created': created,
            'preference': {
                'id': pref.id,
                'notification_type': pref.notification_type,
                'enabled': pref.enabled,
                'frequency': pref.frequency,
                'preferred_time': pref.preferred_time.strftime('%H:%M') if pref.preferred_time else None
            }
        })


# =============================================================================
# NOVAS APIs AVANÇADAS
# =============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([NotificationRateThrottle])
def mark_as_read(request):
    """Marca notificação como lida"""
    notification_id = request.data.get('notification_id')
    
    if not notification_id:
        return Response({
            'error': 'notification_id é obrigatório'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        notification = NotificationLog.objects.get(
            id=notification_id,
            user=request.user
        )
        
        notification.mark_as_read()
        
        return Response({
            'message': 'Notificação marcada como lida',
            'notification_id': notification.id,
            'read_at': notification.read_at.isoformat()
        })
        
    except NotificationLog.DoesNotExist:
        return Response({
            'error': 'Notificação não encontrada'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([NotificationRateThrottle])
def mark_as_clicked(request):
    """Marca notificação como clicada"""
    notification_id = request.data.get('notification_id')
    
    if not notification_id:
        return Response({
            'error': 'notification_id é obrigatório'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        notification = NotificationLog.objects.get(
            id=notification_id,
            user=request.user
        )
        
        # Marca como lida automaticamente se ainda não foi
        if not notification.read_at:
            notification.mark_as_read()
            
        notification.mark_as_clicked()
        
        return Response({
            'message': 'Notificação marcada como clicada',
            'notification_id': notification.id,
            'clicked_at': notification.clicked_at.isoformat()
        })
        
    except NotificationLog.DoesNotExist:
        return Response({
            'error': 'Notificação não encontrada'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([NotificationRateThrottle])
def mark_all_as_read(request):
    """Marca todas as notificações como lidas"""
    notification_type = request.data.get('notification_type', 'all')
    
    # Query base - notificações não lidas do usuário
    notifications = NotificationLog.objects.filter(
        user=request.user,
        read_at__isnull=True
    )
    
    # Filtrar por tipo se especificado
    if notification_type != 'all':
        notifications = notifications.filter(notification_type=notification_type)
    
    # Atualizar todas de uma vez
    updated_count = notifications.update(
        status='read',
        read_at=timezone.now()
    )
    
    return Response({
        'message': f'{updated_count} notificações marcadas como lidas',
        'updated_count': updated_count,
        'filter_type': notification_type
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AINotificationRateThrottle])
def send_test_notification(request):
    """Envia notificação de teste"""
    notification_type = request.data.get('notification_type', 'general')
    custom_title = request.data.get('title')
    custom_message = request.data.get('message')
    priority = request.data.get('priority', 'normal')
    
    service = NotificationService()
    
    try:
        # Criar contexto de teste
        context_data = {
            'test_mode': True,
            'timestamp': timezone.now().isoformat(),
            'source': 'api_test'
        }
        
        notification = service.create_notification(
            user=request.user,
            notification_type=notification_type,
            title=custom_title,
            message=custom_message,
            context_data=context_data,
            priority=priority,
            scheduled_for=timezone.now()  # Enviar imediatamente
        )
        
        if notification:
            return Response({
                'message': 'Notificação de teste enviada com sucesso',
                'notification_id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'created_at': notification.created_at.isoformat()
            })
        else:
            return Response({
                'message': 'Notificação bloqueada pelas suas preferências',
                'suggestion': 'Verifique suas configurações de notificação'
            })
            
    except Exception as e:
        return Response({
            'error': f'Erro ao enviar notificação: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AINotificationRateThrottle])
def trigger_smart_reminder(request):
    """Dispara lembrete inteligente baseado no contexto do usuário"""
    reminder_type = request.data.get('type', 'workout_reminder')
    context_data = request.data.get('context_data', {})
    
    service = NotificationService()
    
    try:
        if reminder_type == 'workout_reminder':
            notification = service.send_workout_reminder(request.user, context_data)
        elif reminder_type == 'motivation':
            context_type = context_data.get('context_type', 'general')
            notification = service.send_motivation_message(request.user, context_type, context_data)
        elif reminder_type == 'progress_summary':
            period = context_data.get('period', 'weekly')
            notification = service.send_progress_summary(request.user, period)
        elif reminder_type == 'comeback':
            notification = service.send_comeback_message(request.user)
        else:
            return Response({
                'error': 'Tipo de lembrete não suportado',
                'available_types': ['workout_reminder', 'motivation', 'progress_summary', 'comeback']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if notification:
            return Response({
                'message': 'Lembrete inteligente disparado',
                'reminder_type': reminder_type,
                'notification_id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'scheduled_for': notification.scheduled_for.isoformat() if notification.scheduled_for else None
            })
        else:
            return Response({
                'message': 'Lembrete não foi disparado',
                'reason': 'Condições não atendidas (ex: já treinou hoje, frequência, preferências)',
                'suggestion': 'Tente novamente mais tarde ou ajuste suas preferências'
            })
            
    except Exception as e:
        return Response({
            'error': f'Erro ao disparar lembrete: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AINotificationRateThrottle])
def schedule_smart_reminders(request):
    """Agenda lembretes inteligentes para os próximos dias"""
    days_ahead = min(int(request.data.get('days_ahead', 7)), 14)  # Máximo 14 dias
    
    service = NotificationService()
    
    try:
        service.schedule_smart_reminders(request.user, days_ahead)
        
        # Contar quantos foram agendados
        scheduled_notifications = NotificationLog.objects.filter(
            user=request.user,
            status='pending',
            scheduled_for__gt=timezone.now(),
            scheduled_for__lt=timezone.now() + timedelta(days=days_ahead)
        ).count()
        
        return Response({
            'message': 'Lembretes inteligentes agendados com sucesso',
            'days_ahead': days_ahead,
            'scheduled_count': scheduled_notifications,
            'schedule_period': f'{timezone.now().date()} até {(timezone.now() + timedelta(days=days_ahead)).date()}'
        })
        
    except Exception as e:
        return Response({
            'error': f'Erro ao agendar lembretes: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([StatsRateThrottle])
def notification_stats(request):
    """Estatísticas completas de notificações do usuário"""
    period_days = min(int(request.GET.get('period_days', 30)), 90)  # Máximo 90 dias
    
    service = NotificationService()
    
    try:
        # Estatísticas básicas
        basic_stats = service.get_user_notification_summary(request.user, period_days)
        
        # Estatísticas do modelo UserNotificationStats
        user_stats, created = UserNotificationStats.objects.get_or_create(
            user=request.user
        )
        
        # Análise temporal das últimas notificações
        cutoff_date = timezone.now() - timedelta(days=period_days)
        recent_notifications = NotificationLog.objects.filter(
            user=request.user,
            created_at__gte=cutoff_date
        )
        
        # Estatísticas por hora do dia
        hourly_stats = {}
        for hour in range(24):
            count = recent_notifications.filter(created_at__hour=hour).count()
            hourly_stats[f"{hour:02d}:00"] = count
        
        # Estatísticas por dia da semana
        daily_stats = {}
        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for i, day in enumerate(weekdays):
            count = recent_notifications.filter(created_at__week_day=i+2).count()  # Django week_day começa com domingo=1
            daily_stats[day] = count
        
        # Top tipos de notificação
        type_stats = list(recent_notifications.values('notification_type').annotate(
            count=Count('id')
        ).order_by('-count')[:5])
        
        return Response({
            'period_analyzed': f'{period_days} days',
            'basic_statistics': basic_stats,
            'user_statistics': {
                'total_sent': user_stats.total_sent,
                'total_delivered': user_stats.total_delivered,
                'total_read': user_stats.total_read,
                'total_clicked': user_stats.total_clicked,
                'delivery_rate': round(user_stats.delivery_rate * 100, 1),
                'read_rate': round(user_stats.read_rate * 100, 1),
                'click_rate': round(user_stats.click_rate * 100, 1),
                'engagement_score': round(user_stats.engagement_score * 100, 1),
                'best_engagement_hour': user_stats.best_engagement_hour,
                'last_interaction': user_stats.last_interaction.isoformat() if user_stats.last_interaction else None
            },
            'temporal_analysis': {
                'hourly_distribution': hourly_stats,
                'daily_distribution': daily_stats
            },
            'top_notification_types': type_stats,
            'recommendations': {
                'optimal_send_time': f"{user_stats.best_engagement_hour or 9}:00",
                'engagement_level': 'High' if user_stats.engagement_score > 0.7 else 'Medium' if user_stats.engagement_score > 0.4 else 'Low',
                'suggested_frequency': user_stats.preferred_frequency or 'daily'
            }
        })
        
    except Exception as e:
        return Response({
            'error': f'Erro ao calcular estatísticas: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# API DE TEMPLATES (BONUS)
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([NotificationRateThrottle])
def list_templates(request):
    """Lista templates de notificação disponíveis"""
    templates = NotificationTemplate.objects.filter(is_active=True)
    
    data = []
    for template in templates:
        data.append({
            'id': template.id,
            'name': template.name,
            'notification_type': template.notification_type,
            'title_template': template.title_template,
            'message_template': template.message_template,
            'priority': template.priority,
            'variables': template.variables,
            'usage_count': template.usage_count
        })
    
    return Response({
        'templates': data,
        'count': len(data)
    })


# =============================================================================
# API DE HEALTH CHECK
# =============================================================================

@api_view(['GET'])
def health_check(request):
    """Health check para monitoramento"""
    try:
        # Verificar banco de dados
        recent_notifications = NotificationLog.objects.count()
        active_templates = NotificationTemplate.objects.filter(is_active=True).count()
        
        # Verificar service
        service = NotificationService()
        ai_available = service.ai_service and service.ai_service.is_available if service.ai_service else False
        
        return Response({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'database': 'connected',
            'recent_notifications_count': recent_notifications,
            'active_templates_count': active_templates,
            'ai_service_available': ai_available,
            'version': '2.0'
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)