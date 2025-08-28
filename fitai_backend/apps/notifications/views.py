# apps/notifications/views.py - VERSÃO TEMPORÁRIA SIMPLIFICADA
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

from .models import NotificationPreference, NotificationLog

@api_view(['GET'])
def test_notifications_api(request):
    """Teste básico da API de notificações"""
    return Response({
        "api_status": "funcionando",
        "timestamp": timezone.now().isoformat(),
        "message": "Sistema de notificações básico funcionando"
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_notifications(request):
    """Lista notificações básicas do usuário"""
    notifications = NotificationLog.objects.filter(user=request.user)[:10]
    
    data = []
    for notif in notifications:
        data.append({
            'id': notif.id,
            'title': notif.title,
            'message': notif.message,
            'status': notif.status,
            'created_at': notif.created_at.isoformat()
        })
    
    return Response({
        'notifications': data,
        'total': len(data)
    })

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def manage_preferences(request):
    """Gerenciar preferências básicas"""
    if request.method == 'GET':
        prefs = NotificationPreference.objects.filter(user=request.user)
        data = []
        for pref in prefs:
            data.append({
                'id': pref.id,
                'notification_type': pref.notification_type,
                'enabled': pref.enabled,
                'created_at': pref.created_at.isoformat()
            })
        return Response({'preferences': data})
    
    elif request.method == 'POST':
        notification_type = request.data.get('notification_type', 'general')
        enabled = request.data.get('enabled', True)
        
        pref, created = NotificationPreference.objects.get_or_create(
            user=request.user,
            notification_type=notification_type,
            defaults={'enabled': enabled}
        )
        
        if not created:
            pref.enabled = enabled
            pref.save()
        
        return Response({
            'message': 'Preferência salva',
            'preference': {
                'id': pref.id,
                'notification_type': pref.notification_type,
                'enabled': pref.enabled
            }
        })