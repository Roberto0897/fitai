# apps/workouts/management/commands/populate_demo_data.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
import random

from apps.users.models import UserProfile, UserProgress, DailyTip
from apps.workouts.models import Workout, WorkoutSession, ExerciseLog
from apps.exercises.models import Exercise

class Command(BaseCommand):
    help = 'Popula o banco com dados de demonstração: usuários, sessões e progresso'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('👥 Iniciando população de dados de demonstração...'))

        # Criar usuários de teste
        self.create_demo_users()
        
        # Criar dicas diárias
        self.create_daily_tips()
        
        # Criar sessões de treino simuladas
        self.create_demo_sessions()
        
        self.stdout.write(
            self.style.SUCCESS('\n🎉 Dados de demonstração criados com sucesso!')
        )

    def create_demo_users(self):
        """Cria usuários de teste com perfis completos"""
        self.stdout.write('\n👤 Criando usuários de demonstração...')
        
        users_data = [
            {
                'username': 'demo_iniciante',
                'email': 'iniciante@fitai.com',
                'password': 'demo123',
                'first_name': 'Maria',
                'last_name': 'Silva',
                'profile': {
                    'goal': 'lose_weight',
                    'activity_level': 'light',
                    'focus_areas': 'cardio,abs',
                    'current_weight': 70.5,
                    'target_weight': 65.0,
                    'bio': 'Iniciando minha jornada fitness! Meta: perder 5kg em 3 meses.'
                }
            },
            {
                'username': 'demo_intermediario', 
                'email': 'intermediario@fitai.com',
                'password': 'demo123',
                'first_name': 'João',
                'last_name': 'Santos',
                'profile': {
                    'goal': 'gain_muscle',
                    'activity_level': 'moderate',
                    'focus_areas': 'chest,arms,shoulders',
                    'current_weight': 75.0,
                    'target_weight': 80.0,
                    'bio': 'Treino há 1 ano. Objetivo: ganhar massa muscular e definir o corpo.'
                }
            },
            {
                'username': 'demo_avancado',
                'email': 'avancado@fitai.com', 
                'password': 'demo123',
                'first_name': 'Ana',
                'last_name': 'Costa',
                'profile': {
                    'goal': 'endurance',
                    'activity_level': 'very_active',
                    'focus_areas': 'full_body,cardio',
                    'current_weight': 60.0,
                    'target_weight': 62.0,
                    'bio': 'Atleta experiente. Foco em resistência e performance geral.'
                }
            },
            {
                'username': 'demo_teste',
                'email': 'teste@fitai.com',
                'password': 'demo123', 
                'first_name': 'Carlos',
                'last_name': 'Oliveira',
                'profile': {
                    'goal': 'maintain',
                    'activity_level': 'active',
                    'focus_areas': 'legs,back',
                    'current_weight': 82.3,
                    'target_weight': 80.0,
                    'bio': 'Mantendo a forma física. Treinos 4x por semana.'
                }
            }
        ]

        for user_data in users_data:
            profile_data = user_data.pop('profile')
            
            # Criar usuário
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'], 
                    'last_name': user_data['last_name']
                }
            )
            
            if created:
                user.set_password(user_data['password'])
                user.save()
                
                # Criar perfil
                profile, profile_created = UserProfile.objects.get_or_create(
                    user=user,
                    defaults=profile_data
                )
                
                # Criar progresso inicial
                progress, progress_created = UserProgress.objects.get_or_create(
                    user=user,
                    defaults={
                        'total_workouts': random.randint(0, 15)
                    }
                )
                
                self.stdout.write(f"✅ Usuário criado: {user.username} ({profile_data['goal']})")
            else:
                self.stdout.write(f"⚠️  Usuário já existe: {user.username}")

    def create_daily_tips(self):
        """Cria dicas diárias motivacionais"""
        self.stdout.write('\n💡 Criando dicas diárias...')
        
        tips_data = [
            {
                'title': 'Hidratação é Fundamental',
                'content': 'Beba pelo menos 2 litros de água por dia. Uma boa hidratação melhora sua performance nos treinos e acelera a recuperação muscular.'
            },
            {
                'title': 'Descanso é Treino Também', 
                'content': 'Seus músculos crescem durante o descanso, não durante o treino. Durma 7-8 horas por noite para otimizar seus resultados.'
            },
            {
                'title': 'Consistência Vence Intensidade',
                'content': 'É melhor treinar 20 minutos todos os dias do que 2 horas uma vez por semana. Pequenas ações diárias levam a grandes resultados.'
            },
            {
                'title': 'Aquecimento Previne Lesões',
                'content': 'Sempre faça 5-10 minutos de aquecimento antes do treino. Músculos aquecidos rendem mais e se machucam menos.'
            },
            {
                'title': 'Proteína Pós-Treino',
                'content': 'Consuma proteína dentro de 30 minutos após o treino. Isso ajuda na recuperação e no crescimento muscular.'
            },
            {
                'title': 'Varie Seus Treinos',
                'content': 'Mude seus exercícios a cada 4-6 semanas para evitar adaptação e manter o progresso constante.'
            },
            {
                'title': 'Ouça Seu Corpo',
                'content': 'Dor muscular normal é diferente de dor de lesão. Aprenda a diferença e descanse quando necessário.'
            }
        ]

        for tip_data in tips_data:
            tip, created = DailyTip.objects.get_or_create(
                title=tip_data['title'],
                defaults=tip_data
            )
            if created:
                self.stdout.write(f"✅ Dica: {tip.title}")

    def create_demo_sessions(self):
        """Cria sessões de treino realistas com logs de exercícios"""
        self.stdout.write('\n🏋️‍♂️ Criando sessões de demonstração...')
        
        users = User.objects.filter(username__startswith='demo_')
        workouts = list(Workout.objects.all())
        
        if not workouts:
            self.stdout.write(self.style.WARNING('⚠️  Nenhum treino encontrado. Execute populate_workouts primeiro!'))
            return

        total_sessions = 0
        total_logs = 0
        
        for user in users:
            # Número de sessões baseado no perfil
            if 'iniciante' in user.username:
                session_count = random.randint(2, 5)
            elif 'intermediario' in user.username:
                session_count = random.randint(5, 10) 
            else:  # avançado/teste
                session_count = random.randint(8, 15)
            
            self.stdout.write(f'\n👤 Criando {session_count} sessões para {user.username}')
            
            # Criar sessões dos últimos 30 dias
            for i in range(session_count):
                # Data aleatória nos últimos 30 dias
                days_ago = random.randint(1, 30)
                session_date = timezone.now() - timedelta(days=days_ago)
                
                # Selecionar treino baseado no nível do usuário
                if 'iniciante' in user.username:
                    available_workouts = [w for w in workouts if w.difficulty_level == 'beginner']
                elif 'intermediario' in user.username:
                    available_workouts = [w for w in workouts if w.difficulty_level in ['beginner', 'intermediate']]
                else:
                    available_workouts = workouts
                
                if not available_workouts:
                    continue
                    
                workout = random.choice(available_workouts)
                
                # 85% das sessões são completas, 15% incompletas/canceladas
                is_completed = random.random() < 0.85
                
                # Criar sessão
                session = WorkoutSession.objects.create(
                    user=user,
                    workout=workout,
                    started_at=session_date,
                    completed=is_completed,
                    completed_at=session_date + timedelta(minutes=random.randint(15, 60)) if is_completed else None,
                    duration_minutes=random.randint(20, 50) if is_completed else random.randint(5, 25),
                    calories_burned=random.randint(100, 400) if is_completed else random.randint(50, 150),
                    user_rating=random.randint(3, 5) if is_completed else None,
                    notes=f"Sessão {'completa' if is_completed else 'incompleta'} - {workout.name}"
                )
                
                total_sessions += 1
                
                # Criar logs dos exercícios
                workout_exercises = workout.workout_exercises.all()
                
                for j, workout_exercise in enumerate(workout_exercises, 1):
                    # Para sessões incompletas, só fazer alguns exercícios
                    if not is_completed and j > random.randint(1, 3):
                        break
                    
                    # Simular progresso realista
                    planned_sets = workout_exercise.sets
                    completed_sets = planned_sets if is_completed else random.randint(0, planned_sets)
                    
                    # Simular se o exercício foi pulado (10% de chance)
                    was_skipped = random.random() < 0.1 if is_completed else False
                    
                    exercise_completed = completed_sets == planned_sets and not was_skipped
                    
                    exercise_log = ExerciseLog.objects.create(
                        session=session,
                        workout_exercise=workout_exercise,
                        sets_completed=completed_sets,
                        reps_completed=workout_exercise.reps if exercise_completed else f"{random.randint(5, 12)} (incompleto)",
                        weight_used=random.uniform(5.0, 25.0) if workout_exercise.exercise.muscle_group in ['chest', 'back', 'arms'] else None,
                        rest_time_actual=workout_exercise.rest_time + random.randint(-15, 30) if exercise_completed else None,
                        completed=exercise_completed,
                        skipped=was_skipped,
                        notes="Exercício pulado - falta de tempo" if was_skipped else ("Completo!" if exercise_completed else "Incompleto"),
                        completed_at=session.started_at + timedelta(minutes=j*3) if exercise_completed else None
                    )
                    
                    total_logs += 1
                
                # Atualizar progresso do usuário
                try:
                    progress = UserProgress.objects.get(user=user)
                    if is_completed:
                        progress.total_workouts += 1
                        progress.save()
                except UserProgress.DoesNotExist:
                    UserProgress.objects.create(
                        user=user,
                        total_workouts=1 if is_completed else 0
                    )
                
                status = "✅ Completa" if is_completed else "⏸️  Incompleta"
                self.stdout.write(f"   {status}: {workout.name} ({session.duration_minutes}min)")

        # Criar uma sessão ativa para demonstração (usuário intermediário)
        self.stdout.write('\n🔥 Criando sessão ativa para demonstração...')
        
        demo_user = User.objects.get(username='demo_intermediario')
        active_workout = Workout.objects.filter(difficulty_level='intermediate').first()
        
        if active_workout:
            # Deletar sessões ativas existentes
            WorkoutSession.objects.filter(user=demo_user, completed=False).delete()
            
            active_session = WorkoutSession.objects.create(
                user=demo_user,
                workout=active_workout, 
                started_at=timezone.now() - timedelta(minutes=15),
                completed=False,
                notes="Sessão ativa para demonstração"
            )
            
            # Criar logs com progresso parcial
            workout_exercises = active_workout.workout_exercises.all()[:3]  # Apenas 3 primeiros
            
            for i, workout_exercise in enumerate(workout_exercises):
                if i == 0:  # Primeiro exercício completo
                    ExerciseLog.objects.create(
                        session=active_session,
                        workout_exercise=workout_exercise,
                        sets_completed=workout_exercise.sets,
                        reps_completed=workout_exercise.reps,
                        completed=True,
                        completed_at=active_session.started_at + timedelta(minutes=5),
                        notes="Primeira série completada!"
                    )
                elif i == 1:  # Segundo exercício parcial
                    ExerciseLog.objects.create(
                        session=active_session,
                        workout_exercise=workout_exercise,
                        sets_completed=2,
                        reps_completed="8 (de 12)",
                        completed=False,
                        notes="Em progresso..."
                    )
                else:  # Terceiro exercício ainda não iniciado
                    ExerciseLog.objects.create(
                        session=active_session,
                        workout_exercise=workout_exercise,
                        sets_completed=0,
                        reps_completed="",
                        completed=False,
                        notes="Aguardando..."
                    )
            
            total_sessions += 1
            total_logs += 3
            
            self.stdout.write(f"🔥 Sessão ativa criada: {active_workout.name}")

        # Estatísticas finais
        self.stdout.write(f'\n📊 RESUMO DA DEMONSTRAÇÃO:')
        self.stdout.write(f'👥 Usuários criados: {users.count()}')
        self.stdout.write(f'💡 Dicas diárias: {DailyTip.objects.count()}')
        self.stdout.write(f'🏋️‍♂️ Sessões criadas: {total_sessions}')
        self.stdout.write(f'📝 Logs de exercícios: {total_logs}')
        
        completed_sessions = WorkoutSession.objects.filter(completed=True).count()
        active_sessions = WorkoutSession.objects.filter(completed=False).count()
        
        self.stdout.write(f'✅ Sessões completas: {completed_sessions}')
        self.stdout.write(f'⏸️  Sessões ativas/incompletas: {active_sessions}')
        
        # Dicas para teste
        self.stdout.write(f'\n🧪 PARA TESTAR:')
        self.stdout.write(f'1. Login: demo_iniciante / demo123')
        self.stdout.write(f'2. Login: demo_intermediario / demo123 (tem sessão ativa)')
        self.stdout.write(f'3. Login: demo_avancado / demo123')
        self.stdout.write(f'4. APIs de analytics e histórico populadas')
        self.stdout.write(f'5. Recomendações de IA baseadas nos perfis')