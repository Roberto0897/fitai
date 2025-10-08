from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    # Campos existentes
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    
    # Campos de onboarding (todos opcionais - seguro)
    goal = models.CharField(max_length=50, blank=True, null=True, 
                           choices=[
                               ('lose_weight', 'Perder Peso'),
                               ('gain_muscle', 'Ganhar Músculo'),
                               ('maintain', 'Manter Forma'),
                               ('endurance', 'Melhorar Resistência')
                           ])
    activity_level = models.CharField(max_length=20, blank=True, null=True,
                                    choices=[
                                        ('sedentary', 'Sedentário'),
                                        ('light', 'Leve'),
                                        ('moderate', 'Moderado'),
                                        ('active', 'Ativo'),
                                        ('very_active', 'Muito Ativo')
                                    ])
    focus_areas = models.CharField(max_length=200, blank=True, null=True,
                                 help_text="Áreas de foco separadas por vírgula")
    current_weight = models.FloatField(blank=True, null=True)
    target_weight = models.FloatField(blank=True, null=True)

    # tres campos novos
    age = models.IntegerField(null=True, blank=True, verbose_name='Idade')
    gender = models.CharField(max_length=1, null=True, blank=True, 
                              choices=[('M', 'Masculino'), ('F', 'Feminino'), ('O', 'Outro')],
                              verbose_name='Sexo')
    height = models.FloatField(null=True, blank=True, verbose_name='Altura (cm)')
    
    def __str__(self):
        return f"Perfil - {self.user.username}"

class UserProgress(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    total_workouts = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Progresso - {self.user.username}"

class DailyTip(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title