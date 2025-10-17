from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime

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
    
    
    # ============================================================
    # 🆕 NOVOS CAMPOS - APENAS 6 ESSENCIAIS
    # ============================================================
    
    # Frequência de treino
    training_frequency = models.IntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(7)],
        help_text="Quantos dias por semana quer treinar"
    )
    
    # Dias preferidos (sistema aprende automaticamente)
    preferred_training_days = models.JSONField(
        default=list,
        blank=True,
        help_text="[0=Dom, 1=Seg, 2=Ter, 3=Qua, 4=Qui, 5=Sex, 6=Sáb]"
    )
    
    # Descanso mínimo
    min_rest_days_between_workouts = models.IntegerField(
        default=1,
        validators=[MinValueValidator(0), MaxValueValidator(3)],
        help_text="Dias de descanso entre treinos"
    )

    # 🆕 NOVO: Horário preferido de treino
    preferred_workout_time = models.CharField(
        max_length=20,
        default='flexible',
        choices=[
            ('morning', 'Manhã'),
            ('afternoon', 'Tarde'),
            ('evening', 'Noite'),
            ('flexible', 'Flexível'),
        ],
        help_text="Período do dia preferido para treino"
    )

    # 🆕 NOVO: Limitações Físicas (texto livre)
    physical_limitations = models.TextField(
        blank=True,
        help_text="Quaisquer lesões, dores ou restrições físicas"
    )
    
    # Padrão aprendido (IA preenche automaticamente)
    learned_training_pattern = models.JSONField(
        default=dict,
        blank=True,
        help_text="Padrão detectado automaticamente pelo sistema"
    )
    
    last_pattern_analysis = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Última atualização do padrão"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # ============================================================
    # 🔧 MÉTODOS ÚTEIS (apenas 3 essenciais)
    # ============================================================
    
    def should_rest_today(self, last_workout_date=None):
        """
        Verifica se deve descansar hoje
        """
        if not last_workout_date:
            return False
        
        from datetime import datetime
        days_since = (datetime.now().date() - last_workout_date).days
        return days_since < self.min_rest_days_between_workouts
    
    def is_preferred_training_day(self, weekday=None):
        """
        Verifica se hoje é dia preferido
        weekday: 0=Domingo, 6=Sábado
        """
        from datetime import datetime
        
        if not self.preferred_training_days:
            return True  # Se vazio, qualquer dia é válido
        
        if weekday is None:
            weekday = datetime.now().weekday()
            weekday = (weekday + 1) % 7  # Converter para 0=Domingo
        
        return weekday in self.preferred_training_days
    
    def is_preferred_rest_day(self, weekday=None):
        """
        Verifica se hoje é dia de descanso preferido
        
        Lógica: Se preferred_training_days estiver configurado,
        qualquer dia que NÃO esteja na lista é considerado dia de descanso.
        
        Args:
            weekday: Dia da semana (0=Domingo, 1=Segunda, ..., 6=Sábado)
                    Se None, usa o dia atual
        
        Returns:
            bool: True se é dia de descanso, False caso contrário
        
        Exemplos:
            >>>profile.preferred_training_days = [1, 3, 5]  # Seg, Qua, Sex
            >>>profile.is_preferred_rest_day(0)  # Domingo
            True
            >>>profile.is_preferred_rest_day(1)  # Segunda
            False
        """
    # Se não configurou dias preferidos, não força descanso
        if not self.preferred_training_days:
            return False
        
        # Se não passou weekday, pega o dia atual
        if weekday is None:
            weekday = datetime.now().weekday()
            # Converter Python (0=Seg) para nosso padrão (0=Dom)
            weekday = (weekday + 1) % 7
        
        # Se NÃO está nos dias de treino = é dia de descanso
        return weekday not in self.preferred_training_days 
    
    def calculate_bmi(self):
        """Calcula IMC"""
        if self.current_weight and self.height:
            height_m = self.height / 100
            return round(self.current_weight / (height_m ** 2), 1)
        return None
    
    def get_bmi_status(self):
        """Retorna status do IMC"""
        bmi = self.calculate_bmi()
        if not bmi:
            return None
        
        if bmi < 18.5:
            return 'Abaixo do peso'
        elif bmi < 25:
            return 'Peso normal'
        elif bmi < 30:
            return 'Sobrepeso'
        else:
            return 'Obesidade'
        
    def __str__(self):
        return f"Perfil - {self.user.username}"
    
    class Meta:
        verbose_name = "Perfil do Usuário"
        verbose_name_plural = "Perfis dos Usuários"

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
    
    