import 'package:flutter/foundation.dart';
import '../models/chat_models.dart';
import 'api_service.dart';

/// Serviço de gerenciamento do Chatbot
class ChatService extends ChangeNotifier {
  // Estado
  ChatConversation? _currentConversation;
  List<ChatMessage> _messages = [];
  bool _isLoading = false;
  bool _isSending = false;
  String? _error;

  // Getters
  ChatConversation? get currentConversation => _currentConversation;
  List<ChatMessage> get messages => _messages;
  bool get isLoading => _isLoading;
  bool get isSending => _isSending;
  String? get error => _error;
  bool get hasActiveConversation => _currentConversation != null;

  // ============================================================
  // INICIAR CONVERSA
  // ============================================================

  Future<bool> startConversation({
    ConversationType type = ConversationType.generalFitness,
    String? initialMessage,
  }) async {
    try {
      _isLoading = true;
      _error = null;
      notifyListeners();

      debugPrint('🤖 Iniciando conversa: ${type.value}');

      final response = await ApiService.startConversation(
        conversationType: type.value,
        initialMessage: initialMessage,
      );

      if (response['conversation_id'] != null) {
        _currentConversation = ChatConversation(
          id: response['conversation_id'],
          title: 'Conversa ${type.label}',
          type: type.value,
          status: 'active',
          createdAt: DateTime.now(),
          lastActivity: DateTime.now(),
          messageCount: 0,
          aiResponsesCount: 0,
          isExpired: false,
        );

        // Se houver mensagem inicial, carregar histórico
        if (initialMessage != null || response['conversation_resumed'] == true) {
          await loadConversationHistory();
        }

        debugPrint('✅ Conversa iniciada: ID ${_currentConversation!.id}');
        _isLoading = false;
        notifyListeners();
        return true;
      }

      throw Exception('Resposta inválida do servidor');
    } catch (e) {
      debugPrint('❌ Erro ao iniciar conversa: $e');
      _error = 'Não foi possível iniciar a conversa. Tente novamente.';
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  // ============================================================
  // ENVIAR MENSAGEM
  // ============================================================

  Future<bool> sendMessage(String text) async {
    if (_currentConversation == null) {
      debugPrint('⚠️ Nenhuma conversa ativa');
      return false;
    }

    if (text.trim().isEmpty) {
      debugPrint('⚠️ Mensagem vazia');
      return false;
    }

    try {
      _isSending = true;
      _error = null;

      // Adicionar mensagem do usuário imediatamente (otimista)
      final userMessage = ChatMessage(
        text: text,
        isUser: true,
        timestamp: DateTime.now(),
      );
      _messages.add(userMessage);
      notifyListeners();

      debugPrint('📤 Enviando mensagem: ${text.substring(0, text.length > 50 ? 50 : text.length)}...');

      // Enviar para backend
      final response = await ApiService.sendChatMessage(
        conversationId: _currentConversation!.id,
        message: text,
      );

      // Adicionar resposta da IA
      if (response['ai_response'] != null) {
        final aiMessage = ChatMessage(
          id: response['ai_response']['message_id'],
          text: response['ai_response']['content'],
          isUser: false,
          timestamp: DateTime.now(),
          intent: response['ai_response']['intent_detected'],
          confidence: response['ai_response']['confidence_score']?.toDouble(),
          metadata: response['ai_response'],
        );
        _messages.add(aiMessage);
      }

      debugPrint('✅ Mensagem enviada e resposta recebida');
      _isSending = false;
      notifyListeners();
      return true;
    } catch (e) {
      debugPrint('❌ Erro ao enviar mensagem: $e');
      _error = 'Erro ao enviar mensagem. Tente novamente.';
      
      // Remover mensagem otimista em caso de erro
      if (_messages.isNotEmpty && _messages.last.isUser) {
        _messages.removeLast();
      }

      _isSending = false;
      notifyListeners();
      return false;
    }
  }

  // ============================================================
  // CARREGAR HISTÓRICO
  // ============================================================

  Future<void> loadConversationHistory({int limit = 50}) async {
    if (_currentConversation == null) return;

    try {
      _isLoading = true;
      notifyListeners();

      debugPrint('📥 Carregando histórico da conversa ${_currentConversation!.id}');

      final response = await ApiService.getConversationHistory(
        conversationId: _currentConversation!.id,
        limit: limit,
      );

      if (response['messages'] != null) {
        _messages = (response['messages'] as List)
            .map((msg) => ChatMessage.fromJson(msg))
            .toList();

        debugPrint('✅ Histórico carregado: ${_messages.length} mensagens');
      }

      _isLoading = false;
      notifyListeners();
    } catch (e) {
      debugPrint('❌ Erro ao carregar histórico: $e');
      _error = 'Erro ao carregar histórico';
      _isLoading = false;
      notifyListeners();
    }
  }

  // ============================================================
  // FINALIZAR CONVERSA
  // ============================================================

  Future<bool> endConversation({double? rating, String? feedback}) async {
    if (_currentConversation == null) return false;

    try {
      debugPrint('🏁 Finalizando conversa ${_currentConversation!.id}');

      await ApiService.endConversation(
        conversationId: _currentConversation!.id,
        rating: rating,
        feedback: feedback,
      );

      _currentConversation = null;
      _messages.clear();

      debugPrint('✅ Conversa finalizada');
      notifyListeners();
      return true;
    } catch (e) {
      debugPrint('❌ Erro ao finalizar conversa: $e');
      return false;
    }
  }

  // ============================================================
  // FEEDBACK EM MENSAGEM
  // ============================================================

  Future<bool> sendMessageFeedback({
    required int messageId,
    required MessageReaction reaction,
    String? feedback,
  }) async {
    try {
      debugPrint('👍 Enviando feedback para mensagem $messageId: ${reaction.value}');

      await ApiService.sendMessageFeedback(
        messageId: messageId,
        reaction: reaction.value,
        feedback: feedback,
      );

      // Atualizar mensagem local
      final messageIndex = _messages.indexWhere((m) => m.id == messageId);
      if (messageIndex != -1) {
        _messages[messageIndex] = ChatMessage(
          id: _messages[messageIndex].id,
          text: _messages[messageIndex].text,
          isUser: _messages[messageIndex].isUser,
          timestamp: _messages[messageIndex].timestamp,
          intent: _messages[messageIndex].intent,
          confidence: _messages[messageIndex].confidence,
          reaction: reaction.value,
          metadata: _messages[messageIndex].metadata,
        );
        notifyListeners();
      }

      debugPrint('✅ Feedback enviado com sucesso');
      return true;
    } catch (e) {
      debugPrint('❌ Erro ao enviar feedback: $e');
      return false;
    }
  }

  // ============================================================
  // LISTAR CONVERSAS
  // ============================================================

  Future<List<ChatConversation>> getUserConversations({
    String status = 'all',
    int days = 30,
  }) async {
    try {
      debugPrint('📋 Buscando conversas do usuário');

      final response = await ApiService.getUserConversations(
        status: status,
        days: days,
      );

      if (response['conversations'] != null) {
        final conversations = (response['conversations'] as List)
            .map((conv) => ChatConversation.fromJson(conv))
            .toList();

        debugPrint('✅ ${conversations.length} conversas encontradas');
        return conversations;
      }

      return [];
    } catch (e) {
      debugPrint('❌ Erro ao buscar conversas: $e');
      return [];
    }
  }

  // ============================================================
  // RETOMAR CONVERSA
  // ============================================================

  Future<bool> resumeConversation(int conversationId) async {
    try {
      _isLoading = true;
      notifyListeners();

      debugPrint('🔄 Retomando conversa $conversationId');

      // Buscar histórico
      final response = await ApiService.getConversationHistory(
        conversationId: conversationId,
      );

      if (response['conversation'] != null) {
        _currentConversation = ChatConversation.fromJson(response['conversation']);
        
        if (response['messages'] != null) {
          _messages = (response['messages'] as List)
              .map((msg) => ChatMessage.fromJson(msg))
              .toList();
        }

        debugPrint('✅ Conversa retomada: ${_messages.length} mensagens');
        _isLoading = false;
        notifyListeners();
        return true;
      }

      throw Exception('Conversa não encontrada');
    } catch (e) {
      debugPrint('❌ Erro ao retomar conversa: $e');
      _error = 'Não foi possível retomar a conversa';
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  // ============================================================
  // LIMPAR ESTADO
  // ============================================================

  void clearError() {
    _error = null;
    notifyListeners();
  }

  void reset() {
    _currentConversation = null;
    _messages.clear();
    _isLoading = false;
    _isSending = false;
    _error = null;
    notifyListeners();
  }
}