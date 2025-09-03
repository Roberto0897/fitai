# apps/chatbot/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta

class Conversation(models.Model):
    """
    Representa uma conversa de chatbot com contexto persistente
    """
    CONVERSATION_STATUS_CHOICES = [
        ('active', 'Ativa'),
        ('paused', 'Pausada'),
        ('completed', 'Finalizada'),
        ('archived', 'Arquivada'),
    ]
    
    CONVERSATION_TYPE_CHOICES = [
        ('workout_consultation', 'Consulta de Treino'),
        ('nutrition_advice', 'Orientação Nutricional'),
        ('progress_analysis', 'Análise de Progresso'),
        ('motivation_chat', 'Chat Motivacional'),
        ('technique_guidance', 'Orientação Técnica'),
        ('general_fitness', 'Fitness Geral'),
    ]
    
    # Relacionamentos
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chatbot_conversations')
    
    # Informações da conversa
    title = models.CharField(max_length=200, help_text="Título automático gerado")
    conversation_type = models.CharField(max_length=30, choices=CONVERSATION_TYPE_CHOICES, default='general_fitness')
    status = models.CharField(max_length=20, choices=CONVERSATION_STATUS_CHOICES, default='active')
    
    # Contexto personalizado
    user_goal_context = models.CharField(max_length=50, blank=True, null=True, help_text="Objetivo específico desta conversa")
    current_focus = models.CharField(max_length=100, blank=True, null=True, help_text="Foco atual da discussão")
    
    # Métricas e controle
    message_count = models.PositiveIntegerField(default=0)
    ai_responses_count = models.PositiveIntegerField(default=0)
    user_satisfaction_rating = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)],
        help_text="Avaliação do usuário (1-5)"
    )
    
    # Controle temporal
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Conversa expira automaticamente")
    
    # Metadados de IA
    ai_model_used = models.CharField(max_length=50, blank=True, null=True)
    total_tokens_used = models.PositiveIntegerField(default=0)
    average_response_time = models.FloatField(default=0.0, help_text="Tempo médio de resposta da IA em segundos")
    
    def save(self, *args, **kwargs):
        # Auto-gerar título se não fornecido
        if not self.title:
            self.title = f"Chat {self.get_conversation_type_display()} - {timezone.now().strftime('%d/%m/%Y')}"
        
        # Auto-definir expiração (7 dias de inatividade)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """Verifica se a conversa expirou"""
        return timezone.now() > self.expires_at if self.expires_at else False
    
    def extend_expiration(self, days=7):
        """Estende prazo de expiração"""
        self.expires_at = timezone.now() + timedelta(days=days)
        self.save(update_fields=['expires_at'])
    
    def get_last_messages(self, limit=10):
        """Retorna últimas mensagens para contexto"""
        return self.messages.order_by('-created_at')[:limit]
    
    def update_activity(self):
        """Atualiza timestamp de última atividade"""
        self.last_activity_at = timezone.now()
        self.extend_expiration()
        self.save(update_fields=['last_activity_at', 'expires_at'])
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    class Meta:
        verbose_name = "Conversa de Chat"
        verbose_name_plural = "Conversas de Chat"
        ordering = ['-last_activity_at']


class Message(models.Model):
    """
    Representa uma mensagem individual no chat
    """
    MESSAGE_TYPE_CHOICES = [
        ('user', 'Usuário'),
        ('ai', 'IA'),
        ('system', 'Sistema'),
    ]
    
    MESSAGE_STATUS_CHOICES = [
        ('sent', 'Enviada'),
        ('processing', 'Processando'),
        ('delivered', 'Entregue'),
        ('failed', 'Falhou'),
        ('retrying', 'Tentando Novamente'),
    ]
    
    # Relacionamentos
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    
    # Conteúdo da mensagem
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES)
    content = models.TextField(help_text="Conteúdo da mensagem")
    status = models.CharField(max_length=20, choices=MESSAGE_STATUS_CHOICES, default='sent')
    
    # Contexto específico da mensagem
    intent_detected = models.CharField(max_length=100, blank=True, null=True, help_text="Intenção detectada pela IA")
    confidence_score = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Confiança da IA na resposta (0-1)"
    )
    
    # Métricas de IA (apenas para mensagens de IA)
    ai_model_version = models.CharField(max_length=50, blank=True, null=True)
    response_time_ms = models.PositiveIntegerField(null=True, blank=True, help_text="Tempo de resposta em milissegundos")
    tokens_used = models.PositiveIntegerField(null=True, blank=True, help_text="Tokens consumidos")
    
    # Feedback do usuário
    user_reaction = models.CharField(
        max_length=20, blank=True, null=True,
        choices=[
            ('helpful', 'Útil'),
            ('not_helpful', 'Não Útil'),
            ('excellent', 'Excelente'),
            ('needs_improvement', 'Precisa Melhorar'),
        ]
    )
    user_feedback = models.TextField(blank=True, null=True, help_text="Feedback detalhado do usuário")
    
    # Controle temporal
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Referências externas (para recomendações de treinos/exercícios)
    referenced_workout_id = models.PositiveIntegerField(null=True, blank=True, help_text="ID do treino referenciado")
    referenced_exercise_id = models.PositiveIntegerField(null=True, blank=True, help_text="ID do exercício referenciado")
    
    def save(self, *args, **kwargs):
        # Atualizar contador de mensagens na conversa
        if not self.pk:  # Apenas em criação
            conversation = self.conversation
            conversation.message_count += 1
            if self.message_type == 'ai':
                conversation.ai_responses_count += 1
            conversation.update_activity()
        
        super().save(*args, **kwargs)
    
    def mark_as_processed(self):
        """Marca mensagem como processada"""
        self.status = 'delivered'
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'processed_at'])
    
    def add_user_feedback(self, reaction, feedback=None):
        """Adiciona feedback do usuário"""
        self.user_reaction = reaction
        if feedback:
            self.user_feedback = feedback
        self.save(update_fields=['user_reaction', 'user_feedback'])
    
    def get_context_summary(self):
        """Resumo da mensagem para contexto"""
        return {
            'type': self.message_type,
            'content_preview': self.content[:100] + "..." if len(self.content) > 100 else self.content,
            'intent': self.intent_detected,
            'confidence': self.confidence_score,
            'timestamp': self.created_at.isoformat()
        }
    
    def __str__(self):
        return f"{self.get_message_type_display()}: {self.content[:50]}..."
    
    class Meta:
        verbose_name = "Mensagem"
        verbose_name_plural = "Mensagens"
        ordering = ['created_at']


class ChatContext(models.Model):
    """
    Contexto dinâmico e histórico da conversa para personalização da IA
    """
    CONTEXT_TYPE_CHOICES = [
        ('user_profile', 'Perfil do Usuário'),
        ('workout_history', 'Histórico de Treinos'),
        ('preferences', 'Preferências'),
        ('progress_data', 'Dados de Progresso'),
        ('conversation_summary', 'Resumo da Conversa'),
        ('external_references', 'Referências Externas'),
    ]
    
    # Relacionamentos
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='context_data')
    
    # Tipo e conteúdo do contexto
    context_type = models.CharField(max_length=30, choices=CONTEXT_TYPE_CHOICES)
    context_key = models.CharField(max_length=100, help_text="Chave identificadora do contexto")
    context_value = models.JSONField(help_text="Dados do contexto em formato JSON")
    
    # Controle de relevância
    relevance_score = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Relevância deste contexto (0-1)"
    )
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Quando este contexto expira")
    
    # Controle temporal
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @classmethod
    def set_context(cls, conversation, context_type, key, value, relevance=1.0):
        """Método helper para definir contexto"""
        context, created = cls.objects.get_or_create(
            conversation=conversation,
            context_type=context_type,
            context_key=key,
            defaults={
                'context_value': value,
                'relevance_score': relevance
            }
        )
        
        if not created:
            context.context_value = value
            context.relevance_score = relevance
            context.updated_at = timezone.now()
            context.save()
        
        return context
    
    @classmethod
    def get_context(cls, conversation, context_type=None, key=None):
        """Recupera contexto específico"""
        queryset = cls.objects.filter(conversation=conversation)
        
        if context_type:
            queryset = queryset.filter(context_type=context_type)
        if key:
            queryset = queryset.filter(context_key=key)
        
        # Filtrar contextos não expirados
        queryset = queryset.filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
        )
        
        return queryset.order_by('-relevance_score', '-updated_at')
    
    def is_expired(self):
        """Verifica se contexto expirou"""
        return self.expires_at and timezone.now() > self.expires_at
    
    def __str__(self):
        return f"{self.get_context_type_display()}: {self.context_key}"
    
    class Meta:
        verbose_name = "Contexto do Chat"
        verbose_name_plural = "Contextos do Chat"
        unique_together = ['conversation', 'context_type', 'context_key']


class ChatMetrics(models.Model):
    """
    Métricas agregadas para análise e melhorias do sistema de chat
    """
    # Relacionamentos
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Período das métricas
    date = models.DateField(default=timezone.now)
    
    # Métricas de uso
    conversations_started = models.PositiveIntegerField(default=0)
    total_messages_sent = models.PositiveIntegerField(default=0)
    ai_responses_received = models.PositiveIntegerField(default=0)
    
    # Métricas de qualidade
    average_satisfaction_rating = models.FloatField(null=True, blank=True)
    positive_feedback_count = models.PositiveIntegerField(default=0)
    negative_feedback_count = models.PositiveIntegerField(default=0)
    
    # Métricas de engajamento
    average_conversation_length = models.FloatField(default=0.0, help_text="Número médio de mensagens por conversa")
    average_session_duration = models.FloatField(default=0.0, help_text="Duração média em minutos")
    
    # Métricas de IA
    total_tokens_consumed = models.PositiveIntegerField(default=0)
    average_ai_response_time = models.FloatField(default=0.0, help_text="Tempo médio em segundos")
    ai_confidence_average = models.FloatField(null=True, blank=True)
    
    # Tópicos mais discutidos
    most_common_intent = models.CharField(max_length=100, blank=True, null=True)
    workout_recommendations_given = models.PositiveIntegerField(default=0)
    
    # Controle temporal
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @classmethod
    def update_daily_metrics(cls, user, date=None):
        """Atualiza métricas diárias para um usuário"""
        if not date:
            date = timezone.now().date()
        
        # Buscar conversas do dia
        conversations = Conversation.objects.filter(
            user=user,
            created_at__date=date
        )
        
        messages = Message.objects.filter(
            conversation__user=user,
            created_at__date=date
        )
        
        ai_messages = messages.filter(message_type='ai')
        user_messages = messages.filter(message_type='user')
        
        # Calcular métricas
        metrics, created = cls.objects.get_or_create(
            user=user,
            date=date,
            defaults={
                'conversations_started': conversations.count(),
                'total_messages_sent': user_messages.count(),
                'ai_responses_received': ai_messages.count(),
            }
        )
        
        if not created:
            metrics.conversations_started = conversations.count()
            metrics.total_messages_sent = user_messages.count()
            metrics.ai_responses_received = ai_messages.count()
        
        # Calcular métricas de qualidade
        rated_conversations = conversations.filter(user_satisfaction_rating__isnull=False)
        if rated_conversations.exists():
            metrics.average_satisfaction_rating = rated_conversations.aggregate(
                avg_rating=models.Avg('user_satisfaction_rating')
            )['avg_rating']
        
        # Métricas de feedback
        metrics.positive_feedback_count = messages.filter(
            user_reaction__in=['helpful', 'excellent']
        ).count()
        
        metrics.negative_feedback_count = messages.filter(
            user_reaction__in=['not_helpful', 'needs_improvement']
        ).count()
        
        # Métricas de IA
        ai_with_tokens = ai_messages.filter(tokens_used__isnull=False)
        if ai_with_tokens.exists():
            metrics.total_tokens_consumed = ai_with_tokens.aggregate(
                total_tokens=models.Sum('tokens_used')
            )['total_tokens'] or 0
            
            metrics.average_ai_response_time = ai_messages.filter(
                response_time_ms__isnull=False
            ).aggregate(
                avg_time=models.Avg('response_time_ms')
            )['avg_time'] or 0.0
            
            metrics.average_ai_response_time /= 1000  # Converter para segundos
        
        metrics.save()
        return metrics
    
    def __str__(self):
        return f"Métricas {self.user.username} - {self.date}"
    
    class Meta:
        verbose_name = "Métricas do Chat"
        verbose_name_plural = "Métricas do Chat"
        unique_together = ['user', 'date']