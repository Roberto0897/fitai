# fitai/urls.py - URLs principais

from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    # Admin do Django
    path('admin/', admin.site.urls),
    
    # API v1 - Todas as apps
    path('api/v1/', include('apps.users.urls')),
    path('api/v1/', include('apps.exercises.urls')),
    path('api/v1/', include('apps.workouts.urls')),
    path('api/v1/recommendations/', include('apps.recommendations.urls')),
    
    # Token de autenticação (alternativa ao login customizado)
    path('api-token-auth/', obtain_auth_token),
    
    # DRF Browsable API (para desenvolvimento)
    path('api-auth/', include('rest_framework.urls')),
]

# URLs resultantes:
# 
# 🔐 ADMIN:
# /admin/                                    - Interface admin
#
# 🔐 AUTENTICAÇÃO:
# /api/v1/users/register/                    - Registrar
# /api/v1/users/login/                       - Login
# /api-token-auth/                           - Token auth (DRF padrão)
#
# 👤 USUÁRIOS:
# /api/v1/users/dashboard/                   - Dashboard
# /api/v1/users/progress/                    - Progresso
# /api/v1/users/daily_tip/                   - Dica diária
# /api/v1/users/update_weight/               - Atualizar peso
# /api/v1/users/set_goal/                    - Definir objetivo
# /api/v1/users/set_activity_level/          - Nível atividade
# /api/v1/users/set_focus_areas/             - Áreas foco
# /api/v1/users/complete_onboarding/         - Completar onboarding
#
# 💪 EXERCÍCIOS:
# /api/v1/exercises/                         - Listar exercícios
# /api/v1/exercises/{id}/                    - Detalhe exercício
# /api/v1/exercises/search/                  - Buscar exercícios
# /api/v1/exercises/by_muscle_group/         - Por grupo muscular
# /api/v1/exercises/recommended/             - Recomendados
#
# 🏋️ TREINOS:
# /api/v1/workouts/                          - Listar treinos
# /api/v1/workouts/{id}/                     - Detalhe treino
# /api/v1/workouts/recommended/              - Treinos recomendados
# /api/v1/workouts/{id}/start/               - Iniciar treino
# /api/v1/workouts/history/                  - Histórico
#
# ⏱️ SESSÕES:
# /api/v1/sessions/                          - Listar/criar sessões
# /api/v1/sessions/{id}/                     - Detalhe sessão
# /api/v1/sessions/{id}/complete/            - Completar
# /api/v1/sessions/{id}/pause/               - Pausar
# /api/v1/sessions/{id}/start_exercise/      - Iniciar exercício
# /api/v1/sessions/{id}/complete_exercise/   - Completar exercício
# /api/v1/sessions/{id}/status/              - Status da sessão