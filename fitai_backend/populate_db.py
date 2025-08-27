#!/usr/bin/env python
"""
Script para popular o banco de dados FitAI com dados de exemplo
IMPORTANTE: Execute este arquivo dentro da pasta fitai_backend (onde está o manage.py)
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fitai.settings')
django.setup()

from django.contrib.auth.models import User
from apps.users.models import UserProfile
from apps.exercises.models import Exercise
from apps.workouts.models import Workout, WorkoutExercise

def criar_exercicios():
    """Criar exercícios de exemplo"""
    exercicios = [
        {
            'nome': 'Flexão de Braço',
            'descricao': 'Exercício clássico para peito, ombros e tríceps',
            'categoria': 'calistenia',
            'grupo_muscular_primario': 'peito',
            'grupos_musculares_secundarios': ['ombros', 'triceps'],
            'equipamento_necessario': 'nenhum',
            'nivel_dificuldade': 'iniciante',
            'instrucoes_detalhadas': 'Posicione-se em prancha, mãos na largura dos ombros. Desça o peito até quase tocar o chão.',
            'dicas_execucao': 'Mantenha o core contraído e o corpo em linha reta.',
            'tempo_execucao': 30,
            'calorias_por_minuto': 8.0,
            'musculos_trabalhados': ['peito', 'ombros', 'triceps']
        },
        {
            'nome': 'Agachamento Livre',
            'descricao': 'Rei dos exercícios para pernas e glúteos',
            'categoria': 'musculacao',
            'grupo_muscular_primario': 'quadriceps',
            'grupos_musculares_secundarios': ['gluteos', 'posteriores'],
            'equipamento_necessario': 'nenhum',
            'nivel_dificuldade': 'iniciante',
            'instrucoes_detalhadas': 'Pés na largura dos ombros, desça como se fosse sentar numa cadeira.',
            'dicas_execucao': 'Joelhos alinhados com os pés. Peso nos calcanhares.',
            'tempo_execucao': 35,
            'calorias_por_minuto': 9.0,
            'musculos_trabalhados': ['quadriceps', 'gluteos', 'posteriores']
        },
        {
            'nome': 'Prancha',
            'descricao': 'Exercício isométrico para core',
            'categoria': 'calistenia',
            'grupo_muscular_primario': 'core',
            'grupos_musculares_secundarios': ['ombros'],
            'equipamento_necessario': 'nenhum',
            'nivel_dificuldade': 'iniciante',
            'instrucoes_detalhadas': 'Mantenha o corpo reto apoiado nos antebraços e pés.',
            'dicas_execucao': 'Evite arqueamento das costas. Respiração normal.',
            'tempo_execucao': 60,
            'calorias_por_minuto': 4.0,
            'musculos_trabalhados': ['core', 'ombros']
        },
        {
            'nome': 'Burpee',
            'descricao': 'Exercício completo que trabalha corpo todo',
            'categoria': 'cardio',
            'grupo_muscular_primario': 'corpo_todo',
            'grupos_musculares_secundarios': ['peito', 'pernas'],
            'equipamento_necessario': 'nenhum',
            'nivel_dificuldade': 'avancado',
            'instrucoes_detalhadas': 'Agache, apoie as mãos no chão, salte para prancha, flexão, volte e salte.',
            'dicas_execucao': 'Movimento fluido. Respiração controlada.',
            'tempo_execucao': 45,
            'calorias_por_minuto': 12.0,
            'musculos_trabalhados': ['corpo_todo']
        },
        {
            'nome': 'Jumping Jacks',
            'descricao': 'Exercício cardio simples e efetivo',
            'categoria': 'cardio',
            'grupo_muscular_primario': 'corpo_todo',
            'grupos_musculares_secundarios': ['pernas', 'ombros'],
            'equipamento_necessario': 'nenhum',
            'nivel_dificuldade': 'iniciante',
            'instrucoes_detalhadas': 'Salte abrindo as pernas e levantando os braços acima da cabeça.',
            'dicas_execucao': 'Aterrisse suavemente. Movimento rítmico.',
            'tempo_execucao': 45,
            'calorias_por_minuto': 8.0,
            'musculos_trabalhados': ['corpo_todo', 'pernas']
        },
        {
            'nome': 'Abdominal Tradicional',
            'descricao': 'Exercício básico para abdômen',
            'categoria': 'calistenia',
            'grupo_muscular_primario': 'abdomen',
            'grupos_musculares_secundarios': ['core'],
            'equipamento_necessario': 'nenhum',
            'nivel_dificuldade': 'iniciante',
            'instrucoes_detalhadas': 'Deitado, flexione o tronco em direção aos joelhos.',
            'dicas_execucao': 'Não puxe o pescoço. Movimento suave.',
            'tempo_execucao': 30,
            'calorias_por_minuto': 6.0,
            'musculos_trabalhados': ['abdomen', 'core']
        },
        {
            'nome': 'Mountain Climber',
            'descricao': 'Exercício cardio que fortalece core e pernas',
            'categoria': 'calistenia',
            'grupo_muscular_primario': 'core',
            'grupos_musculares_secundarios': ['pernas', 'ombros'],
            'equipamento_necessario': 'nenhum',
            'nivel_dificuldade': 'intermediario',
            'instrucoes_detalhadas': 'Em posição de prancha, alterne trazendo os joelhos em direção ao peito rapidamente.',
            'dicas_execucao': 'Mantenha os quadris estáveis. Core sempre contraído.',
            'tempo_execucao': 30,
            'calorias_por_minuto': 10.0,
            'musculos_trabalhados': ['core', 'pernas', 'ombros']
        },
        {
            'nome': 'Glute Bridge',
            'descricao': 'Ativa e fortalece os glúteos',
            'categoria': 'calistenia',
            'grupo_muscular_primario': 'gluteos',
            'grupos_musculares_secundarios': ['posteriores'],
            'equipamento_necessario': 'nenhum',
            'nivel_dificuldade': 'iniciante',
            'instrucoes_detalhadas': 'Deitado, eleve o quadril contraindo os glúteos.',
            'dicas_execucao': 'Pausa no topo. Squeeze nos glúteos.',
            'tempo_execucao': 30,
            'calorias_por_minuto': 5.0,
            'musculos_trabalhados': ['gluteos', 'posteriores', 'core']
        }
    ]
    
    for dados in exercicios:
        exercicio, created = Exercise.objects.get_or_create(
            nome=dados['nome'],
            defaults=dados
        )
        if created:
            print(f"✅ Exercício criado: {exercicio.nome}")
        else:
            print(f"⚠️  Exercício já existe: {exercicio.nome}")

def criar_usuarios_teste():
    """Criar usuários de exemplo"""
    usuarios = [
        {
            'username': 'joao_silva',
            'email': 'joao@teste.com',
            'first_name': 'João',
            'last_name': 'Silva',
            'profile': {
                'nome_completo': 'João Silva',
                'idade': 25,
                'sexo': 'M',
                'peso_atual': 75.0,
                'altura': 175.0,
                'meta_principal': 'ganho_muscular',
                'nivel_atividade': 'moderado',
                'areas_foco': ['peito', 'bracos'],
                'tipos_treino_preferidos': ['musculacao'],
                'equipamentos_disponiveis': 'basicos',
                'tempo_disponivel': 45,
                'frequencia_semanal': 4,
                'onboarding_completo': True
            }
        },
        {
            'username': 'maria_santos',
            'email': 'maria@teste.com',
            'first_name': 'Maria',
            'last_name': 'Santos',
            'profile': {
                'nome_completo': 'Maria Santos',
                'idade': 30,
                'sexo': 'F',
                'peso_atual': 60.0,
                'altura': 165.0,
                'meta_principal': 'bem_estar',
                'nivel_atividade': 'ativo',
                'areas_foco': ['corpo_todo'],
                'tipos_treino_preferidos': ['cardio', 'calistenia'],
                'equipamentos_disponiveis': 'sem_equipamentos',
                'tempo_disponivel': 30,
                'frequencia_semanal': 5,
                'onboarding_completo': True
            }
        },
        {
            'username': 'ana_costa',
            'email': 'ana@teste.com',
            'first_name': 'Ana',
            'last_name': 'Costa',
            'profile': {
                'nome_completo': 'Ana Costa',
                'idade': 22,
                'sexo': 'F',
                'peso_atual': 55.0,
                'altura': 160.0,
                'meta_principal': 'emagrecimento',
                'nivel_atividade': 'sedentario',
                'areas_foco': ['abdomen', 'pernas'],
                'tipos_treino_preferidos': ['cardio'],
                'equipamentos_disponiveis': 'sem_equipamentos',
                'tempo_disponivel': 30,
                'frequencia_semanal': 3,
                'onboarding_completo': True
            }
        }
    ]
    
    for dados_user in usuarios:
        dados_profile = dados_user.pop('profile')
        
        user, created = User.objects.get_or_create(
            username=dados_user['username'],
            defaults=dados_user
        )
        
        if created:
            user.set_password('123456')  # Senha para testes
            user.save()
            print(f"✅ Usuário criado: {user.username}")
            
            # Criar perfil
            UserProfile.objects.create(
                user=user,
                **dados_profile
            )
            print(f"✅ Perfil criado para: {user.username}")
        else:
            print(f"⚠️  Usuário já existe: {user.username}")

def criar_treinos():
    """Criar treinos de exemplo"""
    treinos = [
        {
            'nome': 'Treino Iniciante - Corpo Todo',
            'descricao': 'Treino completo para iniciantes que trabalha todos os grupos musculares',
            'categoria': 'forca',
            'nivel_dificuldade': 'iniciante',
            'duracao_estimada': 30,
            'calorias_estimadas': 200,
            'tipo_treino': 'full_body',
            'equipamentos_necessarios': [],
            'areas_focadas': ['corpo_todo'],
            'is_template': True,
            'exercicios': [
                {'nome': 'Flexão de Braço', 'series': 3, 'repeticoes': 10, 'tempo_descanso': 60, 'ordem': 1},
                {'nome': 'Agachamento Livre', 'series': 3, 'repeticoes': 15, 'tempo_descanso': 60, 'ordem': 2},
                {'nome': 'Prancha', 'series': 3, 'repeticoes': 30, 'tempo_descanso': 45, 'ordem': 3},
                {'nome': 'Glute Bridge', 'series': 3, 'repeticoes': 15, 'tempo_descanso': 45, 'ordem': 4}
            ]
        },
        {
            'nome': 'HIIT Cardio Explosivo',
            'descricao': 'Treino de alta intensidade para queima de gordura',
            'categoria': 'cardio',
            'nivel_dificuldade': 'intermediario',
            'duracao_estimada': 20,
            'calorias_estimadas': 300,
            'tipo_treino': 'hiit',
            'equipamentos_necessarios': [],
            'areas_focadas': ['cardio', 'corpo_todo'],
            'is_template': True,
            'exercicios': [
                {'nome': 'Burpee', 'series': 4, 'repeticoes': 8, 'tempo_descanso': 30, 'ordem': 1},
                {'nome': 'Mountain Climber', 'series': 4, 'repeticoes': 20, 'tempo_descanso': 30, 'ordem': 2},
                {'nome': 'Jumping Jacks', 'series': 4, 'repeticoes': 30, 'tempo_descanso': 30, 'ordem': 3}
            ]
        },
        {
            'nome': 'Core & Abdômen',
            'descricao': 'Fortalecimento focado no core e abdômen',
            'categoria': 'forca',
            'nivel_dificuldade': 'iniciante',
            'duracao_estimada': 25,
            'calorias_estimadas': 150,
            'tipo_treino': 'funcional',
            'equipamentos_necessarios': [],
            'areas_focadas': ['core', 'abdomen'],
            'is_template': True,
            'exercicios': [
                {'nome': 'Prancha', 'series': 3, 'repeticoes': 45, 'tempo_descanso': 45, 'ordem': 1},
                {'nome': 'Abdominal Tradicional', 'series': 3, 'repeticoes': 15, 'tempo_descanso': 30, 'ordem': 2},
                {'nome': 'Mountain Climber', 'series': 3, 'repeticoes': 20, 'tempo_descanso': 30, 'ordem': 3}
            ]
        }
    ]
    
    for dados_treino in treinos:
        exercicios_dados = dados_treino.pop('exercicios')
        
        treino, created = Workout.objects.get_or_create(
            nome=dados_treino['nome'],
            defaults=dados_treino
        )
        
        if created:
            print(f"✅ Treino criado: {treino.nome}")
            
            # Adicionar exercícios
            for exercicio_dados in exercicios_dados:
                try:
                    exercicio = Exercise.objects.get(nome=exercicio_dados['nome'])
                    WorkoutExercise.objects.create(
                        workout=treino,
                        exercise=exercicio,
                        series=exercicio_dados['series'],
                        repeticoes=exercicio_dados['repeticoes'],
                        tempo_descanso=exercicio_dados['tempo_descanso'],
                        ordem=exercicio_dados['ordem']
                    )
                except Exercise.DoesNotExist:
                    print(f"⚠️  Exercício não encontrado: {exercicio_dados['nome']}")
        else:
            print(f"⚠️  Treino já existe: {treino.nome}")

def main():
    """Executar tudo"""
    print("🚀 Populando banco de dados FitAI...")
    print("=" * 50)
    
    print("\n1️⃣ Criando exercícios...")
    criar_exercicios()
    
    print("\n2️⃣ Criando usuários de teste...")
    criar_usuarios_teste()
    
    print("\n3️⃣ Criando treinos...")
    criar_treinos()
    
    print("\n" + "=" * 50)
    print("✅ Pronto! Dados criados com sucesso!")
    print(f"   - Exercícios: {Exercise.objects.count()}")
    print(f"   - Usuários: {User.objects.count()}")
    print(f"   - Perfis: {UserProfile.objects.count()}")
    print(f"   - Treinos: {Workout.objects.count()}")
    print("\n🔐 Logins de teste:")
    print("   - Username: joao_silva / Senha: 123456")
    print("   - Username: maria_santos / Senha: 123456")
    print("   - Username: ana_costa / Senha: 123456")

if __name__ == '__main__':
    main()