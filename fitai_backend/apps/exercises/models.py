from django.db import models

class Exercise(models.Model):
    # Informações básicas
    name = models.CharField(max_length=100)
    description = models.TextField()
    
    # Novas informações detalhadas (todas opcionais - seguro)
    muscle_group = models.CharField(max_length=50, blank=True, null=True,
                                  choices=[
                                      ('chest', 'Peito'),
                                      ('back', 'Costas'),
                                      ('shoulders', 'Ombros'),
                                      ('arms', 'Braços'),
                                      ('legs', 'Pernas'),
                                      ('abs', 'Abdômen'),
                                      ('cardio', 'Cardio'),
                                      ('full_body', 'Corpo Inteiro')
                                  ])
    difficulty_level = models.CharField(max_length=20, blank=True, null=True,
                                      choices=[
                                          ('beginner', 'Iniciante'),
                                          ('intermediate', 'Intermediário'),
                                          ('advanced', 'Avançado')
                                      ])
    equipment_needed = models.CharField(max_length=100, blank=True, null=True,
                                      help_text="Equipamentos necessários, separados por vírgula")
    duration_minutes = models.IntegerField(blank=True, null=True,
                                         help_text="Duração estimada em minutos")
    calories_per_minute = models.FloatField(blank=True, null=True,
                                          help_text="Calorias queimadas por minuto (estimativa)")
    instructions = models.TextField(blank=True, null=True,
                                  help_text="Instruções passo a passo")
    video_url = models.URLField(blank=True, null=True,
                              help_text="URL do vídeo demonstrativo")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.muscle_group or 'Sem grupo'})"

    class Meta:
        ordering = ['muscle_group', 'name']