# apps/workouts/management/commands/populate_workouts.py

from django.core.management.base import BaseCommand
from apps.workouts.models import Workout, WorkoutExercise
from apps.exercises.models import Exercise

class Command(BaseCommand):
    help = 'Popula o banco de dados com treinos estruturados e profissionais'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🏋️‍♂️ Iniciando população de treinos...'))

        # Limpar treinos existentes
        WorkoutExercise.objects.all().delete()
        Workout.objects.all().delete()
        self.stdout.write('🗑️ Treinos anteriores removidos')

        # Dados dos treinos
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
                'is_recommended': True,
                'exercises': [
                    {'name': 'Jumping Jacks', 'sets': 2, 'reps': '30 segundos', 'rest_time': 45, 'order': 1},
                    {'name': 'Flexão de Braço Inclinada', 'sets': 2, 'reps': '8-10', 'rest_time': 60, 'order': 2},
                    {'name': 'Agachamento Livre', 'sets': 3, 'reps': '10-12', 'rest_time': 60, 'order': 3},
                    {'name': 'Prancha (Plank)', 'sets': 2, 'reps': '20 segundos', 'rest_time': 45, 'order': 4},
                    {'name': 'Lunges (Afundo)', 'sets': 2, 'reps': '6 cada perna', 'rest_time': 60, 'order': 5},
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
                'is_recommended': True,
                'exercises': [
                    {'name': 'Jumping Jacks', 'sets': 3, 'reps': '30 segundos', 'rest_time': 30, 'order': 1},
                    {'name': 'High Knees (Joelho Alto)', 'sets': 3, 'reps': '20 segundos', 'rest_time': 40, 'order': 2},
                    {'name': 'Mountain Climbers', 'sets': 2, 'reps': '15 segundos', 'rest_time': 45, 'order': 3},
                    {'name': 'Agachamento Livre', 'sets': 3, 'reps': '15', 'rest_time': 30, 'order': 4},
                    {'name': 'Prancha (Plank)', 'sets': 2, 'reps': '15 segundos', 'rest_time': 60, 'order': 5},
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
                'is_recommended': True,
                'exercises': [
                    {'name': 'Flexão de Braço Inclinada', 'sets': 3, 'reps': '8-12', 'rest_time': 60, 'order': 1},
                    {'name': 'Agachamento Livre', 'sets': 3, 'reps': '12-15', 'rest_time': 60, 'order': 2},
                    {'name': 'Superman', 'sets': 3, 'reps': '10', 'rest_time': 45, 'order': 3},
                    {'name': 'Abdominal Tradicional', 'sets': 3, 'reps': '10-15', 'rest_time': 45, 'order': 4},
                    {'name': 'Elevação de Panturrilha', 'sets': 2, 'reps': '15-20', 'rest_time': 30, 'order': 5},
                ]
            },

            # TREINOS INTERMEDIÁRIOS (INTERMEDIATE) - 10 treinos
            {
                'name': 'Push (Empurrar) - Peito e Ombros',
                'description': 'Treino focado em movimentos de empurrar, trabalhando peito, ombros e tríceps.',
                'difficulty_level': 'intermediate',
                'estimated_duration': 40,
                'target_muscle_groups': 'Peito, Ombros, Tríceps',
                'equipment_needed': 'Halteres',
                'calories_estimate': 220,
                'workout_type': 'strength',
                'is_recommended': True,
                'exercises': [
                    {'name': 'Flexão de Braço Tradicional', 'sets': 3, 'reps': '10-15', 'rest_time': 60, 'order': 1},
                    {'name': 'Desenvolvimento com Halteres', 'sets': 4, 'reps': '8-12', 'rest_time': 75, 'order': 2},
                    {'name': 'Supino com Halteres', 'sets': 4, 'reps': '10-12', 'rest_time': 75, 'order': 3},
                    {'name': 'Elevação Lateral', 'sets': 3, 'reps': '12-15', 'rest_time': 60, 'order': 4},
                    {'name': 'Tríceps Francês', 'sets': 3, 'reps': '10-12', 'rest_time': 60, 'order': 5},
                    {'name': 'Elevação Frontal', 'sets': 2, 'reps': '12-15', 'rest_time': 45, 'order': 6},
                ]
            },
            {
                'name': 'Pull (Puxar) - Costas e Bíceps',
                'description': 'Treino focado em movimentos de puxar, desenvolvendo costas e bíceps.',
                'difficulty_level': 'intermediate',
                'estimated_duration': 40,
                'target_muscle_groups': 'Costas, Bíceps',
                'equipment_needed': 'Halteres',
                'calories_estimate': 210,
                'workout_type': 'strength',
                'is_recommended': True,
                'exercises': [
                    {'name': 'Remada Curvada com Halteres', 'sets': 4, 'reps': '10-12', 'rest_time': 75, 'order': 1},
                    {'name': 'Pullover com Halter', 'sets': 3, 'reps': '12-15', 'rest_time': 60, 'order': 2},
                    {'name': 'Rosca Direta com Halteres', 'sets': 4, 'reps': '10-12', 'rest_time': 60, 'order': 3},
                    {'name': 'Superman', 'sets': 3, 'reps': '12-15', 'rest_time': 45, 'order': 4},
                    {'name': 'Rosca Martelo', 'sets': 3, 'reps': '10-12', 'rest_time': 60, 'order': 5},
                ]
            },
            {
                'name': 'Legs (Pernas) - Força e Volume',
                'description': 'Treino intensivo para desenvolvimento completo das pernas.',
                'difficulty_level': 'intermediate',
                'estimated_duration': 45,
                'target_muscle_groups': 'Quadríceps, Glúteos, Posterior',
                'equipment_needed': 'Halteres (opcional)',
                'calories_estimate': 280,
                'workout_type': 'strength',
                'is_recommended': True,
                'exercises': [
                    {'name': 'Agachamento Livre', 'sets': 4, 'reps': '12-15', 'rest_time': 90, 'order': 1},
                    {'name': 'Lunges (Afundo)', 'sets': 3, 'reps': '10 cada perna', 'rest_time': 75, 'order': 2},
                    {'name': 'Agachamento Sumo', 'sets': 3, 'reps': '12-15', 'rest_time': 75, 'order': 3},
                    {'name': 'Elevação de Panturrilha', 'sets': 4, 'reps': '15-20', 'rest_time': 45, 'order': 4},
                    {'name': 'Superman', 'sets': 3, 'reps': '12', 'rest_time': 60, 'order': 5},
                ]
            },
            {
                'name': 'HIIT Intermediário - Alta Intensidade',
                'description': 'Treino intervalado de alta intensidade para condicionamento.',
                'difficulty_level': 'intermediate',
                'estimated_duration': 25,
                'target_muscle_groups': 'Corpo inteiro',
                'equipment_needed': 'Nenhum',
                'calories_estimate': 300,
                'workout_type': 'hiit',
                'is_recommended': True,
                'exercises': [
                    {'name': 'Burpees', 'sets': 4, 'reps': '20 segundos', 'rest_time': 40, 'order': 1},
                    {'name': 'Mountain Climbers', 'sets': 4, 'reps': '30 segundos', 'rest_time': 30, 'order': 2},
                    {'name': 'Jumping Jacks', 'sets': 4, 'reps': '30 segundos', 'rest_time': 30, 'order': 3},
                    {'name': 'Flexão de Braço Tradicional', 'sets': 3, 'reps': '20 segundos', 'rest_time': 40, 'order': 4},
                    {'name': 'High Knees (Joelho Alto)', 'sets': 4, 'reps': '20 segundos', 'rest_time': 40, 'order': 5},
                ]
            },
            {
                'name': 'Core Power - Abdômen Forte',
                'description': 'Treino específico para desenvolvimento do core e estabilidade.',
                'difficulty_level': 'intermediate',
                'estimated_duration': 25,
                'target_muscle_groups': 'Abdômen, Core',
                'equipment_needed': 'Nenhum',
                'calories_estimate': 150,
                'workout_type': 'strength',
                'is_recommended': True,
                'exercises': [
                    {'name': 'Prancha (Plank)', 'sets': 4, 'reps': '30-45 segundos', 'rest_time': 45, 'order': 1},
                    {'name': 'Bicicleta (Bicycle Crunch)', 'sets': 3, 'reps': '20 cada lado', 'rest_time': 45, 'order': 2},
                    {'name': 'Elevação de Pernas', 'sets': 3, 'reps': '12-15', 'rest_time': 60, 'order': 3},
                    {'name': 'Abdominal Tradicional', 'sets': 3, 'reps': '15-20', 'rest_time': 45, 'order': 4},
                    {'name': 'Superman', 'sets': 3, 'reps': '12-15', 'rest_time': 45, 'order': 5},
                ]
            },

            # TREINOS AVANÇADOS (ADVANCED) - 7 treinos
            {
                'name': 'Advanced Full Body - Completo',
                'description': 'Treino avançado trabalhando todo o corpo com alta intensidade.',
                'difficulty_level': 'advanced',
                'estimated_duration': 50,
                'target_muscle_groups': 'Corpo inteiro',
                'equipment_needed': 'Halteres',
                'calories_estimate': 350,
                'workout_type': 'mixed',
                'is_recommended': True,
                'exercises': [
                    {'name': 'Thruster com Halteres', 'sets': 4, 'reps': '8-10', 'rest_time': 90, 'order': 1},
                    {'name': 'Burpees', 'sets': 4, 'reps': '8-12', 'rest_time': 75, 'order': 2},
                    {'name': 'Turkish Get-Up', 'sets': 3, 'reps': '3 cada lado', 'rest_time': 120, 'order': 3},
                    {'name': 'Flexão Diamante', 'sets': 3, 'reps': '8-12', 'rest_time': 75, 'order': 4},
                    {'name': 'Bear Crawl', 'sets': 3, 'reps': '30 segundos', 'rest_time': 60, 'order': 5},
                ]
            },
            {
                'name': 'HIIT Extremo - Máximo Desafio',
                'description': 'Treino de alta intensidade para atletas experientes.',
                'difficulty_level': 'advanced',
                'estimated_duration': 30,
                'target_muscle_groups': 'Corpo inteiro',
                'equipment_needed': 'Nenhum',
                'calories_estimate': 400,
                'workout_type': 'hiit',
                'is_recommended': False,
                'exercises': [
                    {'name': 'Burpees', 'sets': 5, 'reps': '45 segundos', 'rest_time': 15, 'order': 1},
                    {'name': 'Mountain Climbers', 'sets': 5, 'reps': '45 segundos', 'rest_time': 15, 'order': 2},
                    {'name': 'Flexão Diamante', 'sets': 4, 'reps': '30 segundos', 'rest_time': 30, 'order': 3},
                    {'name': 'High Knees (Joelho Alto)', 'sets': 4, 'reps': '45 segundos', 'rest_time': 15, 'order': 4},
                    {'name': 'Bear Crawl', 'sets': 3, 'reps': '30 segundos', 'rest_time': 30, 'order': 5},
                ]
            },
            {
                'name': 'Strength Master - Força Máxima',
                'description': 'Treino avançado focado no desenvolvimento de força pura.',
                'difficulty_level': 'advanced',
                'estimated_duration': 55,
                'target_muscle_groups': 'Todos os grupos musculares',
                'equipment_needed': 'Halteres',
                'calories_estimate': 300,
                'workout_type': 'strength',
                'is_recommended': True,
                'exercises': [
                    {'name': 'Agachamento Livre', 'sets': 5, 'reps': '5-8', 'rest_time': 120, 'order': 1},
                    {'name': 'Supino com Halteres', 'sets': 5, 'reps': '5-8', 'rest_time': 120, 'order': 2},
                    {'name': 'Remada Curvada com Halteres', 'sets': 4, 'reps': '6-8', 'rest_time': 90, 'order': 3},
                    {'name': 'Desenvolvimento com Halteres', 'sets': 4, 'reps': '6-8', 'rest_time': 90, 'order': 4},
                    {'name': 'Turkish Get-Up', 'sets': 3, 'reps': '2 cada lado', 'rest_time': 120, 'order': 5},
                ]
            }
        ]

        created_workouts = 0
        created_exercises = 0

        for workout_data in workouts_data:
            # Extrair dados dos exercícios
            exercises_data = workout_data.pop('exercises')
            
            # Criar treino
            workout, created = Workout.objects.get_or_create(
                name=workout_data['name'],
                defaults=workout_data
            )
            
            if created:
                created_workouts += 1
                self.stdout.write(f"✅ Treino: {workout.name}")
                
                # Adicionar exercícios ao treino
                for ex_data in exercises_data:
                    try:
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
                        self.stdout.write(f"   → {exercise.name} ({ex_data['sets']}x{ex_data['reps']})")
                        
                    except Exercise.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(f"⚠️  Exercício '{ex_data['name']}' não encontrado!")
                        )

        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 Sucesso! {created_workouts} treinos e {created_exercises} exercícios vinculados!')
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
        for workout_type in ['strength', 'cardio', 'hiit', 'mixed']:
            count = Workout.objects.filter(workout_type=workout_type).count()
            if count > 0:
                by_type[workout_type] = count

        self.stdout.write(f'\n📊 ESTATÍSTICAS DOS TREINOS:')
        self.stdout.write(f'Total de treinos: {total_workouts}')
        self.stdout.write(f'Total de exercícios vinculados: {total_workout_exercises}')
        
        self.stdout.write(f'\n🎯 Por Dificuldade:')
        for difficulty, count in by_difficulty.items():
            self.stdout.write(f'{difficulty.upper()}: {count} treinos')
            
        self.stdout.write(f'\n💪 Por Tipo:')
        for wtype, count in by_type.items():
            self.stdout.write(f'{wtype.upper()}: {count} treinos')
        
        recommended_count = Workout.objects.filter(is_recommended=True).count()
        self.stdout.write(f'\n⭐ Treinos recomendados pela IA: {recommended_count}')
        
        self.stdout.write(
            self.style.SUCCESS('\n🚀 População de treinos concluída com sucesso!')
        )