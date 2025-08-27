from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
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
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    workout_recomendado = models.ForeignKey(Workout, on_delete=models.CASCADE)
    
    # Informações da IA
    algoritmo_utilizado = models.CharField(max_length=20, choices=ALGORITMO_CHOICES)
    score_confianca = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(1)])
    motivo_recomendacao = models.TextField(help_text="Explicação gerada por IA")
    
    # Controle temporal
    data_geracao = models.DateTimeField(auto_now_add=True)
    aceita_pelo_usuario = models.BooleanField(null=True, blank=True)
    data_aceite = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Recomendação para {self.usuario.username} - {self.workout_recomendado.nome}"
    
    class Meta:
        verbose_name = "Recomendação"
        verbose_name_plural = "Recomendações"