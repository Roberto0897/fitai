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