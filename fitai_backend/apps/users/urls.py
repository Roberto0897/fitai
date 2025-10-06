from django.urls import path
from . import views

urlpatterns = [
    # APIs básicas  
    path('users/test/', views.test_users_api, name='test_users_api'),
    path('users/register/', views.register_user, name='register_user'),
    path('users/login/', views.login_user, name='login_user'),
    path('users/dashboard/', views.user_dashboard, name='user_dashboard'),
    path('users/daily_tip/', views.daily_tip, name='daily_tip'),
    
    # APIs de onboarding (novas)
    path('users/set_goal/', views.set_goal, name='set_goal'),
    path('users/set_activity_level/', views.set_activity_level, name='set_activity_level'),
    path('users/set_weight_info/', views.set_weight_info, name='set_weight_info'),


    #novo
    # ANALYTICS - IMPORTANTE: deve estar em /users/analytics/ para o Flutter
    path('user/analytics/', views.user_analytics, name='user_analytics'),
    
    # PESO
    path('user/weight_history/', views.weight_history, name='weight_history'),
    path('user/add_weight/', views.add_weight_log, name='add_weight_log'),
    
    # Perfil
    path('user/profile/', views.user_dashboard, name='user_profile'),
]