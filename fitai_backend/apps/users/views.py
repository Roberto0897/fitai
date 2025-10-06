# apps/users/views.py

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from firebase_admin import auth
from django.contrib.auth.models import User
from .models import UserProfile, UserProgress, DailyTip


def verify_firebase_token(request):
    """Verifica o token do Firebase e retorna o UID"""
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    
    if not auth_header.startswith('Bearer '):
        return None, Response(
            {'error': 'Token não fornecido'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    token = auth_header.split('Bearer ')[1]
    
    try:
        decoded_token = auth.verify_id_token(token)
        firebase_uid = decoded_token['uid']
        email = decoded_token.get('email', '')
        
        print(f"✅ Token verificado: {firebase_uid} ({email})")
        return firebase_uid, None
        
    except Exception as e:
        print(f"❌ Erro ao verificar token: {e}")
        return None, Response(
            {'error': 'Token inválido'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )


def get_or_create_user_and_profile(firebase_uid, email=None):
    """Obtém ou cria usuário Django + UserProfile"""
    # Buscar ou criar User Django
    try:
        user = User.objects.get(username=firebase_uid)
        print(f"✅ User Django encontrado: {firebase_uid}")
    except User.DoesNotExist:
        print(f"📝 Criando User Django para {firebase_uid}")
        
        try:
            firebase_user = auth.get_user(firebase_uid)
            email = firebase_user.email
            display_name = firebase_user.display_name or email.split('@')[0]
        except Exception as e:
            print(f"⚠️ Erro ao obter dados Firebase: {e}")
            email = email or 'user@email.com'
            display_name = firebase_uid[:20]
        
        user = User.objects.create_user(
            username=firebase_uid,
            email=email,
            first_name=display_name
        )
        #evitar que o django acesse senhas , remover caso erro
        user.set_unusable_password()
        user.save()

        print(f"✅ User Django criado: {user.username}")
    
    # Buscar ou criar UserProfile
    try:
        profile = UserProfile.objects.get(user=user)
        print(f"✅ UserProfile encontrado para user_id={user.id}")
        return profile, False
        
    except UserProfile.DoesNotExist:
        print(f"📝 Criando UserProfile para user_id={user.id}")
        
        profile = UserProfile.objects.create(
            user=user,
            goal='maintain',
            activity_level='moderate',
            current_weight=70.0,
            target_weight=65.0,
            focus_areas='',
            bio=''
        )
        
        print(f"✅ UserProfile criado: user_id={user.id}")
        return profile, True


@api_view(['GET'])
@permission_classes([AllowAny])
def test_users_api(request):
    """Endpoint de teste"""
    return Response({
        'message': 'API Users funcionando com Firebase!',
        'version': '3.0',
    })


@api_view(['GET'])
def user_dashboard(request):
    """Dashboard do usuário"""
    firebase_uid, error_response = verify_firebase_token(request)
    if error_response:
        return error_response
    
    try:
        profile, created = get_or_create_user_and_profile(firebase_uid)
        
        if created:
            print(f"🆕 Novo perfil criado")
        
        # Obter ou criar progresso
        try:
            progress = UserProgress.objects.get(user=profile.user)
        except UserProgress.DoesNotExist:
            progress = UserProgress.objects.create(
                user=profile.user,
                total_workouts=0
            )
            print(f"✅ UserProgress criado")
        
        # Obter dica do dia
        try:
            daily_tip = DailyTip.objects.filter(is_active=True).first()
            tip_data = {
                'title': daily_tip.title if daily_tip else 'Bem-vindo!',
                'content': daily_tip.content if daily_tip else 'Complete seu perfil.',
                'category': 'general'
            }
        except:
            tip_data = {
                'title': 'Bem-vindo!',
                'content': 'Complete seu perfil para começar.',
                'category': 'general'
            }
        
        return Response({
            'success': True,
            'profile_created': created,
            'user': {
                'id': profile.id,
                'username': profile.user.username,
                'email': profile.user.email,
                'first_name': profile.user.first_name,
                'goal': profile.goal,
                'activity_level': profile.activity_level,
                'focus_areas': profile.focus_areas,
                'bio': profile.bio,
                'current_weight': profile.current_weight,
                'target_weight': profile.target_weight,
            },
            'progress': {
                'id': progress.id,
                'total_workouts': progress.total_workouts,
            },
            'daily_tip': tip_data
        })
        
    except Exception as e:
        print(f"❌ Erro no dashboard: {e}")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Erro: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def register_user(request):
    """Criar/atualizar perfil"""
    firebase_uid, error_response = verify_firebase_token(request)
    if error_response:
        return error_response
    
    try:
        data = request.data
        profile, created = get_or_create_user_and_profile(firebase_uid, data.get('email'))
        
        if 'nome' in data:
            profile.user.first_name = data['nome']
            profile.user.save()
        
        if 'objetivo' in data:
            goal_map = {
                'Perder peso': 'lose_weight',
                'Ganhar massa': 'gain_muscle',
                'Manter forma': 'maintain'
            }
            profile.goal = goal_map.get(data['objetivo'], 'maintain')
        
        if 'nivel_atividade' in data:
            activity_map = {
                'Sedentário': 'sedentary',
                'Leve': 'light',
                'Moderado': 'moderate',
                'Intenso': 'very_active'
            }
            profile.activity_level = activity_map.get(data['nivel_atividade'], 'moderate')
        
        if 'peso_atual' in data:
            profile.current_weight = float(data['peso_atual'])
        if 'peso_desejado' in data:
            profile.target_weight = float(data['peso_desejado'])
        
        profile.save()
        
        return Response({
            'success': True,
            'created': created,
        })
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def set_weight_info(request):
    """Atualizar peso"""
    firebase_uid, error_response = verify_firebase_token(request)
    if error_response:
        return error_response
    
    try:
        profile, _ = get_or_create_user_and_profile(firebase_uid)
        
        if 'peso_atual' in request.data:
            profile.current_weight = float(request.data['peso_atual'])
        if 'peso_desejado' in request.data:
            profile.target_weight = float(request.data['peso_desejado'])
        
        profile.save()
        
        return Response({'success': True})
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def set_goal(request):
    """Atualizar objetivo"""
    firebase_uid, error_response = verify_firebase_token(request)
    if error_response:
        return error_response
    
    try:
        profile, _ = get_or_create_user_and_profile(firebase_uid)
        
        goal_map = {
            'Perder peso': 'lose_weight',
            'Ganhar massa': 'gain_muscle',
            'Manter forma': 'maintain'
        }
        profile.goal = goal_map.get(request.data.get('objetivo'), 'maintain')
        profile.save()
        
        return Response({'success': True})
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def set_activity_level(request):
    """Atualizar nível de atividade"""
    firebase_uid, error_response = verify_firebase_token(request)
    if error_response:
        return error_response
    
    try:
        profile, _ = get_or_create_user_and_profile(firebase_uid)
        
        activity_map = {
            'Sedentário': 'sedentary',
            'Leve': 'light',
            'Moderado': 'moderate',
            'Intenso': 'very_active'
        }
        profile.activity_level = activity_map.get(request.data.get('nivel_atividade'), 'moderate')
        profile.save()
        
        return Response({'success': True})
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def daily_tip(request):
    """Dica diária"""
    firebase_uid, error_response = verify_firebase_token(request)
    if error_response:
        return error_response
    
    try:
        tip = DailyTip.objects.filter(is_active=True).order_by('?').first()
        
        if tip:
            return Response({
                'success': True,
                'tip': {
                    'title': tip.title,
                    'content': tip.content,
                    'category': getattr(tip, 'category', 'general')
                }
            })
        
        return Response({
            'success': True,
            'tip': {
                'title': 'Mantenha-se ativo!',
                'content': 'Pequenos passos levam a grandes resultados.',
                'category': 'motivation'
            }
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """Login via Firebase"""
    return Response({
        'message': 'Use Firebase Authentication no frontend',
        'success': True
    })

# ============================================================
# ANALYTICS - Estatísticas do usuário (SEM MIGRATIONS)
# ============================================================

@api_view(['GET'])
def user_analytics(request):
    """
    Retorna estatísticas completas do usuário
    USA APENAS WorkoutSession existente - NÃO PRECISA DE MIGRATIONS
    """
    firebase_uid, error_response = verify_firebase_token(request)
    if error_response:
        return error_response
    
    try:
        profile, _ = get_or_create_user_and_profile(firebase_uid)
        user = profile.user
        
        print(f"📊 Calculando analytics para user_id={user.id}")
        
        # Importar WorkoutSession
        try:
            from workouts.models import WorkoutSession, ExerciseLog
        except ImportError:
            print("⚠️ Models de workout não encontrados")
            return _return_empty_analytics()
        
        # Pegar treinos concluídos dos últimos 90 dias
        ninety_days_ago = timezone.now() - timedelta(days=90)
        sessions = WorkoutSession.objects.filter(
            user=user,
            completed_at__isnull=False,
            completed_at__gte=ninety_days_ago
        ).order_by('-completed_at')
        
        if not sessions.exists():
            print("ℹ️ Nenhum treino concluído encontrado")
            return _return_empty_analytics()
        
        # Estatísticas básicas
        total_workouts = sessions.count()
        total_duration = sessions.aggregate(total=Sum('duration_minutes'))['total'] or 0
        total_calories = sessions.aggregate(total=Sum('calories_burned'))['total'] or 0
        
        # Dias ativos
        active_dates = sessions.values_list('completed_at__date', flat=True).distinct()
        active_days = len(set(active_dates))
        
        # Calcular streak
        current_streak = _calculate_workout_streak_simple(sessions)
        
        # Treinos por categoria
        workouts_by_category = _calculate_workouts_by_category(sessions)
        
        # Frequência de grupos musculares
        muscle_group_frequency = _calculate_muscle_frequency_simple(sessions)
        
        # Exercício favorito
        favorite_exercise, favorite_count = _get_favorite_exercise_simple(user)
        
        # Duração média
        average_duration = float(total_duration / total_workouts) if total_workouts > 0 else 0.0
        
        analytics_data = {
            'total_workouts': total_workouts,
            'total_duration': total_duration,
            'total_calories': total_calories,
            'active_days': active_days,
            'current_streak': current_streak,
            'workouts_by_category': workouts_by_category,
            'muscle_group_frequency': muscle_group_frequency,
            'favorite_exercise': favorite_exercise,
            'favorite_exercise_count': favorite_count,
            'average_duration': round(average_duration, 1),
        }
        
        print(f"✅ Analytics: {total_workouts} treinos, {active_days} dias ativos")
        return Response(analytics_data)
        
    except Exception as e:
        print(f"❌ Erro ao calcular analytics: {e}")
        import traceback
        traceback.print_exc()
        return _return_empty_analytics()


def _return_empty_analytics():
    """Retorna analytics vazio quando não há dados"""
    return Response({
        'total_workouts': 0,
        'total_duration': 0,
        'total_calories': 0,
        'active_days': 0,
        'current_streak': 0,
        'workouts_by_category': {},
        'muscle_group_frequency': {},
        'favorite_exercise': 'Nenhum',
        'favorite_exercise_count': 0,
        'average_duration': 0.0,
    })


def _calculate_workout_streak_simple(sessions):
    """Calcula streak de dias consecutivos"""
    try:
        workout_dates = set(sessions.values_list('completed_at__date', flat=True))
        if not workout_dates:
            return 0
        
        current_date = timezone.now().date()
        streak = 0
        
        # Verificar se treinou hoje ou ontem (permite 1 dia de descanso)
        if current_date not in workout_dates and (current_date - timedelta(days=1)) not in workout_dates:
            return 0
        
        # Contar dias consecutivos
        while current_date in workout_dates:
            streak += 1
            current_date = current_date - timedelta(days=1)
            if streak > 365:  # Limite de segurança
                break
        
        return streak
        
    except Exception as e:
        print(f"⚠️ Erro ao calcular streak: {e}")
        return 0


def _calculate_workouts_by_category(sessions):
    """Calcula distribuição de treinos por categoria"""
    category_counts = defaultdict(int)
    
    for session in sessions:
        if session.workout:
            category = session.workout.workout_type or 'Geral'
            category_counts[category] += 1
    
    return dict(category_counts)


def _calculate_muscle_frequency_simple(sessions):
    """Calcula frequência de grupos musculares"""
    muscle_frequency = defaultdict(int)
    
    for session in sessions:
        if session.workout and session.workout.target_muscle_groups:
            groups = [g.strip() for g in session.workout.target_muscle_groups.split(',')]
            for group in groups:
                if group:
                    muscle_frequency[group] += 1
    
    return dict(muscle_frequency)


def _get_favorite_exercise_simple(user):
    """Encontra exercício mais realizado"""
    try:
        from workouts.models import ExerciseLog
        
        exercise_counts = ExerciseLog.objects.filter(
            session__user=user,
            status='completed'
        ).values('exercise__name').annotate(
            count=Count('id')
        ).order_by('-count').first()
        
        if exercise_counts:
            return exercise_counts['exercise__name'], exercise_counts['count']
        
        return 'Nenhum', 0
        
    except Exception as e:
        print(f"⚠️ Erro ao buscar exercício favorito: {e}")
        return 'Nenhum', 0


# ============================================================
# PESO - USA current_weight DO UserProfile (SEM MIGRATIONS)
# ============================================================

@api_view(['GET'])
def weight_history(request):
    """
    Retorna histórico de peso do usuário
    USA APENAS current_weight do UserProfile - SEM TABELA SEPARADA
    """
    firebase_uid, error_response = verify_firebase_token(request)
    if error_response:
        return error_response
    
    try:
        profile, _ = get_or_create_user_and_profile(firebase_uid)
        
        # Verificar se existe histórico armazenado como JSON (opcional)
        weight_history_json = getattr(profile, 'weight_history_json', None)
        
        if weight_history_json:
            try:
                weights = json.loads(weight_history_json)
            except (json.JSONDecodeError, TypeError):
                weights = []
        else:
            # Se não tem histórico, criar entry com peso atual
            weights = []
            if profile.current_weight:
                weights = [{
                    'date': timezone.now().date().isoformat(),
                    'weight': float(profile.current_weight),
                    'notes': ''
                }]
        
        print(f"✅ {len(weights)} registros de peso")
        
        return Response({
            'success': True,
            'count': len(weights),
            'weights': weights,
            'current_weight': float(profile.current_weight) if profile.current_weight else None
        })
        
    except Exception as e:
        print(f"❌ Erro ao buscar peso: {e}")
        return Response(
            {'error': f'Erro: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def add_weight_log(request):
    """
    Adiciona peso (atualiza current_weight no UserProfile)
    NÃO PRECISA DE TABELA SEPARADA
    """
    firebase_uid, error_response = verify_firebase_token(request)
    if error_response:
        return error_response
    
    try:
        profile, _ = get_or_create_user_and_profile(firebase_uid)
        
        weight = request.data.get('weight')
        notes = request.data.get('notes', '')
        
        if not weight:
            return Response(
                {'error': 'Peso é obrigatório'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            weight = float(weight)
        except (ValueError, TypeError):
            return Response(
                {'error': 'Peso inválido'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if weight <= 0 or weight > 500:
            return Response(
                {'error': 'Peso deve estar entre 0 e 500 kg'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Atualizar peso atual
        profile.current_weight = weight
        profile.save()
        
        print(f"✅ Peso atualizado: {weight}kg")
        
        return Response({
            'success': True,
            'created': True,
            'weight_log': {
                'id': profile.id,
                'date': timezone.now().date().isoformat(),
                'weight': weight,
                'notes': notes
            }
        })
        
    except Exception as e:
        print(f"❌ Erro ao adicionar peso: {e}")
        return Response(
            {'error': f'Erro: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
