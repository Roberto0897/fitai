from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from .models import UserProfile, UserProgress, DailyTip
import random

@api_view(['GET'])
def test_users_api(request):
    return Response({"message": "Users API funcionando!"})

@api_view(['POST'])
def register_user(request):
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email', '')
    
    if User.objects.filter(username=username).exists():
        return Response({"error": "Usuário já existe"}, status=status.HTTP_400_BAD_REQUEST)
    
    user = User.objects.create_user(username=username, password=password, email=email)
    
    # Criar perfil e progresso automaticamente
    UserProfile.objects.create(user=user)
    UserProgress.objects.create(user=user)
    
    token, created = Token.objects.get_or_create(user=user)
    
    return Response({
        "message": "Usuário criado com sucesso",
        "token": token.key,
        "user_id": user.id
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def login_user(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    user = authenticate(username=username, password=password)
    if user:
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            "message": "Login realizado com sucesso",
            "token": token.key,
            "user_id": user.id
        })
    else:
        return Response({"error": "Credenciais inválidas"}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_dashboard(request):
    try:
        profile = UserProfile.objects.get(user=request.user)
        progress = UserProgress.objects.get(user=request.user)
        
        return Response({
            "username": request.user.username,
            "goal": profile.goal,
            "activity_level": profile.activity_level,
            "total_workouts": progress.total_workouts,
            "current_weight": profile.current_weight,
            "target_weight": profile.target_weight
        })
    except (UserProfile.DoesNotExist, UserProgress.DoesNotExist):
        return Response({"error": "Perfil não encontrado"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def daily_tip(request):
    tips = DailyTip.objects.all()
    if tips:
        random_tip = random.choice(tips)
        return Response({
            "title": random_tip.title,
            "content": random_tip.content
        })
    return Response({"message": "Nenhuma dica disponível"})

# NOVAS APIs DE ONBOARDING
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_goal(request):
    goal = request.data.get('goal')
    
    if goal not in ['lose_weight', 'gain_muscle', 'maintain', 'endurance']:
        return Response({"error": "Meta inválida"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        profile = UserProfile.objects.get(user=request.user)
        profile.goal = goal
        profile.save()
        return Response({"message": "Meta definida com sucesso", "goal": goal})
    except UserProfile.DoesNotExist:
        return Response({"error": "Perfil não encontrado"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_activity_level(request):
    activity_level = request.data.get('activity_level')
    
    valid_levels = ['sedentary', 'light', 'moderate', 'active', 'very_active']
    if activity_level not in valid_levels:
        return Response({"error": "Nível de atividade inválido"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        profile = UserProfile.objects.get(user=request.user)
        profile.activity_level = activity_level
        profile.save()
        return Response({"message": "Nível de atividade definido", "activity_level": activity_level})
    except UserProfile.DoesNotExist:
        return Response({"error": "Perfil não encontrado"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_weight_info(request):
    current_weight = request.data.get('current_weight')
    target_weight = request.data.get('target_weight')
    
    try:
        profile = UserProfile.objects.get(user=request.user)
        if current_weight:
            profile.current_weight = float(current_weight)
        if target_weight:
            profile.target_weight = float(target_weight)
        profile.save()
        
        return Response({
            "message": "Informações de peso atualizadas",
            "current_weight": profile.current_weight,
            "target_weight": profile.target_weight
        })
    except (ValueError, UserProfile.DoesNotExist):
        return Response({"error": "Dados inválidos"}, status=status.HTTP_400_BAD_REQUEST)