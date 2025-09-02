# apps/chatbot/urls.py
from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    # Teste da API do chatbot
    path('test/', views.test_chatbot_api, name='test'),
    
    # Gerenciamento de conversas
    path('conversations/start/', views.start_conversation, name='start_conversation'),
    path('conversations/<int:conversation_id>/message/', views.send_message, name='send_message'),
    path('conversations/<int:conversation_id>/history/', views.get_conversation_history, name='conversation_history'),
    path('conversations/<int:conversation_id>/end/', views.end_conversation, name='end_conversation'),
    path('conversations/', views.get_user_conversations, name='user_conversations'),
    
    # Feedback e interações
    path('messages/<int:message_id>/feedback/', views.message_feedback, name='message_feedback'),
    
    # Analytics e métricas
    path('analytics/', views.get_chat_analytics, name='chat_analytics'),
]

# URLs resultantes após integração:
#
# 🤖 CHATBOT - Teste e Status:
# /api/v1/chat/test/                                    - Teste da API do chatbot
#
# 💬 CONVERSAS:
# /api/v1/chat/conversations/start/                     - Iniciar nova conversa
# /api/v1/chat/conversations/{id}/message/              - Enviar mensagem
# /api/v1/chat/conversations/{id}/history/              - Histórico da conversa
# /api/v1/chat/conversations/{id}/end/                  - Finalizar conversa
# /api/v1/chat/conversations/                           - Listar conversas do usuário
#
# 🔄 INTERAÇÕES:
# /api/v1/chat/messages/{id}/feedback/                  - Feedback em mensagem específica
#
# 📊 ANALYTICS:
# /api/v1/chat/analytics/                               - Analytics pessoais do chat