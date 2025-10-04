from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from apps.workouts.models import Workout

class Recommendation(models.Model):
    """
    Recomendações de treinos feitas pela IA para cada usuário
    """
    ALGORITMO_CHOICES = [
        ('content_based', 'Baseado em Conteúdo'),
        ('collaborative', 'Colaborativo'),
        ('hybrid', 'Híbrido'),
        ('ml_personalized', 'ML Personalizado'),
    ]
    
    # Relacionamentos
    usuario = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='recommendations',
        help_text="Usuário que recebeu a recomendação"
    )
    workout_recomendado = models.ForeignKey(
        Workout, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recommendations',
        help_text="Treino recomendado pela IA"
    )
    
    # Informações da IA
    algoritmo_utilizado = models.CharField(
        max_length=20, 
        choices=ALGORITMO_CHOICES,
        help_text="Algoritmo usado para gerar a recomendação"
    )
    score_confianca = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Score de confiança da recomendação (0-1)"
    )
    motivo_recomendacao = models.TextField(
        help_text="Explicação gerada por IA do porquê desta recomendação"
    )
    
    # Controle de interação do usuário
    visualizada = models.BooleanField(
        default=False,
        help_text="Se o usuário visualizou a recomendação"
    )
    data_visualizacao = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Quando o usuário visualizou a recomendação"
    )
    aceita_pelo_usuario = models.BooleanField(
        null=True, 
        blank=True,
        default=None,
        help_text="True=aceita, False=rejeitada, None=ainda não decidiu"
    )
    data_aceite = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Quando o usuário aceitou/rejeitou"
    )
    
    # Controle temporal
    data_geracao = models.DateTimeField(
        auto_now_add=True,
        help_text="Quando a recomendação foi gerada"
    )
    expira_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Data de expiração da recomendação (opcional)"
    )
    
    def __str__(self):
        workout_name = self.workout_recomendado.name if self.workout_recomendado else "Treino Deletado"
        return f"Recomendação para {self.usuario.username} - {workout_name}"
    
    def marcar_como_visualizada(self):
        """Marca a recomendação como visualizada"""
        if not self.visualizada:
            self.visualizada = True
            self.data_visualizacao = timezone.now()
            self.save(update_fields=['visualizada', 'data_visualizacao'])
    
    def aceitar(self):
        """Marca a recomendação como aceita"""
        self.aceita_pelo_usuario = True
        self.data_aceite = timezone.now()
        self.save(update_fields=['aceita_pelo_usuario', 'data_aceite'])
    
    def rejeitar(self):
        """Marca a recomendação como rejeitada"""
        self.aceita_pelo_usuario = False
        self.data_aceite = timezone.now()
        self.save(update_fields=['aceita_pelo_usuario', 'data_aceite'])
    
    @property
    def esta_expirada(self):
        """Verifica se a recomendação expirou"""
        if self.expira_em:
            return timezone.now() > self.expira_em
        return False
    
    @property
    def taxa_confianca_percentual(self):
        """Retorna o score de confiança em percentual"""
        return f"{self.score_confianca * 100:.0f}%"
    
    class Meta:
        verbose_name = "Recomendação"
        verbose_name_plural = "Recomendações"
        ordering = ['-data_geracao']
        indexes = [
            models.Index(fields=['usuario', '-data_geracao']),
            models.Index(fields=['aceita_pelo_usuario']),
            models.Index(fields=['visualizada']),
        ]
        # Evita recomendar o mesmo treino múltiplas vezes ao mesmo usuário
        # (comentado porque pode querer recomendar o mesmo treino depois de um tempo)
        # unique_together = [['usuario', 'workout_recomendado']]