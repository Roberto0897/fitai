import 'package:flutter/foundation.dart';
import '../models/chat_models.dart';
import 'api_service.dart';


/// Serviço de gerenciamento do Chatbot COM geração automática de treino
class ChatService extends ChangeNotifier {
  // Estado
  ChatConversation? _currentConversation;
  List<ChatMessage> _messages = [];
  bool _isLoading = false;
  bool _isSending = false;
  String? _error;
  
  // 🔥 Estado para geração de treino
  bool _isGeneratingWorkout = false;
  Map<String, dynamic>? _lastGeneratedWorkout;

  Map<String, dynamic>? _detectedPlanInfo;

  // Getters
  ChatConversation? get currentConversation => _currentConversation;
  List<ChatMessage> get messages => _messages;
  bool get isLoading => _isLoading;
  bool get isSending => _isSending;
  String? get error => _error;
  bool get hasActiveConversation => _currentConversation != null;
  bool get isGeneratingWorkout => _isGeneratingWorkout;
  Map<String, dynamic>? get lastGeneratedWorkout => _lastGeneratedWorkout;

  Map<String, dynamic>? get detectedPlanInfo => _detectedPlanInfo;
  // ============================================================
  // INICIAR CONVERSA
  // ============================================================

  Future<bool> startConversation({
    ConversationType type = ConversationType.generalFitness,
    String? initialMessage,
    bool forceNew = true,
  }) async {
    try {
      _isLoading = true;
      _error = null;
      notifyListeners();

      debugPrint('🤖 Iniciando conversa: ${type.value}');

      final response = await ApiService.startConversation(
        conversationType: type.value,
        initialMessage: initialMessage,
        forceNew: forceNew,
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
  // ENVIAR MENSAGEM COM DETECÇÃO DE AÇÃO
  // ============================================================

 Future<bool> sendMessage(String text) async {
  if (text.trim().isEmpty) {
    debugPrint('⚠️ Mensagem vazia');
    return false;
  }

  // ============================================================
  // ✅ AUTO-RECOVERY: Criar conversa se não existir
  // ============================================================
  
  if (_currentConversation == null) {
    debugPrint('⚠️ Nenhuma conversa ativa, criando nova...');
    
    final success = await startConversation(
      type: ConversationType.generalFitness,
      forceNew: true,
    );
    
    if (!success) {
      debugPrint('❌ Não foi possível criar conversa');
      _error = 'Erro ao iniciar conversa';
      notifyListeners();
      return false;
    }
    
    debugPrint('✅ Nova conversa criada automaticamente');
  }

  try {
    _isSending = true;
    _error = null;

    // Adicionar mensagem do usuário
    final userMessage = ChatMessage(
      text: text,
      isUser: true,
      timestamp: DateTime.now(),
    );
    _messages.add(userMessage);
    notifyListeners();

    debugPrint('📤 Enviando: "$text"');

    // Enviar para backend
    final response = await ApiService.sendChatMessage(
      conversationId: _currentConversation!.id,
      message: text,
    );

    // 🔍 Verificar se backend retornou plan_info
  if (response.containsKey('plan_info') && response['plan_info'] != null) {
    _detectedPlanInfo = response['plan_info'] as Map<String, dynamic>;
    
    debugPrint('✅ Plan info detectado:');
    debugPrint('   Dias: ${_detectedPlanInfo!['days_per_week']}');
    debugPrint('   Foco: ${_detectedPlanInfo!['focus']}');
    debugPrint('   Dificuldade: ${_detectedPlanInfo!['difficulty']}');
  }
    
    // ============================================================
    // ✅ PROCESSAR RESPOSTA (CAMINHO CORRETO)
    // ============================================================
    
    // Extrair conteúdo da IA
    final aiContent = response['ai_response']?['content'] as String?;
    
    if (aiContent != null && aiContent.isNotEmpty) {
      final aiMessage = ChatMessage(
        text: aiContent,
        isUser: false,
        timestamp: DateTime.now(),
      );
      _messages.add(aiMessage);
      debugPrint('✅ Resposta da IA adicionada: ${aiContent.substring(0, 50)}...');
    } else {
      debugPrint('⚠️ Resposta da IA vazia');
    }

    _isSending = false;
    notifyListeners();
    
    debugPrint('✅ Mensagem processada');
    return true;
    
  } on ApiException catch (e) {
    // ============================================================
    // ✅ RECOVERY: Se conversa não existe (404), criar nova
    // ============================================================
    
    if (e.statusCode == 404) {
      debugPrint('⚠️ Conversa ${_currentConversation!.id} não existe mais');
      
      // Limpar conversa inválida
      _currentConversation = null;
      
      // Remover mensagem otimista
      if (_messages.isNotEmpty && _messages.last.isUser) {
        _messages.removeLast();
      }
      
      debugPrint('🔄 Tentando reenviar em nova conversa...');
      
      // Reenviar mensagem (vai criar nova conversa via check acima)
      _isSending = false;
      notifyListeners();
      
      return await sendMessage(text); // Recursão segura
    }
    
    // Outros erros
    debugPrint('❌ Erro API: ${e.message}');
    _error = 'Erro ao enviar mensagem';
    
    if (_messages.isNotEmpty && _messages.last.isUser) {
      _messages.removeLast();
    }

    _isSending = false;
    notifyListeners();
    return false;
    
  } catch (e, stackTrace) {
    debugPrint('❌ Erro inesperado: $e');
    debugPrint('Stack: $stackTrace');
    
    _error = 'Erro ao enviar mensagem';
    
    if (_messages.isNotEmpty && _messages.last.isUser) {
      _messages.removeLast();
    }

    _isSending = false;
    notifyListeners();
    return false;
  }
}
  // ============================================================
  // 🔥 GERAR TREINO AUTOMÁTICO COM PREFERÊNCIAS
  // ============================================================

  /// Método privado chamado automaticamente quando o backend retorna action: 'generate_workout'
  Future<void> _generateWorkoutWithPreferences(Map<String, dynamic> preferences) async {
    try {
      _isGeneratingWorkout = true;
      notifyListeners();

      debugPrint('🏋️ Gerando treino automático com preferências da conversa...');
      debugPrint('   Dias: ${preferences['days']}');
      debugPrint('   Foco: ${preferences['focus']}');
      debugPrint('   Dificuldade: ${preferences['difficulty']}');

      // Chamar endpoint específico do chatbot
      final response = await ApiService.generateWorkoutFromChat(
        conversationId: _currentConversation!.id,
        daysPerWeek: preferences['days'] ?? 5,
        focus: preferences['focus'] ?? 'full_body',
      );

      debugPrint('📦 Resposta do backend:');
      debugPrint(response.toString());

      // Processar resposta
      if (response.containsKey('workout_created') && response['workout_created'] == true) {
        // ✅ Treino já criado no banco
        final workout = response['workout'];
        _lastGeneratedWorkout = workout;
        
        debugPrint('✅ Treino gerado com sucesso!');
        debugPrint('   ID: ${workout['id']}');
        debugPrint('   Nome: ${workout['name']}');
        debugPrint('   Exercícios: ${workout['exercises']?.length ?? 0}');

        // Adicionar mensagem de sucesso na conversa
        final successMessage = ChatMessage(
          text: '✅ Treino criado com sucesso!\n\n'
                '📋 ${workout['name']}\n'
                '⏱️ Duração: ${workout['estimated_duration']} min\n'
                '💪 ${workout['exercises']?.length ?? 0} exercícios\n\n'
                'Acesse a seção "Recomendações da IA" para ver detalhes!',
          isUser: false,
          timestamp: DateTime.now(),
          intent: 'workout_generated',
          confidence: 1.0,
        );
        _messages.add(successMessage);

      } else if (response.containsKey('ai_generated_workout')) {
        // 📝 Apenas plano gerado, criar treino no banco
        debugPrint('📝 Criando treino no banco...');
        
        final aiWorkout = response['ai_generated_workout'];
        final planInfo = aiWorkout['plan_info'] as Map<String, dynamic>;
        final workoutPlan = aiWorkout['workout_plan'] as List<dynamic>;

        // Criar nome do treino
        final focus = preferences['focus'] ?? 'full_body';
        final duration = planInfo['estimated_duration'] ?? 30;
        final focusLabel = _getFocusLabel(focus);
        final workoutName = 'Treino IA - $focusLabel ($duration min)';

        // 1. Criar treino
        final createResponse = await ApiService.createWorkout(
          name: workoutName,
          description: 'Treino personalizado gerado pela IA',
          difficultyLevel: preferences['difficulty'] ?? 'intermediate',
          estimatedDuration: duration,
          workoutType: focus,
        );

        int? workoutId;
        if (createResponse.containsKey('id')) {
          workoutId = createResponse['id'] as int;
        } else if (createResponse.containsKey('workout')) {
          workoutId = (createResponse['workout'] as Map)['id'] as int;
        }

        if (workoutId == null) {
          throw Exception('ID do treino não retornado');
        }

        debugPrint('✅ Treino criado! ID: $workoutId');

        // 2. Adicionar exercícios
        int successCount = 0;
        for (var exerciseData in workoutPlan) {
          try {
            final exercise = exerciseData['exercise'] as Map<String, dynamic>;
            await ApiService.addExerciseToWorkout(
              workoutId: workoutId,
              exerciseId: exercise['id'] as int,
              sets: exerciseData['sets'] as int,
              reps: exerciseData['reps']?.toString() ?? '8-12',
              restTime: exerciseData['rest_time_seconds'] as int,
              orderInWorkout: exerciseData['order'] as int,
            );
            successCount++;
          } catch (e) {
            debugPrint('⚠️ Erro ao adicionar exercício: $e');
          }
        }

        debugPrint('🎉 $successCount/${workoutPlan.length} exercícios adicionados');

        // Mensagem de sucesso
        final successMessage = ChatMessage(
          text: '✅ Treino "$workoutName" criado!\n\n'
                '💪 $successCount exercícios adicionados\n'
                '⏱️ Duração: $duration min\n\n'
                'Veja na seção "Recomendações da IA"!',
          isUser: false,
          timestamp: DateTime.now(),
          intent: 'workout_generated',
          confidence: 1.0,
        );
        _messages.add(successMessage);

      } else {
        throw Exception('Formato de resposta desconhecido');
      }

    } catch (e, stackTrace) {
      debugPrint('❌ Erro ao gerar treino: $e');
      debugPrint('Stack: $stackTrace');
      
      _error = 'Erro ao gerar treino';
      
      // Adicionar mensagem de erro
      final errorMessage = ChatMessage(
        text: '❌ Desculpe, houve um erro ao gerar seu treino.\n\n'
              'Tente novamente ou entre em contato com o suporte.',
        isUser: false,
        timestamp: DateTime.now(),
        intent: 'error',
      );
      _messages.add(errorMessage);
      
    } finally {
      _isGeneratingWorkout = false;
      notifyListeners();
    }
  }

  /// Helper para traduzir código de foco em label
  String _getFocusLabel(String focus) {
    const labels = {
      'full_body': 'Corpo Completo',
      'upper': 'Parte Superior',
      'lower': 'Parte Inferior',
      'chest': 'Peito',
      'back': 'Costas',
      'legs': 'Pernas',
      'arms': 'Braços',
      'shoulders': 'Ombros',
      'cardio': 'Cardio',
    };
    return labels[focus] ?? focus;
  }

  // ============================================================
// 🔥 GERAR TREINO MANUAL (CHAMADA DIRETA)
// ============================================================


/// Método público para gerar treino manualmente (ex: botão na UI)
Future<bool> generateWorkoutFromConversation() async {
  if (_currentConversation == null) {
    debugPrint('⚠️ Nenhuma conversa ativa');
    _error = 'Inicie uma conversa antes de gerar um treino';
    notifyListeners();
    return false;
  }

  try {
    _isGeneratingWorkout = true;
    notifyListeners();

    debugPrint('🏋️ Gerando treino manual');
    
    // ✅ VERIFICAR SE TEM plan_info DETECTADO
    if (_detectedPlanInfo != null) {
      debugPrint('✅ Usando plan_info detectado do chat:');
      debugPrint('   Dias: ${_detectedPlanInfo!['days_per_week']}');
      debugPrint('   Foco: ${_detectedPlanInfo!['focus']}');
      debugPrint('   Dificuldade: ${_detectedPlanInfo!['difficulty']}');
    } else {
      debugPrint('⚠️ Nenhum plan_info detectado, usando fallback genérico');
    }

    // 🔥 CORREÇÃO: PASSAR planInfo como primeiro argumento
    final response = await ApiService.generateWorkoutFromChat(
      conversationId: _currentConversation!.id,
      planInfo: _detectedPlanInfo,  // ✅ USAR O DETECTADO!
      daysPerWeek: 5,               // Fallback se planInfo for null
      focus: 'full_body',           // Fallback se planInfo for null
    );

    debugPrint('📦 Resposta do backend (manual):');
    debugPrint(response.toString());

    // 🔥 FIX: Tratar AMBOS os casos igual ao método automático
    if (response.containsKey('workout_created') && response['workout_created'] == true) {
      // ✅ CASO 1: Treino já criado no banco
      final workout = response['workout'];
      _lastGeneratedWorkout = workout;
      
      debugPrint('✅ Treino manual gerado (já criado)!');
      debugPrint('   ID: ${workout['id']}');
      
      // Adicionar mensagem de sucesso
      final successMessage = ChatMessage(
        text: '✅ Treino criado com sucesso!\n\n'
              '📋 ${workout['name']}\n'
              '⏱️ Duração: ${workout['estimated_duration']} min\n'
              '💪 ${workout['exercises']?.length ?? 0} exercícios\n\n'
              'Acesse "Meus Treinos" para começar!',
        isUser: false,
        timestamp: DateTime.now(),
        intent: 'workout_generated',
        confidence: 1.0,
      );
      _messages.add(successMessage);
      
      _isGeneratingWorkout = false;
      notifyListeners();
      return true;

    } else if (response.containsKey('ai_generated_workout')) {
      // 📝 CASO 2: Apenas plano gerado, CRIAR treino no banco
      debugPrint('📝 Plano gerado, criando treino no banco...');
      
      final aiWorkout = response['ai_generated_workout'];
      final planInfo = aiWorkout['plan_info'] as Map<String, dynamic>;
      final workoutPlan = aiWorkout['workout_plan'] as List<dynamic>;

      // Extrair info do plano
      final focus = planInfo['focus'] ?? 'full_body';
      final difficulty = planInfo['difficulty'] ?? 'intermediate';
      final duration = planInfo['estimated_duration'] ?? 30;
      final daysPerWeek = planInfo['days_per_week'] ?? 5;
      
      final focusLabel = _getFocusLabel(focus);
      final workoutName = 'Treino IA - $focusLabel';

      debugPrint('   Nome: $workoutName');
      debugPrint('   Exercícios: ${workoutPlan.length}');

      // 1️⃣ Criar treino
      final createResponse = await ApiService.createWorkout(
        name: workoutName,
        description: 'Treino personalizado gerado pela IA com base na conversa.\n'
                    'Foco: $focusLabel | $daysPerWeek dias/semana',
        difficultyLevel: difficulty,
        estimatedDuration: duration,
        workoutType: focus,
      );

      // Obter ID do treino criado
      int? workoutId;
      if (createResponse.containsKey('id')) {
        workoutId = createResponse['id'] as int;
      } else if (createResponse.containsKey('workout')) {
        workoutId = (createResponse['workout'] as Map)['id'] as int;
      }

      if (workoutId == null) {
        throw Exception('ID do treino não retornado pelo backend');
      }

      debugPrint('✅ Treino criado! ID: $workoutId');

      // 2️⃣ Adicionar exercícios ao treino
      int successCount = 0;
      int errorCount = 0;
      
      for (var exerciseData in workoutPlan) {
        try {
          final exercise = exerciseData['exercise'] as Map<String, dynamic>;
          final exerciseId = exercise['id'] as int;
          
          await ApiService.addExerciseToWorkout(
            workoutId: workoutId,
            exerciseId: exerciseId,
            sets: exerciseData['sets'] as int,
            reps: exerciseData['reps']?.toString() ?? '8-12',
            restTime: exerciseData['rest_time_seconds'] as int,
            orderInWorkout: exerciseData['order'] as int,
          );
          
          successCount++;
          debugPrint('   ✓ Exercício ${exercise['name']} adicionado');
          
        } catch (e) {
          errorCount++;
          debugPrint('   ✗ Erro ao adicionar exercício: $e');
        }
      }

      debugPrint('🎉 Treino finalizado:');
      debugPrint('   ✅ $successCount exercícios adicionados');
      debugPrint('   ❌ $errorCount erros');

      // Salvar info do treino
      _lastGeneratedWorkout = {
        'id': workoutId,
        'name': workoutName,
        'exercises': workoutPlan,
        'duration': duration,
        'focus': focus,
      };

      // Mensagem de sucesso na conversa
      final successMessage = ChatMessage(
        text: '✅ Treino "$workoutName" criado!\n\n'
              '💪 $successCount exercícios adicionados\n'
              '⏱️ Duração estimada: $duration min\n'
              '📅 $daysPerWeek dias por semana\n\n'
              '👉 Acesse "Meus Treinos" para começar!',
        isUser: false,
        timestamp: DateTime.now(),
        intent: 'workout_generated',
        confidence: 1.0,
      );
      _messages.add(successMessage);

      _isGeneratingWorkout = false;
      notifyListeners();
      return true;

    } else {
      // ❌ Resposta inesperada
      throw Exception('Formato de resposta desconhecido: ${response.keys}');
    }

  } catch (e, stackTrace) {
    debugPrint('❌ Erro ao gerar treino manual: $e');
    debugPrint('Stack: $stackTrace');
    
    _error = 'Erro ao gerar treino: ${e.toString()}';
    
    // Adicionar mensagem de erro na conversa
    final errorMessage = ChatMessage(
      text: '❌ Desculpe, houve um erro ao gerar seu treino.\n\n'
            'Detalhes: ${e.toString()}\n\n'
            'Por favor, tente novamente.',
      isUser: false,
      timestamp: DateTime.now(),
      intent: 'error',
    );
    _messages.add(errorMessage);
    
    _isGeneratingWorkout = false;
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
      _lastGeneratedWorkout = null;

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
    _isGeneratingWorkout = false;
    _lastGeneratedWorkout = null;
    notifyListeners();
  }
}