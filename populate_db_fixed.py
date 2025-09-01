#!/usr/bin/env python
"""
Script para popular o banco de dados FitAI - VERSÃO CORRIGIDA
Execute: python populate_db_fixed.py
"""

import os
import django

# Configurar Django ANTES de importar qualquer modelo
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fitai.settings')
django.setup()

# Importar DEPOIS do django.setup()
from django.contrib.auth.models import User
from apps.users.models import UserProfile
from apps.exercises.models import Exercise
from apps.workouts.models import Workout, WorkoutExercise

def criar_exercicios():
    """Criar exercícios básicos"""
    exercicios = [
        {
            'nome': 'Flexão de Braço',
            'descricao': 'Exercício clássico para peito, ombros e tríceps',
            'categoria': 'calistenia',
            'grupo_muscular_primario': 'peito',
            'grupos_musculares_secundarios': ['ombros', 'triceps'],
            'equipamento_necessario': 'nenhum',
            'nivel_dificuldade': 'iniciante',
            'instrucoes_detalhadas': 'Deite-se de bruços, apoie as mãos no chão na largura dos ombros e empurre o corpo para cima.',
            'dicas_execucao': 'Mantenha o corpo reto e o core contraído durante todo o movimento.',
            'tempo_execucao': 30,
            'calorias_por_minuto': 8.0,
            'musculos_trabalhados': ['peito', 'ombros', 'triceps']
        },
        {
            'nome': 'Agachamento',
            'descricao': 'Exercício fundamental para pernas e glúteos',
            'categoria': 'musculacao',
            'grupo_muscular_primario': 'quadriceps',
            'grupos_musculares_secundarios': ['gluteos', 'posteriores'],
            'equipamento_necessario': 'nenhum',
            'nivel_dificuldade': 'iniciante',
            'instrucoes_detalhadas': 'Fique em pé, pés na largura dos ombros, desça como se fosse sentar numa cadeira.',
            'dicas_execucao': 'Mantenha o peso nos calcanhares e os joelhos alinhados com os pés.',
            'tempo_execucao': 40,
            'calorias_por_minuto': 9.0,
            'musculos_trabalhados': ['quadriceps', 'gluteos', 'posteriores']
        },
        {
            'nome': 'Prancha',
            'descricao': 'Exercício isométrico para fortalecimento do core',
            'categoria': 'calistenia',
            'grupo_muscular_primario': 'core',
            'grupos_musculares_secundarios': ['ombros'],
            'equipamento_necessario': 'nenhum',
            'nivel_dificuldade': 'iniciante',
            'instrucoes_detalhadas': 'Apoie-se nos antebraços e pontas dos pés, mantendo o corpo em linha reta.',
            'dicas_execucao': 'Não deixe o quadril cair nem levantar demais. Respire normalmente.',
            'tempo_execucao': 60,
            'calorias_por_minuto': 4.0,
            'musculos_trabalhados': ['core', 'ombros']
        },
        {
            'nome': 'Jumping Jacks',
            'descricao': 'Exercício aeróbico simples e eficaz',
            'categoria': 'cardio',
            'grupo_muscular_primario': 'corpo_todo',
            'grupos_musculares_secundarios': ['pernas', 'ombros'],
            'equipamento_necessario': 'nenhum',
            'nivel_dificuldade': 'iniciante',
            'instrucoes_detalhadas': 'Salte abrindo as pernas e levantando os braços acima da cabeça simultaneamente.',
            'dicas_execucao': 'Mantenha um ritmo constante e aterrisse suavemente.',
            'tempo_execucao': 60,
            'calorias_por_minuto': 8.0,
            'musculos_trabalhados': ['corpo_todo']
        },
        {
            'nome': 'Abdominal',
            'descricao': 'Exercício básico para fortalecimento abdominal',
            'categoria': 'calistenia',
            'grupo_muscular_primario': 'abdomen',
            'grupos_musculares_secundarios': ['core'],
            'equipamento_necessario': 'nenhum',
            'nivel_dificuldade': 'iniciante',
            'instrucoes_detalhadas': 'Deitado de costas, flexione o tronco em direção aos joelhos.',
            'dicas_execucao': 'Evite puxar o pescoço. Use a força do abdômen.',
            'tempo_execucao': 30,
            'calorias_por_minuto': 6.0,
            'musculos_trabalhados': ['abdomen']
        }
    ]
    
    print("Criando exercícios...")
    for dados in exercicios:
        exercicio, created = Exercise.objects.get_or_create(
            nome=dados['nome'],
            defaults=dados
        )
        if created:
            print(f"✅ Exercício criado: {exercicio.nome}")
        else:
            print(f"⚠️  Exercício já existe: {exercicio.nome}")

def criar_usuarios():
    """Criar usuários de teste"""
    usuarios_dados = [
        {
            'username': 'joao_silva',
            'email': 'joao@teste.com',
            'first_name': 'João',
            'last_name': 'Silva',
            'perfil': {
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
            'perfil': {
                'nome_completo': 'Maria Santos',
                'idade': 30,
                'sexo': 'F',
                'peso_atual': 60.0,
                'altura': 165.0,
                'meta_principal': 'bem_estar',
                'nivel_atividade': 'ativo',
                'areas_foco': ['corpo_todo'],
                'tipos_treino_preferidos': ['cardio'],
                'equipamentos_disponiveis': 'sem_equipamentos',
                'tempo_disponivel': 30,
                'frequencia_semanal': 5,
                'onboarding_completo': True
            }
        }
    ]
    
    print("Criando usuários...")
    for dados in usuarios_dados:
        dados_perfil = dados.pop('perfil')
        
        user, created = User.objects.get_or_create(
            username=dados['username'],
            defaults=dados
        )
        
        if created:
            user.set_password('123456')
            user.save()
            print(f"✅ Usuário criado: {user.username}")
            
            # Criar perfil
            UserProfile.objects.create(
                user=user,
                **dados_perfil
            )
            print(f"✅ Perfil criado para: {user.username}")
        else:
            print(f"⚠️  Usuário já existe: {user.username}")

def criar_treinos():
    """Criar treinos básicos"""
    treinos_dados = [
        {
            'nome': 'Iniciante - Corpo Todo',
            'descricao': 'Treino completo para iniciantes',
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
                {'nome': 'Agachamento', 'series': 3, 'repeticoes': 15, 'tempo_descanso': 60, 'ordem': 2},
                {'nome': 'Prancha', 'series': 3, 'repeticoes': 30, 'tempo_descanso': 45, 'ordem': 3}
            ]
        },
        {
            'nome': 'Cardio Básico',
            'descricao': 'Treino cardiovascular simples',
            'categoria': 'cardio',
            'nivel_dificuldade': 'iniciante',
            'duracao_estimada': 20,
            'calorias_estimadas': 150,
            'tipo_treino': 'cardio',
            'equipamentos_necessarios': [],
            'areas_focadas': ['cardio'],
            'is_template': True,
            'exercicios': [
                {'nome': 'Jumping Jacks', 'series': 3, 'repeticoes': 30, 'tempo_descanso': 30, 'ordem': 1},
                {'nome': 'Abdominal', 'series': 3, 'repeticoes': 15, 'tempo_descanso': 30, 'ordem': 2}
            ]
        }
    ]
    
    print("Criando treinos...")
    for dados in treinos_dados:
        exercicios_dados = dados.pop('exercicios')
        
        treino, created = Workout.objects.get_or_create(
            nome=dados['nome'],
            defaults=dados
        )
        
        if created:
            print(f"✅ Treino criado: {treino.nome}")
            
            # Adicionar exercícios ao treino
            for ex_dados in exercicios_dados:
                try:
                    exercicio = Exercise.objects.get(nome=ex_dados['nome'])
                    WorkoutExercise.objects.create(
                        workout=treino,
                        exercise=exercicio,
                        series=ex_dados['series'],
                        repeticoes=ex_dados['repeticoes'],
                        tempo_descanso=ex_dados['tempo_descanso'],
                        ordem=ex_dados['ordem']
                    )
                    print(f"   ✅ Exercício adicionado: {exercicio.nome}")
                except Exercise.DoesNotExist:
                    print(f"   ❌ Exercício não encontrado: {ex_dados['nome']}")
        else:
            print(f"⚠️  Treino já existe: {treino.nome}")

def main():
    """Função principal"""
    print("🚀 Populando banco de dados FitAI...")
    print("=" * 50)
    
try:
    print("\n1️⃣ Criando exercícios...")
    criar_exercicios()
    
    print("\n2️⃣ Criando usuários...")
    criar_usuarios()
    
    print("\n3️⃣ Criando treinos...")
    criar_treinos()
    
    print("\n" + "=" * 50)
    print("✅ Sucesso! Banco populado com:")
    print(f"   - Exercícios: {Exercise.objects.count()}")
    print(f"   - Usuários: {User.objects.count()}")
    print(f"   - Perfis: {UserProfile.objects.count()}")
    print(f"   - Treinos: {Workout.objects.count()}")
    print("\n🔐 Logins de teste:")
    print("   Username: joao_silva / Senha: 123456")
    print("   Username: maria_santos / Senha: 123456")
    
except Exception as e:
    print(f"\n❌ Erro durante a execução: {e}")
    import traceback
    traceback.print_exc()  