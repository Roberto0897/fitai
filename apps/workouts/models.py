from django.db import models
from django.contrib.auth.models import User
from apps.exercises.models import Exercise

class Workout(models.Model):
    # Informações básicas
    name = models.CharField(max_length=100)
    description = models.TextField()
    
    # Novas informações detalhadas (opcionais - seguro)
    difficulty_level = models.CharField(max_length=20, blank=True, null=True,
                                      choices=[
                                          ('beginner', 'Iniciante'),
                                          ('intermediate', 'Intermediário'),
                                          ('advanced', 'Avançado')
                                      ])
    estimated_duration = models.IntegerField(blank=True, null=True,
                                           help_text="Duração estimada em minutos")
    target_muscle_groups = models.CharField(max_length=200, blank=True, null=True,
                                          help_text="Grupos musculares alvo, separados por vírgula")
    equipment_needed = models.CharField(max_length=200, blank=True, null=True,
                                      help_text="Equipamentos necessários")
    calories_estimate = models.IntegerField(blank=True, null=True,
                                          help_text="Estimativa de calorias queimadas")
    workout_type = models.CharField(max_length=30, blank=True, null=True,
                                  choices=[
                                      ('strength', 'Força'),
                                      ('cardio', 'Cardio'),
                                      ('flexibility', 'Flexibilidade'),
                                      ('hiit', 'HIIT'),
                                      ('yoga', 'Yoga'),
                                      ('mixed', 'Misto')
                                  ])
    is_recommended = models.BooleanField(default=False,
                                       help_text="Se este treino é recomendado pela IA")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.difficulty_level or 'Sem dificuldade'})"

    class Meta:
        ordering = ['difficulty_level', 'name']

class WorkoutExercise(models.Model):
    """Relaciona exercícios com treinos, incluindo séries e repetições"""
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE, related_name='workout_exercises')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    
    # Configurações do exercício no treino
    sets = models.IntegerField(default=3, help_text="Número de séries")
    reps = models.CharField(max_length=20, blank=True, null=True,
                           help_text="Repetições (ex: '12', '10-15', 'até falha')")
    weight = models.FloatField(blank=True, null=True,
                             help_text="Peso em kg (opcional)")
    rest_time = models.IntegerField(blank=True, null=True,
                                  help_text="Tempo de descanso em segundos")
    order_in_workout = models.IntegerField(default=1,
                                         help_text="Ordem do exercício no treino")
    notes = models.TextField(blank=True, null=True,
                           help_text="Observações específicas")
    
    def __str__(self):
        return f"{self.workout.name} - {self.exercise.name} ({self.sets}x{self.reps})"

    class Meta:
        ordering = ['order_in_workout']

class WorkoutSession(models.Model):
    # Campos existentes
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    
    # Novos campos detalhados (opcionais - seguro)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    duration_minutes = models.IntegerField(blank=True, null=True,
                                         help_text="Duração real da sessão")
    calories_burned = models.IntegerField(blank=True, null=True,
                                        help_text="Calorias queimadas (estimativa)")
    user_rating = models.IntegerField(blank=True, null=True,
                                    choices=[(i, i) for i in range(1, 6)],
                                    help_text="Avaliação do usuário (1-5)")
    notes = models.TextField(blank=True, null=True,
                           help_text="Observações da sessão")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        status = "Completo" if self.completed else "Em andamento"
        return f"{self.user.username} - {self.workout.name} ({status})"

    class Meta:
        ordering = ['-created_at']

class ExerciseLog(models.Model):
    """Log detalhado de cada exercício durante uma sessão"""
    session = models.ForeignKey(WorkoutSession, on_delete=models.CASCADE, related_name='exercise_logs')
    workout_exercise = models.ForeignKey(WorkoutExercise, on_delete=models.CASCADE)
    
    # Dados realizados (vs planejados)
    sets_completed = models.IntegerField(default=0)
    reps_completed = models.CharField(max_length=20, blank=True, null=True)
    weight_used = models.FloatField(blank=True, null=True)
    rest_time_actual = models.IntegerField(blank=True, null=True,
                                         help_text="Tempo de descanso real em segundos")
    completed = models.BooleanField(default=False)
    skipped = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.session.user.username} - {self.workout_exercise.exercise.name}"

    class Meta:
        ordering = ['workout_exercise__order_in_workout']