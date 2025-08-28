# =====================================
# apps/notifications/admin.py
# =====================================
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    NotificationPreference, 
    NotificationLog, 
    NotificationTemplate, 
    UserNotificationStats
)


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'notification_type', 'delivery_channel', 
        'enabled', 'frequency_days', 'preferred_time', 'created_at'
    ]
    list_filter = [
        'notification_type', 'delivery_channel', 'enabled', 
        'preferred_time', 'only_on_inactive_days'
    ]
    search_fields = ['user__username', 'user__email']
    list_editable = ['enabled', 'frequency_days']
    
    fieldsets = (
        ('Usuário e Tipo', {
            'fields': ('user', 'notification_type', 'delivery_channel')
        }),
        ('Configurações Básicas', {
            'fields': ('enabled', 'frequency_days', 'preferred_time', 'custom_time')
        }),
        ('Configurações Avançadas', {
            'fields': ('only_on_inactive_days', 'respect_rest_days'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'notification_type', 'title', 'status_badge', 
        'delivery_channel', 'scheduled_for', 'engagement_info'
    ]
    list_filter = [
        'status', 'notification_type', 'delivery_channel', 
        'priority', 'created_at'
    ]
    search_fields = ['user__username', 'title', 'message']
    readonly_fields = [
        'created_at', 'updated_at', 'sent_at', 'delivered_at', 
        'opened_at', 'clicked_at', 'engagement_level'
    ]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('user', 'notification_type', 'title', 'message')
        }),
        ('Configurações de Entrega', {
            'fields': ('delivery_channel', 'priority', 'scheduled_for')
        }),
        ('Status e Rastreamento', {
            'fields': (
                'status', 'external_id', 'error_message', 'retry_count'
            )
        }),
        ('Timestamps', {
            'fields': (
                'sent_at', 'delivered_at', 'opened_at', 'clicked_at'
            ),
            'classes': ('collapse',)
        }),
        ('Dados Contextuais', {
            'fields': ('context_data',),
            'classes': ('collapse',)
        })
    )
    
    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'sent': 'blue', 
            'delivered': 'green',
            'opened': 'purple',
            'clicked': 'darkgreen',
            'failed': 'red',
            'cancelled': 'gray'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def engagement_info(self, obj):
        if obj.clicked_at:
            return format_html('<span style="color: green;">✓ Clicada</span>')
        elif obj.opened_at:
            return format_html('<span style="color: blue;">◐ Aberta</span>')
        elif obj.delivered_at:
            return format_html('<span style="color: orange;">◑ Entregue</span>')
        else:
            return format_html('<span style="color: gray;">○ Pendente</span>')
    engagement_info.short_description = 'Engajamento'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'preference')


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'notification_type', 'name', 'priority', 'delivery_channel', 
        'active', 'usage_count', 'created_at'
    ]
    list_filter = ['notification_type', 'priority', 'delivery_channel', 'active']
    search_fields = ['name', 'description', 'title_template']
    list_editable = ['active', 'priority']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('notification_type', 'name', 'description')
        }),
        ('Templates', {
            'fields': ('title_template', 'message_template'),
            'description': 'Use {{variavel}} para substituições dinâmicas'
        }),
        ('Configurações', {
            'fields': ('priority', 'delivery_channel', 'active')
        }),
        ('Condições de Uso', {
            'fields': ('conditions',),
            'classes': ('collapse',),
            'description': 'JSON com condições para usar este template'
        }),
        ('Estatísticas', {
            'fields': ('usage_count',),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        """Validar JSON antes de salvar"""
        super().save_model(request, obj, form, change)


@admin.register(UserNotificationStats)
class UserNotificationStatsAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'total_notifications_received', 'open_rate_display', 
        'click_rate_display', 'engagement_level', 'most_engaging_type'
    ]
    list_filter = ['engagement_level', 'most_engaging_type']
    search_fields = ['user__username']
    readonly_fields = [
        'total_notifications_received', 'total_notifications_opened', 
        'total_notifications_clicked', 'open_rate', 'click_rate',
        'engagement_level', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Usuário', {
            'fields': ('user',)
        }),
        ('Contadores Gerais', {
            'fields': (
                'total_notifications_received', 'total_notifications_opened', 
                'total_notifications_clicked'
            )
        }),
        ('Contadores por Tipo', {
            'fields': (
                'workout_reminders_sent', 'achievements_sent', 'motivational_sent'
            )
        }),
        ('Métricas de Engajamento', {
            'fields': (
                'open_rate', 'click_rate', 'engagement_level',
                'last_notification_opened', 'last_notification_clicked'
            )
        }),
        ('Preferências Implícitas', {
            'fields': (
                'best_time_to_notify', 'most_engaging_type', 'least_engaging_type'
            ),
            'classes': ('collapse',)
        })
    )
    
    def open_rate_display(self, obj):
        rate = obj.open_rate
        if rate >= 50:
            color = 'green'
        elif rate >= 25:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>', color, rate
        )
    open_rate_display.short_description = 'Taxa Abertura'
    
    def click_rate_display(self, obj):
        rate = obj.click_rate
        if rate >= 15:
            color = 'green'
        elif rate >= 5:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>', color, rate
        )
    click_rate_display.short_description = 'Taxa Clique'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


# Configurações do admin site
admin.site.site_header = "FitAI - Administração"
admin.site.site_title = "FitAI Admin"
admin.site.index_title = "Sistema de Administração FitAI"


# =====================================
# ATUALIZAÇÃO NECESSÁRIA NO settings.py
# =====================================
"""
Adicionar no INSTALLED_APPS:

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Novos apps que instalamos
    'rest_framework',
    'corsheaders',
    # Nossos apps
    'apps.users',
    'apps.exercises',
    'apps.workouts',
    'apps.recommendations',
    'apps.notifications',  # ← ADICIONAR ESTA LINHA
    'apps.core',
]
"""