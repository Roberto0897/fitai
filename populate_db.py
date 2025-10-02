#!/usr/bin/env python
"""
Script para popular o banco de dados FitAI com dados de exemplo
Execute: python populate_db.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fitai.settings')
django.setup()

from apps.exercises.models import Exercise
from apps.workouts.models import Workout, WorkoutExercise

def criar_exercicios():
    """Criar exercícios de exemplo"""
    exercicios = [
        # PEITO
        {
            'name': 'Supino Reto',
            'description': 'Exercício clássico para desenvolvimento do peitoral',
            'muscle_group': 'chest',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Barra, Banco',
            'instructions': 'Deite no banco, pegue a barra com pegada média, desça até o peito e empurre.',
            'duration_minutes': 8,
        },
        {
            'name': 'Flexão de Braço',
            'description': 'Exercício básico para peito, ombros e tríceps',
            'muscle_group': 'chest',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Nenhum',
            'instructions': 'Posição de prancha, mãos na largura dos ombros, desça até quase tocar o chão.',
            'duration_minutes': 5,
        },
        
        # COSTAS
        {
            'name': 'Remada Curvada',
            'description': 'Fortalece toda a musculatura das costas',
            'muscle_group': 'back',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Barra',
            'instructions': 'Corpo inclinado, puxe a barra em direção ao abdômen.',
            'duration_minutes': 7,
        },
        {
            'name': 'Pull-ups',
            'description': 'Exercício composto para costas e bíceps',
            'muscle_group': 'back',
            'difficulty_level': 'advanced',
            'equipment_needed': 'Barra fixa',
            'instructions': 'Puxe o corpo até o queixo passar a barra.',
            'duration_minutes': 6,
        },
        
        # PERNAS
        {
            'name': 'Agachamento Livre',
            'description': 'Rei dos exercícios para pernas',
            'muscle_group': 'legs',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Barra',
            'instructions': 'Barra nas costas, desça até coxas paralelas ao chão.',
            'duration_minutes': 10,
        },
        {
            'name': 'Leg Press',
            'description': 'Fortalece quadríceps e glúteos',
            'muscle_group': 'legs',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Máquina de leg press',
            'instructions': 'Empurre a plataforma com os pés.',
            'duration_minutes': 8,
        },
        {
            'name': 'Agachamento Livre (Peso Corporal)',
            'description': 'Versão sem peso do agachamento',
            'muscle_group': 'legs',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Nenhum',
            'instructions': 'Pés na largura dos ombros, desça como se fosse sentar.',
            'duration_minutes': 5,
        },
        
        # OMBROS
        {
            'name': 'Desenvolvimento Militar',
            'description': 'Desenvolvimento de ombros com barra',
            'muscle_group': 'shoulders',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Barra',
            'instructions': 'Empurre a barra acima da cabeça.',
            'duration_minutes': 7,
        },
        
        # BRAÇOS
        {
            'name': 'Rosca Direta',
            'description': 'Fortalece o bíceps',
            'muscle_group': 'arms',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Halteres ou barra',
            'instructions': 'Flexione os cotovelos levantando o peso.',
            'duration_minutes': 5,
        },
        {
            'name': 'Tríceps Testa',
            'description': 'Isolamento do tríceps',
            'muscle_group': 'arms',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Barra W',
            'instructions': 'Deite, flexione apenas os cotovelos baixando a barra.',
            'duration_minutes': 5,
        },
        
        # CORE/ABS
        {
            'name': 'Prancha',
            'description': 'Exercício isométrico para core',
            'muscle_group': 'abs',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Nenhum',
            'instructions': 'Corpo reto apoiado nos antebraços e pés.',
            'duration_minutes': 3,
        },
        {
            'name': 'Abdominal Tradicional',
            'description': 'Exercício básico para abdômen',
            'muscle_group': 'abs',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Nenhum',
            'instructions': 'Deitado, flexione o tronco em direção aos joelhos.',
            'duration_minutes': 4,
        },
        
        # CARDIO
        {
            'name': 'Corrida na Esteira',
            'description': 'Cardio clássico',
            'muscle_group': 'cardio',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Esteira',
            'instructions': 'Mantenha ritmo constante e respiração controlada.',
            'duration_minutes': 15,
        },
        {
            'name': 'Burpee',
            'description': 'Exercício completo corpo todo',
            'muscle_group': 'cardio',
            'difficulty_level': 'advanced',
            'equipment_needed': 'Nenhum',
            'instructions': 'Agache, apoie mãos, salte para prancha, flexão, volte e salte.',
            'duration_minutes': 5,
        },
        {
            'name': 'Jumping Jacks',
            'description': 'Cardio simples e efetivo',
            'muscle_group': 'cardio',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Nenhum',
            'instructions': 'Salte abrindo as pernas e levantando os braços.',
            'duration_minutes': 5,
        },
    ]
    
    for dados in exercicios:
        exercicio, created = Exercise.objects.get_or_create(
            name=dados['name'],
            defaults=dados
        )
        if created:
            print(f"✅ Exercício criado: {exercicio.name}")
        else:
            print(f"⏭️  Já existe: {exercicio.name}")
    
    return Exercise.objects.all()


def criar_treinos():
    """Criar treinos de exemplo"""
    treinos = [
        {
            'name': 'Push - Peito e Tríceps',
            'description': 'Treino focado em músculos de empurrar (peito, ombros, tríceps)',
            'difficulty_level': 'intermediate',
            'estimated_duration': 50,
            'target_muscle_groups': 'chest, shoulders, arms',
            'workout_type': 'strength',
            'calories_estimate': 320,
            'is_recommended': True,
            'equipment_needed': 'Barra, Banco, Halteres',
            'exercicios': [
                {'name': 'Supino Reto', 'sets': 4, 'reps': '8-12', 'rest_time': 60, 'order': 1},
                {'name': 'Flexão de Braço', 'sets': 3, 'reps': '15-20', 'rest_time': 45, 'order': 2},
                {'name': 'Desenvolvimento Militar', 'sets': 3, 'reps': '10-12', 'rest_time': 60, 'order': 3},
                {'name': 'Tríceps Testa', 'sets': 3, 'reps': '12-15', 'rest_time': 45, 'order': 4},
            ]
        },
        {
            'name': 'Pull - Costas e Bíceps',
            'description': 'Treino focado em músculos de puxar (costas, bíceps)',
            'difficulty_level': 'intermediate',
            'estimated_duration': 45,
            'target_muscle_groups': 'back, arms',
            'workout_type': 'strength',
            'calories_estimate': 300,
            'is_recommended': True,
            'equipment_needed': 'Barra, Barra fixa',
            'exercicios': [
                {'name': 'Remada Curvada', 'sets': 4, 'reps': '8-12', 'rest_time': 60, 'order': 1},
                {'name': 'Pull-ups', 'sets': 3, 'reps': '6-10', 'rest_time': 90, 'order': 2},
                {'name': 'Rosca Direta', 'sets': 3, 'reps': '12-15', 'rest_time': 45, 'order': 3},
            ]
        },
        {
            'name': 'Legs - Pernas Completo',
            'description': 'Treino completo de membros inferiores',
            'difficulty_level': 'advanced',
            'estimated_duration': 60,
            'target_muscle_groups': 'legs, abs',
            'workout_type': 'strength',
            'calories_estimate': 400,
            'is_recommended': True,
            'equipment_needed': 'Barra, Leg Press',
            'exercicios': [
                {'name': 'Agachamento Livre', 'sets': 4, 'reps': '8-12', 'rest_time': 90, 'order': 1},
                {'name': 'Leg Press', 'sets': 3, 'reps': '12-15', 'rest_time': 60, 'order': 2},
                {'name': 'Prancha', 'sets': 3, 'reps': '60 seg', 'rest_time': 30, 'order': 3},
                {'name': 'Abdominal Tradicional', 'sets': 3, 'reps': '20', 'rest_time': 30, 'order': 4},
            ]
        },
        {
            'name': 'Treino Iniciante - Corpo Todo',
            'description': 'Treino completo para quem está começando',
            'difficulty_level': 'beginner',
            'estimated_duration': 30,
            'target_muscle_groups': 'full body',
            'workout_type': 'full_body',
            'calories_estimate': 200,
            'is_recommended': True,
            'equipment_needed': 'Nenhum',
            'exercicios': [
                {'name': 'Flexão de Braço', 'sets': 3, 'reps': '8-10', 'rest_time': 60, 'order': 1},
                {'name': 'Agachamento Livre (Peso Corporal)', 'sets': 3, 'reps': '15', 'rest_time': 60, 'order': 2},
                {'name': 'Prancha', 'sets': 3, 'reps': '30 seg', 'rest_time': 45, 'order': 3},
                {'name': 'Jumping Jacks', 'sets': 3, 'reps': '30', 'rest_time': 30, 'order': 4},
            ]
        },
        {
            'name': 'HIIT Cardio Explosivo',
            'description': 'Treino de alta intensidade para queima de gordura',
            'difficulty_level': 'intermediate',
            'estimated_duration': 25,
            'target_muscle_groups': 'full body, cardio',
            'workout_type': 'cardio',
            'calories_estimate': 350,
            'is_recommended': True,
            'equipment_needed': 'Nenhum',
            'exercicios': [
                {'name': 'Burpee', 'sets': 4, 'reps': '10', 'rest_time': 30, 'order': 1},
                {'name': 'Jumping Jacks', 'sets': 4, 'reps': '30', 'rest_time': 20, 'order': 2},
                {'name': 'Flexão de Braço', 'sets': 3, 'reps': '15', 'rest_time': 30, 'order': 3},
            ]
        },
    ]
    
    for dados_treino in treinos:
        exercicios_dados = dados_treino.pop('exercicios')
        
        treino, created = Workout.objects.get_or_create(
            name=dados_treino['name'],
            defaults=dados_treino
        )
        
        if created:
            print(f"\n✅ Treino criado: {treino.name}")
            
            # Adicionar exercícios ao treino
            for ex_dados in exercicios_dados:
                try:
                    exercicio = Exercise.objects.get(name=ex_dados['name'])
                    WorkoutExercise.objects.create(
                        workout=treino,
                        exercise=exercicio,
                        sets=ex_dados['sets'],
                        reps=ex_dados['reps'],
                        rest_time=ex_dados['rest_time'],
                        order_in_workout=ex_dados['order']
                    )
                    print(f"  ➕ {ex_dados['name']}")
                except Exercise.DoesNotExist:
                    print(f"  ⚠️  Exercício não encontrado: {ex_dados['name']}")
        else:
            print(f"\n⏭️  Já existe: {treino.name}")


def main():
    """Executar script"""
    print("=" * 60)
    print("🚀 POPULANDO BANCO DE DADOS FITAI")
    print("=" * 60)
    
    print("\n1️⃣  CRIANDO EXERCÍCIOS...")
    print("-" * 60)
    criar_exercicios()
    
    print("\n2️⃣  CRIANDO TREINOS...")
    print("-" * 60)
    criar_treinos()
    
    print("\n" + "=" * 60)
    print("✅ BANCO POPULADO COM SUCESSO!")
    print("=" * 60)
    print(f"\n📊 ESTATÍSTICAS:")
    print(f"   • Exercícios: {Exercise.objects.count()}")
    print(f"   • Treinos: {Workout.objects.count()}")
    print(f"   • Relações Treino-Exercício: {WorkoutExercise.objects.count()}")
    print("\n💡 Agora você pode testar o app Flutter!")
    print("   - Acesse a página de treinos")
    print("   - Teste a geração de treino com IA")
    print("\n")

if __name__ == '__main__':
    main()