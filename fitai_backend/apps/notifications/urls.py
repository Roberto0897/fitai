# apps/notifications/urls.py - VERSÃO TEMPORÁRIA SIMPLIFICADA
from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Apenas APIs básicas para testar
    path('test/', views.test_notifications_api, name='test'),
    path('list/', views.list_notifications, name='list'),
    path('preferences/', views.manage_preferences, name='preferences'),
]