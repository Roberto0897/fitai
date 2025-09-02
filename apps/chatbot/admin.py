# apps/chatbot/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import Conversation, Message, ChatContext, ChatMetrics


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user_display', 'title_short', 'conversation_type', 
        'status', 'message_count', 'ai_responses_count', 
        'satisfaction_display', 'created_at', 'last_activity_at'
    ]
    list_filter = [
        'conversation_type', 'status', 'created_at', 
        'user_satisfaction_rating'
    ]
    search_fields = ['user__username', 'user__email', 'title']
    readonly_fields = [
        'message_count', 'ai_responses_count', 'total_tokens_used',
        'average_response_time', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('user', 'title', 'conversation_type', 'status')
        }),
        ('Contexto', {
            'fields': ('user_goal_context', 'current_focus'),
            'classes': ('collapse',)
        }),
        ('Métricas', {
            'fields': (
                'message_count', 'ai_responses_count', 'user_satisfaction_rating',
                'total_tokens_used', 'average_response_time'
            ),
            'classes': ('collapse',)
        }),
        ('IA e Metadados', {
            'fields': ('ai_model_used', 'expires_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_activity_at'),
            'classes': ('collapse',)
        })
    )
    
    def user_display(self, obj):
        return f"{obj.user.username} ({obj.user.get_full_name()})"
    user_display.short_description = 'Usuário'
    
    def title_short(self, obj):
        return obj.title[:50] + "..." if len(obj.title) > 50 else obj.title
    title_short.short_description = 'Título'
    
    def satisfaction_display(self, obj):
        if obj.user_satisfaction_rating:
            rating = obj.user_satisfaction_rating
            color = 'green' if rating >= 4 else 'orange' if rating >= 3 else 'red'
            stars = '⭐' * int(rating)
            return format_html(
                '<span style="color: {};">{} ({})</span>',
                color, stars, rating
            )
        return '-'
    satisfaction_display.short_description = 'Satisfação'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'conversation_display', 'message_type', 'content_preview',
        'intent_detected', 'confidence_score', 'user_reaction', 
        'response_time_ms', 'created_at'
    ]
    list_filter = [
        'message_type', 'status', 'user_reaction', 
        'intent_detected', 'created_at'
    ]
    search_fields = [
        'content', 'conversation__title', 
        'conversation__user__username', 'intent_detected'
    ]
    readonly_fields = [
        'conversation', 'message_type', 'content', 'status',
        'intent_detected', 'confidence_score', 'ai_model_version',
        'response_time_ms', 'tokens_used', 'created_at', 'processed_at'
    ]
    
    fieldsets = (
        ('Informações da Mensagem', {
            'fields': ('conversation', 'message_type', 'content', 'status')
        }),
        ('Análise de IA', {
            'fields': (
                'intent_detected', 'confidence_score', 
                'ai_model_version', 'response_time_ms', 'tokens_used'
            ),
            'classes': ('collapse',)
        }),
        ('Feedback do Usuário', {
            'fields': ('user_reaction', 'user_feedback'),
            'classes': ('collapse',)
        }),
        ('Referências', {
            'fields': ('referenced_workout_id', 'referenced_exercise_id'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'processed_at'),
            'classes': ('collapse',)
        })
    )
    
    def conversation_display(self, obj):
        return f"Conv #{obj.conversation.id} - {obj.conversation.user.username}"
    conversation_display.short_description = 'Conversa'
    
    def content_preview(self, obj):
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Conteúdo'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'conversation', 'conversation__user'
        )


@admin.register(ChatContext)
class ChatContextAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'conversation_display', 'context_type', 'context_key',
        'relevance_score', 'expires_at', 'updated_at'
    ]
    list_filter = ['context_type', 'relevance_score', 'expires_at', 'created_at']
    search_fields = [
        'conversation__user__username', 'context_key', 'context_type'
    ]
    readonly_fields = ['conversation', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Informações do Contexto', {
            'fields': ('conversation', 'context_type', 'context_key')
        }),
        ('Dados', {
            'fields': ('context_value', 'relevance_score', 'expires_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def conversation_display(self, obj):
        return f"Conv #{obj.conversation.id} - {obj.conversation.user.username}"
    conversation_display.short_description = 'Conversa'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'conversation', 'conversation__user'
        )


@admin.register(ChatMetrics)
class ChatMetricsAdmin(admin.ModelAdmin):
    list_display = [
        'user_display', 'date', 'conversations_started',
        'total_messages_sent', 'ai_responses_received',
        'satisfaction_display', 'engagement_score'
    ]
    list_filter = ['date', 'average_satisfaction_rating']
    search_fields = ['user__username', 'user__email']
    readonly_fields = [
        'user', 'date', 'conversations_started', 'total_messages_sent',
        'ai_responses_received', 'average_satisfaction_rating',
        'positive_feedback_count', 'negative_feedback_count',
        'average_conversation_length', 'average_session_duration',
        'total_tokens_consumed', 'average_ai_response_time',
        'ai_confidence_average', 'most_common_intent',
        'workout_recommendations_given', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Usuário e Período', {
            'fields': ('user', 'date')
        }),
        ('Métricas de Uso', {
            'fields': (
                'conversations_started', 'total_messages_sent', 
                'ai_responses_received', 'average_conversation_length',
                'average_session_duration'
            )
        }),
        ('Métricas de Qualidade', {
            'fields': (
                'average_satisfaction_rating', 'positive_feedback_count',
                'negative_feedback_count'
            ),
            'classes': ('collapse',)
        }),
        ('Métricas de IA', {
            'fields': (
                'total_tokens_consumed', 'average_ai_response_time',
                'ai_confidence_average', 'most_common_intent',
                'workout_recommendations_given'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def user_display(self, obj):
        return f"{obj.user.username} ({obj.user.get_full_name()})"
    user_display.short_description = 'Usuário'
    
    def satisfaction_display(self, obj):
        if obj.average_satisfaction_rating:
            rating = obj.average_satisfaction_rating
            color = 'green' if rating >= 4 else 'orange' if rating >= 3 else 'red'
            return format_html(
                '<span style="color: {};">{:.1f}/5.0</span>',
                color, rating
            )
        return '-'
    satisfaction_display.short_description = 'Satisfação Média'
    
    def engagement_score(self, obj):
        # Calcular score de engajamento baseado nas métricas
        base_score = min(obj.conversations_started * 10, 50)  # Max 50 pts
        message_score = min(obj.total_messages_sent * 2, 30)  # Max 30 pts
        quality_score = 0
        
        if obj.average_satisfaction_rating:
            quality_score = obj.average_satisfaction_rating * 4  # Max 20 pts
        
        total_score = base_score + message_score + quality_score
        color = 'green' if total_score >= 80 else 'orange' if total_score >= 50 else 'red'
        
        return format_html(
            '<span style="color: {};">{:.0f}/100</span>',
            color, total_score
        )
    engagement_score.short_description = 'Engajamento'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


# Personalizar o admin site
admin.site.site_header = "FitAI - Administração do Chatbot"
admin.site.site_title = "FitAI Chatbot Admin"
admin.site.index_title = "Gerenciamento do Sistema de Chat"