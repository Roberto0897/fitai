"""
Firebase Authentication para Django
Inicializa o Firebase Admin SDK e fornece funções de verificação de token
"""
import firebase_admin
from firebase_admin import credentials, auth
from django.conf import settings
import os

# Variável global para controlar inicialização
_firebase_initialized = False

def initialize_firebase():
    """
    Inicializa o Firebase Admin SDK
    Deve ser chamado apenas uma vez durante o startup do Django
    """
    global _firebase_initialized
    
    if _firebase_initialized:
        print("✅ Firebase já inicializado")
        return
    
    try:
        # Caminho para o arquivo de credenciais
        cred_path = os.path.join(settings.BASE_DIR, 'firebase-credentials.json')
        
        if not os.path.exists(cred_path):
            raise FileNotFoundError(
                f"❌ Arquivo firebase-credentials.json não encontrado em: {cred_path}\n"
                "Por favor, baixe as credenciais do Firebase Console e coloque na raiz do projeto."
            )
        
        # Inicializar Firebase Admin SDK
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        
        _firebase_initialized = True
        print("✅ Firebase Admin SDK inicializado com sucesso")
        
    except Exception as e:
        print(f"❌ Erro ao inicializar Firebase: {e}")
        raise


def verify_firebase_token(id_token):
    """
    Verifica um Firebase ID Token e retorna os dados do usuário
    
    Args:
        id_token (str): O Firebase ID Token recebido do cliente
        
    Returns:
        dict: Dados do usuário decodificados do token
        
    Raises:
        auth.InvalidIdTokenError: Se o token for inválido
        auth.ExpiredIdTokenError: Se o token estiver expirado
    """
    try:
        # Verificar e decodificar o token
        decoded_token = auth.verify_id_token(id_token)
        
        return {
            'uid': decoded_token['uid'],
            'email': decoded_token.get('email', ''),
            'name': decoded_token.get('name', ''),
            'email_verified': decoded_token.get('email_verified', False),
            'firebase_data': decoded_token  # Dados completos do Firebase
        }
        
    except auth.InvalidIdTokenError:
        raise ValueError("Token Firebase inválido")
    except auth.ExpiredIdTokenError:
        raise ValueError("Token Firebase expirado")
    except Exception as e:
        raise ValueError(f"Erro ao verificar token: {str(e)}")


def get_firebase_user(uid):
    """
    Busca informações de um usuário pelo UID no Firebase
    
    Args:
        uid (str): Firebase UID do usuário
        
    Returns:
        dict: Dados do usuário do Firebase
    """
    try:
        user = auth.get_user(uid)
        return {
            'uid': user.uid,
            'email': user.email,
            'display_name': user.display_name,
            'photo_url': user.photo_url,
            'email_verified': user.email_verified,
            'disabled': user.disabled,
        }
    except auth.UserNotFoundError:
        raise ValueError(f"Usuário com UID {uid} não encontrado no Firebase")
    except Exception as e:
        raise ValueError(f"Erro ao buscar usuário: {str(e)}")