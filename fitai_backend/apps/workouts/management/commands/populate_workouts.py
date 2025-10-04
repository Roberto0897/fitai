# apps/workouts/management/commands/populate_workouts.py

from django.core.management.base import BaseCommand
from apps.workouts.models import Workout, WorkoutExercise
from apps.exercises.models import Exercise

class Command(BaseCommand):
    help = 'Popula o banco de dados com treinos estruturados e profissionais'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando população de treinos...'))

        # Limpar treinos existentes
        WorkoutExercise.objects.all().delete()
        Workout.objects.all().delete()
        self.stdout.write('Treinos anteriores removidos')

        # Dados dos treinos
        # IMPORTANTE: is_recommended AGORA é False por padrão, indicando treinos de catálogo
        workouts_data = [
            # TREINOS PARA INICIANTES (BEGINNER) - 8 treinos
            {
                'name': 'Primeiro Treino - Corpo Inteiro',
                'description': 'Treino perfeito para quem está começando. Movimentos básicos e seguros.',
                'difficulty_level': 'beginner',
                'estimated_duration': 25,
                'target_muscle_groups': 'Corpo inteiro',
                'equipment_needed': 'Nenhum',
                'calories_estimate': 150,
                'workout_type': 'mixed',
                'is_recommended': False, # CORRIGIDO
                'exercises': [
                    {'name': 'Jumping Jacks', 'sets': 2, 'reps': '30 seg', 'rest_time': 45, 'order': 1},
                    {'name': 'Flexão de Braço Tradicional', 'sets': 2, 'reps': '6-8', 'rest_time': 60, 'order': 2},
                    {'name': 'Agachamento Livre com Barra', 'sets': 3, 'reps': '10-12', 'rest_time': 60, 'order': 3},
                    {'name': 'Prancha Frontal', 'sets': 2, 'reps': '20 seg', 'rest_time': 45, 'order': 4},
                    {'name': 'Afundo com Halteres', 'sets': 2, 'reps': '6 cada', 'rest_time': 60, 'order': 5},
                ]
            },
            {
                'name': 'Cardio Básico - Queima Calorias',
                'description': 'Treino cardiovascular para iniciantes focado em queima de gordura.',
                'difficulty_level': 'beginner', 
                'estimated_duration': 20,
                'target_muscle_groups': 'Cardio, Corpo inteiro',
                'equipment_needed': 'Nenhum',
                'calories_estimate': 180,
                'workout_type': 'cardio',
                'is_recommended': False, # CORRIGIDO
                'exercises': [
                    {'name': 'Jumping Jacks', 'sets': 3, 'reps': '30 seg', 'rest_time': 30, 'order': 1},
                    {'name': 'High Knees', 'sets': 3, 'reps': '20 seg', 'rest_time': 40, 'order': 2},
                    {'name': 'Mountain Climber', 'sets': 2, 'reps': '15 seg', 'rest_time': 45, 'order': 3},
                    {'name': 'Agachamento Livre com Barra', 'sets': 3, 'reps': '15', 'rest_time': 30, 'order': 4},
                    {'name': 'Prancha Frontal', 'sets': 2, 'reps': '15 seg', 'rest_time': 60, 'order': 5},
                ]
            },
            {
                'name': 'Força Básica - Sem Pesos',
                'description': 'Desenvolvimento de força usando apenas peso corporal.',
                'difficulty_level': 'beginner',
                'estimated_duration': 30,
                'target_muscle_groups': 'Peito, Pernas, Core',
                'equipment_needed': 'Nenhum',
                'calories_estimate': 160,
                'workout_type': 'strength',
                'is_recommended': False, # CORRIGIDO
                'exercises': [
                    {'name': 'Flexão de Braço Tradicional', 'sets': 3, 'reps': '8-12', 'rest_time': 60, 'order': 1},
                    {'name': 'Agachamento Livre com Barra', 'sets': 3, 'reps': '12-15', 'rest_time': 60, 'order': 2},
                    {'name': 'Good Morning', 'sets': 3, 'reps': '10', 'rest_time': 45, 'order': 3},
                    {'name': 'Abdominal Tradicional', 'sets': 3, 'reps': '10-15', 'rest_time': 45, 'order': 4},
                    {'name': 'Panturrilha em Pé', 'sets': 2, 'reps': '15-20', 'rest_time': 30, 'order': 5},
                ]
            },
            {
                'name': 'Peito e Tríceps Iniciante',
                'description': 'Treino básico para desenvolvimento de peito e tríceps.',
                'difficulty_level': 'beginner',
                'estimated_duration': 30,
                'target_muscle_groups': 'Peito, Tríceps',
                'equipment_needed': 'Nenhum',
                'calories_estimate': 140,
                'workout_type': 'strength',
                'is_recommended': False, # CORRIGIDO
                'exercises': [
                    {'name': 'Flexão de Braço Tradicional', 'sets': 3, 'reps': '8-12', 'rest_time': 60, 'order': 1},
                    {'name': 'Flexão Diamante', 'sets': 2, 'reps': '6-8', 'rest_time': 60, 'order': 2},
                    {'name': 'Mergulho no Banco', 'sets': 3, 'reps': '8-12', 'rest_time': 60, 'order': 3},
                    {'name': 'Prancha Frontal', 'sets': 2, 'reps': '30 seg', 'rest_time': 45, 'order': 4},
                ]
            },
            {
                'name': 'Costas Iniciante',
                'description': 'Fortalecimento básico das costas e postura.',
                'difficulty_level': 'beginner',
                'estimated_duration': 25,
                'target_muscle_groups': 'Costas',
                'equipment_needed': 'Nenhum ou halteres leves',
                'calories_estimate': 130,
                'workout_type': 'strength',
                'is_recommended': False, # CORRIGIDO
                'exercises': [
                    {'name': 'Remada Invertida', 'sets': 3, 'reps': '8-10', 'rest_time': 60, 'order': 1},
                    {'name': 'Good Morning', 'sets': 3, 'reps': '10-12', 'rest_time': 60, 'order': 2},
                    {'name': 'Face Pull', 'sets': 3, 'reps': '12-15', 'rest_time': 45, 'order': 3},
                    {'name': 'Prancha Frontal', 'sets': 2, 'reps': '25 seg', 'rest_time': 45, 'order': 4},
                ]
            },
            {
                'name': 'Pernas Iniciante',
                'description': 'Desenvolvimento básico de pernas e glúteos.',
                'difficulty_level': 'beginner',
                'estimated_duration': 28,
                'target_muscle_groups': 'Pernas, Glúteos',
                'equipment_needed': 'Nenhum',
                'calories_estimate': 160,
                'workout_type': 'strength',
                'is_recommended': False, # CORRIGIDO
                'exercises': [
                    {'name': 'Agachamento Livre com Barra', 'sets': 3, 'reps': '12-15', 'rest_time': 60, 'order': 1},
                    {'name': 'Afundo com Halteres', 'sets': 3, 'reps': '8 cada', 'rest_time': 60, 'order': 2},
                    {'name': 'Elevação Pélvica', 'sets': 3, 'reps': '12-15', 'rest_time': 45, 'order': 3},
                    {'name': 'Panturrilha em Pé', 'sets': 3, 'reps': '15-20', 'rest_time': 30, 'order': 4},
                ]
            },
            {
                'name': 'Core Iniciante',
                'description': 'Fortalecimento do abdômen e core.',
                'difficulty_level': 'beginner',
                'estimated_duration': 20,
                'target_muscle_groups': 'Abdômen, Core',
                'equipment_needed': 'Nenhum',
                'calories_estimate': 100,
                'workout_type': 'strength',
                'is_recommended': False, # CORRIGIDO
                'exercises': [
                    {'name': 'Prancha Frontal', 'sets': 3, 'reps': '20-30 seg', 'rest_time': 45, 'order': 1},
                    {'name': 'Abdominal Tradicional', 'sets': 3, 'reps': '12-15', 'rest_time': 45, 'order': 2},
                    {'name': 'Elevação de Pernas', 'sets': 3, 'reps': '10-12', 'rest_time': 60, 'order': 3},
                    {'name': 'Bicicleta', 'sets': 3, 'reps': '15 cada', 'rest_time': 45, 'order': 4},
                ]
            },
            {
                'name': 'Mobilidade e Alongamento',
                'description': 'Treino leve focado em mobilidade e recuperação.',
                'difficulty_level': 'beginner',
                'estimated_duration': 20,
                'target_muscle_groups': 'Corpo inteiro',
                'equipment_needed': 'Nenhum',
                'calories_estimate': 80,
                'workout_type': 'flexibility',
                'is_recommended': False, # CORRIGIDO
                'exercises': [
                    {'name': 'Jumping Jacks', 'sets': 2, 'reps': '30 seg', 'rest_time': 30, 'order': 1},
                    {'name': 'Agachamento Livre com Barra', 'sets': 2, 'reps': '10', 'rest_time': 30, 'order': 2},
                    {'name': 'Prancha Frontal', 'sets': 2, 'reps': '20 seg', 'rest_time': 45, 'order': 3},
                    {'name': 'Dead Bug', 'sets': 2, 'reps': '10 cada', 'rest_time': 45, 'order': 4},
                ]
            },

            # TREINOS INTERMEDIÁRIOS (INTERMEDIATE) - 12 treinos
            {
                'name': 'Push - Peito, Ombros e Tríceps',
                'description': 'Treino focado em movimentos de empurrar.',
                'difficulty_level': 'intermediate',
                'estimated_duration': 45,
                'target_muscle_groups': 'Peito, Ombros, Tríceps',
                'equipment_needed': 'Halteres, Barra',
                'calories_estimate': 240,
                'workout_type': 'strength',
                'is_recommended': False, # CORRIGIDO
                'exercises': [
                    {'name': 'Supino Reto com Barra', 'sets': 4, 'reps': '8-10', 'rest_time': 90, 'order': 1},
                    {'name': 'Supino Inclinado', 'sets': 3, 'reps': '10-12', 'rest_time': 75, 'order': 2},
                    {'name': 'Desenvolvimento com Barra', 'sets': 4, 'reps': '8-10', 'rest_time': 75, 'order': 3},
                    {'name': 'Elevação Lateral', 'sets': 3, 'reps': '12-15', 'rest_time': 60, 'order': 4},
                    {'name': 'Tríceps Pulley', 'sets': 3, 'reps': '10-12', 'rest_time': 60, 'order': 5},
                    {'name': 'Tríceps Francês', 'sets': 3, 'reps': '10-12', 'rest_time': 60, 'order': 6},
                ]
            },
            {
                'name': 'Pull - Costas e Bíceps',
                'description': 'Treino focado em movimentos de puxar.',
                'difficulty_level': 'intermediate',
                'estimated_duration': 45,
                'target_muscle_groups': 'Costas, Bíceps',
                'equipment_needed': 'Barra fixa, Halteres',
                'calories_estimate': 230,
                'workout_type': 'strength',
                'is_recommended': False, # CORRIGIDO
                'exercises': [
                    {'name': 'Barra Fixa Pronada', 'sets': 4, 'reps': '6-10', 'rest_time': 90, 'order': 1},
                    {'name': 'Remada Curvada com Barra', 'sets': 4, 'reps': '10-12', 'rest_time': 75, 'order': 2},
                    {'name': 'Remada Unilateral com Halter', 'sets': 3, 'reps': '10 cada', 'rest_time': 60, 'order': 3},
                    {'name': 'Rosca Direta com Barra', 'sets': 3, 'reps': '10-12', 'rest_time': 60, 'order': 4},
                    {'name': 'Rosca Martelo', 'sets': 3, 'reps': '10-12', 'rest_time': 60, 'order': 5},
                ]
            },
            {
                'name': 'Legs - Pernas Completo',
                'description': 'Treino intensivo para pernas e glúteos.',
                'difficulty_level': 'intermediate',
                'estimated_duration': 50,
                'target_muscle_groups': 'Quadríceps, Glúteos, Posterior',
                'equipment_needed': 'Barra, Halteres',
                'calories_estimate': 300,
                'workout_type': 'strength',
                'is_recommended': False, # CORRIGIDO
                'exercises': [
                    {'name': 'Agachamento Livre com Barra', 'sets': 4, 'reps': '10-12', 'rest_time': 90, 'order': 1},
                    {'name': 'Leg Press 45°', 'sets': 4, 'reps': '12-15', 'rest_time': 75, 'order': 2},
                    {'name': 'Stiff', 'sets': 3, 'reps': '10-12', 'rest_time': 75, 'order': 3},
                    {'name': 'Afundo com Halteres', 'sets': 3, 'reps': '10 cada', 'rest_time': 60, 'order': 4},
                    {'name': 'Panturrilha em Pé', 'sets': 4, 'reps': '15-20', 'rest_time': 45, 'order': 5},
                ]
            },
            {
                'name': 'Ombros e Trapézio',
                'description': 'Desenvolvimento completo de ombros.',
                'difficulty_level': 'intermediate',
                'estimated_duration': 40,
                'target_muscle_groups': 'Ombros, Trapézio',
                'equipment_needed': 'Barra, Halteres',
                'calories_estimate': 200,
                'workout_type': 'strength',
                'is_recommended': False, # CORRIGIDO
                'exercises': [
                    {'name': 'Desenvolvimento com Barra', 'sets': 4, 'reps': '8-10', 'rest_time': 90, 'order': 1},
                    {'name': 'Desenvolvimento Arnold', 'sets': 3, 'reps': '10-12', 'rest_time': 75, 'order': 2},
                    {'name': 'Elevação Lateral', 'sets': 4, 'reps': '12-15', 'rest_time': 60, 'order': 3},
                    {'name': 'Crucifixo Invertido', 'sets': 3, 'reps': '12-15', 'rest_time': 60, 'order': 4},
                    {'name': 'Encolhimento com Barra', 'sets': 3, 'reps': '12-15', 'rest_time': 60, 'order': 5},
                ]
            },
            {
                'name': 'Braços - Bíceps e Tríceps',
                'description': 'Treino específico para braços.',
                'difficulty_level': 'intermediate',
                'estimated_duration': 35,
                'target_muscle_groups': 'Bíceps, Tríceps',
                'equipment_needed': 'Barra, Halteres',
                'calories_estimate': 180,
                'workout_type': 'strength',
                'is_recommended': False, # CORRIGIDO
                'exercises': [
                    {'name': 'Rosca Direta com Barra', 'sets': 4, 'reps': '10-12', 'rest_time': 60, 'order': 1},
                    {'name': 'Rosca Alternada', 'sets': 3, 'reps': '10-12', 'rest_time': 60, 'order': 2},
                    {'name': 'Tríceps Testa', 'sets': 4, 'reps': '10-12', 'rest_time': 60, 'order': 3},
                    {'name': 'Tríceps Corda', 'sets': 3, 'reps': '12-15', 'rest_time': 60, 'order': 4},
                    {'name': 'Rosca Martelo', 'sets': 3, 'reps': '10-12', 'rest_time': 60, 'order': 5},
                ]
            },
            {
                'name': 'HIIT Intermediário',
                'description': 'Treino intervalado de alta intensidade.',
                'difficulty_level': 'intermediate',
                'estimated_duration': 25,
                'target_muscle_groups': 'Corpo inteiro',
                'equipment_needed': 'Nenhum',
                'calories_estimate': 300,
                'workout_type': 'hiit',
                'is_recommended': False, # CORRIGIDO
                'exercises': [
                    {'name': 'Burpee Completo', 'sets': 4, 'reps': '20 seg', 'rest_time': 40, 'order': 1},
                    {'name': 'Mountain Climber', 'sets': 4, 'reps': '30 seg', 'rest_time': 30, 'order': 2},
                    {'name': 'Jump Squat', 'sets': 4, 'reps': '20 seg', 'rest_time': 40, 'order': 3},
                    {'name': 'Flexão de Braço Tradicional', 'sets': 3, 'reps': '20 seg', 'rest_time': 40, 'order': 4},
                    {'name': 'High Knees', 'sets': 4, 'reps': '20 seg', 'rest_time': 40, 'order': 5},
                ]
            },
            {
                'name': 'Core Power - Abdômen Avançado',
                'description': 'Treino intenso para core e abdômen.',
                'difficulty_level': 'intermediate',
                'estimated_duration': 30,
                'target_muscle_groups': 'Abdômen, Core',
                'equipment_needed': 'Nenhum',
                'calories_estimate': 170,
                'workout_type': 'strength',
                'is_recommended': False, # CORRIGIDO
                'exercises': [
                    {'name': 'Prancha Frontal', 'sets': 4, 'reps': '40-60 seg', 'rest_time': 45, 'order': 1},
                    {'name': 'Prancha Lateral', 'sets': 3, 'reps': '30 seg cada', 'rest_time': 45, 'order': 2},
                    {'name': 'Bicicleta', 'sets': 4, 'reps': '20 cada', 'rest_time': 45, 'order': 3},
                    {'name': 'V-Up', 'sets': 3, 'reps': '10-12', 'rest_time': 60, 'order': 4},
                    {'name': 'Russian Twist', 'sets': 3, 'reps': '20 total', 'rest_time': 45, 'order': 5},
                ]
            },
            {
                'name': 'Peito Focado',
                'description': 'Treino específico para hipertrofia de peito.',
                'difficulty_level': 'intermediate',
                'estimated_duration': 40,
                'target_muscle_groups': 'Peito',
                'equipment_needed': 'Barra, Halteres',
                'calories_estimate': 210,
                'workout_type': 'strength',
                'is_recommended': False, # CORRIGIDO
                'exercises': [
                    {'name': 'Supino Reto com Barra', 'sets': 4, 'reps': '8-10', 'rest_time': 90, 'order': 1},
                    {'name': 'Supino Inclinado', 'sets': 4, 'reps': '10-12', 'rest_time': 75, 'order': 2},
                    {'name': 'Crucifixo com Halteres', 'sets': 3, 'reps': '12-15', 'rest_time': 60, 'order': 3},
                    {'name': 'Crossover no Cabo', 'sets': 3, 'reps': '12-15', 'rest_time': 60, 'order': 4},
                    {'name': 'Flexão de Braço Tradicional', 'sets': 2, 'reps': 'máximo', 'rest_time': 60, 'order': 5},
                ]
            },
            {
                'name': 'Costas Focado',
                'description': 'Treino específico para hipertrofia de costas.',
                'difficulty_level': 'intermediate',
                'estimated_duration': 45,
                'target_muscle_groups': 'Costas',
                'equipment_needed': 'Barra fixa, Barra, Halteres',
                'calories_estimate': 220,
                'workout_type': 'strength',
                'is_recommended': False, # CORRIGIDO
                'exercises': [
                    {'name': 'Levantamento Terra', 'sets': 4, 'reps': '6-8', 'rest_time': 120, 'order': 1},
                    {'name': 'Barra Fixa Pronada', 'sets': 4, 'reps': '8-12', 'rest_time': 90, 'order': 2},
                    {'name': 'Remada Curvada com Barra', 'sets': 4, 'reps': '10-12', 'rest_time': 75, 'order': 3},
                    {'name': 'Pullover com Halter', 'sets': 3, 'reps': '12-15', 'rest_time': 60, 'order': 4},
                    {'name': 'Face Pull', 'sets': 3, 'reps': '15-20', 'rest_time': 45, 'order': 5},
                ]
            },
            {
                'name': 'Upper Body - Parte Superior',
                'description': 'Treino completo da parte superior do corpo.',
                'difficulty_level': 'intermediate',
                'estimated_duration': 50,
                'target_muscle_groups': 'Peito, Costas, Ombros, Braços',
                'equipment_needed': 'Barra, Halteres',
                'calories_estimate': 260,
                'workout_type': 'strength',
                'is_recommended': False, # CORRIGIDO
                'exercises': [
                    {'name': 'Supino Reto com Barra', 'sets': 3, 'reps': '10-12', 'rest_time': 75, 'order': 1},
                    {'name': 'Remada Curvada com Barra', 'sets': 3, 'reps': '10-12', 'rest_time': 75, 'order': 2},
                    {'name': 'Desenvolvimento com Barra', 'sets': 3, 'reps': '10-12', 'rest_time': 75, 'order': 3},
                    {'name': 'Rosca Direta com Barra', 'sets': 3, 'reps': '10-12', 'rest_time': 60, 'order': 4},
                    {'name': 'Tríceps Pulley', 'sets': 3, 'reps': '12-15', 'rest_time': 60, 'order': 5},
                ]
            },
            {
                'name': 'Lower Body - Parte Inferior',
                'description': 'Treino completo da parte inferior do corpo.',
                'difficulty_level': 'intermediate',
                'estimated_duration': 45,
                'target_muscle_groups': 'Pernas, Glúteos',
                'equipment_needed': 'Barra, Halteres',
                'calories_estimate': 280,
                'workout_type': 'strength',
                'is_recommended': False, # CORRIGIDO
                'exercises': [
                    {'name': 'Agachamento Livre com Barra', 'sets': 4, 'reps': '10-12', 'rest_time': 90, 'order': 1},
                    {'name': 'Stiff', 'sets': 3, 'reps': '10-12', 'rest_time': 75, 'order': 2},
                    {'name': 'Leg Press 45°', 'sets': 3, 'reps': '12-15', 'rest_time': 75, 'order': 3},
                    {'name': 'Cadeira Extensora', 'sets': 3, 'reps': '12-15', 'rest_time': 60, 'order': 4},
                    {'name': 'Mesa Flexora', 'sets': 3, 'reps': '12-15', 'rest_time': 60, 'order': 5},
                ]
            },
            {
                'name': 'Cardio Intenso',
                'description': 'Treino cardiovascular de alta intensidade.',
                'difficulty_level': 'intermediate',
                'estimated_duration': 30,
                'target_muscle_groups': 'Corpo inteiro',
                'equipment_needed': 'Nenhum',
                'calories_estimate': 320,
                'workout_type': 'cardio',
                'is_recommended': False, # CORRIGIDO
                'exercises': [
                    {'name': 'Burpee Completo', 'sets': 5, 'reps': '30 seg', 'rest_time': 30, 'order': 1},
                    {'name': 'Mountain Climber', 'sets': 4, 'reps': '40 seg', 'rest_time': 30, 'order': 2},
                    {'name': 'Jump Squat', 'sets': 4, 'reps': '30 seg', 'rest_time': 30, 'order': 3},
                    {'name': 'High Knees', 'sets': 4, 'reps': '30 seg', 'rest_time': 30, 'order': 4},
                    {'name': 'Jumping Jacks', 'sets': 3, 'reps': '45 seg', 'rest_time': 30, 'order': 5},
                ]
            },

            # TREINOS AVANÇADOS (ADVANCED) - 10 treinos
            {
                'name': 'Push Avançado - Força e Hipertrofia',
                'description': 'Treino avançado de empurrar com volume alto.',
                'difficulty_level': 'advanced',
                'estimated_duration': 55,
                'target_muscle_groups': 'Peito, Ombros, Tríceps',
                'equipment_needed': 'Barra, Halteres, Cabos',
                'calories_estimate': 280,
                'workout_type': 'strength',
                'is_recommended': False, # CORRIGIDO
                'exercises': [
                    {'name': 'Supino Reto com Barra', 'sets': 5, 'reps': '6-8', 'rest_time': 120, 'order': 1},
                    {'name': 'Supino Inclinado', 'sets': 4, 'reps': '8-10', 'rest_time': 90, 'order': 2},
                    {'name': 'Desenvolvimento com Barra', 'sets': 4, 'reps': '8-10', 'rest_time': 90, 'order': 3},
                    {'name': 'Dips para Peito', 'sets': 3, 'reps': '8-12', 'rest_time': 75, 'order': 4},
                    {'name': 'Elevação Lateral', 'sets': 4, 'reps': '12-15', 'rest_time': 60, 'order': 5},
                    {'name': 'Tríceps Testa', 'sets': 4, 'reps': '10-12', 'rest_time': 60, 'order': 6},
                ]
            },
            {
                'name': 'Pull Avançado - Costas Completo',
                'description': 'Treino avançado de puxar com foco em costas.',
                'difficulty_level': 'advanced',
                'estimated_duration': 55,
                'target_muscle_groups': 'Costas, Bíceps',
                'equipment_needed': 'Barra fixa, Barra, Halteres',
                'calories_estimate': 270,
                'workout_type': 'strength',
                'is_recommended': False, # CORRIGIDO
                'exercises': [
                    {'name': 'Levantamento Terra', 'sets': 5, 'reps': '5-6', 'rest_time': 180, 'order': 1},
                    {'name': 'Barra Fixa Pronada', 'sets': 4, 'reps': '8-12', 'rest_time': 90, 'order': 2},
                    {'name': 'Remada Curvada com Barra', 'sets': 4, 'reps': '8-10', 'rest_time': 90, 'order': 3},
                    {'name': 'T-Bar Row', 'sets': 3, 'reps': '10-12', 'rest_time': 75, 'order': 4},
                    {'name': 'Rosca Direta com Barra', 'sets': 4, 'reps': '8-10', 'rest_time': 60, 'order': 5},
                ]
            },
            {
                'name': 'Legs Avançado - Força Brutal',
                'description': 'Treino de pernas de alta intensidade.',
                'difficulty_level': 'advanced',
                'estimated_duration': 60,
                'target_muscle_groups': 'Pernas completas',
                'equipment_needed': 'Barra, Máquinas',
                'calories_estimate': 350,
                'workout_type': 'strength',
                'is_recommended': False, # CORRIGIDO
                'exercises': [
                    {'name': 'Agachamento Livre com Barra', 'sets': 5, 'reps': '6-8', 'rest_time': 180, 'order': 1},
                    {'name': 'Agachamento Frontal', 'sets': 4, 'reps': '8-10', 'rest_time': 120, 'order': 2},
                    {'name': 'Levantamento Terra Romeno', 'sets': 4, 'reps': '8-10', 'rest_time': 90, 'order': 3},
                    {'name': 'Leg Press 45°', 'sets': 4, 'reps': '12-15', 'rest_time': 75, 'order': 4},
                    {'name': 'Agachamento Búlgaro', 'sets': 3, 'reps': '10 cada', 'rest_time': 75, 'order': 5},
                ]
            },
            {
                'name': 'HIIT Extremo',
                'description': 'Treino de alta intensidade para atletas avançados.',
                'difficulty_level': 'advanced',
                'estimated_duration': 30,
                'target_muscle_groups': 'Corpo inteiro',
                'equipment_needed': 'Nenhum',
                'calories_estimate': 400,
                'workout_type': 'hiit',
                'is_recommended': False, # JÁ ESTAVA FALSE, MANTIDO
                'exercises': [
                    {'name': 'Burpee Completo', 'sets': 6, 'reps': '45 seg', 'rest_time': 15, 'order': 1},
                    {'name': 'Mountain Climber', 'sets': 5, 'reps': '45 seg', 'rest_time': 15, 'order': 2},
                    {'name': 'Box Jump', 'sets': 5, 'reps': '30 seg', 'rest_time': 30, 'order': 3},
                    {'name': 'Flexão com Palmas', 'sets': 4, 'reps': '20 seg', 'rest_time': 40, 'order': 4},
                    {'name': 'Jump Squat', 'sets': 5, 'reps': '30 seg', 'rest_time': 30, 'order': 5},
                ]
            },
            {
                'name': 'Força Máxima - Powerlifting',
                'description': 'Treino focado em força pura nos 3 grandes.',
                'difficulty_level': 'advanced',
                'estimated_duration': 60,
                'target_muscle_groups': 'Corpo inteiro',
                'equipment_needed': 'Barra, Rack',
                'calories_estimate': 320,
                'workout_type': 'strength',
                'is_recommended': False, # CORRIGIDO
                'exercises': [
                    {'name': 'Agachamento Livre com Barra', 'sets': 5, 'reps': '3-5', 'rest_time': 240, 'order': 1},
                    {'name': 'Supino Reto com Barra', 'sets': 5, 'reps': '3-5', 'rest_time': 240, 'order': 2},
                    {'name': 'Levantamento Terra', 'sets': 5, 'reps': '3-5', 'rest_time': 300, 'order': 3},
                ]
            },
            {
                'name': 'Upper Body Avançado',
                'description': 'Treino intensivo da parte superior.',
                'difficulty_level': 'advanced',
                'estimated_duration': 55,
                'target_muscle_groups': 'Peito, Costas, Ombros',
                'equipment_needed': 'Barra, Halteres, Cabos',
                'calories_estimate': 290,
                'workout_type': 'strength',
                'is_recommended': False, # CORRIGIDO
                'exercises': [
                    {'name': 'Supino Reto com Barra', 'sets': 4, 'reps': '8-10', 'rest_time': 90, 'order': 1},
                    {'name': 'Barra Fixa Pronada', 'sets': 4, 'reps': '8-12', 'rest_time': 90, 'order': 2},
                    {'name': 'Desenvolvimento com Barra', 'sets': 4, 'reps': '8-10', 'rest_time': 75, 'order': 3},
                    {'name': 'Remada Curvada com Barra', 'sets': 4, 'reps': '8-10', 'rest_time': 75, 'order': 4},
                    {'name': 'Dips para Tríceps', 'sets': 3, 'reps': '8-12', 'rest_time': 60, 'order': 5},
                ]
            },
            {
                'name': 'Peito Avançado - Hipertrofia',
                'description': 'Treino específico para máximo desenvolvimento de peito.',
                'difficulty_level': 'advanced',
                'estimated_duration': 50,
                'target_muscle_groups': 'Peito',
                'equipment_needed': 'Barra, Halteres, Cabos',
                'calories_estimate': 250,
                'workout_type': 'strength',
                'is_recommended': False, # CORRIGIDO
                'exercises': [
                    {'name': 'Supino Reto com Barra', 'sets': 5, 'reps': '6-8', 'rest_time': 120, 'order': 1},
                    {'name': 'Supino Inclinado', 'sets': 4, 'reps': '8-10', 'rest_time': 90, 'order': 2},
                    {'name': 'Supino Declinado', 'sets': 4, 'reps': '10-12', 'rest_time': 75, 'order': 3},
                    {'name': 'Crucifixo com Halteres', 'sets': 3, 'reps': '12-15', 'rest_time': 60, 'order': 4},
                    {'name': 'Crossover no Cabo', 'sets': 3, 'reps': '15-20', 'rest_time': 45, 'order': 5},
                ]
            },
            {
                'name': 'Costas Avançado - Volume Alto',
                'description': 'Treino de costas com alto volume para hipertrofia.',
                'difficulty_level': 'advanced',
                'estimated_duration': 55,
                'target_muscle_groups': 'Costas completas',
                'equipment_needed': 'Barra fixa, Barra, Halteres',
                'calories_estimate': 270,
                'workout_type': 'strength',
                'is_recommended': False, # CORRIGIDO
                'exercises': [
                    {'name': 'Levantamento Terra', 'sets': 4, 'reps': '6-8', 'rest_time': 150, 'order': 1},
                    {'name': 'Barra Fixa Pronada', 'sets': 4, 'reps': '8-12', 'rest_time': 90, 'order': 2},
                    {'name': 'Barra Fixa Supinada', 'sets': 3, 'reps': '8-12', 'rest_time': 90, 'order': 3},
                    {'name': 'Remada Curvada com Barra', 'sets': 4, 'reps': '8-10', 'rest_time': 75, 'order': 4},
                    {'name': 'Remada Unilateral com Halter', 'sets': 3, 'reps': '10 cada', 'rest_time': 60, 'order': 5},
                    {'name': 'Pullover com Halter', 'sets': 3, 'reps': '12-15', 'rest_time': 60, 'order': 6},
                ]
            },
            {
                'name': 'Ombros Avançado - 3D Shoulders',
                'description': 'Desenvolvimento completo dos três deltoides.',
                'difficulty_level': 'advanced',
                'estimated_duration': 45,
                'target_muscle_groups': 'Ombros completos',
                'equipment_needed': 'Barra, Halteres',
                'calories_estimate': 230,
                'workout_type': 'strength',
                'is_recommended': False, # CORRIGIDO
                'exercises': [
                    {'name': 'Desenvolvimento com Barra', 'sets': 5, 'reps': '6-8', 'rest_time': 120, 'order': 1},
                    {'name': 'Desenvolvimento Arnold', 'sets': 4, 'reps': '8-10', 'rest_time': 90, 'order': 2},
                    {'name': 'Elevação Lateral', 'sets': 4, 'reps': '12-15', 'rest_time': 60, 'order': 3},
                    {'name': 'Elevação Frontal', 'sets': 3, 'reps': '12-15', 'rest_time': 60, 'order': 4},
                    {'name': 'Crucifixo Invertido', 'sets': 4, 'reps': '12-15', 'rest_time': 60, 'order': 5},
                ]
            },
            {
                'name': 'Atleta Completo - Full Body',
                'description': 'Treino avançado trabalhando todo o corpo.',
                'difficulty_level': 'advanced',
                'estimated_duration': 60,
                'target_muscle_groups': 'Corpo inteiro',
                'equipment_needed': 'Barra, Halteres',
                'calories_estimate': 370,
                'workout_type': 'mixed',
                'is_recommended': False, # CORRIGIDO
                'exercises': [
                    {'name': 'Levantamento Terra', 'sets': 4, 'reps': '6-8', 'rest_time': 180, 'order': 1},
                    {'name': 'Agachamento Frontal', 'sets': 4, 'reps': '8-10', 'rest_time': 120, 'order': 2},
                    {'name': 'Supino Reto com Barra', 'sets': 4, 'reps': '8-10', 'rest_time': 90, 'order': 3},
                    {'name': 'Barra Fixa Pronada', 'sets': 3, 'reps': '8-12', 'rest_time': 90, 'order': 4},
                    {'name': 'Desenvolvimento com Barra', 'sets': 3, 'reps': '8-10', 'rest_time': 75, 'order': 5},
                ]
            },
        ]

        created_workouts = 0
        created_exercises = 0

        for workout_data in workouts_data:
            # Extrair dados dos exercícios
            exercises_data = workout_data.pop('exercises')
            
            # Criar treino
            # Usamos get_or_create para garantir que treinos duplicados não sejam criados
            workout, created = Workout.objects.get_or_create(
                name=workout_data['name'],
                defaults={
                    **workout_data,
                    # Campos de controle (configurados para Treino de Catálogo/Sistema)
                    'created_by_user': None,  
                    'is_personalized': False, 
                }
            )
            
            if created:
                created_workouts += 1
                self.stdout.write(f"Treino: {workout.name}")
                
                # Adicionar exercícios ao treino
                for ex_data in exercises_data:
                    try:
                        # Assumindo que os exercícios já foram populados
                        exercise = Exercise.objects.get(name=ex_data['name'])
                        workout_exercise = WorkoutExercise.objects.create(
                            workout=workout,
                            exercise=exercise,
                            sets=ex_data['sets'],
                            reps=ex_data['reps'],
                            rest_time=ex_data['rest_time'],
                            order_in_workout=ex_data['order']
                        )
                        created_exercises += 1
                        self.stdout.write(f"  -> {exercise.name} ({ex_data['sets']}x{ex_data['reps']})")
                        
                    except Exercise.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(f"Exercício '{ex_data['name']}' não encontrado! O treino '{workout.name}' pode estar incompleto.")
                        )

        self.stdout.write(
            self.style.SUCCESS(f'\nSucesso! {created_workouts} treinos e {created_exercises} exercícios vinculados!')
        )
        
        # Estatísticas finais
        total_workouts = Workout.objects.count()
        total_workout_exercises = WorkoutExercise.objects.count()
        
        by_difficulty = {}
        for difficulty in ['beginner', 'intermediate', 'advanced']:
            count = Workout.objects.filter(difficulty_level=difficulty).count()
            if count > 0:
                by_difficulty[difficulty] = count
        
        by_type = {}
        for workout_type in ['strength', 'cardio', 'hiit', 'mixed', 'flexibility']:
            count = Workout.objects.filter(workout_type=workout_type).count()
            if count > 0:
                by_type[workout_type] = count

        self.stdout.write(f'\nESTATÍSTICAS DOS TREINOS:')
        self.stdout.write(f'Total de treinos: {total_workouts}')
        self.stdout.write(f'Total de exercícios vinculados: {total_workout_exercises}')
        
        self.stdout.write(f'\nPor Dificuldade:')
        for difficulty, count in by_difficulty.items():
            self.stdout.write(f'{difficulty.upper()}: {count} treinos')
            
        self.stdout.write(f'\nPor Tipo:')
        for wtype, count in by_type.items():
            self.stdout.write(f'{wtype.upper()}: {count} treinos')
        
        # Agora o count deve ser 0 (ou apenas o treino HIIT Extremo, se ele for o único com is_recommended=False)
        recommended_count = Workout.objects.filter(is_recommended=True).count()
        self.stdout.write(f'\nTreinos marcados como recomendados pela IA: {recommended_count}')
        
        self.stdout.write(
            self.style.SUCCESS('\nPopulação de treinos concluída com sucesso!')
        )