import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../service/chat_service.dart';
import '../../../models/chat_models.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  late ChatService _chatService;
  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    _chatService = Provider.of<ChatService>(context, listen: false);
    _initializeChat();
  }

  Future<void> _initializeChat() async {
    await _chatService.startConversation(
      type: ConversationType.generalFitness, // ✅ Corrigido: usando enum
      forceNew: false,
    );
  }

  void _scrollToBottom() {
    Future.delayed(Duration(milliseconds: 100), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          0.0,
          duration: Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _sendMessage() async {
    final text = _messageController.text.trim();
    if (text.isEmpty) return;

    _messageController.clear();
    _scrollToBottom();

    await _chatService.sendMessage(text);
  }

  void _handleOptionSelected(String optionId, ChatMessage message) {
    debugPrint('✅ Opção selecionada: $optionId');
    // Aqui você pode adicionar analytics ou logging
  }

  // ✅ Corrigido: convertendo String para enum MessageReaction
  Future<void> _sendFeedback(
    int messageId,
    String reaction,
    String? feedback,
  ) async {
    // Converter string para enum
    MessageReaction? messageReaction;
    if (reaction == 'helpful') {
      messageReaction = MessageReaction.helpful;
    } else if (reaction == 'not_helpful') {
      messageReaction = MessageReaction.notHelpful;
    }

    if (messageReaction != null) {
      await _chatService.sendMessageFeedback(
        messageId: messageId,
        reaction: messageReaction,
        feedback: feedback,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Chat Fitness'),
        centerTitle: true,
        elevation: 0,
        backgroundColor: Colors.blue.shade600,
      ),
      body: Consumer<ChatService>(
        builder: (context, chatService, _) {
          return Column(
            children: [
              // Lista de mensagens
              Expanded(
                child: chatService.messages.isEmpty
                    ? _buildEmptyState()
                    : ListView.builder(
                        controller: _scrollController,
                        reverse: true,
                        itemCount: chatService.messages.length,
                        itemBuilder: (context, index) {
                          final message = chatService.messages[
                              chatService.messages.length - 1 - index
                          ];

                          return ChatMessageWidget(
                            message: message,
                            onOptionSelected: (optionId) {
                              _handleOptionSelected(optionId, message);
                            },
                            onFeedback: (messageId, reaction, feedback) {
                              _sendFeedback(messageId, reaction, feedback);
                            },
                          );
                        },
                      ),
              ),

              // Indicador de digitação
              if (chatService.isSending)
                Padding(
                  padding: EdgeInsets.all(8.0),
                  child: Row(
                    children: [
                      SizedBox(width: 12),
                      SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          valueColor:
                              AlwaysStoppedAnimation<Color>(Colors.blue),
                        ),
                      ),
                      SizedBox(width: 8),
                      Text(
                        'Digitando...',
                        style: TextStyle(color: Colors.grey),
                      ),
                    ],
                  ),
                ),

              // Campo de entrada
              _buildInputField(chatService),
            ],
          );
        },
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.fitness_center, size: 64, color: Colors.grey[300]),
          SizedBox(height: 16),
          Text(
            'Bem-vindo ao Chat Fitness!',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          SizedBox(height: 8),
          Text(
            'Digite uma mensagem para começar',
            style: TextStyle(color: Colors.grey),
          ),
        ],
      ),
    );
  }

  Widget _buildInputField(ChatService chatService) {
    return Container(
      padding: EdgeInsets.all(12.0),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border(top: BorderSide(color: Colors.grey[300]!)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: Offset(0, -5),
          ),
        ],
      ),
      child: SafeArea(
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: _messageController,
                decoration: InputDecoration(
                  hintText: 'Digite sua mensagem...',
                  hintStyle: TextStyle(color: Colors.grey[400]),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(24.0),
                    borderSide: BorderSide(color: Colors.grey[300]!),
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(24.0),
                    borderSide: BorderSide(color: Colors.grey[300]!),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(24.0),
                    borderSide: BorderSide(color: Colors.blue, width: 2),
                  ),
                  contentPadding: EdgeInsets.symmetric(
                    horizontal: 16.0,
                    vertical: 10.0,
                  ),
                ),
                onSubmitted: (_) => _sendMessage(),
                enabled: !chatService.isSending,
              ),
            ),
            SizedBox(width: 8.0),
            FloatingActionButton(
              mini: true,
              onPressed: chatService.isSending ? null : _sendMessage,
              backgroundColor:
                  chatService.isSending ? Colors.grey : Colors.blue,
              child: chatService.isSending
                  ? SizedBox(
                      width: 24,
                      height: 24,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                      ),
                    )
                  : Icon(Icons.send),
            ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    super.dispose();
  }
}

// ============================================================
// ChatMessageWidget - Widget que renderiza cada mensagem
// ============================================================

class ChatMessageWidget extends StatefulWidget {
  final ChatMessage message;
  final Function(String)? onOptionSelected;
  final Function(int, String, String?)? onFeedback;

  const ChatMessageWidget({
    super.key,
    required this.message,
    this.onOptionSelected,
    this.onFeedback,
  });

  @override
  State<ChatMessageWidget> createState() => _ChatMessageWidgetState();
}

class _ChatMessageWidgetState extends State<ChatMessageWidget> {
  bool _showFeedback = false;

  @override
  Widget build(BuildContext context) {
    final message = widget.message;

    return Column(
      crossAxisAlignment: message.isUser
          ? CrossAxisAlignment.end
          : CrossAxisAlignment.start,
      children: [
        // ============================================================
        // MENSAGEM PRINCIPAL
        // ============================================================
        Container(
          margin: EdgeInsets.symmetric(vertical: 8.0, horizontal: 12.0),
          padding: EdgeInsets.all(12.0),
          decoration: BoxDecoration(
            color: message.isUser ? Colors.blue : Colors.grey[200],
            borderRadius: BorderRadius.only(
              topLeft: Radius.circular(12),
              topRight: Radius.circular(12),
              bottomLeft: Radius.circular(message.isUser ? 12 : 0),
              bottomRight: Radius.circular(message.isUser ? 0 : 12),
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Texto da mensagem
              SelectableText(
                message.text,
                style: TextStyle(
                  color: message.isUser ? Colors.white : Colors.black87,
                  fontSize: 14.0,
                  height: 1.4,
                ),
              ),

              // ============================================================
              // 🔥 BOTÕES DE OPÇÃO (se existirem)
              // ============================================================
              // ✅ Agora usando a propriedade options diretamente
              if (message.hasOptions)
                Padding(
                  padding: EdgeInsets.only(top: 12.0),
                  child: _buildOptions(message.options!),
                ),
            ],
          ),
        ),

        // ============================================================
        // FEEDBACK (👍 👎) - APENAS PARA MENSAGENS DA IA
        // ============================================================
        if (!message.isUser)
          MouseRegion(
            onEnter: (_) => setState(() => _showFeedback = true),
            onExit: (_) => setState(() => _showFeedback = false),
            child: Padding(
              padding: EdgeInsets.symmetric(horizontal: 12.0, vertical: 4.0),
              child: AnimatedOpacity(
                opacity: _showFeedback ? 1.0 : 0.5,
                duration: Duration(milliseconds: 200),
                child: Row(
                  children: [
                    IconButton(
                      icon: Icon(Icons.thumb_up),
                      iconSize: 18.0,
                      tooltip: 'Útil',
                      onPressed: () {
                        widget.onFeedback?.call(
                          message.id ?? 0,
                          'helpful',
                          null,
                        );
                        setState(() => _showFeedback = false);
                      },
                    ),
                    IconButton(
                      icon: Icon(Icons.thumb_down),
                      iconSize: 18.0,
                      tooltip: 'Não útil',
                      onPressed: () {
                        widget.onFeedback?.call(
                          message.id ?? 0,
                          'not_helpful',
                          null,
                        );
                        setState(() => _showFeedback = false);
                      },
                    ),
                  ],
                ),
              ),
            ),
          ),
      ],
    );
  }

  // ✅ Método auxiliar para verificar se há opções
  bool _hasOptions(ChatMessage message) {
    try {
      // Tenta acessar a propriedade options se existir
      final options = (message as dynamic).options;
      return options != null && options is List && options.isNotEmpty;
    } catch (e) {
      return false;
    }
  }

  // ✅ Método auxiliar para obter as opções
  List<Map<String, dynamic>> _getOptions(ChatMessage message) {
    try {
      final options = (message as dynamic).options;
      if (options != null && options is List) {
        return List<Map<String, dynamic>>.from(options);
      }
    } catch (e) {
      debugPrint('Erro ao obter opções: $e');
    }
    return [];
  }

  /// Renderiza os botões de opção
  Widget _buildOptions(List<Map<String, dynamic>> options) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: List.generate(
        options.length,
        (index) {
          final option = options[index];
          final label = option['label'] as String? ?? 'Opção';
          final emoji = option['emoji'] as String? ?? '';
          final id = option['id'] as String? ?? '';
          final action = option['action'] as String? ?? 'chat';
          final data = option['data'] as Map<String, dynamic>? ?? {};

          return Padding(
            padding: EdgeInsets.only(
              bottom: index < options.length - 1 ? 8.0 : 0,
            ),
            child: SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blue.shade600,
                  foregroundColor: Colors.white,
                  padding: EdgeInsets.symmetric(vertical: 10.0),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8.0),
                  ),
                  elevation: 2,
                ),
                onPressed: () => _handleOptionPressed(
                  option: option,
                  id: id,
                  action: action,
                  data: data,
                ),
                child: Text(
                  '$emoji $label',
                  style: TextStyle(fontSize: 13.0),
                  textAlign: TextAlign.center,
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  /// Trata o clique em uma opção
  Future<void> _handleOptionPressed({
    required Map<String, dynamic> option,
    required String id,
    required String action,
    required Map<String, dynamic> data,
  }) async {
    debugPrint('📌 Opção clicada: $id | Ação: $action');

    // Notificar o callback
    widget.onOptionSelected?.call(id);

    // Executar ação baseada no tipo
    switch (action) {
      case 'navigate':
        _navigateToScreen(data);
        break;

      case 'start_workout':
        await _startWorkout(data);
        break;

      case 'chat':
        // Continuar conversa
        debugPrint('💬 Continuando conversa');
        break;

      default:
        debugPrint('⚠️ Ação desconhecida: $action');
    }
  }

  /// Navega para outra tela
  void _navigateToScreen(Map<String, dynamic> data) {
    final screen = data['screen'] as String?;

    debugPrint('🔄 Navegando para: $screen');

    switch (screen) {
      case 'my_workouts':
        Navigator.pushNamed(
          context,
          '/workouts',
          arguments: data,
        );
        break;

      case 'workout_detail':
        final workoutId = data['workout_id'] as int?;
        Navigator.pushNamed(
          context,
          '/workout_detail',
          arguments: {'workout_id': workoutId},
        );
        break;

      default:
        debugPrint('⚠️ Tela desconhecida: $screen');
    }
  }

  /// Inicia uma sessão de treino
  Future<void> _startWorkout(Map<String, dynamic> data) async {
    final workoutId = data['workout_id'] as int?;

    if (workoutId == null) {
      debugPrint('⚠️ Workout ID não fornecido');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Erro: ID do treino não encontrado'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    debugPrint('▶️ Iniciando treino: $workoutId');

    try {
      // Mostrar loading
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Row(
            children: [
              SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                ),
              ),
              SizedBox(width: 12),
              Text('Iniciando treino...'),
            ],
          ),
          duration: Duration(seconds: 3),
        ),
      );

      // Navegar para a tela de treino
      Navigator.pushNamed(
        context,
        '/workout_session',
        arguments: {
          'workout_id': workoutId,
          'start_immediately': true,
        },
      );
    } catch (e) {
      debugPrint('❌ Erro ao iniciar treino: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Erro ao iniciar treino'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }
}