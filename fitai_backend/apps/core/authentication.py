"""
Custom Authentication Backend para Firebase
Substitui o sistema de autenticação padrão do Django
"""
from rest_framework import authentication, exceptions
from django.contrib.auth.models import User
from .firebase_auth import verify_firebase_token


class FirebaseAuthentication(authentication.BaseAuthentication):
    """
    Autenticação usando Firebase ID Token
    
    O cliente deve enviar o token no header:
    Authorization: Bearer <firebase_id_token>
    """
    
    def authenticate(self, request):
        """Autentica o usuário usando Firebase ID Token"""
        # Obter token do header Authorization
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header:
            return None  # Permite requisições sem autenticação
        
        # Formato esperado: "Bearer <token>"
        parts = auth_header.split()
        
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            raise exceptions.AuthenticationFailed(
                'Formato de autenticação inválido. Use: Authorization: Bearer <token>'
            )
        
        id_token = parts[1]
        
        try:
            # Verificar token com Firebase
            firebase_data = verify_firebase_token(id_token)
            
            # Buscar ou criar usuário Django
            user = self.get_or_create_user(firebase_data)
            
            return (user, id_token)
            
        except ValueError as e:
            raise exceptions.AuthenticationFailed(str(e))
        except Exception as e:
            raise exceptions.AuthenticationFailed(f'Erro na autenticação: {str(e)}')
    
    
    def get_or_create_user(self, firebase_data):
     """Busca usuário Django pelo Firebase UID ou cria um novo"""
     firebase_uid = firebase_data['uid']
     email = firebase_data.get('email', '')
     name = firebase_data.get('name', '')
    
        # Buscar ou criar usuário (mais robusto)
     user, created = User.objects.get_or_create(
            username=firebase_uid,
            defaults={
                'email': email,
                'first_name': name or 'Usuário',
            }
        )
    
        # Se já existia, atualizar dados
     if not created:
            if email and user.email != email:
                user.email = email
            if name and user.first_name != name:
                user.first_name = name
            user.save()
    
        # Criar perfil se não existir
     if created:
            try:
                from apps.users.models import UserProfile
                UserProfile.objects.get_or_create(user=user)
            except Exception as e:
                print(f"Aviso: Não foi possível criar UserProfile: {e}")
            
            print(f"✅ Novo usuário criado: {email} (UID: {firebase_uid})")
        
     return user  # ← DEVE ESTAR AQUI (dentro da função, alinhado com os if's)