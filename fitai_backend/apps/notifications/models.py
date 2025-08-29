# apps/notifications/models.py - VERSÃO EXPANDIDA
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json

class NotificationPreference(models.Model):
    """Preferências de notificação do usuário - EXPANDIDO"""
    NOTIFICATION_TYPES = [
        ('workout_reminder', 'Lembrete de Treino'),
        ('progress_update', 'Atualização de Progresso'),
        ('achievement', 'Conquistas'),
        ('motivational', 'Mensagens Motivacionais'),
        ('system', 'Notificações do Sistema'),
        ('general', 'Geral'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_preferences')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    enabled = models.BooleanField(default=True)
    
    # NOVOS CAMPOS AVANÇADOS
    preferred_time = models.TimeField(null=True, blank=True, help_text="Horário preferido para notificações")
    frequency = models.CharField(max_length=20, default='daily', choices=[
        ('instant', 'Instantâneo'),
        ('daily', 'Diário'),
        ('weekly', 'Semanal'),
        ('never', 'Nunca')
    ])
    custom_settings = models.JSONField(default=dict, blank=True, help_text="Configurações personalizadas JSON")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'notifications'
        unique_together = ['user', 'notification_type']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_notification_type_display()}"
    
    def is_active_now(self):
        """Verifica se notificação deve ser enviada agora baseado nas preferências"""
        if not self.enabled:
            return False
        
        if self.preferred_time:
            current_time = timezone.now().time()
            # Permite margem de 30 minutos
            return abs((current_time.hour * 60 + current_time.minute) - 
                      (self.preferred_time.hour * 60 + self.preferred_time.minute)) <= 30
        
        return True


class NotificationLog(models.Model):
    """Log de notificações enviadas - EXPANDIDO"""
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('sent', 'Enviada'),
        ('delivered', 'Entregue'),
        ('read', 'Lida'),
        ('clicked', 'Clicada'),
        ('failed', 'Falhou'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Baixa'),
        ('normal', 'Normal'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # NOVOS CAMPOS AVANÇADOS  
    notification_type = models.CharField(max_length=50)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    template_id = models.IntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True, help_text="Dados extras da notificação")
    
    # TRACKING DE ENGAJAMENTO
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    
    # CONTROLE
    scheduled_for = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    retry_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['notification_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def mark_as_read(self):
        """Marca notificação como lida"""
        if self.status in ['sent', 'delivered']:
            self.status = 'read'
            self.read_at = timezone.now()
            self.save(update_fields=['status', 'read_at', 'updated_at'])
    
    def mark_as_clicked(self):
        """Marca notificação como clicada"""
        if self.status == 'read':
            self.clicked_at = timezone.now()
            self.save(update_fields=['clicked_at', 'updated_at'])
    
    @property
    def is_expired(self):
        """Verifica se notificação expirou"""
        return self.expires_at and timezone.now() > self.expires_at


class NotificationTemplate(models.Model):
    """Templates reutilizáveis para notificações - NOVO MODEL"""
    name = models.CharField(max_length=100, unique=True)
    notification_type = models.CharField(max_length=50)
    title_template = models.CharField(max_length=200, help_text="Use {{variavel}} para placeholders")
    message_template = models.TextField(help_text="Use {{variavel}} para placeholders") 
    
    # CONFIGURAÇÕES DO TEMPLATE
    priority = models.CharField(max_length=10, choices=NotificationLog.PRIORITY_CHOICES, default='normal')
    is_active = models.BooleanField(default=True)
    variables = models.JSONField(default=list, help_text="Lista de variáveis disponíveis")
    
    # METADADOS
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    usage_count = models.IntegerField(default=0)
    
    class Meta:
        app_label = 'notifications'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.notification_type})"
    
    def render(self, context=None):
        """Renderiza template com variáveis"""
        if not context:
            context = {}
        
        title = self.title_template
        message = self.message_template
        
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            title = title.replace(placeholder, str(value))
            message = message.replace(placeholder, str(value))
        
        return title, message
    
    def increment_usage(self):
        """Incrementa contador de uso"""
        self.usage_count += 1
        self.save(update_fields=['usage_count', 'updated_at'])


class UserNotificationStats(models.Model):
    """Estatísticas de engajamento por usuário - NOVO MODEL"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_stats')
    
    # CONTADORES GERAIS
    total_sent = models.IntegerField(default=0)
    total_delivered = models.IntegerField(default=0)  
    total_read = models.IntegerField(default=0)
    total_clicked = models.IntegerField(default=0)
    total_failed = models.IntegerField(default=0)
    
    # MÉTRICAS POR TIPO
    stats_by_type = models.JSONField(default=dict, blank=True)
    
    # PADRÕES TEMPORAIS
    best_engagement_hour = models.IntegerField(null=True, blank=True)
    avg_time_to_read = models.DurationField(null=True, blank=True)
    last_interaction = models.DateTimeField(null=True, blank=True)
    
    # PREFERÊNCIAS CALCULADAS
    preferred_frequency = models.CharField(max_length=20, null=True, blank=True)
    engagement_score = models.FloatField(default=0.0, help_text="Score de 0-1 baseado no engajamento")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'notifications'
    
    def __str__(self):
        return f"Stats: {self.user.username}"
    
    @property
    def delivery_rate(self):
        """Taxa de entrega"""
        return (self.total_delivered / self.total_sent) if self.total_sent > 0 else 0
    
    @property  
    def read_rate(self):
        """Taxa de leitura"""
        return (self.total_read / self.total_delivered) if self.total_delivered > 0 else 0
    
    @property
    def click_rate(self):
        """Taxa de cliques"""
        return (self.total_clicked / self.total_read) if self.total_read > 0 else 0
    
    def update_stats(self, notification_log):
        """Atualiza estatísticas baseado em uma notificação"""
        # Incrementa contadores baseado no status
        if notification_log.status == 'sent':
            self.total_sent += 1
        elif notification_log.status == 'delivered':
            self.total_delivered += 1
        elif notification_log.status == 'read':
            self.total_read += 1
        elif notification_log.status == 'clicked':
            self.total_clicked += 1
        elif notification_log.status == 'failed':
            self.total_failed += 1
        
        # Atualiza stats por tipo
        notif_type = notification_log.notification_type
        if notif_type not in self.stats_by_type:
            self.stats_by_type[notif_type] = {'sent': 0, 'read': 0, 'clicked': 0}
        
        if notification_log.status in ['sent', 'delivered']:
            self.stats_by_type[notif_type]['sent'] += 1
        elif notification_log.status == 'read':
            self.stats_by_type[notif_type]['read'] += 1
        elif notification_log.status == 'clicked':
            self.stats_by_type[notif_type]['clicked'] += 1
        
        # Calcula engagement score
        total_interactions = self.total_read + self.total_clicked
        self.engagement_score = (total_interactions / self.total_sent) if self.total_sent > 0 else 0
        
        # Atualiza última interação
        if notification_log.status in ['read', 'clicked']:
            self.last_interaction = timezone.now()
        
        self.save()