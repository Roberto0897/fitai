# apps/chatbot/tests.py
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from .models import Conversation, Message
from .services.chat_service import ChatService

class ChatbotIntegrationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_chatbot_api_status(self):
        """Teste básico da API do chatbot"""
        response = self.client.get('/api/v1/chat/test/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['chatbot_status'], 'funcionando')
    
    def test_start_conversation(self):
        """Teste de criação de conversa"""
        data = {
            'type': 'general_fitness',
            'message': 'Olá! Preciso de ajuda com treinos.'
        }
        response = self.client.post('/api/v1/chat/conversations/start/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['conversation_started'])
        self.assertIn('conversation_id', response.data)
    
    def test_send_message(self):
        """Teste de envio de mensagem"""
        # Primeiro criar conversa
        conversation = Conversation.objects.create(
            user=self.user,
            conversation_type='general_fitness'
        )
        
        data = {'message': 'Qual o melhor exercício para iniciantes?'}
        response = self.client.post(
            f'/api/v1/chat/conversations/{conversation.id}/message/', 
            data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['message_sent'])
    
    def test_chat_service_initialization(self):
        """Teste de inicialização do serviço"""
        chat_service = ChatService()
        self.assertIsNotNone(chat_service)
        self.assertIsNotNone(chat_service.ai_service)