# apps/chatbot/apps.py
from django.apps import AppConfig


class ChatbotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.chatbot'
    verbose_name = 'Chatbot Fitness'
    
    def ready(self):
        """
        Configurações executadas quando a app é carregada
        """
        # Importar signals se necessário no futuro
        try:
            # Registro de métricas ou outras inicializações podem ir aqui
            self._setup_logging()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in ChatbotConfig.ready(): {e}")
    
    def _setup_logging(self):
        """Configurar logging específico para chatbot se necessário"""
        import logging
        logger = logging.getLogger('apps.chatbot')
        logger.info("Chatbot app initialized successfully")