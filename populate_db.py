#!/usr/bin/env python
"""
Script para popular banco com 100 exercícios + treinos
Execute: python manage.py shell < populate_db.py
"""

import os

import django

# Caminho da pasta backend (onde está o pacote 'fitai')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fitai.settings') 
django.setup()

from apps.exercises.models import Exercise
from apps.workouts.models import Workout, WorkoutExercise

def criar_exercicios():
    """Criar 100 exercícios variados"""
    exercicios = [
        # ========================================
        # PEITO (15 exercícios)
        # ========================================
        {
            'name': 'Supino Reto com Barra',
            'description': 'Exercício clássico para desenvolvimento do peitoral maior',
            'muscle_group': 'chest',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Barra, Banco',
            'instructions': 'Deite no banco, pegue a barra com pegada média, desça até o peito e empurre.',
            'duration_minutes': 8,
            'video_url': 'https://www.youtube.com/watch?v=rT7DgCr-3pg'
        },
        {
            'name': 'Supino Inclinado',
            'description': 'Foca na porção superior do peitoral',
            'muscle_group': 'chest',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Barra, Banco inclinado',
            'instructions': 'No banco inclinado a 45°, execute o movimento de supino.',
            'duration_minutes': 8,
            'video_url': 'https://www.youtube.com/watch?v=DbFgADa2PL8'
        },
        {
            'name': 'Supino Declinado',
            'description': 'Trabalha a porção inferior do peitoral',
            'muscle_group': 'chest',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Barra, Banco declinado',
            'instructions': 'No banco declinado, desça a barra controladamente até o peito.',
            'duration_minutes': 7,
            'video_url': 'https://www.youtube.com/watch?v=LfyQBUKR8SE'
        },
        {
            'name': 'Flexão de Braço Tradicional',
            'description': 'Exercício básico para peito usando peso corporal',
            'muscle_group': 'chest',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Nenhum',
            'instructions': 'Posição de prancha, desça até peito quase tocar o chão.',
            'duration_minutes': 5,
            'video_url': 'https://www.youtube.com/watch?v=IODxDxX7oi4'
        },
        {
            'name': 'Flexão Diamante',
            'description': 'Variação que enfatiza tríceps e centro do peito',
            'muscle_group': 'chest',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Nenhum',
            'instructions': 'Mãos juntas formando diamante, execute flexões.',
            'duration_minutes': 6,
            'video_url': 'https://www.youtube.com/watch?v=J0DnG1_S92I'
        },
        {
            'name': 'Flexão Archer',
            'description': 'Flexão avançada com ênfase unilateral',
            'muscle_group': 'chest',
            'difficulty_level': 'advanced',
            'equipment_needed': 'Nenhum',
            'instructions': 'Estenda um braço lateralmente enquanto flexiona o outro.',
            'duration_minutes': 7,
            'video_url': 'https://www.youtube.com/watch?v=Uw7A-C4qkHs'
        },
        {
            'name': 'Crucifixo com Halteres',
            'description': 'Isolamento do peitoral com amplitude completa',
            'muscle_group': 'chest',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Halteres, Banco',
            'instructions': 'Abra os braços lateralmente e retorne controladamente.',
            'duration_minutes': 7,
            'video_url': 'https://www.youtube.com/watch?v=eozdVDA78K0'
        },
        {
            'name': 'Peck Deck',
            'description': 'Isolamento em máquina para peitoral',
            'muscle_group': 'chest',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Máquina peck deck',
            'instructions': 'Junte os braços à frente mantendo cotovelos levemente flexionados.',
            'duration_minutes': 6,
            'video_url': 'https://www.youtube.com/watch?v=Z54ZW2PxI_8'
        },
        {
            'name': 'Chest Press na Máquina',
            'description': 'Supino em máquina com trajeto guiado',
            'muscle_group': 'chest',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Máquina chest press',
            'instructions': 'Empurre as alças para frente mantendo costas apoiadas.',
            'duration_minutes': 7,
            'video_url': 'https://www.youtube.com/watch?v=xUm0BiZCWlQ'
        },
        {
            'name': 'Crossover no Cabo',
            'description': 'Isolamento com tensão constante',
            'muscle_group': 'chest',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Polia dupla',
            'instructions': 'Cruze os cabos à frente do corpo em movimento amplo.',
            'duration_minutes': 6,
            'video_url': 'https://www.youtube.com/watch?v=taI4XduLpTk'
        },
        {
            'name': 'Pullover com Halter',
            'description': 'Trabalha peito e serrátil',
            'muscle_group': 'chest',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Halter, Banco',
            'instructions': 'Segure halter acima do peito e leve para trás da cabeça.',
            'duration_minutes': 6,
            'video_url': 'https://www.youtube.com/watch?v=FK0MZLJj5qw'
        },
        {
            'name': 'Flexão com Pés Elevados',
            'description': 'Aumenta ênfase na porção superior do peito',
            'muscle_group': 'chest',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Banco ou elevação',
            'instructions': 'Pés em superfície elevada, execute flexões.',
            'duration_minutes': 6,
            'video_url': 'https://www.youtube.com/watch?v=g4HGFZRo-4o'
        },
        {
            'name': 'Flexão com Palmas',
            'description': 'Exercício pliométrico para potência',
            'muscle_group': 'chest',
            'difficulty_level': 'advanced',
            'equipment_needed': 'Nenhum',
            'instructions': 'Empurre explosivamente e bata palmas no ar.',
            'duration_minutes': 5,
            'video_url': 'https://www.youtube.com/watch?v=qAQ_dvKk_x8'
        },
        {
            'name': 'Supino com Halteres',
            'description': 'Maior amplitude e trabalho estabilizador',
            'muscle_group': 'chest',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Halteres, Banco',
            'instructions': 'Desça halteres até nível do peito e empurre.',
            'duration_minutes': 8,
            'video_url': 'https://www.youtube.com/watch?v=VmB1G1K7v94'
        },
        {
            'name': 'Dips para Peito',
            'description': 'Exercício avançado em barras paralelas',
            'muscle_group': 'chest',
            'difficulty_level': 'advanced',
            'equipment_needed': 'Barras paralelas',
            'instructions': 'Incline-se para frente e desça com controle.',
            'duration_minutes': 7,
            'video_url': 'https://www.youtube.com/watch?v=2z8JmcrW-As'
        },

        # ========================================
        # COSTAS (15 exercícios)
        # ========================================
        {
            'name': 'Barra Fixa Pronada',
            'description': 'Exercício fundamental para desenvolvimento das costas',
            'muscle_group': 'back',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Barra fixa',
            'instructions': 'Puxe o corpo até queixo passar a barra.',
            'duration_minutes': 7,
            'video_url': 'https://www.youtube.com/watch?v=eGo4IYlbE5g'
        },
        {
            'name': 'Barra Fixa Supinada',
            'description': 'Ênfase maior em bíceps e latíssimo inferior',
            'muscle_group': 'back',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Barra fixa',
            'instructions': 'Pegada supinada, puxe até queixo na barra.',
            'duration_minutes': 7,
            'video_url': 'https://www.youtube.com/watch?v=sIvJTfGxdFo'
        },
        {
            'name': 'Remada Curvada com Barra',
            'description': 'Massa e espessura para as costas',
            'muscle_group': 'back',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Barra',
            'instructions': 'Tronco inclinado, puxe barra em direção ao umbigo.',
            'duration_minutes': 8,
            'video_url': 'https://www.youtube.com/watch?v=FWJR5Ve8bnQ'
        },
        {
            'name': 'Remada Unilateral com Halter',
            'description': 'Trabalho isolado de cada lado',
            'muscle_group': 'back',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Halter, Banco',
            'instructions': 'Apoiado no banco, puxe halter até o quadril.',
            'duration_minutes': 7,
            'video_url': 'https://www.youtube.com/watch?v=roCP6wCXPqo'
        },
        {
            'name': 'Puxada Frontal',
            'description': 'Desenvolvimento da largura das costas',
            'muscle_group': 'back',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Polia alta',
            'instructions': 'Puxe a barra até o peito mantendo tronco reto.',
            'duration_minutes': 7,
            'video_url': 'https://www.youtube.com/watch?v=CAwf7n6Luuc'
        },
        {
            'name': 'Puxada na Nuca',
            'description': 'Foca na porção superior das costas',
            'muscle_group': 'back',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Polia alta',
            'instructions': 'Puxe barra até a nuca com cuidado.',
            'duration_minutes': 7,
            'video_url': 'https://www.youtube.com/watch?v=lKSsYH6xLbQ'
        },
        {
            'name': 'Remada Cavalinho',
            'description': 'Trabalha músculos profundos das costas',
            'muscle_group': 'back',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Polia baixa',
            'instructions': 'Sentado, puxe o cabo em direção ao abdômen.',
            'duration_minutes': 7,
            'video_url': 'https://www.youtube.com/watch?v=UCXxvVItLoM'
        },
        {
            'name': 'Pulldown com Corda',
            'description': 'Amplitude maior e trabalho de trapézio',
            'muscle_group': 'back',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Polia alta, Corda',
            'instructions': 'Puxe corda abrindo na descida.',
            'duration_minutes': 6,
            'video_url': 'https://www.youtube.com/watch?v=A5K_gdKcd0g'
        },
        {
            'name': 'Levantamento Terra',
            'description': 'Exercício composto para corpo todo',
            'muscle_group': 'back',
            'difficulty_level': 'advanced',
            'equipment_needed': 'Barra',
            'instructions': 'Levante a barra do chão mantendo costas retas.',
            'duration_minutes': 10,
            'video_url': 'https://www.youtube.com/watch?v=op9kVnSso6Q'
        },
        {
            'name': 'Levantamento Terra Romeno',
            'description': 'Ênfase em lombar e posteriores de coxa',
            'muscle_group': 'back',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Barra',
            'instructions': 'Desça a barra deslizando pelas pernas.',
            'duration_minutes': 8,
            'video_url': 'https://www.youtube.com/watch?v=JCXUYuzwNrM'
        },
        {
            'name': 'Remada na Máquina',
            'description': 'Movimento guiado para remada horizontal',
            'muscle_group': 'back',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Máquina de remada',
            'instructions': 'Puxe as alças mantendo peito apoiado.',
            'duration_minutes': 7,
            'video_url': 'https://www.youtube.com/watch?v=UCXxvVItLoM'
        },
        {
            'name': 'Face Pull',
            'description': 'Trabalha deltoide posterior e trapézio',
            'muscle_group': 'back',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Polia alta, Corda',
            'instructions': 'Puxe corda em direção ao rosto abrindo braços.',
            'duration_minutes': 6,
            'video_url': 'https://www.youtube.com/watch?v=rep-qVOkqgk'
        },
        {
            'name': 'Remada Invertida',
            'description': 'Peso corporal para desenvolvimento das costas',
            'muscle_group': 'back',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Barra baixa ou TRX',
            'instructions': 'Suspenso na barra, puxe peito em direção a ela.',
            'duration_minutes': 6,
            'video_url': 'https://www.youtube.com/watch?v=hXTc1mDnZCw'
        },
        {
            'name': 'T-Bar Row',
            'description': 'Remada com barra fixa em uma extremidade',
            'muscle_group': 'back',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Barra T ou landmine',
            'instructions': 'Puxe a barra mantendo tronco inclinado.',
            'duration_minutes': 8,
            'video_url': 'https://www.youtube.com/watch?v=j3Igk5yZKBE'
        },
        {
            'name': 'Good Morning',
            'description': 'Fortalece lombar e posteriores',
            'muscle_group': 'back',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Barra',
            'instructions': 'Barra nas costas, incline tronco para frente.',
            'duration_minutes': 7,
            'video_url': 'https://www.youtube.com/watch?v=YA-h3n20qNo'
        },

        # ========================================
        # PERNAS (20 exercícios)
        # ========================================
        {
            'name': 'Agachamento Livre com Barra',
            'description': 'Rei dos exercícios para pernas',
            'muscle_group': 'legs',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Barra, Rack',
            'instructions': 'Desça até coxas paralelas ao chão.',
            'duration_minutes': 10,
            'video_url': 'https://www.youtube.com/watch?v=ultWZbUMPL8'
        },
        {
            'name': 'Agachamento Frontal',
            'description': 'Ênfase maior em quadríceps',
            'muscle_group': 'legs',
            'difficulty_level': 'advanced',
            'equipment_needed': 'Barra, Rack',
            'instructions': 'Barra na frente dos ombros, agache profundamente.',
            'duration_minutes': 9,
            'video_url': 'https://www.youtube.com/watch?v=uYumuL_G_V0'
        },
        {
            'name': 'Agachamento Sumô',
            'description': 'Trabalha mais glúteos e adutor',
            'muscle_group': 'legs',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Barra ou halter',
            'instructions': 'Pés bem afastados, desça mantendo tronco reto.',
            'duration_minutes': 8,
            'video_url': 'https://www.youtube.com/watch?v=0BQCbqgY02E'
        },
        {
            'name': 'Agachamento Búlgaro',
            'description': 'Trabalho unilateral intenso',
            'muscle_group': 'legs',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Banco, Halteres',
            'instructions': 'Pé traseiro elevado, desça com a perna da frente.',
            'duration_minutes': 8,
            'video_url': 'https://www.youtube.com/watch?v=2C-uSU5Bc1g'
        },
        {
            'name': 'Leg Press 45°',
            'description': 'Grande ativação de quadríceps e glúteos',
            'muscle_group': 'legs',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Máquina leg press',
            'instructions': 'Empurre a plataforma com os pés.',
            'duration_minutes': 8,
            'video_url': 'https://www.youtube.com/watch?v=IZxyjW7MPJQ'
        },
        {
            'name': 'Cadeira Extensora',
            'description': 'Isolamento de quadríceps',
            'muscle_group': 'legs',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Máquina extensora',
            'instructions': 'Estenda as pernas contra a resistência.',
            'duration_minutes': 6,
            'video_url': 'https://www.youtube.com/watch?v=YyvSfVjQeL0'
        },
        {
            'name': 'Mesa Flexora',
            'description': 'Isolamento de posteriores de coxa',
            'muscle_group': 'legs',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Máquina flexora',
            'instructions': 'Flexione as pernas trazendo calcanhares aos glúteos.',
            'duration_minutes': 6,
            'video_url': 'https://www.youtube.com/watch?v=ELOCsoDSmrg'
        },
        {
            'name': 'Stiff',
            'description': 'Desenvolvimento de posteriores e glúteos',
            'muscle_group': 'legs',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Barra ou halteres',
            'instructions': 'Desça o peso deslizando pelas pernas.',
            'duration_minutes': 8,
            'video_url': 'https://www.youtube.com/watch?v=1uDiW5--rAE'
        },
        {
            'name': 'Afundo com Halteres',
            'description': 'Trabalho unilateral completo',
            'muscle_group': 'legs',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Halteres',
            'instructions': 'Dê um passo à frente e desça até joelho quase tocar o chão.',
            'duration_minutes': 8,
            'video_url': 'https://www.youtube.com/watch?v=QOVaHwm-Q6U'
        },
        {
            'name': 'Afundo Caminhando',
            'description': 'Afundo dinâmico e funcional',
            'muscle_group': 'legs',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Halteres ou peso corporal',
            'instructions': 'Execute afundos alternados caminhando para frente.',
            'duration_minutes': 7,
            'video_url': 'https://www.youtube.com/watch?v=D7KaRcUTQeE'
        },
        {
            'name': 'Passada',
            'description': 'Grande amplitude de movimento',
            'muscle_group': 'legs',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Nenhum ou halteres',
            'instructions': 'Dê passos largos alternando as pernas.',
            'duration_minutes': 7,
            'video_url': 'https://www.youtube.com/watch?v=L8fvypPrzzs'
        },
        {
            'name': 'Hack Squat',
            'description': 'Agachamento em máquina com ângulo',
            'muscle_group': 'legs',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Máquina hack',
            'instructions': 'Desça controladamente na máquina hack.',
            'duration_minutes': 8,
            'video_url': 'https://www.youtube.com/watch?v=0tn5K9NlCfo'
        },
        {
            'name': 'Elevação Pélvica',
            'description': 'Foco em glúteos',
            'muscle_group': 'legs',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Nenhum ou barra',
            'instructions': 'Apoiado no chão, eleve quadril contraindo glúteos.',
            'duration_minutes': 6,
            'video_url': 'https://www.youtube.com/watch?v=wPM8icPu6H8'
        },
        {
            'name': 'Hip Thrust',
            'description': 'Máxima ativação de glúteos',
            'muscle_group': 'legs',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Barra, Banco',
            'instructions': 'Costas no banco, eleve quadril com barra.',
            'duration_minutes': 8,
            'video_url': 'https://www.youtube.com/watch?v=xDmFkJxPzeM'
        },
        {
            'name': 'Panturrilha em Pé',
            'description': 'Desenvolvimento das panturrilhas',
            'muscle_group': 'legs',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Máquina ou step',
            'instructions': 'Eleve-se nas pontas dos pés.',
            'duration_minutes': 5,
            'video_url': 'https://www.youtube.com/watch?v=gwLzBJYoWlI'
        },
        {
            'name': 'Panturrilha Sentado',
            'description': 'Isolamento do sóleo',
            'muscle_group': 'legs',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Máquina de panturrilha',
            'instructions': 'Sentado, eleve calcanhares contra resistência.',
            'duration_minutes': 5,
            'video_url': 'https://www.youtube.com/watch?v=JbyjNymZOt0'
        },
        {
            'name': 'Pistol Squat',
            'description': 'Agachamento unilateral avançado',
            'muscle_group': 'legs',
            'difficulty_level': 'advanced',
            'equipment_needed': 'Nenhum',
            'instructions': 'Agache em uma perna só, outra estendida.',
            'duration_minutes': 7,
            'video_url': 'https://www.youtube.com/watch?v=vq5-vdgJc0I'
        },
        {
            'name': 'Jump Squat',
            'description': 'Agachamento pliométrico',
            'muscle_group': 'legs',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Nenhum',
            'instructions': 'Agache e salte explosivamente.',
            'duration_minutes': 6,
            'video_url': 'https://www.youtube.com/watch?v=Azl5qدسB_Sg'
        },
        {
            'name': 'Box Jump',
            'description': 'Salto em caixa para potência',
            'muscle_group': 'legs',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Caixa ou step',
            'instructions': 'Salte sobre a caixa e desça controladamente.',
            'duration_minutes': 7,
            'video_url': 'https://www.youtube.com/watch?v=NBY9-kTuHEk'
        },
        {
            'name': 'Wall Sit',
            'description': 'Isometria para resistência',
            'muscle_group': 'legs',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Parede',
            'instructions': 'Apoiado na parede, mantenha posição de agachamento.',
            'duration_minutes': 3,
            'video_url': 'https://www.youtube.com/watch?v=y-wV4Venusw'
        },

        # ========================================
        # OMBROS (12 exercícios)
        # ========================================
        {
            'name': 'Desenvolvimento com Barra',
            'description': 'Massa para ombros completos',
            'muscle_group': 'shoulders',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Barra',
            'instructions': 'Empurre a barra acima da cabeça.',
            'duration_minutes': 7,
            'video_url': 'https://www.youtube.com/watch?v=2yjwXTZQDDI'
        },
        {
            'name': 'Desenvolvimento Arnold',
            'description': 'Variação com rotação completa',
            'muscle_group': 'shoulders',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Halteres',
            'instructions': 'Gire halteres durante o movimento de elevação.',
            'duration_minutes': 7,
            'video_url': 'https://www.youtube.com/watch?v=6Z15_WdXmVw'
        },
        {
            'name': 'Elevação Lateral',
            'description': 'Isolamento de deltoide médio',
            'muscle_group': 'shoulders',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Halteres',
            'instructions': 'Eleve halteres lateralmente até altura dos ombros.',
            'duration_minutes': 6,
            'video_url': 'https://www.youtube.com/watch?v=3VcKaXpzqRo'
        },
        {
            'name': 'Elevação Frontal',
            'description': 'Trabalha deltoide anterior',
            'muscle_group': 'shoulders',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Halteres ou barra',
            'instructions': 'Eleve peso à frente até altura dos olhos.',
            'duration_minutes': 6,
            'video_url': 'https://www.youtube.com/watch?v=-t7fuZ0KhDA'
        },
        {
            'name': 'Remada Alta',
            'description': 'Trapézio e deltoides',
            'muscle_group': 'shoulders',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Barra',
            'instructions': 'Puxe barra até próximo ao queixo.',
            'duration_minutes': 6,
            'video_url': 'https://www.youtube.com/watch?v=Q5AWhIscenc'
        },
        {
            'name': 'Crucifixo Invertido',
            'description': 'Deltoide posterior isolado',
            'muscle_group': 'shoulders',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Halteres, Banco',
            'instructions': 'Inclinado, abra halteres lateralmente.',
            'duration_minutes': 6,
            'video_url': 'https://www.youtube.com/watch?v=ttvfGg9d76c'
        },
        {
            'name': 'Desenvolvimento na Máquina',
            'description': 'Trajeto guiado para ombros',
            'muscle_group': 'shoulders',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Máquina shoulder press',
            'instructions': 'Empurre as alças para cima.',
            'duration_minutes': 6,
            'video_url': 'https://www.youtube.com/watch?v=M2rwvNhTOu0'
        },
        {
            'name': 'Encolhimento com Barra',
            'description': 'Massa para trapézio',
            'muscle_group': 'shoulders',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Barra',
            'instructions': 'Eleve ombros em direção às orelhas.',
            'duration_minutes': 5,
            'video_url': 'https://www.youtube.com/watch?v=g6qbq4Lf1FI'
        },
        {
            'name': 'Encolhimento com Halteres',
            'description': 'Variação com maior amplitude',
            'muscle_group': 'shoulders',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Halteres',
            'instructions': 'Segure halteres lateralmente e encolha ombros.',
            'duration_minutes': 5,
            'video_url': 'https://www.youtube.com/watch?v=cJRVVxmytaM'
        },
        {
            'name': 'Elevação W',
            'description': 'Fortalecimento de manguito rotador',
            'muscle_group': 'shoulders',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Halteres leves',
            'instructions': 'Forme W com os braços e eleve.',
            'duration_minutes': 5,
            'video_url': 'https://www.youtube.com/watch?v=XPPfnSEATJA'
        },
        {
            'name': 'Pike Push-up',
            'description': 'Flexão para ombros sem equipamento',
            'muscle_group': 'shoulders',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Nenhum',
            'instructions': 'Corpo em V invertido, flexione braços.',
            'duration_minutes': 6,
            'video_url': 'https://www.youtube.com/watch?v=x4YNjHHyW4Y'
        },

        # ========================================
        # BRAÇOS (15 exercícios)
        # ========================================
        {
            'name': 'Rosca Direta com Barra',
            'description': 'Exercício clássico para bíceps',
            'muscle_group': 'arms',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Barra',
            'instructions': 'Flexione cotovelos levantando a barra.',
            'duration_minutes': 6,
            'video_url': 'https://www.youtube.com/watch?v=kwG2ipFRgfo'
        },
        {
            'name': 'Rosca Alternada',
            'description': 'Trabalho isolado de cada bíceps',
            'muscle_group': 'arms',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Halteres',
            'instructions': 'Alterne flexões de cotovelo com halteres.',
            'duration_minutes': 6,
            'video_url': 'https://www.youtube.com/watch?v=sAq_ocpRh_I'
        },
        {
            'name': 'Rosca Martelo',
            'description': 'Trabalha bíceps e braquial',
            'muscle_group': 'arms',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Halteres',
            'instructions': 'Flexione com pegada neutra (palmas frente a frente).',
            'duration_minutes': 6,
            'video_url': 'https://www.youtube.com/watch?v=zC3nLlEvin4'
        },
        {
            'name': 'Rosca Scott',
            'description': 'Isolamento máximo de bíceps',
            'muscle_group': 'arms',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Banco Scott, Barra W',
            'instructions': 'Braços apoiados, flexione até contração máxima.',
            'duration_minutes': 6,
            'video_url': 'https://www.youtube.com/watch?v=fIWP-FRFNU0'
        },
        {
            'name': 'Rosca Concentrada',
            'description': 'Pico de contração no bíceps',
            'muscle_group': 'arms',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Halter',
            'instructions': 'Sentado, cotovelo apoiado, flexione.',
            'duration_minutes': 5,
            'video_url': 'https://www.youtube.com/watch?v=Jvj2wV0vOYU'
        },
        {
            'name': 'Tríceps Testa',
            'description': 'Isolamento de tríceps deitado',
            'muscle_group': 'arms',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Barra W',
            'instructions': 'Deitado, desça barra até próximo à testa.',
            'duration_minutes': 6,
            'video_url': 'https://www.youtube.com/watch?v=d_KZxkY_0cM'
        },
        {
            'name': 'Tríceps Pulley',
            'description': 'Extensão de tríceps no cabo',
            'muscle_group': 'arms',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Polia alta',
            'instructions': 'Empurre a barra para baixo estendendo cotovelos.',
            'duration_minutes': 6,
            'video_url': 'https://www.youtube.com/watch?v=2-LAMcpzODU'
        },
        {
            'name': 'Tríceps Francês',
            'description': 'Extensão acima da cabeça',
            'muscle_group': 'arms',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Halter ou barra',
            'instructions': 'Braços acima da cabeça, desça peso atrás.',
            'duration_minutes': 6,
            'video_url': 'https://www.youtube.com/watch?v=Zib6vB3zSLI'
        },
        {
            'name': 'Tríceps Corda',
            'description': 'Extensão com corda para maior amplitude',
            'muscle_group': 'arms',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Polia alta, Corda',
            'instructions': 'Abra a corda na parte final do movimento.',
            'duration_minutes': 6,
            'video_url': 'https://www.youtube.com/watch?v=kiuVA0gs3EI'
        },
        {
            'name': 'Mergulho no Banco',
            'description': 'Tríceps com peso corporal',
            'muscle_group': 'arms',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Banco',
            'instructions': 'Mãos no banco atrás de você, flexione cotovelos.',
            'duration_minutes': 5,
            'video_url': 'https://www.youtube.com/watch?v=0326dy_-CzM'
        },
        {
            'name': 'Dips para Tríceps',
            'description': 'Exercício avançado em barras paralelas',
            'muscle_group': 'arms',
            'difficulty_level': 'advanced',
            'equipment_needed': 'Barras paralelas',
            'instructions': 'Corpo vertical, desça flexionando cotovelos.',
            'duration_minutes': 6,
            'video_url': 'https://www.youtube.com/watch?v=yN6Q1UI_xkE'
        },
        {
            'name': 'Rosca Inversa',
            'description': 'Trabalha antebraços e braquial',
            'muscle_group': 'arms',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Barra',
            'instructions': 'Pegada pronada, flexione cotovelos.',
            'duration_minutes': 5,
            'video_url': 'https://www.youtube.com/watch?v=nRiJVZDpdL0'
        },
        {
            'name': 'Rosca Punho',
            'description': 'Fortalecimento de antebraços',
            'muscle_group': 'arms',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Barra ou halteres',
            'instructions': 'Antebraços apoiados, flexione apenas os punhos.',
            'duration_minutes': 4,
            'video_url': 'https://www.youtube.com/watch?v=28ttfDeVfqg'
        },
        {
            'name': 'Kickback de Tríceps',
            'description': 'Isolamento unilateral de tríceps',
            'muscle_group': 'arms',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Halter',
            'instructions': 'Inclinado, estenda cotovelo para trás.',
            'duration_minutes': 5,
            'video_url': 'https://www.youtube.com/watch?v=6SS6K3lAwZ8'
        },
        {
            'name': 'Close Grip Bench',
            'description': 'Supino com pegada fechada para tríceps',
            'muscle_group': 'arms',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Barra, Banco',
            'instructions': 'Pegada mais estreita, desça controladamente.',
            'duration_minutes': 7,
            'video_url': 'https://www.youtube.com/watch?v=nEF0bv2FW94'
        },

        # ========================================
        # ABDÔMEN/CORE (13 exercícios)
        # ========================================
        {
            'name': 'Prancha Frontal',
            'description': 'Isometria fundamental para core',
            'muscle_group': 'abs',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Nenhum',
            'instructions': 'Corpo reto apoiado nos antebraços.',
            'duration_minutes': 3,
            'video_url': 'https://www.youtube.com/watch?v=ASdvN_XEl_c'
        },
        {
            'name': 'Prancha Lateral',
            'description': 'Trabalha oblíquos e estabilizadores',
            'muscle_group': 'abs',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Nenhum',
            'instructions': 'Apoiado em um antebraço, corpo lateral.',
            'duration_minutes': 3,
            'video_url': 'https://www.youtube.com/watch?v=K2VljzCC24Y'
        },
        {
            'name': 'Abdominal Tradicional',
            'description': 'Crunch básico',
            'muscle_group': 'abs',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Nenhum',
            'instructions': 'Deitado, flexione tronco em direção aos joelhos.',
            'duration_minutes': 4,
            'video_url': 'https://www.youtube.com/watch?v=Xyd_fa5zoEU'
        },
        {
            'name': 'Abdominal Canivete',
            'description': 'Trabalha reto abdominal completo',
            'muscle_group': 'abs',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Nenhum',
            'instructions': 'Deitado, eleve tronco e pernas simultaneamente.',
            'duration_minutes': 5,
            'video_url': 'https://www.youtube.com/watch?v=Ep5YN338XoY'
        },
        {
            'name': 'Bicicleta',
            'description': 'Trabalho dinâmico de oblíquos',
            'muscle_group': 'abs',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Nenhum',
            'instructions': 'Alterne cotovelo com joelho oposto.',
            'duration_minutes': 4,
            'video_url': 'https://www.youtube.com/watch?v=9FGilxCbdz8'
        },
        {
            'name': 'Elevação de Pernas',
            'description': 'Foco em abdômen inferior',
            'muscle_group': 'abs',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Nenhum',
            'instructions': 'Deitado, eleve pernas estendidas até vertical.',
            'duration_minutes': 4,
            'video_url': 'https://www.youtube.com/watch?v=JB2oyawG9KI'
        },
        {
            'name': 'Mountain Climber',
            'description': 'Cardio integrado com core',
            'muscle_group': 'abs',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Nenhum',
            'instructions': 'Posição de prancha, alterne joelhos ao peito.',
            'duration_minutes': 5,
            'video_url': 'https://www.youtube.com/watch?v=nmwgirgXLYM'
        },
        {
            'name': 'Russian Twist',
            'description': 'Rotação para oblíquos',
            'muscle_group': 'abs',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Peso opcional',
            'instructions': 'Sentado, gire tronco de lado a lado.',
            'duration_minutes': 4,
            'video_url': 'https://www.youtube.com/watch?v=wkD8rjkodUI'
        },
        {
            'name': 'Abdominal na Polia',
            'description': 'Resistência progressiva',
            'muscle_group': 'abs',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Polia alta, Corda',
            'instructions': 'Ajoelhado, flexione tronco puxando cabo.',
            'duration_minutes': 5,
            'video_url': 'https://www.youtube.com/watch?v=C9lqnCrrowU'
        },
        {
            'name': 'Dead Bug',
            'description': 'Estabilização e coordenação',
            'muscle_group': 'abs',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Nenhum',
            'instructions': 'Deitado, alterne braço e perna opostos.',
            'duration_minutes': 4,
            'video_url': 'https://www.youtube.com/watch?v=4XLEnwUr1d8'
        },
        {
            'name': 'Hollow Body Hold',
            'description': 'Isometria avançada',
            'muscle_group': 'abs',
            'difficulty_level': 'advanced',
            'equipment_needed': 'Nenhum',
            'instructions': 'Corpo arqueado, braços e pernas elevados.',
            'duration_minutes': 3,
            'video_url': 'https://www.youtube.com/watch?v=LlDNef_Ztsc'
        },
        {
            'name': 'V-Up',
            'description': 'Movimento completo e dinâmico',
            'muscle_group': 'abs',
            'difficulty_level': 'advanced',
            'equipment_needed': 'Nenhum',
            'instructions': 'Forme V com o corpo tocando mãos nos pés.',
            'duration_minutes': 5,
            'video_url': 'https://www.youtube.com/watch?v=7UVgs18Y1P4'
        },
        {
            'name': 'Pallof Press',
            'description': 'Anti-rotação para core',
            'muscle_group': 'abs',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Banda elástica ou cabo',
            'instructions': 'Resista à rotação empurrando peso.',
            'duration_minutes': 5,
            'video_url': 'https://www.youtube.com/watch?v=AH_QZLm_0-s'
        },

        # ========================================
        # CARDIO/CORPO INTEIRO (10 exercícios)
        # ========================================
        {
            'name': 'Burpee Completo',
            'description': 'Exercício metabólico explosivo',
            'muscle_group': 'cardio',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Nenhum',
            'instructions': 'Agache, prancha, flexão, salte.',
            'duration_minutes': 6,
            'video_url': 'https://www.youtube.com/watch?v=TU8QYVW0gDU'
        },
        {
            'name': 'Jumping Jacks',
            'description': 'Aquecimento e cardio leve',
            'muscle_group': 'cardio',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Nenhum',
            'instructions': 'Salte abrindo pernas e braços.',
            'duration_minutes': 5,
            'video_url': 'https://www.youtube.com/watch?v=c4DAnQ6DtF8'
        },
        {
            'name': 'High Knees',
            'description': 'Corrida estacionária intensa',
            'muscle_group': 'cardio',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Nenhum',
            'instructions': 'Eleve joelhos alternadamente em ritmo rápido.',
            'duration_minutes': 5,
            'video_url': 'https://www.youtube.com/watch?v=8opcQdC-V-U'
        },
        {
            'name': 'Corrida Esteira',
            'description': 'Cardio clássico controlado',
            'muscle_group': 'cardio',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Esteira',
            'instructions': 'Mantenha ritmo constante.',
            'duration_minutes': 20,
            'video_url': 'https://www.youtube.com/watch?v=brFHyOtTwH4'
        },
        {
            'name': 'Bike Ergométrica',
            'description': 'Cardio de baixo impacto',
            'muscle_group': 'cardio',
            'difficulty_level': 'beginner',
            'equipment_needed': 'Bicicleta ergométrica',
            'instructions': 'Pedale mantendo cadência adequada.',
            'duration_minutes': 20,
            'video_url': 'https://www.youtube.com/watch?v=79BPXWZy-vE'
        },
        {
            'name': 'Pular Corda',
            'description': 'Cardio intenso e coordenação',
            'muscle_group': 'cardio',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Corda',
            'instructions': 'Salte ritmicamente girando a corda.',
            'duration_minutes': 10,
            'video_url': 'https://www.youtube.com/watch?v=FJmRQ5iTXKE'
        },
        {
            'name': 'Battle Rope',
            'description': 'Ondulações para cardio e força',
            'muscle_group': 'cardio',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Cordas battle rope',
            'instructions': 'Crie ondas alternadas com as cordas.',
            'duration_minutes': 8,
            'video_url': 'https://www.youtube.com/watch?v=w8lorDQ55rU'
        },
        {
            'name': 'Kettlebell Swing',
            'description': 'Explosão e cardio combinados',
            'muscle_group': 'full_body',
            'difficulty_level': 'intermediate',
            'equipment_needed': 'Kettlebell',
            'instructions': 'Balance kettlebell usando quadril.',
            'duration_minutes': 7,
            'video_url': 'https://www.youtube.com/watch?v=YSxHifyI6s8'
        },
        {
            'name': 'Thruster',
            'description': 'Agachamento com desenvolvimento',
            'muscle_group': 'full_body',
            'difficulty_level': 'advanced',
            'equipment_needed': 'Barra ou halteres',
            'instructions': 'Agache e empurre peso acima da cabeça.',
            'duration_minutes': 8,
            'video_url': 'https://www.youtube.com/watch?v=L219ltL15zk'
        },
        {
            'name': 'Man Maker',
            'description': 'Combinação de movimentos complexos',
            'muscle_group': 'full_body',
            'difficulty_level': 'advanced',
            'equipment_needed': 'Halteres',
            'instructions': 'Burpee + remadas + thruster.',
            'duration_minutes': 10,
            'video_url': 'https://www.youtube.com/watch?v=4YoJE59uTJQ'
        },
    ]
    
    print(f"Total de exercícios para criar: {len(exercicios)}")
    
    for dados in exercicios:
        exercicio, created = Exercise.objects.get_or_create(
            name=dados['name'],
            defaults=dados
        )
        if created:
            print(f"✅ {exercicio.name}")
        else:
            print(f"⏭️  {exercicio.name}")
    
    return Exercise.objects.all()


def criar_treinos():
    """Criar treinos de exemplo"""
    treinos = [
        {
            'name': 'Push - Peito e Tríceps',
            'description': 'Treino focado em músculos de empurrar',
            'difficulty_level': 'intermediate',
            'estimated_duration': 50,
            'target_muscle_groups': 'chest, shoulders, arms',
            'workout_type': 'strength',
            'calories_estimate': 320,
            'is_recommended': True,
            'equipment_needed': 'Barra, Banco, Halteres',
            'exercicios': [
                {'name': 'Supino Reto com Barra', 'sets': 4, 'reps': '8-12', 'rest_time': 60, 'order': 1},
                {'name': 'Supino Inclinado', 'sets': 3, 'reps': '10-12', 'rest_time': 60, 'order': 2},
                {'name': 'Crucifixo com Halteres', 'sets': 3, 'reps': '12-15', 'rest_time': 45, 'order': 3},
                {'name': 'Tríceps Pulley', 'sets': 3, 'reps': '12-15', 'rest_time': 45, 'order': 4},
                {'name': 'Tríceps Testa', 'sets': 3, 'reps': '10-12', 'rest_time': 45, 'order': 5},
            ]
        },
        {
            'name': 'Pull - Costas e Bíceps',
            'description': 'Treino focado em músculos de puxar',
            'difficulty_level': 'intermediate',
            'estimated_duration': 50,
            'target_muscle_groups': 'back, arms',
            'workout_type': 'strength',
            'calories_estimate': 310,
            'is_recommended': True,
            'equipment_needed': 'Barra, Barra fixa, Halteres',
            'exercicios': [
                {'name': 'Barra Fixa Pronada', 'sets': 4, 'reps': '6-10', 'rest_time': 90, 'order': 1},
                {'name': 'Remada Curvada com Barra', 'sets': 4, 'reps': '8-12', 'rest_time': 60, 'order': 2},
                {'name': 'Remada Unilateral com Halter', 'sets': 3, 'reps': '10-12', 'rest_time': 60, 'order': 3},
                {'name': 'Rosca Direta com Barra', 'sets': 3, 'reps': '10-12', 'rest_time': 45, 'order': 4},
                {'name': 'Rosca Martelo', 'sets': 3, 'reps': '12-15', 'rest_time': 45, 'order': 5},
            ]
        },
        {
            'name': 'Legs - Pernas Completo',
            'description': 'Treino completo de membros inferiores',
            'difficulty_level': 'advanced',
            'estimated_duration': 60,
            'target_muscle_groups': 'legs',
            'workout_type': 'strength',
            'calories_estimate': 420,
            'is_recommended': True,
            'equipment_needed': 'Barra, Leg Press, Máquinas',
            'exercicios': [
                {'name': 'Agachamento Livre com Barra', 'sets': 4, 'reps': '8-12', 'rest_time': 120, 'order': 1},
                {'name': 'Leg Press 45°', 'sets': 4, 'reps': '12-15', 'rest_time': 90, 'order': 2},
                {'name': 'Stiff', 'sets': 3, 'reps': '10-12', 'rest_time': 60, 'order': 3},
                {'name': 'Cadeira Extensora', 'sets': 3, 'reps': '12-15', 'rest_time': 45, 'order': 4},
                {'name': 'Mesa Flexora', 'sets': 3, 'reps': '12-15', 'rest_time': 45, 'order': 5},
                {'name': 'Panturrilha em Pé', 'sets': 4, 'reps': '15-20', 'rest_time': 30, 'order': 6},
            ]
        },
        {
            'name': 'Upper - Tronco Completo',
            'description': 'Treino de todo tronco superior',
            'difficulty_level': 'intermediate',
            'estimated_duration': 55,
            'target_muscle_groups': 'chest, back, shoulders, arms',
            'workout_type': 'strength',
            'calories_estimate': 340,
            'is_recommended': True,
            'equipment_needed': 'Variado',
            'exercicios': [
                {'name': 'Supino Reto com Barra', 'sets': 3, 'reps': '8-10', 'rest_time': 60, 'order': 1},
                {'name': 'Barra Fixa Pronada', 'sets': 3, 'reps': '6-10', 'rest_time': 90, 'order': 2},
                {'name': 'Desenvolvimento com Barra', 'sets': 3, 'reps': '8-10', 'rest_time': 60, 'order': 3},
                {'name': 'Rosca Direta com Barra', 'sets': 3, 'reps': '10-12', 'rest_time': 45, 'order': 4},
                {'name': 'Tríceps Pulley', 'sets': 3, 'reps': '12-15', 'rest_time': 45, 'order': 5},
            ]
        },
        {
            'name': 'Full Body Iniciante',
            'description': 'Treino completo para iniciantes',
            'difficulty_level': 'beginner',
            'estimated_duration': 40,
            'target_muscle_groups': 'full_body',
            'workout_type': 'full_body',
            'calories_estimate': 250,
            'is_recommended': True,
            'equipment_needed': 'Básico',
            'exercicios': [
                {'name': 'Agachamento Búlgaro', 'sets': 3, 'reps': '12', 'rest_time': 60, 'order': 1},
                {'name': 'Flexão de Braço Tradicional', 'sets': 3, 'reps': '10-15', 'rest_time': 60, 'order': 2},
                {'name': 'Remada Unilateral com Halter', 'sets': 3, 'reps': '12', 'rest_time': 60, 'order': 3},
                {'name': 'Desenvolvimento com Barra', 'sets': 3, 'reps': '10', 'rest_time': 60, 'order': 4},
                {'name': 'Prancha Frontal', 'sets': 3, 'reps': '45 seg', 'rest_time': 45, 'order': 5},
            ]
        },
        {
            'name': 'HIIT Cardio Explosivo',
            'description': 'Treino de alta intensidade para queima de gordura',
            'difficulty_level': 'intermediate',
            'estimated_duration': 25,
            'target_muscle_groups': 'full_body, cardio',
            'workout_type': 'cardio',
            'calories_estimate': 380,
            'is_recommended': True,
            'equipment_needed': 'Nenhum',
            'exercicios': [
                {'name': 'Burpee Completo', 'sets': 4, 'reps': '12', 'rest_time': 30, 'order': 1},
                {'name': 'Mountain Climber', 'sets': 4, 'reps': '30 seg', 'rest_time': 20, 'order': 2},
                {'name': 'Jumping Jacks', 'sets': 4, 'reps': '40', 'rest_time': 20, 'order': 3},
                {'name': 'High Knees', 'sets': 4, 'reps': '30 seg', 'rest_time': 30, 'order': 4},
            ]
        },
        {
            'name': 'Lower Body - Pernas e Glúteos',
            'description': 'Foco em membros inferiores com exercícios variados',
            'difficulty_level': 'intermediate',
            'estimated_duration': 45,
            'target_muscle_groups': 'legs',
            'workout_type': 'strength',
            'calories_estimate': 350,
            'is_recommended': True,
            'equipment_needed': 'Halteres, Banco',
            'exercicios': [
                {'name': 'Agachamento Búlgaro', 'sets': 4, 'reps': '12', 'rest_time': 60, 'order': 1},
                {'name': 'Hip Thrust', 'sets': 4, 'reps': '15', 'rest_time': 60, 'order': 2},
                {'name': 'Afundo com Halteres', 'sets': 3, 'reps': '12', 'rest_time': 60, 'order': 3},
                {'name': 'Stiff', 'sets': 3, 'reps': '12', 'rest_time': 60, 'order': 4},
                {'name': 'Panturrilha em Pé', 'sets': 3, 'reps': '20', 'rest_time': 30, 'order': 5},
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
    print("=" * 70)
    print("🚀 POPULANDO BANCO DE DADOS FITAI - 100 EXERCÍCIOS")
    print("=" * 70)
    
    print("\n1️⃣  CRIANDO 100 EXERCÍCIOS...")
    print("-" * 70)
    criar_exercicios()
    
    print("\n2️⃣  CRIANDO 7 TREINOS FUNDAMENTAIS...")
    print("-" * 70)
    criar_treinos()
    
    print("\n" + "=" * 70)
    print("✅ BANCO POPULADO COM SUCESSO!")
    print("=" * 70)
    print(f"\n📊 ESTATÍSTICAS:")
    print(f"   • Exercícios: {Exercise.objects.count()}")
    print(f"   • Treinos: {Workout.objects.count()}")
    print(f"   • Relações Treino-Exercício: {WorkoutExercise.objects.count()}")
    print("\n💡 PRÓXIMOS PASSOS:")
    print("   1. Teste o app Flutter - acesse página de treinos")
    print("   2. Verifique se treinos aparecem com exercícios corretos")
    print("   3. Teste geração de treino com IA")
    print("   4. IA usará estes exercícios como base para gerar treinos personalizados")
    print("\n🎯 TREINOS DISPONÍVEIS:")
    print("   • Push/Pull/Legs (divisão clássica)")
    print("   • Upper/Lower")
    print("   • Full Body Iniciante")
    print("   • HIIT Cardio")
    print("\n")

if __name__ == '__main__':
    main()