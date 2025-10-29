# apps/chatbot/services/chat_service.py
# VERSÃO COMPLETA COM FLUXO DE GERAÇÃO DE TREINO
import json
import time
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.contrib.auth.models import User

from ..models import Conversation, Message, ChatContext
from apps.users.models import UserProfile
from apps.workouts.models import Workout, WorkoutSession
from apps.recommendations.services.ai_service import AIService
import traceback

logger = logging.getLogger(__name__)


# ============================================================
# 🔥 CLASSE DE FLUXO DE GERAÇÃO DE TREINO
# ============================================================

class WorkoutGenerationFlow:
    """
    Gerencia o fluxo conversacional para geração de treinos personalizados
    """
    
    # Estados do fluxo
    STATE_INITIAL = 'initial'
    STATE_WAITING_FOCUS = 'waiting_focus'
    STATE_WAITING_DAYS = 'waiting_days'
    STATE_WAITING_DIFFICULTY = 'waiting_difficulty'
    STATE_WAITING_CONFIRMATION = 'waiting_confirmation'
    STATE_GENERATING = 'generating'
    STATE_COMPLETED = 'completed'
    
    # Opções de foco
    FOCUS_OPTIONS = {
        'completo': {
            'value': 'full_body',
            'label': '💪 Treino Completo',
            'description': 'Trabalha todos os grupos musculares',
            'emoji': '🏋️'
        },
        'superior': {
            'value': 'upper',
            'label': '💪 Parte Superior',
            'description': 'Peito, costas, ombros e braços',
            'emoji': '💪'
        },
        'inferior': {
            'value': 'lower',
            'label': '🦵 Parte Inferior',
            'description': 'Pernas, glúteos e panturrilhas',
            'emoji': '🦵'
        },
        'peito': {
            'value': 'chest',
            'label': '🫀 Peito',
            'description': 'Foco em peitoral e tríceps',
            'emoji': '🫀'
        },
        'costas': {
            'value': 'back',
            'label': '🔙 Costas',
            'description': 'Foco em dorsais e bíceps',
            'emoji': '🔙'
        },
        'pernas': {
            'value': 'legs',
            'label': '🦵 Pernas',
            'description': 'Quadríceps, posteriores e glúteos',
            'emoji': '🦵'
        },
        'bracos': {
            'value': 'arms',
            'label': '💪 Braços',
            'description': 'Bíceps e tríceps',
            'emoji': '💪'
        },
        'ombros': {
            'value': 'shoulders',
            'label': '🏔️ Ombros',
            'description': 'Deltoides e trapézio',
            'emoji': '🏔️'
        },
        'cardio': {
            'value': 'cardio',
            'label': '🏃 Cardio',
            'description': 'Resistência e queima de calorias',
            'emoji': '🏃'
        }
    }
    
    # Opções de dias
    DAYS_OPTIONS = {
        '3': {'value': 3, 'label': '3 dias/semana', 'description': 'Ideal para iniciantes'},
        '4': {'value': 4, 'label': '4 dias/semana', 'description': 'Bom equilíbrio'},
        '5': {'value': 5, 'label': '5 dias/semana', 'description': 'Rotina intensa'},
        '6': {'value': 6, 'label': '6 dias/semana', 'description': 'Muito avançado'},
    }
    
    # Opções de dificuldade
    DIFFICULTY_OPTIONS = {
        'iniciante': {'value': 'beginner', 'label': '🌱 Iniciante', 'description': 'Começando agora'},
        'intermediario': {'value': 'intermediate', 'label': '💪 Intermediário', 'description': 'Já treino regularmente'},
        'avancado': {'value': 'advanced', 'label': '🔥 Avançado', 'description': 'Atleta experiente'},
    }
    
    
    @staticmethod
    def detect_workout_intent(message: str) -> bool:
        """Detecta se o usuário quer gerar um treino"""
        keywords = [
            'gerar treino', 'criar treino', 'montar treino',
            'quero treinar', 'treino personalizado', 'plano de treino',
            'monta um treino', 'cria um treino', 'preciso de treino',
            'workout', 'plano semanal', 'rotina de treino',
            'me ajuda com treino', 'treino para mim',
            'quero um treino', 'fazer treino', 'começar treinar',
            
            # 🔥 ADICIONAR:
            'detalhes do treino', 'outros dias', 'completar treino',
            'resto do treino', 'continuar treino', 'demais dias'
        ]

        message_lower = message.lower()
        return any(keyword in message_lower for keyword in keywords)

    @staticmethod
    def detect_focus_intent(message: str) -> dict:
        """
        Detecta quais focos o usuário escolheu
        RETORNA: {'single': 'peito'} OU {'multiple': ['peito', 'ombros', 'bracos']}
        """
        message_lower = message.lower().strip()
        
        message_clean = re.sub(r'[^\w\s]', '', message_lower)
        
        focus_keywords = {
            'completo': ['completo', 'full body', 'corpo todo', 'geral', '1'],
            'superior': ['superior', 'upper', 'parte de cima', '2'],
            'inferior': ['inferior', 'lower', 'parte de baixo', '3'],
            'peito': ['peito', 'peitoral', 'chest', 'peit', '4'],
            'costas': ['costas', 'costa', 'dorsal', 'back', '5'],
            'pernas': ['perna', 'pernas', 'leg', 'legs', 'coxa', '6'],
            'bracos': ['braço', 'bracos', 'braco', 'arm', 'biceps', 'triceps', '7'],
            'ombros': ['ombro', 'ombros', 'shoulder', 'deltoide', '8'],
            'cardio': ['cardio', 'aerobico', 'corrida', '9'],
        }
        
        # 🔥 DETECTAR TODOS OS GRUPOS MENCIONADOS
        detected_groups = []
        for focus, keywords in focus_keywords.items():
            if any(keyword in message_clean for keyword in keywords):
                detected_groups.append(focus)
        
        # Se não detectou nada, tentar números
        if not detected_groups:
            numbers = re.findall(r'\d+', message)
            if numbers:
                focus_map = {1: 'completo', 2: 'superior', 3: 'inferior', 
                           4: 'peito', 5: 'costas', 6: 'pernas', 
                           7: 'bracos', 8: 'ombros', 9: 'cardio'}
                for num in numbers:
                    if int(num) in focus_map:
                        detected_groups.append(focus_map[int(num)])
        
        # Retornar estrutura adequada
        if len(detected_groups) == 0:
            return None
        elif len(detected_groups) == 1:
            return {'type': 'single', 'focus': detected_groups[0]}
        else:
            return {'type': 'multiple', 'groups': detected_groups}
        
    @staticmethod
    def detect_days_intent(message: str) -> int:
        """Detecta quantos dias o usuário escolheu"""
        message_lower = message.lower().strip()
        numbers = re.findall(r'\d+', message_lower)
        if numbers:
            days = int(numbers[0])
            if 3 <= days <= 6:
                return days
        
        # Detectar por extenso
        day_words = {
            'três': 3, 'tres': 3, '3': 3,
            'quatro': 4, '4': 4,
            'cinco': 5, '5': 5,
            'seis': 6, '6': 6
        }
        
        for word, value in day_words.items():
            if word in message_lower:
                return value
        
        return None
    
    @staticmethod
    def get_days_prompt(focus_data) -> dict:
        """Adapta prompt baseado em single ou multiple"""
        
        # Se recebeu string diretamente (compatibilidade)
        if isinstance(focus_data, str):
            message = f"✅ Foco escolhido: **{focus_data}**\n\n"
        
        # Se recebeu dict
        elif isinstance(focus_data, dict):
            if focus_data['type'] == 'single':
                focus_label = WorkoutGenerationFlow.FOCUS_OPTIONS[focus_data['focus']]['label']
                message = f"✅ Foco escolhido: **{focus_label}**\n\n"
            else:
                # Múltiplos grupos
                groups = focus_data['groups']
                labels = [WorkoutGenerationFlow.FOCUS_OPTIONS[g]['label'] for g in groups]
                message = f"✅ Focos escolhidos: **{', '.join(labels)}**\n\n"
        else:
            message = "✅ Foco selecionado!\n\n"
        
        message += "**Quantos dias por semana você pode treinar?**"
        
        return {
            'message': message,
            'options': [
                {'id': '3', 'label': '3 dias/semana', 'description': 'Ideal para iniciantes'},
                {'id': '4', 'label': '4 dias/semana', 'description': 'Bom equilíbrio'},
                {'id': '5', 'label': '5 dias/semana', 'description': 'Rotina intensa'},
                {'id': '6', 'label': '6 dias/semana', 'description': 'Muito avançado'},
            ],
            'next_state': WorkoutGenerationFlow.STATE_WAITING_DAYS
        }

    @staticmethod
    def detect_difficulty_intent(message: str) -> str:
        """Detecta dificuldade - MELHORADO"""
        message_lower = message.lower().strip()
        
        import re
        message_clean = re.sub(r'[^\w\s]', '', message_lower)
        
        difficulty_keywords = {
            'iniciante': ['iniciante', 'beginner', 'começo', 'começando', 'comeco', 'novo', 
                        'primeira vez', '1', 'opcao 1', 'opção 1'],
            'intermediario': ['intermediário', 'intermediario', 'intermediate', 'médio', 
                            'medio', 'regular', '2', 'opcao 2', 'opção 2'],
            'avancado': ['avançado', 'avancado', 'advanced', 'experiente', 'atleta', 
                        'pro', 'profissional', '3', 'opcao 3', 'opção 3'],
        }
        
        for difficulty, keywords in difficulty_keywords.items():
            if any(keyword in message_clean for keyword in keywords):
                return difficulty
        
        # Tentar número
        numbers = re.findall(r'\d+', message)
        if numbers:
            num = int(numbers[0])
            diff_map = {1: 'iniciante', 2: 'intermediario', 3: 'avancado'}
            return diff_map.get(num)
        
        return None
    
    @staticmethod
    def get_difficulty_prompt(days: int) -> dict:
        """Pergunta sobre dificuldade"""
        return {
            'message': f"✅ Frequência: **{days} dias/semana**\n\n"
                    f"**Qual é o seu nível de experiência?**",
            'options': [
                {'id': '1', 'label': '🌱 Iniciante', 'description': 'Começando agora'},
                {'id': '2', 'label': '💪 Intermediário', 'description': 'Já treino regularmente'},
                {'id': '3', 'label': '🔥 Avançado', 'description': 'Atleta experiente'},
            ],
            'next_state': WorkoutGenerationFlow.STATE_WAITING_DIFFICULTY
        }

    @staticmethod
    def get_initial_prompt(user_name: str = 'Atleta') -> dict:
        """Mensagem inicial quando detecta intenção de gerar treino"""
        return {
            'message': f"🏋️ Ótimo, {user_name}! Vamos criar seu treino personalizado!\n\n"
                      f"**Primeiro, qual é o seu foco principal?**\n\n"
                      f"Responda com o número ou nome da opção:",
            'options': [
                {'id': '1', 'label': '💪 Treino Completo', 'description': 'Corpo todo'},
                {'id': '2', 'label': '🔝 Parte Superior', 'description': 'Peito, costas, ombros, braços'},
                {'id': '3', 'label': '🦵 Parte Inferior', 'description': 'Pernas e glúteos'},
                {'id': '4', 'label': '🫀 Peito', 'description': 'Foco em peitoral'},
                {'id': '5', 'label': '🔙 Costas', 'description': 'Foco em dorsais'},
                {'id': '6', 'label': '🦵 Pernas', 'description': 'Quadríceps e posteriores'},
                {'id': '7', 'label': '💪 Braços', 'description': 'Bíceps e tríceps'},
                {'id': '8', 'label': '🏔️ Ombros', 'description': 'Deltoides'},
                {'id': '9', 'label': '🏃 Cardio', 'description': 'Resistência'},
            ],
            'next_state': WorkoutGenerationFlow.STATE_WAITING_FOCUS
        }
    

    @staticmethod
    def get_confirmation_prompt(focus_label: str, days: int, difficulty_label: str) -> dict:
        return {
            'message': f"🎯 **Resumo do seu treino:**\n\n"
                      f"• Foco: {focus_label}\n"
                      f"• Frequência: {days} dias/semana\n"
                      f"• Nível: {difficulty_label}\n\n"
                      f"**Tudo certo?** Digite 'sim' para gerar ou 'cancelar'.",
            'options': [
                {'id': 'sim', 'label': '✅ Sim, gerar treino!'},
                {'id': 'cancelar', 'label': '❌ Cancelar'},
            ],
            'next_state': WorkoutGenerationFlow.STATE_WAITING_CONFIRMATION
        }

# apps/chatbot/services/chat_service.py

class WorkoutPlanExtractor:
    """
    🔥 VERSÃO MELHORADA - Detecta planos em QUALQUER formato
    """
    
    @staticmethod
    def extract_plan_info(ai_response_content: str) -> Optional[Dict]:
        """
        Analisa a resposta da IA e extrai treinos
        """
        try:
            content_lower = ai_response_content.lower()
            
            # 🔥 1. DETECTAR SE É UM PLANO (MAIS FLEXÍVEL)
            plan_indicators = [
                'treino de',
                'treino para',
                'sugestão de treino',
                'plano',
                'dia 1', 'dia 2', 'dia 3',
                'segunda', 'terça', 'quarta', 'quinta', 'sexta',
                '**dia',  # ← ADICIONAR formato Markdown
                'séries',
                'repetições',
                'reps',
                'supino', 'agachamento', 'flexão', 'remada',
            ]
            
            # 🔥 REDUZIR para 3 indicadores
            indicator_count = sum(1 for indicator in plan_indicators 
                                 if indicator in content_lower)
            
            logger.info(f"📊 Indicadores encontrados: {indicator_count}")
            
            if indicator_count < 3:
                logger.info("⚠️ Resposta não contém plano de treino")
                return None
            
            logger.info("✅ Plano de treino detectado")
            
            # 🔥 2. EXTRAIR DIAS
            days_per_week = WorkoutPlanExtractor._extract_days(ai_response_content)
            
            # 🔥 3. EXTRAIR FOCO
            focus = WorkoutPlanExtractor._extract_focus(ai_response_content)
            
            # 🔥 4. EXTRAIR DIFICULDADE
            difficulty = WorkoutPlanExtractor._extract_difficulty(ai_response_content)
            
            # 🔥 5. EXTRAIR EXERCÍCIOS POR DIA (MELHORADO)
            exercises_by_day = WorkoutPlanExtractor._extract_exercises_by_day_improved(
                ai_response_content
            )
            
            if not exercises_by_day or len(exercises_by_day) == 0:
                logger.warning("⚠️ Nenhum exercício extraído")
                return None
            
            logger.info(f"📊 Plano extraído:")
            logger.info(f"   Dias: {days_per_week}")
            logger.info(f"   Foco: {focus}")
            logger.info(f"   Dificuldade: {difficulty}")
            logger.info(f"   Dias com exercícios: {len(exercises_by_day)}")
            
            return {
                'days_per_week': days_per_week,
                'focus': focus,
                'difficulty': difficulty,
                'exercises_by_day': exercises_by_day,
                'extracted_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair plano: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    @staticmethod
    def _extract_days(content: str) -> int:
        """Extrai quantos dias - MELHORADO"""
        content_lower = content.lower()
        
        # Procurar "X dias"
        pattern = r'(\d+)\s*dias?'
        match = re.search(pattern, content_lower)
        
        if match:
            days = int(match.group(1))
            if 1 <= days <= 7:
                return days
        
        # Contar quantos "Dia X:" ou "**Dia X:**"
        day_pattern = r'\*?\*?dia\s*(\d+)'
        day_matches = re.findall(day_pattern, content_lower)
        
        if day_matches:
            max_day = max([int(d) for d in day_matches])
            logger.info(f"   Detectou {max_day} dias pelo padrão 'Dia X'")
            return max_day
        
        # Contar dias da semana
        days_count = sum(1 for day in ['segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado', 'domingo']
                        if day in content_lower)
        
        if days_count > 0:
            return days_count
        
        return 3  # Default
    
    @staticmethod
    def _extract_focus(content: str) -> str:
        """Extrai foco - IGUAL"""
        focus_map = {
            'corpo completo': 'full_body',
            'full body': 'full_body',
            'corpo todo': 'full_body',
            'parte superior': 'upper',
            'upper': 'upper',
            'membros superiores': 'upper',
            'parte inferior': 'lower',
            'lower': 'lower',
            'membros inferiores': 'lower',
            'peito': 'chest',
            'peitoral': 'chest',
            'costas': 'back',
            'dorsal': 'back',
            'pernas': 'legs',
            'leg': 'legs',
            'braços': 'arms',
            'braco': 'arms',
            'arm': 'arms',
            'ombro': 'shoulders',
            'shoulder': 'shoulders',
            'triceps': 'arms',
            'ganho de massa': 'hypertrophy',
            'massa muscular': 'hypertrophy',
            'hipertrofia': 'hypertrophy',
        }
        
        content_lower = content.lower()
        
        for text_pattern, focus_value in focus_map.items():
            if text_pattern in content_lower:
                return focus_value
        
        return 'full_body'
    
    @staticmethod
    def _extract_difficulty(content: str) -> str:
        """Extrai dificuldade - IGUAL"""
        content_lower = content.lower()
        
        if 'iniciante' in content_lower or 'beginner' in content_lower:
            return 'beginner'
        elif 'intermediário' in content_lower or 'intermediario' in content_lower:
            return 'intermediate'
        elif 'avançado' in content_lower or 'avancado' in content_lower:
            return 'advanced'
        
        return 'intermediate'
    
    @staticmethod
    def _extract_exercises_by_day_improved(content: str) -> Dict:
        """
        🔥 VERSÃO MELHORADA - Detecta múltiplos formatos
        
        Formatos suportados:
        - **Dia 1: Peito**
        - Dia 1: Peito
        - Segunda: Peito
        - **Segunda-feira: Peito**
        """
        exercises_by_day = {}
        
        # 🔥 Padrões MELHORADOS (case-insensitive com re.IGNORECASE)
        day_patterns = [
            # Formato: **Dia 1:** ou Dia 1:
            (r'\*?\*?dia\s*(\d+):?\*?\*?\s*([^\n*]*)', 'dia_{}'),
            
            # Formato: **Segunda:** ou Segunda:
            (r'\*?\*?(segunda|terça|quarta|quinta|sexta|sábado|domingo):?\*?\*?\s*([^\n*]*)', '{}'),
            
            # Formato: **Segunda-feira:** 
            (r'\*?\*?(segunda-feira|terça-feira|quarta-feira|quinta-feira|sexta-feira|sábado|domingo):?\*?\*?\s*([^\n*]*)', '{}'),
        ]
        
        for pattern, key_format in day_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                day_key = match.group(1)
                day_title = match.group(2) if len(match.groups()) >= 2 else day_key
                
                # Formatar chave do dia
                if pattern.startswith(r'\*?\*?dia'):
                    formatted_key = key_format.format(day_key)
                else:
                    formatted_key = day_key.lower().replace('-feira', '')
                
                logger.info(f"   🔍 Detectou dia: {formatted_key} - {day_title}")
                
                # Extrair exercícios deste dia
                # Pegar texto até o próximo "**Dia" ou "**Segunda" ou fim
                start_pos = match.end()
                
                # Procurar próximo marcador de dia
                next_day_pattern = r'\*?\*?(dia\s*\d+|segunda|terça|quarta|quinta|sexta|sábado|domingo)'
                next_match = re.search(next_day_pattern, content[start_pos:], re.IGNORECASE)
                
                if next_match:
                    end_pos = start_pos + next_match.start()
                else:
                    end_pos = len(content)
                
                day_content = content[start_pos:end_pos]
                
                # Extrair exercícios
                exercises = WorkoutPlanExtractor._extract_exercises_from_text(day_content)
                
                if exercises:
                    exercises_by_day[formatted_key] = {
                        'name': day_title.strip() or formatted_key,
                        'exercises': exercises
                    }
                    
                    logger.info(f"      ✅ {len(exercises)} exercícios extraídos")
        
        return exercises_by_day
    
    @staticmethod
    def _extract_exercises_from_text(text: str) -> List[Dict]:
        """
        Extrai exercícios de um bloco de texto
        
        Formatos suportados:
        - Supino Reto: 3 séries de 8-12 repetições
        - * Supino Reto (barra): 3 séries de 8-12 reps
        - Supino Reto - 3x8-12
        """
        exercises = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            
            if not line or line.startswith('*   Aquecimento') or line.startswith('*   Alongamento'):
                continue
            
            # 🔥 Padrões de exercício (múltiplos formatos)
            patterns = [
                # Formato: Supino Reto: 3 séries de 8-12 repetições
                r'^[*\-•]?\s*([^:()]+?)(?:\([^)]*\))?:\s*(\d+)\s*séries?\s*de\s*([\d\-]+)\s*(?:repetições?|reps?)',
                
                # Formato: Supino Reto - 3x8-12
                r'^[*\-•]?\s*([^:()]+?)(?:\([^)]*\))?\s*-\s*(\d+)\s*x\s*([\d\-]+)',
                
                # Formato: Supino Reto (barra ou halteres): 3 séries de 8-12 reps
                r'^[*\-•]?\s*([^:]+?):\s*(\d+)\s*séries?\s*de\s*([\d\-]+)\s*reps?',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                
                if match:
                    exercise_name = match.group(1).strip()
                    
                    # Limpar nome (remover texto entre parênteses)
                    exercise_name = re.sub(r'\([^)]*\)', '', exercise_name).strip()
                    
                    sets = int(match.group(2))
                    reps = match.group(3).strip()
                    
                    exercises.append({
                        'name': exercise_name,
                        'sets': sets,
                        'reps': reps,
                        'rest_time': 60,
                    })
                    
                    logger.info(f"         • {exercise_name}: {sets}x{reps}")
                    break
        
        return exercises
    
# apps/chatbot/services/chat_service.py



# ============================================================
# CLASSE PRINCIPAL DO CHATBOT
# ============================================================

class ChatService:
    """
    Serviço principal para gerenciamento de conversas de chatbot com IA
    Integrado com Google Gemini + Fluxo de Geração de Treino
    """
    
    def __init__(self):
        self.ai_service = AIService()
        self.max_context_messages = 10
        self.conversation_timeout_hours = 24
        
    def start_conversation(self, user: User, conversation_type: str = 'general_fitness',
                          initial_message: str = None) -> Dict:
        """Inicia nova conversa de chatbot com contexto personalizado"""
        try:
            recent_conversation = Conversation.objects.filter(
                user=user,
                status='active',
                created_at__gte=timezone.now() - timedelta(hours=2)
            ).first()
            
            if recent_conversation and not initial_message:
                return {
                    'conversation_id': recent_conversation.id,
                    'status': 'resumed',
                    'message': 'Continuando conversa anterior...',
                    'conversation_type': recent_conversation.conversation_type,
                    'context_loaded': True
                }
            
            conversation = Conversation.objects.create(
                user=user,
                conversation_type=conversation_type,
                ai_model_used=getattr(settings, 'GEMINI_MODEL', 'gemini-2.5-flash') #gemini-2.0-flash
            )
            
            self._initialize_conversation_context(conversation)
            
            if not initial_message:
                welcome_response = self._generate_welcome_message(conversation)
                if welcome_response:
                    self._save_ai_message(
                        conversation, 
                        welcome_response['content'],
                        response_time_ms=welcome_response.get('response_time', 0),
                        confidence_score=welcome_response.get('confidence', 0.8)
                    )
            else:
                user_message = self._save_user_message(conversation, initial_message)
                ai_response = self.process_user_message(conversation.id, initial_message)
            
            return {
                'conversation_id': conversation.id,
                'status': 'created',
                'conversation_type': conversation_type,
                'context_loaded': True,
                'welcome_message': True,
                'ai_available': self.ai_service.is_available
            }
            
        except Exception as e:
            logger.error(f"Error starting conversation for user {user.id}: {e}")
            return {
                'error': 'Não foi possível iniciar conversa',
                'fallback': 'Tente novamente em alguns instantes'
            }
    
    def process_user_message(self, conversation_id: int, message: str) -> Dict:
        """
        🔥 Processa mensagem do usuário e DETECTA PLANOS DE TREINO
        """
        start_time = time.time()
        
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            
            if conversation.is_expired():
                return {'error': 'Conversa expirada'}
            
            # Salvar mensagem do usuário
            user_message = self._save_user_message(conversation, message)
            
            intent_analysis = self._analyze_message_intent(message, conversation)
            user_message.intent_detected = intent_analysis.get('intent', 'general_question')
            user_message.save()
            
            self._update_conversation_context(conversation, message, intent_analysis)
            
            # Gerar resposta da IA
            ai_response = self._generate_ai_response(conversation, message, intent_analysis)
            
            if ai_response and ai_response.get('success'):
                # 🔥 DEBUG: LOG ANTES DE DETECTAR
                logger.error("=" * 80)
                logger.error("🔍 TENTANDO DETECTAR PLANO DE TREINO")
                logger.error(f"📝 Conteúdo da IA (primeiros 500 chars):")
                logger.error(ai_response['content'][:500])
                logger.error("=" * 80)
                
                # 🔥 DETECÇÃO AUTOMÁTICA DE PLANO
                plan_info = WorkoutPlanExtractor.extract_plan_info(ai_response['content'])
                
                # 🔥 DEBUG: LOG DEPOIS DE DETECTAR
                logger.error("=" * 80)
                logger.error(f"🎯 RESULTADO DA DETECÇÃO:")
                logger.error(f"   plan_info = {plan_info}")
                logger.error("=" * 80)
                
                if plan_info:
                    logger.error("🏋️ Plano detectado! Criando treinos...")
                    
                    workout_creation = self._create_workouts_from_plan(
                        conversation,
                        plan_info
                    )
                    
                    if workout_creation.get('success'):
                        logger.error(f"✅ {len(workout_creation['workouts'])} treinos criados!")
                        
                        structured_response = self._create_workout_success_response(
                            conversation,
                            ai_response['content'],
                            workout_creation['workouts'],
                            plan_info
                        )
                        
                        ai_message = self._save_ai_message(
                            conversation,
                            structured_response['response'],
                            response_time_ms=round((time.time() - start_time) * 1000, 2),
                            confidence_score=ai_response.get('confidence_score', 0.8),
                            intent='workout_generated'
                        )
                        
                        conversation.message_count += 2
                        conversation.ai_responses_count += 1
                        conversation.last_activity_at = timezone.now()
                        conversation.save()
                        
                        return {
                            'message_id': ai_message.id,
                            'response': structured_response['response'],
                            'conversation_updated': True,
                            'intent_detected': 'workout_generated',
                            'action': 'workouts_created',
                            'workouts_created': len(workout_creation['workouts']),
                            'workout_ids': [w['id'] for w in workout_creation['workouts']],
                            'options': structured_response.get('options', []),
                            'method': 'ai_plan_extraction',
                        }
                
                # Resposta normal (sem plano detectado)
                ai_message = self._save_ai_message(
                    conversation,
                    ai_response['content'],
                    response_time_ms=round((time.time() - start_time) * 1000, 2),
                    confidence_score=ai_response.get('confidence_score', 0.8),
                    intent=intent_analysis.get('intent')
                )
                
                conversation.message_count += 2
                conversation.ai_responses_count += 1
                conversation.last_activity_at = timezone.now()
                conversation.save()
                
                return {
                    'message_id': ai_message.id,
                    'response': ai_response['content'],
                    'conversation_updated': True,
                    'intent_detected': intent_analysis.get('intent'),
                    'confidence_score': ai_response.get('confidence_score'),
                    'method': 'gemini_ai',
                }
            
            # Fallback se IA falhou
            fallback_response = self._generate_fallback_response(
                conversation, message, intent_analysis
            )
            
            ai_message = self._save_ai_message(
                conversation,
                fallback_response,
                response_time_ms=round((time.time() - start_time) * 1000, 2),
                confidence_score=0.6,
                intent=intent_analysis.get('intent')
            )
            
            conversation.message_count += 2
            conversation.ai_responses_count += 1
            conversation.last_activity_at = timezone.now()
            conversation.save()
            
            return {
                'message_id': ai_message.id,
                'response': fallback_response,
                'conversation_updated': True,
                'method': 'rule_based_fallback',
            }
            
        except Conversation.DoesNotExist:
            return {'error': 'Conversa não encontrada'}
        except Exception as e:
            logger.error(f"❌ ERRO no process_user_message: {e}")
            logger.error(traceback.format_exc())
            return {
                'error': 'Erro ao processar mensagem',
                'details': str(e),
                'method': 'error_handler'
            }
    
    def _create_workouts_from_plan(self, conversation: Conversation, plan_info: Dict) -> Dict:
        """Cria múltiplos treinos (um por dia) a partir do plano extraído"""
        try:
            from apps.workouts.models import Workout, WorkoutExercise
            from apps.exercises.models import Exercise
            
            user = conversation.user
            workouts_created = []
            exercises_by_day = plan_info.get('exercises_by_day', {})
            
            logger.info(f"📋 Criando treinos para {len(exercises_by_day)} dias...")
            
            for day_num, (day_name, day_data) in enumerate(exercises_by_day.items(), 1):
                try:
                    workout_name = f"{day_data['name']} - {day_name.capitalize()}"
                    
                    # 🔥 CORRIGIDO: Criar Workout com campos corretos do modelo
                    workout = Workout.objects.create(
                        name=workout_name,
                        description=f"Treino de {day_name} gerado pela IA\n"
                                   f"Foco: {plan_info.get('focus', 'full body')}\n"
                                   f"Criado em: {datetime.now().strftime('%d/%m/%Y')}",
                        workout_type=plan_info.get('focus', 'full_body'),
                        difficulty_level=plan_info.get('difficulty', 'intermediate'),
                        created_by_user=user,  # 🔥 Campo correto para associar ao usuário
                        is_recommended=True,  # 🔥 Marcar como treino recomendado pela IA
                        is_personalized=True,
                    )
                    
                    logger.info(f"✅ Workout criado: {workout.name} (ID: {workout.id})")
                    
                    exercises = day_data.get('exercises', [])
                    
                    for order, exercise_data in enumerate(exercises, 1):
                        try:
                            exercise = Exercise.objects.filter(
                                name__icontains=exercise_data['name']
                            ).first()
                            
                            if not exercise:
                                logger.warning(
                                    f"⚠️ Exercício não encontrado: {exercise_data['name']}. "
                                    f"Criando genérico..."
                                )
                                exercise = Exercise.objects.create(
                                    name=exercise_data['name'],
                                    description=f"Exercício: {exercise_data['name']}",
                                    difficulty_level=plan_info.get('difficulty', 'intermediate'),
                                )
                            
                            WorkoutExercise.objects.create(
                                workout=workout,
                                exercise=exercise,
                                sets=exercise_data.get('sets', 3),
                                reps=exercise_data.get('reps', '8-12'),
                                rest_time=exercise_data.get('rest_time', 60),
                                order_in_workout=order,
                            )
                            
                            logger.info(f"   ✓ {exercise.name}")
                            
                        except Exception as e:
                            logger.warning(f"   ✗ Erro ao adicionar exercício: {e}")
                    
                    workouts_created.append({
                        'id': workout.id,
                        'name': workout.name,
                        'day': day_name,
                        'exercises': len(exercises),
                    })
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao criar workout para {day_name}: {e}")
            
            # 🔥 RETURN DENTRO DO TRY PRINCIPAL
            return {
                'success': len(workouts_created) > 0,
                'workouts': workouts_created,
                'total': len(workouts_created),
            }
            
        except Exception as e:
            logger.error(f"❌ Erro crítico ao criar workouts: {e}")
            # 🔥 RETURN DENTRO DO EXCEPT
            return {'success': False, 'workouts': []}
    
    def _create_workout_success_response(self, conversation: Conversation, ai_content: str, 
                                        workouts: List[Dict], plan_info: Dict) -> Dict:
        """Cria resposta estruturada com botões para os treinos criados"""
        try:
            days_created = ', '.join([w['day'].capitalize() for w in workouts])
            
            response_text = (
                f"✅ **Treino criado com sucesso!**\n\n"
                f"📋 {len(workouts)} treinos gerados:\n"
                f"   • {days_created}\n\n"
                f"💪 {sum(w['exercises'] for w in workouts)} exercícios no total\n"
                f"📅 {plan_info.get('days_per_week', 5)} dias por semana\n\n"
                f"**O que fazer agora?**"
            )
            
            options = []
            
            # Opção 1: Ver todos os treinos
            options.append({
                'id': 'view_all_workouts',
                'label': '👁️ Ver Todos os Treinos',
                'emoji': '👁️',
                'action': 'navigate',
                'data': {
                    'screen': 'my_workouts',
                    'filter': 'recent',
                }
            })
            
            # Opção 2: Começar primeiro treino
            if workouts:
                first_workout = workouts[0]
                options.append({
                    'id': 'start_first_workout',
                    'label': f"▶️ Iniciar: {first_workout['day'].capitalize()}",
                    'emoji': '▶️',
                    'action': 'start_workout',
                    'data': {
                        'workout_id': first_workout['id'],
                    }
                })
            
            # Opção 3: Continuar conversa
            options.append({
                'id': 'continue_chat',
                'label': '💬 Continuar Conversa',
                'emoji': '💬',
                'action': 'chat',
                'data': {}
            })
            
            return {
                'response': response_text,
                'options': options,
                'action': 'workouts_created',
                'metadata': {
                    'workouts_count': len(workouts),
                    'total_exercises': sum(w['exercises'] for w in workouts),
                    'created_at': datetime.now().isoformat(),
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar resposta: {e}")
            return {
                'response': '✅ Treinos criados com sucesso!',
                'options': [],
                'action': 'workouts_created',
                'metadata': {}
            }
        # ============================================================
        # 🔥 MÉTODOS DO FLUXO DE GERAÇÃO DE TREINO
        # ============================================================
    
    def _check_workout_generation_flow(self, conversation_id: int, message: str) -> dict:
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            
            context = ChatContext.objects.filter(
                conversation=conversation,
                context_type='workflow',
                context_key='workout_generation'
            ).first()
            
            if not context:
               # context = ChatContext.set_context(...)
               context = ChatContext.set_context(
                conversation=conversation,
                context_type='workflow',
                key='workout_generation',
                value={'workout_flow_state': WorkoutGenerationFlow.STATE_INITIAL, 'workout_flow_data': {}},
                relevance=1.0
)
            
            flow_state = context.context_value.get('workout_flow_state')
            flow_data = context.context_value.get('workout_flow_data', {})
            
            logger.info(f"📊 Estado: {flow_state} | Dados: {flow_data}")
            
            # 🔥 NOVO: Verificar se o estado foi mantido incorretamente
            if flow_state and flow_data:
                # Se já tem focus E days, não pode estar em WAITING_FOCUS
                if (flow_state == WorkoutGenerationFlow.STATE_WAITING_FOCUS and 
                    'focus' in flow_data and 'days' in flow_data):
                    
                    logger.warning("⚠️ Estado inconsistente! Corrigindo...")
                    
                    # Determinar estado correto
                    if 'difficulty' in flow_data:
                        correct_state = WorkoutGenerationFlow.STATE_WAITING_CONFIRMATION
                    elif 'days' in flow_data:
                        correct_state = WorkoutGenerationFlow.STATE_WAITING_DIFFICULTY
                    else:
                        correct_state = WorkoutGenerationFlow.STATE_WAITING_DAYS
                    
                    # Atualizar
                    ChatContext.set_context(
                        conversation=conversation,
                        context_type='workflow',
                        key='workout_generation',
                        value={
                            'workout_flow_state': correct_state,
                            'workout_flow_data': flow_data
                        },
                        relevance=1.0
                    )
                    
                    flow_state = correct_state
                    logger.info(f"✅ Estado corrigido para: {flow_state}")
            
            # ============================================================
            # 5. PROCESSAR ESTADOS DO FLUXO
            # ============================================================
            
            # WAITING_FOCUS
            if flow_state == WorkoutGenerationFlow.STATE_WAITING_FOCUS:
                logger.info("⏳ WAITING_FOCUS")
                
                focus_key = WorkoutGenerationFlow.detect_focus_intent(message)
                logger.info(f"🎯 Focus detectado: {focus_key}")
                
                if focus_key:
                    focus_info = WorkoutGenerationFlow.FOCUS_OPTIONS.get(focus_key)
                    
                    if not focus_info:
                        logger.error(f"❌ Focus inválido: {focus_key}")
                        return {
                            'in_flow': True,
                            'response': "❌ Opção inválida. Escolha 1-9 ou digite o nome."
                        }
                    
                    # Atualizar dados
                    flow_data['focus'] = focus_info['value']
                    flow_data['focus_label'] = focus_info['label']
                    
                    prompt = WorkoutGenerationFlow.get_days_prompt(focus_info['label'])
                    
                    # Salvar estado
                    ChatContext.set_context(
                        conversation=conversation,
                        context_type='workflow',
                        key='workout_generation',
                        value={
                            'workout_flow_state': prompt['next_state'],
                            'workout_flow_data': flow_data
                        },
                        relevance=1.0
                    )
                    
                    logger.info(f"✅ Focus: {focus_info['label']} | Próximo: {prompt['next_state']}")
                    
                    return {
                        'in_flow': True,
                        'response': prompt['message'],
                        'options': prompt.get('options', [])
                    }
                else:
                    logger.warning(f"⚠️ Focus não reconhecido: {message}")
                    return {
                        'in_flow': True,
                        'response': "❌ Opção inválida.\n\n"
                                "**Escolha:**\n"
                                "• Número: 1, 2, 3...\n"
                                "• Nome: 'completo', 'peito', 'pernas'..."
                    }
            
            # WAITING_DAYS
            elif flow_state == WorkoutGenerationFlow.STATE_WAITING_DAYS:
                logger.info("⏳ WAITING_DAYS")
                
                days = WorkoutGenerationFlow.detect_days_intent(message)
                logger.info(f"🎯 Dias detectados: {days}")
                
                if days:
                    flow_data['days'] = days
                    
                    prompt = WorkoutGenerationFlow.get_difficulty_prompt(days)
                    
                    # Salvar estado
                    ChatContext.set_context(
                        conversation=conversation,
                        context_type='workflow',
                        key='workout_generation',
                        value={
                            'workout_flow_state': prompt['next_state'],
                            'workout_flow_data': flow_data
                        },
                        relevance=1.0
                    )
                    
                    logger.info(f"✅ Dias: {days} | Próximo: {prompt['next_state']}")
                    
                    return {
                        'in_flow': True,
                        'response': prompt['message'],
                        'options': prompt.get('options', [])
                    }
                else:
                    logger.warning(f"⚠️ Dias inválidos: {message}")
                    return {
                        'in_flow': True,
                        'response': "❌ Escolha entre 3, 4, 5 ou 6 dias.\n\n"
                                "**Exemplo:** Digite apenas o número: '5'"
                    }
            
            # WAITING_DIFFICULTY
            elif flow_state == WorkoutGenerationFlow.STATE_WAITING_DIFFICULTY:
                logger.info("⏳ WAITING_DIFFICULTY")
                
                difficulty_key = WorkoutGenerationFlow.detect_difficulty_intent(message)
                logger.info(f"🎯 Dificuldade: {difficulty_key}")
                
                if difficulty_key:
                    difficulty_info = WorkoutGenerationFlow.DIFFICULTY_OPTIONS.get(difficulty_key)
                    
                    if not difficulty_info:
                        logger.error(f"❌ Dificuldade inválida: {difficulty_key}")
                        return {
                            'in_flow': True,
                            'response': "❌ Escolha: 1, 2 ou 3."
                        }
                    
                    flow_data['difficulty'] = difficulty_info['value']
                    flow_data['difficulty_label'] = difficulty_info['label']
                    
                    prompt = WorkoutGenerationFlow.get_confirmation_prompt(
                        flow_data.get('focus_label', ''),
                        flow_data.get('days', 5),
                        difficulty_info['label']
                    )
                    
                    # Salvar estado
                    ChatContext.set_context(
                        conversation=conversation,
                        context_type='workflow',
                        key='workout_generation',
                        value={
                            'workout_flow_state': prompt['next_state'],
                            'workout_flow_data': flow_data
                        },
                        relevance=1.0
                    )
                    
                    logger.info(f"✅ Dificuldade: {difficulty_info['label']} | Próximo: {prompt['next_state']}")
                    
                    return {
                        'in_flow': True,
                        'response': prompt['message'],
                        'options': prompt.get('options', [])
                    }
                else:
                    logger.warning(f"⚠️ Dificuldade não reconhecida: {message}")
                    return {
                        'in_flow': True,
                        'response': "❌ Escolha:\n"
                                "• 1 = Iniciante\n"
                                "• 2 = Intermediário\n"
                                "• 3 = Avançado"
                    }
            
            # Nenhum fluxo ativo
            logger.info("ℹ️ Sem fluxo ativo")
            return {'in_flow': False}
            
            
        except Exception as e:
            logger.error(f"❌ ERRO CRÍTICO: {e}")
            logger.error(traceback.format_exc())
            return {
                'in_flow': False,
                'error': str(e)
            }
    def generate_workout_with_ai(self, user, preferences: Dict) -> Dict:
        """
        Gera treino SEMANAL (separado por dias) usando IA
        
        preferences: {
            'focus': 'full_body', 'upper', 'lower', 'cardio', etc
            'days': 3-6
            'difficulty': 'beginner', 'intermediate', 'advanced'
        }
        
        Retorna:
        {
            'success': True,
            'workout_id': id,
            'workout_data': {...}
        }
        """
        try:
            from apps.users.models import UserProfile
            from apps.workouts.models import Workout, WorkoutExercise
            from apps.exercises.models import Exercise
            from apps.recommendations.services.ai_service import AIService
            
            logger.info(f"🤖 Gerando treino IA via chat para {user.email}")
            logger.info(f"   Preferências: {preferences}")
            
            # 1. Buscar perfil do usuário
            try:
                profile = UserProfile.objects.get(user=user)
            except UserProfile.DoesNotExist:
                logger.error("Perfil não encontrado")
                return {
                    'success': False,
                    'error': 'Perfil incompleto',
                    'message': 'Complete seu perfil para gerar treinos'
                }
            
            # 2. Mapear dificuldade
            difficulty_map = {
                'iniciante': 'beginner',
                'intermediario': 'intermediate',
                'avancado': 'advanced'
            }
            difficulty = difficulty_map.get(
                preferences.get('difficulty', 'intermediate'),
                'intermediate'
            )
            
            # 3. Chamar IA para gerar plano
            ai_service = AIService()
            if not ai_service.is_available:
                logger.warning("IA não disponível, usando fallback")
                return self._generate_fallback_workout(user, preferences)
            
            # Calcular duração estimada (30-60 min por treino)
            duration = preferences.get('duration', 45)
            
            workout_plan = ai_service.generate_personalized_workout_plan(
                profile,
                duration=duration,
                focus=preferences.get('focus', 'full_body'),
                difficulty=difficulty
            )
            
            if not workout_plan:
                logger.error("IA não retornou plano válido")
                return self._generate_fallback_workout(user, preferences)
            
            # 4. NOVO: Estruturar como plano SEMANAL
            weekly_workout = self._structure_workout_by_days(
                workout_plan,
                preferences.get('days', 5),
                preferences.get('focus', 'full_body')
            )
            
            # 5. Criar Workout no banco de dados
            workout = Workout.objects.create(
                name=weekly_workout['name'],
                description=weekly_workout['description'],
                difficulty_level=difficulty,
                estimated_duration=duration,
                target_muscle_groups=weekly_workout.get('target_muscle_groups', ''),
                equipment_needed=weekly_workout.get('equipment_needed', 'Variado'),
                calories_estimate=weekly_workout.get('calories_estimate', 200),
                workout_type=weekly_workout.get('workout_type', 'full_body'),
                is_recommended=True,
                is_personalized=True,
                created_by_user=user
            )
            
            logger.info(f"✅ Workout criado: {workout.name} (ID: {workout.id})")
            
            # 6. Adicionar exercícios por dia
            exercises_added = 0
            for day_data in weekly_workout.get('days', []):
                for idx, ex_data in enumerate(day_data.get('exercises', []), start=1):
                    # Buscar ou criar exercício
                    exercise, created = Exercise.objects.get_or_create(
                        name=ex_data.get('name', f'Exercício {idx}'),
                        defaults={
                            'description': ex_data.get('description', ''),
                            'muscle_group': ex_data.get('muscle_group', 'full_body'),
                            'difficulty_level': difficulty,
                            'equipment_needed': ex_data.get('equipment_needed', 'bodyweight'),
                            'duration_minutes': ex_data.get('duration_minutes', 5),
                            'calories_per_minute': 5.0,
                            'instructions': ex_data.get('instructions', []),
                        }
                    )
                    
                    # Criar WorkoutExercise
                    WorkoutExercise.objects.create(
                        workout=workout,
                        exercise=exercise,
                        sets=ex_data.get('sets', 3),
                        reps=ex_data.get('reps', '12-15'),
                        weight=ex_data.get('weight'),
                        rest_time=ex_data.get('rest_time', 60),
                        order_in_workout=idx,
                        notes=f"Dia: {day_data.get('day', 'N/A')}\n" + 
                            '\n'.join(ex_data.get('tips', []))
                    )
                    exercises_added += 1
            
            logger.info(f"✅ Total: {exercises_added} exercícios adicionados")
            
            return {
                'success': True,
                'workout_id': workout.id,
                'workout_name': workout.name,
                'total_exercises': exercises_added,
                'days_per_week': preferences.get('days', 5),
                'difficulty': difficulty,
                'focus': preferences.get('focus', 'full_body'),
                'estimated_duration': duration
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar treino com IA: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {
                'success': False,
                'error': 'Erro ao gerar treino',
                'details': str(e)
            }

    def _structure_workout_by_days(self, workout_plan: Dict, days_per_week: int, 
                                focus: str) -> Dict:
        """
        Estrutura plano de treino da IA para organização por DIAS
        
        Exemplo retorno:
        {
            'name': 'Plano Semanal - Upper/Lower',
            'days': [
                {
                    'day': 'Segunda',
                    'focus': 'Peito e Tríceps',
                    'exercises': [...]
                },
                ...
            ]
        }
        """
        exercises = workout_plan.get('exercises', [])
        
        # Definir estrutura de dias
        if focus == 'full_body':
            day_structure = [
                {'day': 'Segunda', 'focus': 'Peito e Tríceps', 'muscle_groups': ['chest', 'arms']},
                {'day': 'Terça', 'focus': 'Costas e Bíceps', 'muscle_groups': ['back', 'arms']},
                {'day': 'Quarta', 'focus': 'Pernas', 'muscle_groups': ['legs', 'glutes']},
                {'day': 'Quinta', 'focus': 'Ombros', 'muscle_groups': ['shoulders']},
                {'day': 'Sexta', 'focus': 'Cardio/Flexibilidade', 'muscle_groups': ['cardio']},
                {'day': 'Sábado', 'focus': 'Complemento', 'muscle_groups': ['full_body']},
            ]
        elif focus == 'upper':
            day_structure = [
                {'day': 'Segunda', 'focus': 'Peito', 'muscle_groups': ['chest']},
                {'day': 'Quarta', 'focus': 'Costas', 'muscle_groups': ['back']},
                {'day': 'Sexta', 'focus': 'Ombros/Braços', 'muscle_groups': ['shoulders', 'arms']},
            ]
        elif focus == 'lower':
            day_structure = [
                {'day': 'Segunda', 'focus': 'Quadríceps', 'muscle_groups': ['legs']},
                {'day': 'Quarta', 'focus': 'Posteriores/Glúteos', 'muscle_groups': ['glutes', 'legs']},
                {'day': 'Sexta', 'focus': 'Pernas Completo', 'muscle_groups': ['legs', 'glutes']},
            ]
        elif focus == 'cardio':
            day_structure = [
                {'day': 'Segunda', 'focus': 'Cardio Intenso', 'muscle_groups': ['cardio']},
                {'day': 'Quarta', 'focus': 'Cardio Moderado', 'muscle_groups': ['cardio']},
                {'day': 'Sexta', 'focus': 'Cardio Leve', 'muscle_groups': ['cardio']},
            ]
        else:
            day_structure = [
                {'day': 'Segunda', 'focus': 'Treino Geral', 'muscle_groups': ['full_body']},
                {'day': 'Quarta', 'focus': 'Treino Geral', 'muscle_groups': ['full_body']},
                {'day': 'Sexta', 'focus': 'Treino Geral', 'muscle_groups': ['full_body']},
            ]
        
        # Selecionar apenas os dias necessários
        selected_days = day_structure[:days_per_week]
        
        # Distribuir exercícios entre os dias
        exercises_per_day = max(1, len(exercises) // len(selected_days))
        
        for i, day_info in enumerate(selected_days):
            start_idx = i * exercises_per_day
            end_idx = start_idx + exercises_per_day
            
            day_exercises = exercises[start_idx:end_idx]
            
            # Se é o último dia, adicionar exercícios restantes
            if i == len(selected_days) - 1:
                day_exercises = exercises[start_idx:]
            
            day_info['exercises'] = day_exercises
        
        return {
            'name': f"Plano Semanal - {focus.replace('_', ' ').title()}",
            'description': f"Treino de {days_per_week} dias por semana focado em {focus}",
            'target_muscle_groups': focus,
            'equipment_needed': workout_plan.get('equipment_needed', 'Variado'),
            'calories_estimate': workout_plan.get('calories_estimate', 200),
            'workout_type': workout_plan.get('workout_type', 'full_body'),
            'days': selected_days
        }

    def _generate_fallback_workout(self, user, preferences: Dict) -> Dict:
        """Fallback quando IA não está disponível"""
        logger.warning("Usando fallback para geração de treino")
        # Retornar erro ou usar método anterior sem IA
        return {
            'success': False,
            'error': 'IA temporariamente indisponível',
            'message': 'Tente novamente em alguns minutos'
        }    
    def clear_workout_flow(self, conversation_id: int):
        """Limpa o fluxo de geração de treino"""
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            
            ChatContext.set_context(
                conversation=conversation,
                context_type='workflow',
                key='workout_generation',
                value={
                    'workout_flow_state': None,
                    'workout_flow_data': {}
                },
                relevance=0.5
            )
            
            logger.info(f"✅ Fluxo limpo: conversa {conversation_id}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao limpar fluxo: {e}")

    # 🔥 ADICIONAR: Método auxiliar no ChatService
    def get_flow_state(self, conversation_id: int) -> dict:
        """Retorna estado atual do fluxo (para debug)"""
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            context = ChatContext.objects.filter(conversation=conversation).first()
            
            if context:
                return {
                    'has_context': True,
                    'context_id': context.id,
                    'context_type': context.context_type,
                    'context_key': context.context_key,
                    'context_value_type': type(context.context_value).__name__,
                    'flow_state': context.context_value.get('workout_flow_state'),
                    'flow_data': context.context_value.get('workout_flow_data'),
                }
            return {'has_context': False}
        
        except Exception as e:
            return {'error': str(e), 'traceback': traceback.format_exc()}
        
    def get_flow_debug(self, conversation_id: int) -> dict:
        """Retorna estado do fluxo para debug"""
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            
            context = ChatContext.objects.filter(
                conversation=conversation,
                context_type='workflow',
                context_key='workout_generation'
            ).first()
            
            if context:
                return {
                    'has_context': True,
                    'context_id': context.id,
                    'flow_state': context.context_value.get('workout_flow_state'),
                    'flow_data': context.context_value.get('workout_flow_data'),
                    'updated_at': context.updated_at.isoformat()
                }
            
            return {'has_context': False}
        
        except Exception as e:
            return {'error': str(e)}
    
    # 🔥 ADICIONAR: Método para verificar estado atual (DEBUG)
    def get_flow_debug_info(self, conversation_id: int) -> dict:
        """Retorna informações de debug do fluxo"""
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            context = ChatContext.objects.filter(conversation=conversation).first()
            
            if context:
                return {
                    'has_context': True,
                    'flow_state': context.context_value.get('workout_flow_state'),
                    'flow_data': context.context_value.get('workout_flow_data'),
                    'context_type': context.context_type,
                    'context_key': context.context_key,
                }
            return {'has_context': False}
        except Exception as e:
            return {'error': str(e)}
    
    # ============================================================
    # MÉTODOS EXISTENTES (SEM ALTERAÇÃO)
    # ============================================================
    
    def _initialize_conversation_context(self, conversation: Conversation):
        """Carrega contexto inicial do usuário para personalização"""
        try:
            user = conversation.user
            
            try:
                profile = UserProfile.objects.get(user=user)
                ChatContext.set_context(
                    conversation, 'user_profile', 'basic_info',
                    {
                        'goal': profile.goal,
                        'activity_level': profile.activity_level,
                        'focus_areas': profile.focus_areas,
                        'age': profile.age,
                        'current_weight': profile.current_weight,
                        'target_weight': profile.target_weight,
                    },
                    relevance=1.0
                )
            except UserProfile.DoesNotExist:
                ChatContext.set_context(
                    conversation, 'user_profile', 'basic_info',
                    {'profile_complete': False},
                    relevance=0.5
                )
            
            recent_sessions = WorkoutSession.objects.filter(
                user=user,
                completed=True,
                completed_at__gte=timezone.now() - timedelta(days=7)
            ).order_by('-completed_at')[:5]
            
            workout_history = []
            for session in recent_sessions:
                workout_history.append({
                    'workout_name': session.workout.name if session.workout else 'Treino Personalizado',
                    'completed_at': session.completed_at.strftime('%d/%m/%Y'),
                    'rating': session.user_rating,
                    'duration': session.actual_duration
                })
            
            ChatContext.set_context(
                conversation, 'workout_history', 'recent_workouts',
                {'recent_sessions': workout_history},
                relevance=0.8
            )
            
            ChatContext.set_context(
                conversation, 'preferences', 'conversation_style',
                {'preferred_response_length': 'medium', 'technical_level': 'intermediate'},
                relevance=0.6
            )
            
        except Exception as e:
            logger.error(f"Error initializing conversation context: {e}")
    
    def _analyze_message_intent(self, message: str, conversation: Conversation) -> Dict:
        """Analisa intenção da mensagem usando regras"""
        try:
            cache_key = f"intent_analysis_{hash(message.lower())}"
            cached_intent = cache.get(cache_key)
            if cached_intent:
                return cached_intent
            
            rule_intent = self._rule_based_intent_analysis(message)
            cache.set(cache_key, rule_intent, 1800)
            return rule_intent
            
        except Exception as e:
            logger.error(f"Error analyzing message intent: {e}")
            return {'intent': 'general_question', 'confidence': 0.5}
    
    def _rule_based_intent_analysis(self, message: str) -> Dict:
        """Análise de intenção baseada em regras"""
        message_lower = message.lower()
        
        intent_keywords = {
            'workout_request': ['treino', 'exercício', 'workout', 'série', 'repetição', 'treinar'],
            'technique_question': ['como', 'técnica', 'forma', 'postura', 'execução', 'executar'],
            'nutrition_advice': ['alimentação', 'dieta', 'nutrição', 'proteína', 'comer', 'comida'],
            'progress_inquiry': ['progresso', 'resultado', 'evolução', 'melhora', 'crescimento'],
            'motivation_need': ['motivação', 'desânimo', 'preguiça', 'força', 'conseguir'],
            'equipment_question': ['equipamento', 'aparelho', 'peso', 'halteres', 'academia'],
            'injury_concern': ['dor', 'lesão', 'machuca', 'problema', 'desconforto'],
            'schedule_planning': ['rotina', 'horário', 'frequência', 'quando', 'quantas vezes']
        }
        
        intent_scores = {}
        for intent, keywords in intent_keywords.items():
            score = sum([1 for keyword in keywords if keyword in message_lower])
            if score > 0:
                intent_scores[intent] = score / len(keywords)
        
        if intent_scores:
            main_intent = max(intent_scores, key=intent_scores.get)
            confidence = intent_scores[main_intent]
        else:
            main_intent = 'general_question'
            confidence = 0.5
        
        return {
            'intent': main_intent,
            'confidence': confidence,
            'secondary_intents': [intent for intent, score in intent_scores.items() 
                                 if intent != main_intent and score > 0.2],
            'keywords': [word for word in message_lower.split() 
                        if any(word in keywords for keywords in intent_keywords.values())],
            'urgency_level': 'high' if any(word in message_lower for word in ['dor', 'lesão', 'urgente']) else 'medium',
            'requires_personalization': True
        }
    
    def _generate_ai_response(self, conversation: Conversation, message: str, intent_analysis: Dict) -> Optional[Dict]:
        """Gera resposta usando Gemini"""
        if not self.ai_service.is_available:
            logger.warning("Gemini AI not available, will use fallback")
            return None
        
        try:
            context_data = self._build_conversation_context(conversation)
            recent_messages = conversation.get_last_messages(6)
            
            conversation_history = ""
            for msg in reversed(recent_messages):
                role = "Usuário" if msg.message_type == 'user' else "Alex"
                conversation_history += f"{role}: {msg.content}\n"
            
            system_context = self._build_fitness_chat_system_prompt(intent_analysis, context_data)
            
            full_prompt = f"""{system_context}

HISTÓRICO DA CONVERSA:
{conversation_history}

MENSAGEM ATUAL DO USUÁRIO:
{message}

Responda de forma natural, personalizada e útil. Máximo 200 palavras."""
            
            response = self.ai_service._make_gemini_request(full_prompt)
            
            if response:
                processed_response = self._process_ai_response(response, intent_analysis)
                return processed_response
            
        except Exception as e:
            logger.error(f"Error generating Gemini AI response: {e}")
        
        return None
    
    def _build_fitness_chat_system_prompt(self, intent_analysis: Dict, context_data: Dict) -> str:
        """Constrói prompt de sistema otimizado para chat fitness"""
        user_profile = context_data.get('user_profile', {})
        workout_history = context_data.get('workout_history', {})
        
        base_prompt = """Você é Alex, um personal trainer virtual especialista em fitness com 10 anos de experiência.

PERSONALIDADE:
- Amigável, motivador e profissional
- Usa linguagem clara e acessível
- Encoraja sem ser excessivo
- Foca na segurança e na progressão gradual
- Baseado em evidência científica

DIRETRIZES DE RESPOSTA:
- Máximo 200 palavras por resposta
- Use emojis ocasionalmente para engajamento
- Seja específico e prático
- Sempre priorize a segurança
- Adapte ao nível do usuário"""
        
        if user_profile.get('goal'):
            base_prompt += f"\n\nOBJETIVO DO USUÁRIO: {user_profile['goal']}"
        
        if user_profile.get('activity_level'):
            base_prompt += f"\nNÍVEL ATUAL: {user_profile['activity_level']}"
        
        intent_contexts = {
            'workout_request': "\nFOCO: Recomende exercícios seguros e progressivos. Sempre inclua aquecimento e alongamento.",
            'technique_question': "\nFOCO: Explique técnica com clareza, enfatize segurança e sugira progressões.",
            'nutrition_advice': "\nFOCO: Dê orientações gerais, sempre recomende consulta com nutricionista para planos específicos.",
            'progress_inquiry': "\nFOCO: Analise dados disponíveis, celebre conquistas e sugira próximos passos.",
            'motivation_need': "\nFOCO: Seja encorajador, lembre dos benefícios e sugira estratégias práticas.",
            'injury_concern': "\nFOCO: Priorize segurança, recomende descanso se necessário e consulta profissional."
        }
        
        intent = intent_analysis.get('intent', 'general_question')
        if intent in intent_contexts:
            base_prompt += intent_contexts[intent]
        
        if workout_history.get('recent_sessions'):
            base_prompt += f"\n\nHISTÓRICO RECENTE: {len(workout_history['recent_sessions'])} treinos realizados recentemente."
        
        base_prompt += "\n\nSempre termine perguntando se precisa de mais alguma coisa ou esclarecimento adicional."
        
        return base_prompt
    
    def _process_ai_response(self, response: str, intent_analysis: Dict) -> Dict:
        """Processa resposta da IA para extrair metadados úteis"""
        processed = {
            'success': True,
            'content': response,
            'confidence_score': 0.85,
            'suggested_actions': [],
            'workout_references': []
        }
        
        response_lower = response.lower()
        
        action_patterns = {
            'try_exercise': ['experimente', 'tente fazer', 'faça'],
            'rest_recovery': ['descanse', 'pause', 'recuperação'],
            'seek_professional': ['consulte', 'procure um', 'médico', 'fisioterapeuta'],
            'schedule_workout': ['agende', 'planeje', 'organize'],
            'track_progress': ['anote', 'registre', 'acompanhe']
        }
        
        for action, patterns in action_patterns.items():
            if any(pattern in response_lower for pattern in patterns):
                processed['suggested_actions'].append(action)
        
        exercise_mentions = []
        common_exercises = ['agachamento', 'flexão', 'corrida', 'caminhada', 'prancha', 'abdominais']
        
        for exercise in common_exercises:
            if exercise in response_lower:
                exercise_mentions.append(exercise)
        
        processed['workout_references'] = exercise_mentions
        
        return processed
    
    def _generate_fallback_response(self, conversation: Conversation, message: str, intent_analysis: Dict) -> str:
        """Gera resposta baseada em regras quando IA não está disponível"""
        intent = intent_analysis.get('intent', 'general_question')
        user_name = conversation.user.first_name or 'amigo(a)'
        
        fallback_responses = {
            'workout_request': f"Olá, {user_name}! Para recomendações de treino personalizadas, que tal começarmos com alguns exercícios básicos? Posso sugerir um treino de corpo inteiro com agachamentos, flexões e prancha. Você tem alguma preferência específica ou restrição?",
            
            'technique_question': f"Ótima pergunta sobre técnica, {user_name}! A execução correta é fundamental para evitar lesões e maximizar resultados. Para exercícios específicos, sempre foque em: postura correta, movimento controlado, respiração adequada e progressão gradual. Sobre qual exercício você gostaria de saber mais?",
            
            'nutrition_advice': f"Nutrição é super importante, {user_name}! Algumas dicas básicas: mantenha-se hidratado, inclua proteínas em cada refeição, e consuma vegetais variados. Para um plano nutricional específico, recomendo consultar um nutricionista qualificado. Posso ajudar com mais alguma coisa sobre fitness?",
            
            'progress_inquiry': f"Que bom que você está acompanhando seu progresso, {user_name}! O importante é a consistência. Celebre cada pequena vitória e lembre-se que resultados levam tempo. Continue firme na sua rotina! Como você tem se sentido nos treinos recentes?",
            
            'motivation_need': f"Entendo, {user_name}. Todos passamos por momentos assim! Lembre-se: cada treino é um investimento na sua saúde e bem-estar. Comece pequeno se necessário - até 10 minutos já fazem diferença. Você é mais forte do que imagina! O que te motivou a começar essa jornada?",
            
            'injury_concern': f"Sua segurança é prioridade, {user_name}. Se você está sentindo dor, é importante parar e avaliar. Para dores persistentes, sempre consulte um profissional de saúde. No treino, escute sempre seu corpo. Posso ajudar com exercícios de baixo impacto enquanto se recupera?",
            
            'general_question': f"Oi, {user_name}! Estou aqui para ajudar com suas dúvidas sobre fitness. Posso orientar sobre exercícios, técnicas, motivação e planejamento de treinos. No que posso te auxiliar hoje?"
        }
        
        return fallback_responses.get(intent, fallback_responses['general_question'])
    
    def _generate_welcome_message(self, conversation: Conversation) -> Optional[Dict]:
        """Gera mensagem de boas-vindas personalizada"""
        try:
            user_name = conversation.user.first_name or 'atleta'
            conversation_type = conversation.conversation_type
            
            if self.ai_service.is_available:
                context_data = self._build_conversation_context(conversation)
                ai_welcome = self._gemini_welcome_message(user_name, conversation_type, context_data)
                if ai_welcome:
                    return ai_welcome
            
            type_messages = {
                'workout_consultation': f"Olá, {user_name}! 💪 Sou Alex, seu personal trainer virtual. Estou aqui para ajudar você a criar treinos personalizados e alcançar seus objetivos. Como posso te ajudar hoje?",
                
                'progress_analysis': f"Oi, {user_name}! 📈 Que bom te ver aqui! Vamos analisar seu progresso e ver como você está evoluindo. Tenho algumas perguntas para entender melhor sua jornada. Pronto para começar?",
                
                'motivation_chat': f"Hey, {user_name}! 🌟 Às vezes todos precisamos de um empurrãozinho, né? Estou aqui para te motivar e lembrar do incrível que você é. Vamos conversar sobre o que está te preocupando?",
                
                'technique_guidance': f"Salve, {user_name}! 🎯 Técnica correta é tudo no fitness! Estou aqui para te ajudar com dúvidas sobre execução de exercícios e boa forma. Qual movimento você gostaria de aperfeiçoar?",
                
                'general_fitness': f"Olá, {user_name}! 🏃‍♂️ Bem-vindo(a) ao seu chat fitness personalizado! Sou Alex e estou aqui para tirar dúvidas, sugerir treinos e te apoiar nessa jornada. O que você gostaria de saber?"
            }
            
            welcome_content = type_messages.get(conversation_type, type_messages['general_fitness'])
            
            return {
                'content': welcome_content,
                'confidence': 0.8,
                'response_time': 100
            }
            
        except Exception as e:
            logger.error(f"Error generating welcome message: {e}")
            return {
                'content': f"Olá! Sou Alex, seu assistente de fitness. Como posso ajudar você hoje?",
                'confidence': 0.6,
                'response_time': 50
            }
    
    def _gemini_welcome_message(self, user_name: str, conversation_type: str, context_data: Dict) -> Optional[Dict]:
        """Gera mensagem de boas-vindas usando Gemini"""
        try:
            user_profile = context_data.get('user_profile', {})
            
            prompt = f"""Crie uma mensagem de boas-vindas personalizada e motivadora para {user_name}.

TIPO DE CONVERSA: {conversation_type}
PERFIL: {user_profile.get('goal', 'não informado')}
NÍVEL: {user_profile.get('activity_level', 'não informado')}

REQUISITOS:
- Máximo 100 palavras
- Tom amigável e profissional
- Mencione o nome da pessoa
- Relacione com o tipo de conversa
- Termine com pergunta envolvente
- Use 1-2 emojis apropriados

Você é Alex, um personal trainer virtual. Responda apenas com a mensagem, sem formatação extra."""
            
            start_time = time.time()
            response = self.ai_service._make_gemini_request(prompt)
            
            if response:
                return {
                    'content': response.strip(),
                    'confidence': 0.9,
                    'response_time': round((time.time() - start_time) * 1000)
                }
                
        except Exception as e:
            logger.error(f"Error generating Gemini welcome message: {e}")
        
        return None
    
    def _save_user_message(self, conversation: Conversation, content: str) -> Message:
        """Salva mensagem do usuário"""
        return Message.objects.create(
            conversation=conversation,
            message_type='user',
            content=content,
            status='delivered'
        )
    
    def _save_ai_message(self, conversation: Conversation, content: str, 
                        response_time_ms: int = 0, confidence_score: float = 0.8,
                        intent: str = None) -> Message:
        """Salva mensagem da IA com modelo Gemini"""
        return Message.objects.create(
            conversation=conversation,
            message_type='ai',
            content=content,
            confidence_score=confidence_score,
            ai_model_version=getattr(settings, 'GEMINI_MODEL', 'gemini-2.5-flash'),
            response_time_ms=response_time_ms,
            tokens_used=len(content.split()) * 1.3,
            intent_detected=intent,
            status='delivered'
        )
    
    def _build_conversation_context(self, conversation: Conversation) -> Dict:
        """Constrói contexto completo da conversa"""
        context_data = {}
        contexts = ChatContext.get_context(conversation)
        
        for context in contexts:
            context_type = context.context_type
            if context_type not in context_data:
                context_data[context_type] = {}
            context_data[context_type][context.context_key] = context.context_value
        
        return context_data
    
    def _update_conversation_context(self, conversation: Conversation, message: str, intent_analysis: Dict):
        """Atualiza contexto da conversa baseado na mensagem atual"""
        try:
            message_length = len(message.split())
            if message_length > 20:
                ChatContext.set_context(
                    conversation, 'preferences', 'message_style',
                    {'prefers_detailed': True, 'last_message_length': message_length},
                    relevance=0.7
                )
            
            intent = intent_analysis.get('intent')
            if intent:
                current_topics = ChatContext.get_context(
                    conversation, 'preferences', 'topics_of_interest'
                ).first()
                
                if current_topics:
                    topics = current_topics.context_value.get('topics', [])
                    if intent not in topics:
                        topics.append(intent)
                        topics = topics[-5:]
                    
                    ChatContext.set_context(
                        conversation, 'preferences', 'topics_of_interest',
                        {'topics': topics},
                        relevance=0.6
                    )
                else:
                    ChatContext.set_context(
                        conversation, 'preferences', 'topics_of_interest',
                        {'topics': [intent]},
                        relevance=0.6
                    )
            
        except Exception as e:
            logger.error(f"Error updating conversation context: {e}")
    
    def get_conversation_history(self, conversation_id: int, limit: int = 50) -> List[Dict]:
        """Retorna histórico formatado da conversa"""
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            messages = conversation.messages.order_by('created_at')[:limit]
            
            history = []
            for message in messages:
                history.append({
                    'id': message.id,
                    'type': message.message_type,
                    'content': message.content,
                    'timestamp': message.created_at.isoformat(),
                    'intent': message.intent_detected,
                    'confidence': message.confidence_score,
                    'user_reaction': message.user_reaction
                })
            
            return history
            
        except Conversation.DoesNotExist:
            return []
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    def end_conversation(self, conversation_id: int, user_rating: float = None) -> Dict:
        """Finaliza conversa com avaliação opcional"""
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            conversation.status = 'completed'
            
            if user_rating:
                conversation.user_satisfaction_rating = user_rating
            
            conversation.save()
            
            # Limpar fluxo de treino ao finalizar
            self.clear_workout_flow(conversation_id)
            
            return {
                'conversation_ended': True,
                'total_messages': conversation.message_count,
                'duration_minutes': (timezone.now() - conversation.created_at).total_seconds() / 60,
                'rating_saved': user_rating is not None
            }
            
        except Conversation.DoesNotExist:
            return {'error': 'Conversa não encontrada'}
        except Exception as e:
            logger.error(f"Error ending conversation: {e}")
            return {'error': 'Erro ao finalizar conversa'}