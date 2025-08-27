from django.urls import path
from . import views

app_name = 'recommendations'

urlpatterns = [
    # Teste da API
    path('test/', views.test_recommendations_api, name='test'),
    
    # Recomendações principais
    path('personalized/', views.get_personalized_recommendations, name='personalized'),
    path('accept/<int:recommendation_id>/', views.accept_recommendation, name='accept'),
    path('history/', views.recommendation_history, name='history'),
    
    # IA Features
    path('ai/generate-workout/', views.generate_ai_workout, name='ai_workout'),
    path('ai/analyze-progress/', views.analyze_progress_ai, name='ai_progress'),
    path('ai/motivational-message/', views.generate_motivational_message, name='ai_motivation'),
]