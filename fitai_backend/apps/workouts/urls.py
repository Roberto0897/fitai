from django.urls import path
from . import views


urlpatterns = [
    # API básica
    path('workouts/test/', views.test_workouts_api, name='test_workouts_api'),
    
    # APIs de workouts
    path('workouts/', views.list_workouts, name='list_workouts'),
    path('workouts/recommended/', views.recommended_workouts, name='recommended_workouts'),
    path('workouts/<int:workout_id>/', views.workout_detail, name='workout_detail'),
    
    # APIs de sessões
    path('workouts/<int:workout_id>/start/', views.start_workout_session, name='start_workout_session'),
    path('sessions/current/', views.current_session_status, name='current_session_status'),
    path('sessions/history/', views.workout_history, name='workout_history'),
    
    # APIs de controle de sessão em tempo real
    path('exercises/<int:exercise_log_id>/update/', views.update_exercise_progress, name='update_exercise_progress'),
    path('exercises/<int:exercise_log_id>/complete/', views.complete_exercise, name='complete_exercise'),
    path('exercises/<int:exercise_log_id>/skip/', views.skip_exercise, name='skip_exercise'),
    path('sessions/pause/', views.pause_session, name='pause_session'),
    path('sessions/complete/', views.complete_workout_session, name='complete_workout_session'),
   # path('sessions/cancel/', views.cancel_active_session, name='cancel_session'),
    
    path('workouts/sessions/<int:session_id>/complete/', views.complete_workout_session, name='complete_workout_session_with_id'),

    # APIs finais de IA e Analytics (NOVAS)
    path('analytics/', views.user_analytics, name='user_analytics'),
    path('ai/exercise-recommendations/', views.ai_exercise_recommendations, name='ai_exercise_recommendations'),
    path('ai/generate-workout/', views.generate_ai_workout_plan, name='generate_ai_workout_plan'),

    # APIs de Treinos Personalizados
    path('workouts/my-workouts/', views.my_personalized_workouts, name='my_personalized_workouts'),
    path('workouts/create/', views.create_personalized_workout, name='create_personalized_workout'),
    path('workouts/<int:workout_id>/update/', views.update_personalized_workout, name='update_personalized_workout'),
   # path('workouts/<int:workout_id>/delete/', views.delete_personalized_workout, name='delete_personalized_workout'),
    #remover treinos
    path('workouts/<int:workout_id>/delete/', views.delete_workout, name='delete_workout'),
    path('workouts/<int:workout_id>/restore/', views.restore_workout, name='restore_workout'),

    path('workouts/<int:workout_id>/duplicate/', views.duplicate_workout, name='duplicate_workout'),

    # Gerenciar exercícios no treino personalizado
    path('workouts/<int:workout_id>/exercises/add/', views.add_exercise_to_workout, name='add_exercise_to_workout'),
    path('workouts/<int:workout_id>/exercises/<int:workout_exercise_id>/update/', views.update_exercise_in_workout, name='update_exercise_in_workout'),
    path('workouts/<int:workout_id>/exercises/<int:workout_exercise_id>/delete/', views.remove_exercise_from_workout, name='remove_exercise_from_workout'),


    path('workouts/sessions/active/', views.get_active_session, name='get_active_session'),
    path('workouts/sessions/<int:session_id>/cancel/', views.cancel_active_session, name='cancel_active_session'),

   # path('ai/generate-onboarding/', views.generate_onboarding_workout, name='ai-onboarding'),

    path('workouts/onboarding/generate/', views.generate_onboarding_workout, name='generate_onboarding_workout'),


     # ============================================================
    # 🆕 RECOMENDAÇÃO INTELIGENTE (NOVA)
    # ============================================================
    path('workouts/smart-recommendation/', views.smart_recommendation_view, name='smart-recommendation'),


     # Buscar treino completo para editar
    path(
        'workouts/<int:workout_id>/fetch/', 
        views.get_workout_for_editing, 
        name='get_workout_for_editing'
    ),
    
    # Editar treino completo (workout + exercícios)
    path(
        'workouts/<int:workout_id>/edit/', 
        views.edit_workout_complete, 
        name='edit_workout_complete'
    ),
    
    # Listar exercícios disponíveis para adicionar
    path(
        'exercises/available/', 
        views.get_available_exercises_for_editing, 
        name='get_available_exercises_for_editing'
    ),
    
]