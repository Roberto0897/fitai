import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/router/app_router.dart';
import '../workouts/workouts_page.dart';
import '../../../service/api_service.dart';

class WorkoutDetailPage extends StatefulWidget {
  final WorkoutModel workout;

  const WorkoutDetailPage({
    super.key,
    required this.workout,
  });

  @override
  State<WorkoutDetailPage> createState() => _WorkoutDetailPageState();
}

class _WorkoutDetailPageState extends State<WorkoutDetailPage> {
  bool _isFavorite = false;
  bool _isLoadingExercises = true;
  List<ExerciseModel> _workoutExercises = [];
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _loadWorkoutExercises();
  }

  // ✅ Carrega os exercícios do treino específico
  Future<void> _loadWorkoutExercises() async {
    setState(() {
      _isLoadingExercises = true;
      _errorMessage = null;
    });

    try {
      print('🔍 Carregando detalhes do treino ID: ${widget.workout.id}');
      
      final response = await ApiService.getWorkoutDetail(widget.workout.id);
      
      print('Resposta da API: $response');
      
      final exercisesList = response['exercises'] as List? ?? [];
      
      print('Total de exercícios: ${exercisesList.length}');
      
      setState(() {
        _workoutExercises = exercisesList.map((exerciseData) {
          final exercise = exerciseData is Map && exerciseData.containsKey('exercise') 
              ? exerciseData['exercise'] 
              : exerciseData;
          
          return ExerciseModel(
            id: exercise['id'] ?? 0,
            name: exercise['name'] ?? 'Sem nome',
            description: exercise['description'] ?? '',
            muscleGroup: _mapMuscleGroup(exercise['muscle_group']),
            difficulty: _mapDifficulty(exercise['difficulty_level']),
            equipment: exercise['equipment_needed'] ?? 'Não especificado',
            series: exerciseData['sets'] != null          
                ? '${exerciseData['sets']} séries x ${exerciseData['reps'] ?? "?"} reps' 
                : '3 séries',
            reps: exerciseData['reps']?.toString(),        
            restTime: exerciseData['rest_time']?.toString(), 
            videoUrl: exercise['video_url'],
            imageUrl: exercise['image_url'],
          );
        }).toList();
        _isLoadingExercises = false;
      });
      
      print('✅ ${_workoutExercises.length} exercícios carregados');
      
    } catch (e, stackTrace) {
      print('❌ Erro ao carregar exercícios: $e');
      print('Stack trace: $stackTrace');
      
      setState(() {
        _errorMessage = 'Erro ao carregar exercícios: ${e.toString()}';
        _isLoadingExercises = false;
      });
    }
  }

  String _mapDifficulty(String? difficulty) {
    switch (difficulty?.toLowerCase()) {
      case 'beginner':
        return 'Iniciante';
      case 'intermediate':
        return 'Intermediário';
      case 'advanced':
        return 'Avançado';
      default:
        return 'Iniciante';
    }
  }

  String _mapMuscleGroup(String? group) {
    switch (group?.toLowerCase()) {
      case 'chest':
        return 'Peito';
      case 'back':
        return 'Costas';
      case 'legs':
        return 'Pernas';
      case 'shoulders':
        return 'Ombros';
      case 'arms':
        return 'Braços';
      case 'abs':
      case 'core':
        return 'Core';
      case 'cardio':
        return 'Cardio';
      default:
        return 'Geral';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            _buildHeader(),
            Expanded(
              child: _buildExerciseList(),
            ),
          ],
        ),
      ),
      bottomNavigationBar: _buildBottomBar(),
    );
  }

  Widget _buildHeader() {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            AppColors.primary,
            AppColors.primary.withOpacity(0.7),
          ],
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                GestureDetector(
                  onTap: () => AppRouter.goBack(),
                  child: Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(
                      Icons.arrow_back,
                      color: Colors.white,
                    ),
                  ),
                ),
                Row(
                  children: [
                    GestureDetector(
                      onTap: () {
                        setState(() => _isFavorite = !_isFavorite);
                      },
                      child: Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.2),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Icon(
                          _isFavorite ? Icons.favorite : Icons.favorite_border,
                          color: Colors.white,
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    GestureDetector(
                      onTap: _loadWorkoutExercises,
                      child: Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.2),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const Icon(
                          Icons.refresh,
                          color: Colors.white,
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
            
            const SizedBox(height: 24),
            
            Text(
              widget.workout.name,
              style: const TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            
            const SizedBox(height: 8),
            
            Text(
              widget.workout.description,
              style: TextStyle(
                fontSize: 14,
                color: Colors.white.withOpacity(0.9),
              ),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            
            const SizedBox(height: 12),
            
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    widget.workout.category,
                    style: const TextStyle(
                      fontSize: 12,
                      color: Colors.white,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    widget.workout.difficulty,
                    style: const TextStyle(
                      fontSize: 12,
                      color: Colors.white,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildExerciseList() {
    if (_isLoadingExercises) {
      return const Center(
        child: CircularProgressIndicator(
          color: AppColors.primary,
        ),
      );
    }

    if (_errorMessage != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(
                Icons.error_outline,
                size: 64,
                color: AppColors.error,
              ),
              const SizedBox(height: 16),
              Text(
                _errorMessage!,
                style: const TextStyle(color: AppColors.textPrimary),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: _loadWorkoutExercises,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                ),
                child: const Text('Tentar Novamente'),
              ),
            ],
          ),
        ),
      );
    }

    if (_workoutExercises.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.fitness_center,
              size: 64,
              color: AppColors.textHint,
            ),
            const SizedBox(height: 16),
            const Text(
              'Nenhum exercício neste treino',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w600,
                color: AppColors.textPrimary,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Adicione exercícios no Django admin',
              textAlign: TextAlign.center,
              style: TextStyle(color: AppColors.textSecondary),
            ),
          ],
        ),
      );
    }
    
    return Container(
      color: AppColors.background,
      child: RefreshIndicator(
        onRefresh: _loadWorkoutExercises,
        color: AppColors.primary,
        child: ListView.builder(
          padding: const EdgeInsets.all(20),
          itemCount: _workoutExercises.length,
          itemBuilder: (context, index) {
            return Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: _ExerciseCard(
                exercise: _workoutExercises[index],
                exerciseNumber: index + 1,
                totalExercises: _workoutExercises.length,
                onTap: () => _openExercisePreview(_workoutExercises[index], index),
              ),
            );
          },
        ),
      ),
    );
  }

  Widget _buildBottomBar() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.surface,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, -5),
          ),
        ],
      ),
      child: SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                _StatItem(
                  icon: Icons.schedule,
                  value: '${widget.workout.duration}',
                  label: 'min',
                ),
                _StatItem(
                  icon: Icons.fitness_center,
                  value: '${_workoutExercises.length}',
                  label: 'exercícios',
                ),
                _StatItem(
                  icon: Icons.local_fire_department,
                  value: '${widget.workout.calories}',
                  label: 'cal',
                ),
              ],
            ),
            
            const SizedBox(height: 16),
            
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _workoutExercises.isEmpty ? null : _startFullWorkout,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  disabledBackgroundColor: AppColors.primary.withOpacity(0.3),
                ),
                child: const Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.play_arrow),
                    SizedBox(width: 8),
                    Text(
                      'Iniciar Treino',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ✅ MÉTODO CORRIGIDO: Iniciar treino completo
Future<void> _startFullWorkout() async {
  if (_workoutExercises.isEmpty) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Adicione exercícios antes de iniciar o treino'),
        backgroundColor: AppColors.error,
      ),
    );
    return;
  }

  try {
    // Mostrar loading
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => const Center(
        child: CircularProgressIndicator(color: AppColors.primary),
      ),
    );

    print('🏁 Iniciando sessão de treino...');
    print('   Workout ID: ${widget.workout.id}');
    
    // ✅ Tentar iniciar sessão (agora com verificação interna)
    final sessionResponse = await ApiService.startWorkoutSession(
      widget.workout.id,
    );
    
    final sessionId = sessionResponse['session_id'];
    print('✅ Sessão criada com sucesso! ID: $sessionId');

    // Fechar loading
    if (mounted) Navigator.pop(context);

    // Navegar para primeiro exercício
    if (mounted) {
      AppRouter.goToExerciseExecution(
        exercise: _workoutExercises[0],
        totalExercises: _workoutExercises.length,
        currentExerciseIndex: 1,
        allExercises: _workoutExercises,
        initialWorkoutSeconds: 0,
        isFullWorkout: true,
        sessionId: sessionId,
        workoutId: widget.workout.id,
      );
    }

  } on ActiveSessionException catch (e) {
    // ✅ Tratamento específico para sessão ativa
    if (mounted) Navigator.pop(context); // Fechar loading
    
    print('⚠️ Sessão ativa detectada:');
    print('   Session ID: ${e.sessionId}');
    print('   Workout: ${e.workoutName}');
    
    if (mounted) {
      _showActiveSessionDialog(
        sessionId: e.sessionId,
        workoutName: e.workoutName,
        startedAt: e.startedAt,
        workoutId: e.workoutId,
      );
    }
    
  } catch (e) {
    // Fechar loading
    if (mounted) Navigator.pop(context);
    
    print('❌ Erro ao iniciar sessão: $e');
    
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Erro ao iniciar treino: ${e.toString()}'),
          backgroundColor: AppColors.error,
          duration: const Duration(seconds: 4),
        ),
      );
    }
  }
}

// ✅ MÉTODO NOVO: Mostrar dialog de sessão ativa
void _showActiveSessionDialog({
  required int sessionId,
  required String workoutName,
  String? startedAt,
  int? workoutId,
}) {
  showDialog(
    context: context,
    barrierDismissible: false,
    builder: (context) => AlertDialog(
      backgroundColor: AppColors.surface,
      title: const Row(
        children: [
          Icon(Icons.warning_amber, color: Colors.orange, size: 28),
          SizedBox(width: 12),
          Expanded(
            child: Text(
              'Treino em Andamento',
              style: TextStyle(color: Colors.white, fontSize: 18),
            ),
          ),
        ],
      ),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Você tem um treino ativo:',
            style: TextStyle(
              color: AppColors.textSecondary,
              fontSize: 14,
            ),
          ),
          const SizedBox(height: 16),
          
          // Card com info da sessão
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.primary.withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: AppColors.primary.withOpacity(0.3),
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(
                      Icons.fitness_center,
                      color: AppColors.primary,
                      size: 20,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        workoutName,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  'ID da Sessão: $sessionId',
                  style: const TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 12,
                  ),
                ),
                if (startedAt != null) ...[
                  const SizedBox(height: 4),
                  Text(
                    'Iniciado: ${_formatDateTime(startedAt)}',
                    style: const TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 12,
                    ),
                  ),
                ],
              ],
            ),
          ),
          
          const SizedBox(height: 16),
          
          const Text(
            'O que deseja fazer?',
            style: TextStyle(
              color: Colors.white,
              fontSize: 14,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
      actions: [
        // Botão: Voltar
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text(
            'Voltar',
            style: TextStyle(color: AppColors.textSecondary),
          ),
        ),
        
        // Botão: Cancelar e Iniciar Novo
        TextButton(
          onPressed: () async {
            Navigator.pop(context); // Fecha dialog
            await _cancelAndStartNew(sessionId);
          },
          child: const Text(
            'Cancelar e Iniciar Novo',
            style: TextStyle(color: AppColors.error),
          ),
        ),
        
        // Botão: Continuar Sessão (se for o mesmo workout)
        if (workoutId != null && workoutId == widget.workout.id)
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              
              // Navegar para primeiro exercício com sessão existente
              if (_workoutExercises.isNotEmpty) {
                AppRouter.goToExerciseExecution(
                  exercise: _workoutExercises[0],
                  totalExercises: _workoutExercises.length,
                  currentExerciseIndex: 1,
                  allExercises: _workoutExercises,
                  initialWorkoutSeconds: 0,
                  isFullWorkout: true,
                  sessionId: sessionId,
                  workoutId: widget.workout.id,
                );
              }
            },
            child: const Text(
              'Continuar',
              style: TextStyle(
                color: AppColors.primary,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
      ],
    ),
  );
}
  // ✅ MÉTODO NOVO: Lidar com erro de sessão ativa
  Future<void> _handleActiveSessionError() async {
    try {
      print('🔍 Buscando informações da sessão ativa...');
      
      final activeSession = await ApiService.getActiveSession();
      
      if (activeSession == null) {
        print('⚠️ Nenhuma sessão ativa encontrada (inconsistência)');
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Erro: Sessão ativa não encontrada'),
              backgroundColor: AppColors.error,
            ),
          );
        }
        return;
      }

      final sessionId = activeSession['active_session_id'];
      final workoutName = activeSession['active_workout'];
      final startedAt = activeSession['started_at'];
      
      print('📋 Sessão ativa:');
      print('   ID: $sessionId');
      print('   Treino: $workoutName');
      print('   Iniciado: $startedAt');

      if (!mounted) return;

      // Mostrar dialog com opções
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (context) => AlertDialog(
          backgroundColor: AppColors.surface,
          title: const Row(
            children: [
              Icon(Icons.warning_amber, color: Colors.orange, size: 28),
              SizedBox(width: 12),
              Expanded(
                child: Text(
                  'Treino em Andamento',
                  style: TextStyle(color: Colors.white, fontSize: 18),
                ),
              ),
            ],
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Você tem um treino ativo:',
                style: TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: 14,
                ),
              ),
              const SizedBox(height: 16),
              
              // Card com info da sessão
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppColors.primary.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: AppColors.primary.withOpacity(0.3),
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(
                          Icons.fitness_center,
                          color: AppColors.primary,
                          size: 20,
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            workoutName ?? 'Treino desconhecido',
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'ID da Sessão: $sessionId',
                      style: const TextStyle(
                        color: AppColors.textSecondary,
                        fontSize: 12,
                      ),
                    ),
                    if (startedAt != null) ...[
                      const SizedBox(height: 4),
                      Text(
                        'Iniciado: ${_formatDateTime(startedAt)}',
                        style: const TextStyle(
                          color: AppColors.textSecondary,
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              
              const SizedBox(height: 16),
              
              const Text(
                'Escolha uma ação:',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          actions: [
            // Botão: Voltar
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text(
                'Voltar',
                style: TextStyle(color: AppColors.textSecondary),
              ),
            ),
            
            // Botão: Cancelar e Iniciar Novo
            TextButton(
              onPressed: () async {
                Navigator.pop(context); // Fecha dialog
                await _cancelAndStartNew(sessionId);
              },
              child: const Text(
                'Cancelar e Iniciar Novo',
                style: TextStyle(color: AppColors.error),
              ),
            ),
            
            // Botão: Continuar Sessão
            TextButton(
              onPressed: () {
                Navigator.pop(context); // Fecha dialog
                
                // Navegar para primeiro exercício com sessão existente
                if (_workoutExercises.isNotEmpty) {
                  AppRouter.goToExerciseExecution(
                    exercise: _workoutExercises[0],
                    totalExercises: _workoutExercises.length,
                    currentExerciseIndex: 1,
                    allExercises: _workoutExercises,
                    initialWorkoutSeconds: 0,
                    isFullWorkout: true,
                    sessionId: sessionId,
                    workoutId: widget.workout.id,
                  );
                }
              },
              child: const Text(
                'Continuar',
                style: TextStyle(color: AppColors.primary),
              ),
            ),
          ],
        ),
      );

    } catch (e) {
      print('❌ Erro ao buscar sessão ativa: $e');
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Erro ao verificar sessão ativa: $e'),
            backgroundColor: AppColors.error,
          ),
        );
      }
    }
  }

  // ✅ MÉTODO CORRIGIDO: Cancelar sessão anterior e iniciar nova
Future<void> _cancelAndStartNew(int sessionId) async {
  try {
    // Mostrar loading
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => const Center(
        child: CircularProgressIndicator(color: AppColors.primary),
      ),
    );

    print('🗑️ Cancelando sessão $sessionId...');
    await ApiService.cancelActiveSession(sessionId);
    
    print('✅ Sessão cancelada com sucesso');
    
    // Fechar loading
    if (mounted) Navigator.pop(context);
    
    print('🔄 Aguardando 1 segundo antes de iniciar nova sessão...');
    await Future.delayed(const Duration(seconds: 1));
    
    // Tentar iniciar novamente
    print('🔄 Tentando iniciar nova sessão...');
    await _startFullWorkout();
    
  } catch (e) {
    // Fechar loading
    if (mounted) Navigator.pop(context);
    
    print('❌ Erro ao cancelar sessão: $e');
    
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Erro ao cancelar sessão: $e'),
          backgroundColor: AppColors.error,
          action: SnackBarAction(
            label: 'Tentar Novamente',
            textColor: Colors.white,
            onPressed: () => _cancelAndStartNew(sessionId),
          ),
        ),
      );
    }
  }
}

  // ✅ MÉTODO AUXILIAR: Formatar data/hora
String _formatDateTime(String isoString) {
  try {
    final dateTime = DateTime.parse(isoString);
    final now = DateTime.now();
    final diff = now.difference(dateTime);
    
    if (diff.inMinutes < 60) {
      return '${diff.inMinutes} min atrás';
    } else if (diff.inHours < 24) {
      return '${diff.inHours}h atrás';
    } else {
      return '${diff.inDays} dias atrás';
    }
  } catch (e) {
    return isoString;
  }
}

  // ✅ MÉTODO CORRIGIDO: Visualizar exercício (preview)
  void _openExercisePreview(ExerciseModel exercise, int index) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppColors.surface,
        title: const Row(
          children: [
            Icon(Icons.info_outline, color: AppColors.primary),
            SizedBox(width: 12),
            Text(
              'Visualização',
              style: TextStyle(color: Colors.white),
            ),
          ],
        ),
        content: const Text(
          'Esta é apenas uma visualização do exercício.\n\n'
          'Para iniciar o treino completo com cronômetro e registro de séries, '
          'use o botão "Iniciar Treino" abaixo.\n\n'
          'Deseja visualizar este exercício mesmo assim?',
          style: TextStyle(color: AppColors.textSecondary),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancelar'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              
              // ✅ Navegar em modo PREVIEW
              AppRouter.goToExerciseExecution(
                exercise: exercise,
                totalExercises: _workoutExercises.length,
                currentExerciseIndex: index + 1,
                allExercises: _workoutExercises,
                initialWorkoutSeconds: 0,
                isFullWorkout: false,  // ✅ NÃO é treino completo
                isPreviewMode: true,   // ✅ É modo visualização
              );
            },
            child: const Text('Visualizar'),
          ),
        ],
      ),
    );
  }
}

// ============================================================
// WIDGETS AUXILIARES
// ============================================================

class _ExerciseCard extends StatelessWidget {
  final ExerciseModel exercise;
  final int exerciseNumber;
  final int totalExercises;
  final VoidCallback onTap;

  const _ExerciseCard({
    required this.exercise,
    required this.exerciseNumber,
    required this.totalExercises,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: AppColors.primary.withOpacity(0.2),
          ),
        ),
        child: Row(
          children: [
            Container(
              width: 60,
              height: 60,
              decoration: BoxDecoration(
                color: AppColors.primary.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Center(
                child: Text(
                  '$exerciseNumber',
                  style: const TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: AppColors.primary,
                  ),
                ),
              ),
            ),
            
            const SizedBox(width: 16),
            
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    exercise.name,
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                      color: AppColors.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '${exercise.muscleGroup} • ${exercise.equipment}',
                    style: const TextStyle(
                      fontSize: 12,
                      color: AppColors.textSecondary,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    exercise.series,
                    style: const TextStyle(
                      fontSize: 11,
                      color: AppColors.textHint,
                    ),
                  ),
                ],
              ),
            ),
            
            const Icon(
              Icons.chevron_right,
              color: AppColors.textSecondary,
              size: 24,
            ),
          ],
        ),
      ),
    );
  }
}

class _StatItem extends StatelessWidget {
  final IconData icon;
  final String value;
  final String label;

  const _StatItem({
    required this.icon,
    required this.value,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, color: AppColors.primary, size: 20),
        const SizedBox(height: 4),
        Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(
              value,
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: AppColors.textPrimary,
              ),
            ),
            const SizedBox(width: 2),
            Text(
              label,
              style: const TextStyle(
                fontSize: 10,
                color: AppColors.textSecondary,
              ),
            ),
          ],
        ),
      ],
    );
  }
}

// ============================================================
// MODEL
// ============================================================

class ExerciseModel {
  final int id;
  final String name;
  final String description;
  final String series;
  final String? videoUrl;
  final String? imageUrl;
  final String muscleGroup;
  final String difficulty;
  final String equipment;
  final String? reps;
  final String? restTime;

  ExerciseModel({
    required this.id,
    required this.name,
    required this.description,
    required this.series,
    this.videoUrl,
    this.imageUrl,
    required this.muscleGroup,
    required this.difficulty,
    required this.equipment,
    this.reps,
    this.restTime,
  });
}