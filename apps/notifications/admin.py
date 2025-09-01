# apps/notifications/admin.py - CORRIGIDO PARA MODELS EXPANDIDOS
from django.contrib import admin
from django.utils.html import format_html
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
        'user', 'notification_type', 'enabled', 
        'frequency', 'preferred_time', 'created_at'
    ]
    list_filter = [
        'notification_type', 'enabled', 'frequency', 'created_at'
    ]
    search_fields = ['user__username', 'user__email', 'notification_type']
    list_editable = ['enabled', 'frequency']
    
    fieldsets = (
        ('Usuário e Tipo', {
            'fields': ('user', 'notification_type')
        }),
        ('Configurações Básicas', {
            'fields': ('enabled', 'frequency', 'preferred_time')
        }),
        ('Configurações Avançadas', {
            'fields': ('custom_settings',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'notification_type', 'title', 'status_badge', 
        'priority', 'created_at', 'engagement_info'
    ]
    list_filter = [
        'status', 'notification_type', 'priority', 'created_at'
    ]
    search_fields = ['user__username', 'title', 'message']
    readonly_fields = [
        'created_at', 'updated_at', 'sent_at', 'delivered_at', 
        'read_at', 'clicked_at'
    ]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('user', 'notification_type', 'title', 'message')
        }),
        ('Configurações', {
            'fields': ('status', 'priority', 'template_id')
        }),
        ('Agendamento', {
            'fields': ('scheduled_for', 'expires_at', 'retry_count')
        }),
        ('Tracking de Engajamento', {
            'fields': ('sent_at', 'delivered_at', 'read_at', 'clicked_at'),
            'classes': ('collapse',)
        }),
        ('Dados Extras', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'sent': 'blue', 
            'delivered': 'green',
            'read': 'purple',
            'clicked': 'darkgreen',
            'failed': 'red'
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
        elif obj.read_at:
            return format_html('<span style="color: blue;">◐ Lida</span>')
        elif obj.delivered_at:
            return format_html('<span style="color: orange;">◑ Entregue</span>')
        elif obj.sent_at:
            return format_html('<span style="color: lightblue;">◒ Enviada</span>')
        else:
            return format_html('<span style="color: gray;">○ Pendente</span>')
    engagement_info.short_description = 'Engajamento'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'notification_type', 'priority', 'is_active', 
        'usage_count', 'created_at'
    ]
    list_filter = ['notification_type', 'priority', 'is_active', 'created_at']
    search_fields = ['name', 'notification_type', 'title_template']
    list_editable = ['is_active', 'priority']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'notification_type', 'priority', 'is_active')
        }),
        ('Templates', {
            'fields': ('title_template', 'message_template'),
            'description': 'Use {{variavel}} para substituições dinâmicas'
        }),
        ('Variáveis Disponíveis', {
            'fields': ('variables',),
            'classes': ('collapse',),
            'description': 'Lista JSON das variáveis disponíveis para este template'
        }),
        ('Metadados', {
            'fields': ('created_by', 'usage_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
    
    def save_model(self, request, obj, form, change):
        if not change:  # Criando novo template
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(UserNotificationStats)
class UserNotificationStatsAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'total_sent', 'delivery_rate_display', 
        'read_rate_display', 'engagement_score_display', 'last_interaction'
    ]
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = [
        'total_sent', 'total_delivered', 'total_read', 'total_clicked', 'total_failed',
        'delivery_rate', 'read_rate', 'click_rate', 'engagement_score',
        'stats_by_type', 'best_engagement_hour', 'avg_time_to_read',
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Usuário', {
            'fields': ('user',)
        }),
        ('Contadores Gerais', {
            'fields': (
                'total_sent', 'total_delivered', 'total_read', 
                'total_clicked', 'total_failed'
            )
        }),
        ('Taxas Calculadas', {
            'fields': ('delivery_rate', 'read_rate', 'click_rate', 'engagement_score')
        }),
        ('Estatísticas por Tipo', {
            'fields': ('stats_by_type',),
            'classes': ('collapse',)
        }),
        ('Padrões Comportamentais', {
            'fields': (
                'best_engagement_hour', 'avg_time_to_read', 
                'last_interaction', 'preferred_frequency'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def delivery_rate_display(self, obj):
        rate = obj.delivery_rate * 100
        if rate >= 90:
            color = 'green'
        elif rate >= 70:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>', color, rate
        )
    delivery_rate_display.short_description = 'Taxa Entrega'
    
    def read_rate_display(self, obj):
        rate = obj.read_rate * 100
        if rate >= 50:
            color = 'green'
        elif rate >= 25:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>', color, rate
        )
    read_rate_display.short_description = 'Taxa Leitura'
    
    def engagement_score_display(self, obj):
        score = obj.engagement_score * 100
        if score >= 70:
            color = 'green'
        elif score >= 40:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>', color, score
        )
    engagement_score_display.short_description = 'Score Engajamento'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    def has_add_permission(self, request):
        # Stats são criadas automaticamente, não manualmente
        return False


# Configurações do admin site
admin.site.site_header = "FitAI - Sistema de Notificações"
admin.site.site_title = "FitAI Admin"
admin.site.index_title = "Administração de Notificações"