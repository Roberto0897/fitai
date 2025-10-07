import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/theme/app_theme.dart';
import '../../../service/chat_service.dart';
import '../../../models/chat_models.dart';
import '../../../core/router/app_router.dart';
import 'package:flutter_markdown/flutter_markdown.dart';

class ChatBotPage extends StatefulWidget {
  final String? initialContext;
  final int? workoutId;
  final String? initialMessage;
  
  const ChatBotPage({
    super.key,
    this.initialContext,
    this.workoutId,
    this.initialMessage,
  });

  @override
  State<ChatBotPage> createState() => _ChatBotPageState();
}

class _ChatBotPageState extends State<ChatBotPage> {
  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  bool _isInitialized = false;

@override
void initState() {
  super.initState();
  WidgetsBinding.instance.addPostFrameCallback((_) {
    _initializeChat();
  });
}

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

 Future<void> _initializeChat() async {
  final chatService = context.read<ChatService>();
  
  // Se não há conversa ativa, iniciar uma com contexto
  if (!chatService.hasActiveConversation) {
    ConversationType conversationType;
    String? firstMessage;
    
    if (widget.initialContext == 'workout_generation') {
      // 🔥 USA workout_consultation (tipo existente no backend)
      conversationType = ConversationType.workoutConsultation;
      firstMessage = widget.initialMessage ?? 
          '🏋️ Olá! Gostaria de criar um treino personalizado para mim baseado no meu perfil e objetivos.';
      
      debugPrint('🤖 CHATBOT: Iniciando geração de treino (como workout_consultation)');
      
    } else if (widget.initialContext == 'workout_modification' && widget.workoutId != null) {
      // 🔥 USA workout_consultation (tipo existente no backend)
      conversationType = ConversationType.workoutConsultation;
      firstMessage = widget.initialMessage ?? 
          '✏️ Quero modificar meu treino atual (ID: ${widget.workoutId}). Pode me ajudar a ajustá-lo?';
      
      debugPrint('🤖 CHATBOT: Iniciando modificação do treino ${widget.workoutId} (como workout_consultation)');
      
    } else if (widget.initialMessage != null) {
      conversationType = ConversationType.generalFitness;
      firstMessage = widget.initialMessage;
      
      debugPrint('🤖 CHATBOT: Conversa geral com mensagem inicial');
      
    } else {
      conversationType = ConversationType.generalFitness;
      firstMessage = null;
      
      debugPrint('🤖 CHATBOT: Conversa geral sem contexto');
    }
    
    // Iniciar conversa
    await chatService.startConversation(
      type: conversationType,
      initialMessage: firstMessage,
      forceNew: true,     
    );
  }

  setState(() => _isInitialized = true);
}

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
          
        );
      }
    });
  }

  Future<void> _sendMessage() async {
    final text = _messageController.text.trim();
    if (text.isEmpty) return;

    final chatService = context.read<ChatService>();
    
    _messageController.clear();
    
    final success = await chatService.sendMessage(text);
    
    if (success) {
      _scrollToBottom();
    } else {
      // Mostrar erro se falhar
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(chatService.error ?? 'Erro ao enviar mensagem'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF2C2C2C),
      appBar: AppBar(
        backgroundColor: AppColors.primary,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        title: Row(
          children: [
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.2),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.smart_toy_outlined,
                color: Colors.white,
                size: 24,
              ),
            ),
            const SizedBox(width: 12),
            const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'FITAI Assistant',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text(
                  'Online',
                  style: TextStyle(
                    color: Colors.white70,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ],
        ),
        actions: [
          // Botão de nova conversa
          IconButton(
            icon: const Icon(Icons.refresh, color: Colors.white),
            onPressed: () async {
              final chatService = context.read<ChatService>();
              chatService.reset();
              await _initializeChat();
            },
            tooltip: 'Nova conversa',
          ),
        ],
      ),
      body: !_isInitialized
          ? const Center(child: CircularProgressIndicator())
          : Consumer<ChatService>(
              builder: (context, chatService, child) {
                return Column(
                  children: [
                    // Lista de mensagens
                    Expanded(
                      child: chatService.messages.isEmpty
                          ? _buildEmptyState()
                          : ListView.builder(
                              controller: _scrollController,
                              padding: const EdgeInsets.all(16),
                              itemCount: chatService.messages.length,
                              itemBuilder: (context, index) {
                                return _buildMessageBubble(
                                  chatService.messages[index],
                                );
                              },
                            ),
                    ),

                    // Indicador de digitação
                    if (chatService.isSending) _buildTypingIndicator(),

                    // Sugestões rápidas
                    if (chatService.messages.length <= 1)
                      _buildQuickSuggestions(),

                    _buildCreateWorkoutButton(chatService),

                    // Input de mensagem
                    _buildMessageInput(chatService.isSending),
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
          Icon(
            Icons.chat_bubble_outline,
            size: 80,
            color: AppColors.textSecondary.withOpacity(0.3),
          ),
          const SizedBox(height: 16),
          const Text(
            'Comece uma conversa',
            style: TextStyle(
              fontSize: 18,
              color: Colors.white70,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Pergunte sobre treinos, exercícios ou dicas',
            style: TextStyle(
              fontSize: 14,
              color: Colors.white.withOpacity(0.5),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMessageBubble(ChatMessage message) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        mainAxisAlignment:
            message.isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!message.isUser) ...[
            Container(
              width: 32,
              height: 32,
              decoration: const BoxDecoration(
                color: AppColors.primary,
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.smart_toy,
                color: Colors.white,
                size: 18,
              ),
            ),
            const SizedBox(width: 8),
          ],
          Flexible(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: message.isUser
                    ? AppColors.primary
                    : const Color(0xFF1A1A1A),
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(16),
                  topRight: const Radius.circular(16),
                  bottomLeft: Radius.circular(message.isUser ? 16 : 4),
                  bottomRight: Radius.circular(message.isUser ? 4 : 16),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Se for mensagem da IA, usar Markdown
                  if (!message.isUser)
                    MarkdownBody(
                      data: message.text,
                      styleSheet: MarkdownStyleSheet(
                        p: TextStyle(
                          color: AppColors.textPrimary,
                          fontSize: 15,
                          height: 1.4,
                        ),
                        strong: TextStyle(
                          color: AppColors.textPrimary,
                          fontSize: 15,
                          fontWeight: FontWeight.bold,
                        ),
                        em: TextStyle(
                          color: AppColors.textPrimary,
                          fontSize: 15,
                          fontStyle: FontStyle.italic,
                        ),
                        code: TextStyle(
                          backgroundColor: Colors.black26,
                          color: AppColors.textPrimary,
                          fontSize: 14,
                          fontFamily: 'monospace',
                        ),
                        blockquote: TextStyle(
                          color: AppColors.textPrimary.withOpacity(0.8),
                          fontSize: 14,
                          fontStyle: FontStyle.italic,
                        ),
                      ),
                    )
                  else
                    // Mensagem do usuário sem markdown
                    Text(
                      message.text,
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 15,
                        height: 1.4,
                      ),
                    ),
                  // Confidence indicator para mensagens da IA
                  if (!message.isUser && message.confidence != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 8),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            (message.confidence != null && message.confidence! >= 0.8)
                                ? Icons.verified
                                : Icons.info_outline,
                            size: 12,
                            color: Colors.white54,
                          ),
                          const SizedBox(width: 4),
                          Text(
                            '${(message.confidence! * 100).toInt()}% confiança',
                            style: const TextStyle(
                              fontSize: 10,
                              color: Colors.white54,
                            ),
                          ),
                        ],
                      ),
                    ),
                ],
              ),
            ),
          ),
          if (message.isUser) ...[
            const SizedBox(width: 8),
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: AppColors.primary.withOpacity(0.2),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.person,
                color: AppColors.primary,
                size: 18,
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildTypingIndicator() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        children: [
          Container(
            width: 32,
            height: 32,
            decoration: const BoxDecoration(
              color: AppColors.primary,
              shape: BoxShape.circle,
            ),
            child: const Icon(
              Icons.smart_toy,
              color: Colors.white,
              size: 18,
            ),
          ),
          const SizedBox(width: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: const Color(0xFF1A1A1A),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Row(
              children: List.generate(
                3,
                (index) => Padding(
                  padding: EdgeInsets.only(left: index > 0 ? 4 : 0),
                  child: _buildDot(index),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDot(int index) {
    return TweenAnimationBuilder<double>(
      key: ValueKey(index),
      tween: Tween(begin: 0.3, end: 1.0),
      duration: const Duration(milliseconds: 600),
      curve: Curves.easeInOut,
      builder: (context, value, child) {
        return AnimatedOpacity(
          opacity: (value + index * 0.2) % 1.0,
          duration: const Duration(milliseconds: 300),
          child: Container(
            width: 8,
            height: 8,
            decoration: const BoxDecoration(
              color: Colors.white70,
              shape: BoxShape.circle,
            ),
          ),
        );
      },
    );
  }

  Widget _buildQuickSuggestions() {
    final suggestions = [
      {'icon': Icons.fitness_center, 'text': 'Sugerir treino'},
      {'icon': Icons.help_outline, 'text': 'Como fazer exercícios?'},
      {'icon': Icons.tips_and_updates, 'text': 'Dicas de fitness'},
    ];

    return SizedBox(
      height: 60,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        itemCount: suggestions.length,
        itemBuilder: (context, index) {
          final suggestion = suggestions[index];
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: ActionChip(
              avatar: Icon(
                suggestion['icon'] as IconData,
                size: 18,
                color: AppColors.primary,
              ),
              label: Text(
                suggestion['text'] as String,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 13,
                ),
              ),
              backgroundColor: const Color(0xFF1A1A1A),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(20),
                side: BorderSide(
                  color: AppColors.primary.withOpacity(0.3),
                ),
              ),
              onPressed: () {
                _messageController.text = suggestion['text'] as String;
                _sendMessage();
              },
            ),
          );
        },
      ),
    );
  }

  // Novo método para mostrar botão de criar treino
Widget _buildCreateWorkoutButton(ChatService chatService) {
  // Só mostrar se:
  // 1. Conversa for de workout_consultation
  // 2. Houver mensagens suficientes (> 4)
  // 3. Não estiver já gerando
  
  final shouldShow = chatService.currentConversation?.type == 'workout_consultation' &&
                     chatService.messages.length >= 4 &&
                     !chatService.isGeneratingWorkout;
  
  if (!shouldShow) return const SizedBox.shrink();
  
  return Container(
    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
    decoration: BoxDecoration(
      color: const Color(0xFF2A2A2A),
      border: Border(
        top: BorderSide(
          color: const Color(0xFF424242),
          width: 1,
        ),
      ),
    ),
    child: SafeArea(
      top: false,
      child: ElevatedButton.icon(
        onPressed: () async {
          // Confirmar antes de gerar
          final confirm = await showDialog<bool>(
            context: context,
            builder: (context) => AlertDialog(
              backgroundColor: const Color(0xFF2A2A2A),
              title: const Text(
                'Criar Treino',
                style: TextStyle(color: Colors.white),
              ),
              content: const Text(
                'Deseja criar um treino personalizado com base nessa conversa?',
                style: TextStyle(color: Colors.white70),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(context, false),
                  child: const Text('Cancelar'),
                ),
                ElevatedButton(
                  onPressed: () => Navigator.pop(context, true),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF00BCD4),
                  ),
                  child: const Text('Criar'),
                ),
              ],
            ),
          );
          
          if (confirm == true) {
            final success = await chatService.generateWorkoutFromConversation();
            
            if (success && mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: const Text('✅ Treino criado com sucesso!'),
                  backgroundColor: Colors.green,
                  action: SnackBarAction(
                    label: 'Ver Treinos',
                    textColor: Colors.white,
                    onPressed: () {
                      AppRouter.goToWorkouts();
                    },
                  ),
                ),
              );
            }
          }
        },
        icon: chatService.isGeneratingWorkout
            ? const SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                ),
              )
            : const Icon(Icons.fitness_center),
        label: Text(
          chatService.isGeneratingWorkout 
              ? 'Criando treino...' 
              : '✨ Criar Treino Personalizado',
        ),
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFF00BCD4),
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(vertical: 14),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
      ),
    ),
  );
}
  Widget _buildMessageInput(bool isDisabled) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF303030),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.2),
            blurRadius: 8,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: SafeArea(
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: _messageController,
                enabled: !isDisabled,
                style: const TextStyle(color: Colors.white),
                decoration: InputDecoration(
                  hintText: isDisabled
                      ? 'Aguarde a resposta...'
                      : 'Digite sua mensagem...',
                  hintStyle: TextStyle(
                    color: Colors.white.withOpacity(0.5),
                  ),
                  filled: true,
                  fillColor: const Color(0xFF1A1A1A),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(24),
                    borderSide: BorderSide.none,
                  ),
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: 20,
                    vertical: 12,
                  ),
                ),
                maxLines: null,
                textInputAction: TextInputAction.send,
                onSubmitted: (_) => isDisabled ? null : _sendMessage(),
              ),
            ),
            const SizedBox(width: 8),
            Container(
              decoration: BoxDecoration(
                color: isDisabled
                    ? Colors.grey
                    : AppColors.primary,
                shape: BoxShape.circle,
              ),
              child: IconButton(
                icon: const Icon(Icons.send, color: Colors.white),
                onPressed: isDisabled ? null : _sendMessage,
              ),
            ),
          ],
        ),
      ),
    );
  }
}