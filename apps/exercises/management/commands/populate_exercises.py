# apps/exercises/management/commands/populate_exercises.py

from django.core.management.base import BaseCommand
from apps.exercises.models import Exercise

class Command(BaseCommand):
    help = 'Popula o banco de dados com exercícios reais e estruturados'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🏋️‍♂️ Iniciando população de exercícios...'))

        # Limpar exercícios existentes (opcional)
        Exercise.objects.all().delete()
        self.stdout.write('🗑️ Exercícios anteriores removidos')

        exercises_data = [
            # PEITO (CHEST) - 10 exercícios
            {
                'name': 'Flexão de Braço Tradicional',
                'description': 'Exercício clássico que trabalha peito, ombros e tríceps usando o peso corporal.',
                'muscle_group': 'chest',
                'difficulty_level': 'beginner',
                'equipment_needed': 'Nenhum',
                'duration_minutes': 5,
                'calories_per_minute': 8.0,
                'instructions': '1. Deite de bruços no chão\n2. Apoie as mãos no chão na largura dos ombros\n3. Mantenha o corpo reto\n4. Desça até quase tocar o peito no chão\n5. Empurre de volta à posição inicial'
            },
            {
                'name': 'Flexão de Braço Inclinada',
                'description': 'Variação mais fácil da flexão tradicional, ideal para iniciantes.',
                'muscle_group': 'chest',
                'difficulty_level': 'beginner',
                'equipment_needed': 'Banco ou superfície elevada',
                'duration_minutes': 5,
                'calories_per_minute': 6.5,
                'instructions': '1. Apoie as mãos em uma superfície elevada (banco/sofá)\n2. Corpo em linha reta\n3. Desça controladamente\n4. Empurre de volta\n5. Mais fácil que flexão no chão'
            },
            {
                'name': 'Supino com Halteres',
                'description': 'Exercício fundamental para desenvolvimento do peitoral com halteres.',
                'muscle_group': 'chest',
                'difficulty_level': 'intermediate',
                'equipment_needed': 'Halteres, Banco',
                'duration_minutes': 8,
                'calories_per_minute': 7.5,
                'instructions': '1. Deite no banco com halter em cada mão\n2. Braços estendidos acima do peito\n3. Desça os halteres controladamente\n4. Empurre de volta à posição inicial\n5. Mantenha os pés firmes no chão'
            },
            {
                'name': 'Crucifixo com Halteres',
                'description': 'Movimento de isolamento para o peitoral com amplitude completa.',
                'muscle_group': 'chest',
                'difficulty_level': 'intermediate',
                'equipment_needed': 'Halteres, Banco',
                'duration_minutes': 6,
                'calories_per_minute': 6.8,
                'instructions': '1. Deite no banco com halteres nas mãos\n2. Braços ligeiramente flexionados\n3. Abra os braços em movimento circular\n4. Sinta o alongamento no peito\n5. Retorne controladamente'
            },
            {
                'name': 'Flexão Diamante',
                'description': 'Variação avançada que enfatiza tríceps e peitoral interno.',
                'muscle_group': 'chest',
                'difficulty_level': 'advanced',
                'equipment_needed': 'Nenhum',
                'duration_minutes': 4,
                'calories_per_minute': 9.2,
                'instructions': '1. Posição de flexão\n2. Junte as mãos formando um diamante\n3. Polegares e indicadores se tocando\n4. Desça mantendo cotovelos próximos\n5. Movimento mais difícil que flexão normal'
            },
            
            # COSTAS (BACK) - 12 exercícios
            {
                'name': 'Remada Curvada com Halteres',
                'description': 'Exercício fundamental para desenvolver a musculatura das costas.',
                'muscle_group': 'back',
                'difficulty_level': 'intermediate',
                'equipment_needed': 'Halteres',
                'duration_minutes': 8,
                'calories_per_minute': 7.8,
                'instructions': '1. Pés na largura dos ombros\n2. Curve o tronco mantendo costas retas\n3. Halteres nas mãos com braços estendidos\n4. Puxe os cotovelos para trás\n5. Contraia as escápulas no topo'
            },
            {
                'name': 'Superman',
                'description': 'Exercício isométrico que fortalece a região lombar e glúteos.',
                'muscle_group': 'back',
                'difficulty_level': 'beginner',
                'equipment_needed': 'Nenhum',
                'duration_minutes': 5,
                'calories_per_minute': 5.2,
                'instructions': '1. Deite de bruços no chão\n2. Braços estendidos à frente\n3. Levante simultaneamente braços, peito e pernas\n4. Mantenha a posição por 2-3 segundos\n5. Desça controladamente'
            },
            {
                'name': 'Pullover com Halter',
                'description': 'Movimento que trabalha peito, costas e músculos respiratórios.',
                'muscle_group': 'back',
                'difficulty_level': 'intermediate',
                'equipment_needed': 'Halter, Banco',
                'duration_minutes': 6,
                'calories_per_minute': 6.5,
                'instructions': '1. Deite no banco segurando um halter\n2. Braços estendidos sobre o peito\n3. Desça o peso atrás da cabeça\n4. Mantenha braços ligeiramente flexionados\n5. Retorne à posição inicial'
            },

            # OMBROS (SHOULDERS) - 10 exercícios
            {
                'name': 'Desenvolvimento com Halteres',
                'description': 'Exercício básico para desenvolvimento dos ombros.',
                'muscle_group': 'shoulders',
                'difficulty_level': 'beginner',
                'equipment_needed': 'Halteres',
                'duration_minutes': 7,
                'calories_per_minute': 7.2,
                'instructions': '1. Sentado ou em pé, halteres na altura dos ombros\n2. Palmas voltadas para frente\n3. Empurre os pesos para cima\n4. Estenda completamente os braços\n5. Desça controladamente'
            },
            {
                'name': 'Elevação Lateral',
                'description': 'Isolamento para a porção lateral do deltóide.',
                'muscle_group': 'shoulders',
                'difficulty_level': 'beginner',
                'equipment_needed': 'Halteres',
                'duration_minutes': 5,
                'calories_per_minute': 6.0,
                'instructions': '1. Em pé, halter em cada mão ao lado do corpo\n2. Braços ligeiramente flexionados\n3. Levante lateralmente até altura dos ombros\n4. Pause no topo\n5. Desça lentamente'
            },
            {
                'name': 'Elevação Frontal',
                'description': 'Trabalha a porção anterior do deltóide.',
                'muscle_group': 'shoulders',
                'difficulty_level': 'beginner',
                'equipment_needed': 'Halteres',
                'duration_minutes': 5,
                'calories_per_minute': 5.8,
                'instructions': '1. Em pé, halteres na frente das coxas\n2. Palmas voltadas para baixo\n3. Levante à frente até altura dos ombros\n4. Braços ligeiramente flexionados\n5. Controle a descida'
            },

            # BRAÇOS (ARMS) - 12 exercícios
            {
                'name': 'Rosca Direta com Halteres',
                'description': 'Exercício clássico para desenvolvimento do bíceps.',
                'muscle_group': 'arms',
                'difficulty_level': 'beginner',
                'equipment_needed': 'Halteres',
                'duration_minutes': 6,
                'calories_per_minute': 6.5,
                'instructions': '1. Em pé, halter em cada mão\n2. Braços estendidos ao lado do corpo\n3. Flexione o cotovelo levantando o peso\n4. Contraia o bíceps no topo\n5. Desça controladamente'
            },
            {
                'name': 'Tríceps Francês',
                'description': 'Exercício de isolamento para tríceps.',
                'muscle_group': 'arms',
                'difficulty_level': 'intermediate',
                'equipment_needed': 'Halter',
                'duration_minutes': 6,
                'calories_per_minute': 6.2,
                'instructions': '1. Sentado, segure um halter com as duas mãos\n2. Braços estendidos acima da cabeça\n3. Flexione apenas os cotovelos\n4. Desça o peso atrás da cabeça\n5. Estenda de volta'
            },
            {
                'name': 'Rosca Martelo',
                'description': 'Variação da rosca que trabalha bíceps e antebraço.',
                'muscle_group': 'arms',
                'difficulty_level': 'beginner',
                'equipment_needed': 'Halteres',
                'duration_minutes': 6,
                'calories_per_minute': 6.0,
                'instructions': '1. Em pé, halteres com pegada neutra\n2. Polegares apontando para cima\n3. Flexione alternadamente\n4. Mantenha pulsos firmes\n5. Movimento controlado'
            },

            # PERNAS (LEGS) - 15 exercícios
            {
                'name': 'Agachamento Livre',
                'description': 'O rei dos exercícios para pernas, trabalha quadríceps, glúteos e posterior.',
                'muscle_group': 'legs',
                'difficulty_level': 'beginner',
                'equipment_needed': 'Nenhum',
                'duration_minutes': 8,
                'calories_per_minute': 8.5,
                'instructions': '1. Pés na largura dos ombros\n2. Desça flexionando quadril e joelhos\n3. Mantenha peito erguido\n4. Desça até coxas paralelas ao chão\n5. Empurre pelos calcanhares para subir'
            },
            {
                'name': 'Lunges (Afundo)',
                'description': 'Exercício unilateral que trabalha pernas e melhora equilíbrio.',
                'muscle_group': 'legs',
                'difficulty_level': 'beginner',
                'equipment_needed': 'Nenhum',
                'duration_minutes': 7,
                'calories_per_minute': 7.8,
                'instructions': '1. Em pé, dê um passo largo à frente\n2. Desça flexionando ambos os joelhos\n3. Joelho da frente não ultrapassa o pé\n4. Empurre para voltar à posição inicial\n5. Alterne as pernas'
            },
            {
                'name': 'Agachamento Sumo',
                'description': 'Variação que enfatiza glúteos e parte interna da coxa.',
                'muscle_group': 'legs',
                'difficulty_level': 'intermediate',
                'equipment_needed': 'Nenhum ou Halter',
                'duration_minutes': 6,
                'calories_per_minute': 8.2,
                'instructions': '1. Pés mais largos que os ombros\n2. Pontas dos pés ligeiramente para fora\n3. Desça mantendo joelhos alinhados\n4. Mantenha tronco ereto\n5. Foque na contração dos glúteos'
            },
            {
                'name': 'Elevação de Panturrilha',
                'description': 'Exercício específico para desenvolvimento das panturrilhas.',
                'muscle_group': 'legs',
                'difficulty_level': 'beginner',
                'equipment_needed': 'Nenhum',
                'duration_minutes': 5,
                'calories_per_minute': 4.5,
                'instructions': '1. Em pé, pés na largura dos ombros\n2. Levante-se na ponta dos pés\n3. Contraia as panturrilhas no topo\n4. Desça controladamente\n5. Pode usar parede para apoio'
            },

            # ABDÔMEN (ABS) - 12 exercícios
            {
                'name': 'Abdominal Tradicional',
                'description': 'Exercício básico para fortalecimento do core.',
                'muscle_group': 'abs',
                'difficulty_level': 'beginner',
                'equipment_needed': 'Nenhum',
                'duration_minutes': 5,
                'calories_per_minute': 6.0,
                'instructions': '1. Deite de costas, joelhos flexionados\n2. Mãos atrás da cabeça (sem puxar o pescoço)\n3. Contraia o abdômen levantando o tronco\n4. Expire na subida\n5. Desça controladamente'
            },
            {
                'name': 'Prancha (Plank)',
                'description': 'Exercício isométrico que fortalece todo o core.',
                'muscle_group': 'abs',
                'difficulty_level': 'beginner',
                'equipment_needed': 'Nenhum',
                'duration_minutes': 3,
                'calories_per_minute': 5.5,
                'instructions': '1. Posição de flexão apoiado nos antebraços\n2. Corpo em linha reta\n3. Contraia abdômen e glúteos\n4. Respire normalmente\n5. Mantenha a posição pelo tempo determinado'
            },
            {
                'name': 'Bicicleta (Bicycle Crunch)',
                'description': 'Exercício dinâmico que trabalha oblíquos e reto abdominal.',
                'muscle_group': 'abs',
                'difficulty_level': 'intermediate',
                'equipment_needed': 'Nenhum',
                'duration_minutes': 5,
                'calories_per_minute': 7.2,
                'instructions': '1. Deite de costas, mãos atrás da cabeça\n2. Joelhos flexionados no ar\n3. Leve cotovelo direito ao joelho esquerdo\n4. Alterne os lados em movimento de pedalada\n5. Mantenha ritmo constante'
            },
            {
                'name': 'Elevação de Pernas',
                'description': 'Foca na porção inferior do abdômen.',
                'muscle_group': 'abs',
                'difficulty_level': 'intermediate',
                'equipment_needed': 'Nenhum',
                'duration_minutes': 4,
                'calories_per_minute': 6.8,
                'instructions': '1. Deite de costas, braços ao lado do corpo\n2. Pernas estendidas\n3. Levante as pernas até 90 graus\n4. Desça lentamente sem tocar o chão\n5. Mantenha lombar no chão'
            },

            # CARDIO - 10 exercícios
            {
                'name': 'Burpees',
                'description': 'Exercício de alta intensidade que trabalha corpo inteiro.',
                'muscle_group': 'cardio',
                'difficulty_level': 'advanced',
                'equipment_needed': 'Nenhum',
                'duration_minutes': 4,
                'calories_per_minute': 12.0,
                'instructions': '1. Em pé, desça em agachamento\n2. Apoie as mãos no chão\n3. Salte as pernas para trás (posição flexão)\n4. Faça uma flexão (opcional)\n5. Volte ao agachamento e salte para cima'
            },
            {
                'name': 'Jumping Jacks',
                'description': 'Exercício cardiovascular clássico e eficiente.',
                'muscle_group': 'cardio',
                'difficulty_level': 'beginner',
                'equipment_needed': 'Nenhum',
                'duration_minutes': 5,
                'calories_per_minute': 9.5,
                'instructions': '1. Em pé, pés juntos, braços ao lado\n2. Salte abrindo pernas\n3. Simultaneamente levante braços acima da cabeça\n4. Salte voltando à posição inicial\n5. Mantenha ritmo constante'
            },
            {
                'name': 'High Knees (Joelho Alto)',
                'description': 'Corrida no lugar com elevação dos joelhos.',
                'muscle_group': 'cardio',
                'difficulty_level': 'beginner',
                'equipment_needed': 'Nenhum',
                'duration_minutes': 3,
                'calories_per_minute': 10.0,
                'instructions': '1. Em pé, comece correndo no lugar\n2. Eleve os joelhos o máximo possível\n3. Tente tocar o peito com os joelhos\n4. Mantenha braços em movimento\n5. Ritmo acelerado'
            },
            {
                'name': 'Mountain Climbers',
                'description': 'Exercício dinâmico que combina cardio e fortalecimento.',
                'muscle_group': 'cardio',
                'difficulty_level': 'intermediate',
                'equipment_needed': 'Nenhum',
                'duration_minutes': 4,
                'calories_per_minute': 11.5,
                'instructions': '1. Posição de prancha alta\n2. Traga um joelho em direção ao peito\n3. Retorne e alterne rapidamente\n4. Mantenha quadris estáveis\n5. Movimento rápido e controlado'
            },

            # CORPO INTEIRO (FULL_BODY) - 8 exercícios
            {
                'name': 'Thruster com Halteres',
                'description': 'Movimento composto que trabalha pernas, core e ombros.',
                'muscle_group': 'full_body',
                'difficulty_level': 'intermediate',
                'equipment_needed': 'Halteres',
                'duration_minutes': 8,
                'calories_per_minute': 10.5,
                'instructions': '1. Agachamento com halteres nos ombros\n2. Desça em agachamento completo\n3. Ao subir, empurre halteres acima da cabeça\n4. Movimento fluído e contínuo\n5. Combine força e cardio'
            },
            {
                'name': 'Bear Crawl',
                'description': 'Movimento animal que desafia coordenação e resistência.',
                'muscle_group': 'full_body',
                'difficulty_level': 'intermediate',
                'equipment_needed': 'Nenhum',
                'duration_minutes': 5,
                'calories_per_minute': 8.8,
                'instructions': '1. Posição quadrúpede, joelhos elevados\n2. Caminhe com mãos e pés\n3. Joelhos próximos ao chão\n4. Mantenha core ativo\n5. Movimento coordenado e controlado'
            },
            {
                'name': 'Turkish Get-Up',
                'description': 'Movimento complexo de mobilidade e estabilidade.',
                'muscle_group': 'full_body',
                'difficulty_level': 'advanced',
                'equipment_needed': 'Halter ou Kettlebell',
                'duration_minutes': 10,
                'calories_per_minute': 7.5,
                'instructions': '1. Deite com peso estendido acima\n2. Siga sequência específica para ficar em pé\n3. Mantenha peso sempre acima da cabeça\n4. Movimento lento e controlado\n5. Requer prática e coordenação'
            }
        ]

        # Criar exercícios
        created_count = 0
        for exercise_data in exercises_data:
            exercise, created = Exercise.objects.get_or_create(
                name=exercise_data['name'],
                defaults=exercise_data
            )
            if created:
                created_count += 1
                self.stdout.write(f"✅ {exercise.name} ({exercise.muscle_group})")

        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 Sucesso! {created_count} exercícios criados!')
        )
        
        # Estatísticas
        total_exercises = Exercise.objects.count()
        by_muscle_group = {}
        for group in ['chest', 'back', 'shoulders', 'arms', 'legs', 'abs', 'cardio', 'full_body']:
            count = Exercise.objects.filter(muscle_group=group).count()
            if count > 0:
                by_muscle_group[group] = count

        self.stdout.write(f'\n📊 ESTATÍSTICAS:')
        self.stdout.write(f'Total de exercícios: {total_exercises}')
        for group, count in by_muscle_group.items():
            self.stdout.write(f'{group.upper()}: {count} exercícios')
        
        self.stdout.write(
            self.style.SUCCESS('\n🚀 População de exercícios concluída com sucesso!')
        )