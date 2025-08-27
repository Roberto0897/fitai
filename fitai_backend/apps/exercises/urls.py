from django.urls import path
from . import views

urlpatterns = [
    # API básica
    path('exercises/test/', views.test_exercises_api, name='test_exercises_api'),
    
    # APIs de exercícios
    path('exercises/', views.list_exercises, name='list_exercises'),
    path('exercises/by_muscle_group/', views.exercises_by_muscle_group, name='exercises_by_muscle_group'),
    path('exercises/search/', views.search_exercises, name='search_exercises'),
    path('exercises/<int:exercise_id>/', views.exercise_detail, name='exercise_detail'),
]