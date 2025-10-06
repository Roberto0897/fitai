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

  // Carrega os exercícios do treino específico
 Future<void> _loadWorkoutExercises() async {
  setState(() {
    _isLoadingExercises = true;
    _errorMessage = null;
  });

  try {
    print('🔍 Carregando detalhes do treino ID: ${widget.workout.id}');
    print('📍 URL será: http://localhost:8000/api/v1/workouts/${widget.workout.id}/');
    
    // Busca os detalhes completos do treino incluindo exercícios
    final response = await ApiService.getWorkoutDetail(widget.workout.id);
    
    print('Resposta completa da API: $response');
    
    // Verifica se existe o campo 'exercises' na resposta
    final exercisesList = response['exercises'] as List? ?? [];
    
    print('Total de exercícios encontrados: ${exercisesList.length}');
    
     setState(() {
      _workoutExercises = exercisesList.map((exerciseData) {
        final exercise = exerciseData is Map && exerciseData.containsKey('exercise') 
            ? exerciseData['exercise'] 
            : exerciseData;
        
        // LOGS COMPLETOS
        print('═══════════════════════════════════════');
        print('TODOS OS CAMPOS DO EXERCISE:');
        if (exercise is Map) {
          exercise.forEach((key, value) {
            print('  $key: $value');
          });
        }
        print('');
        print('video_url: ${exercise['video_url']}');
        print('image_url: ${exercise['image_url']}');
        print('primary_muscle_group: ${exercise['primary_muscle_group']}');
        print('muscle_group: ${exercise['muscle_group']}');
        print('═══════════════════════════════════════');
        
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
          imageUrl:  exercise['video_url'] ?? exercise['image_url'], 
        );
      }).toList();
      _isLoadingExercises = false;
    });
    
    print('✅ ${_workoutExercises.length} exercícios carregados do treino ${widget.workout.id}');
    
  } catch (e, stackTrace) {
    print('❌ Erro ao carregar exercícios do treino: $e');
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
            AppColors.primary.withValues(alpha: 0.7),
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
                      color: Colors.white.withValues(alpha: 0.2),
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
                          color: Colors.white.withValues(alpha: 0.2),
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
                          color: Colors.white.withValues(alpha: 0.2),
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
                color: Colors.white.withValues(alpha: 0.9),
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
                    color: Colors.white.withValues(alpha: 0.2),
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
                    color: Colors.white.withValues(alpha: 0.2),
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
          color: Colors.white,
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
                color: Colors.red,
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
                onTap: () => _openExerciseDetail(_workoutExercises[index], index),
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
            color: Colors.black.withValues(alpha: 0.1),
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
                onPressed: _workoutExercises.isEmpty ? null : _startWorkout,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  disabledBackgroundColor: AppColors.primary.withValues(alpha: 0.3),
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

 Future<void> _startWorkout() async {
  if (_workoutExercises.isEmpty) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Adicione exercícios antes de iniciar o treino'),
        backgroundColor: Colors.red,
      ),
    );
    return;
  }

  try {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => const Center(
        child: CircularProgressIndicator(),
      ),
    );

    print('Iniciando sessão de treino no backend...');
    
    final sessionResponse = await ApiService.startWorkoutSession(
      widget.workout.id,
    );
    
    print('Sessão criada com sucesso!');
    print('   Session ID: ${sessionResponse['session_id']}');

    if (mounted) Navigator.pop(context);

    AppRouter.goToExerciseExecution(
      exercise: _workoutExercises[0],
      totalExercises: _workoutExercises.length,
      currentExerciseIndex: 1,
      allExercises: _workoutExercises,
      initialWorkoutSeconds: 0,
      isFullWorkout: true,
      sessionId: sessionResponse['session_id'],
      workoutId: widget.workout.id,
    );

  } catch (e) {
    if (mounted) Navigator.pop(context);
    
    print('Erro ao iniciar sessão: $e');
    
    // Verifica se é erro de sessão ativa
    if (e.toString().contains('já tem uma sessão em andamento')) {
      _handleActiveSession(e);
    } else {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Erro ao iniciar treino: $e'),
            backgroundColor: Colors.red,
            duration: const Duration(seconds: 4),
          ),
        );
      }
    }
  }
}

Future<void> _handleActiveSession(dynamic error) async {
  // Tenta extrair info da sessão ativa do erro
  final activeSession = await ApiService.getActiveSession();
  
  if (!mounted) return;
  
  showDialog(
    context: context,
    builder: (context) => AlertDialog(
      backgroundColor: AppColors.surface,
      title: Row(
        children: [
          const Icon(Icons.warning_amber, color: Colors.orange),
          const SizedBox(width: 12),
          const Text('Treino em Andamento', style: TextStyle(color: Colors.white)),
        ],
      ),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (activeSession != null) ...[
            Text(
              'Você tem um treino ativo:',
              style: const TextStyle(color: AppColors.textSecondary),
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.primary.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    activeSession['active_workout'] ?? 'Treino Ativo',
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'ID da Sessão: ${activeSession['active_session_id']}',
                    style: const TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
          ],
          const Text(
            'Escolha uma ação:',
            style: TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Voltar'),
        ),
        TextButton(
          onPressed: () async {
            Navigator.pop(context);
            if (activeSession != null) {
              await _cancelAndStartNew(activeSession['active_session_id']);
            }
          },
          child: const Text(
            'Cancelar Anterior e Iniciar',
            style: TextStyle(color: AppColors.error),
          ),
        ),
      ],
    ),
  );
}

Future<void> _cancelAndStartNew(int sessionId) async {
  try {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => const Center(
        child: CircularProgressIndicator(),
      ),
    );

    print('Cancelando sessão $sessionId...');
    await ApiService.cancelActiveSession(sessionId);
    
    print('Sessão cancelada. Iniciando nova...');
    
    if (mounted) Navigator.pop(context);
    
    // Tenta iniciar novamente
    await _startWorkout();
    
  } catch (e) {
    if (mounted) Navigator.pop(context);
    
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Erro ao cancelar sessão: $e'),
        backgroundColor: Colors.red,
      ),
    );
  }
}

  void _openExerciseDetail(ExerciseModel exercise, int index) {
    // Mostra aviso de que deve iniciar pelo botão
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppColors.surface,
        title: const Text(
          'Dica',
          style: TextStyle(color: Colors.white),
        ),
        content: const Text(
          'Para iniciar o treino completo com cronômetro, use o botão "Iniciar Treino" abaixo.\n\nDeseja visualizar este exercício mesmo assim?',
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
              // Abre apenas para visualização, sem fluxo de treino
              AppRouter.goToExerciseExecution(
                exercise: exercise,
                totalExercises: _workoutExercises.length,
                currentExerciseIndex: index + 1,
                allExercises: _workoutExercises,
                initialWorkoutSeconds: 0,
              );
            },
            child: const Text('Visualizar'),
          ),
        ],
      ),
    );
  }
}

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
            color: AppColors.primary.withValues(alpha: 0.2),
          ),
        ),
        child: Row(
          children: [
            Container(
              width: 60,
              height: 60,
              decoration: BoxDecoration(
                color: AppColors.primary.withValues(alpha: 0.1),
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