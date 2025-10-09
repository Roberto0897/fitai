import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:youtube_player_iframe/youtube_player_iframe.dart';
import 'dart:async';
import '../../../core/theme/app_theme.dart';
import '../../../core/router/app_router.dart';
import '../workouts/workout_detail_page.dart';
import 'rest_page.dart';
import '../../../service/api_service.dart';

class SeriesData {
  int number;
  double weight;
  int reps;
  bool isCompleted;
  final TextEditingController weightController;
  final TextEditingController repsController;

  SeriesData({
    required this.number,
    required this.weight,
    required this.reps,
    required this.isCompleted,
    required this.weightController,
    required this.repsController,
  });
}

class ExerciseExecutionPage extends StatefulWidget {
  final ExerciseModel exercise;
  final int totalExercises;
  final int currentExerciseIndex;
  final List<ExerciseModel> allExercises;
  final int initialWorkoutSeconds;
  final bool isFullWorkout;
  final int? sessionId;
  final int? workoutId;
  final bool isPreviewMode;

  const ExerciseExecutionPage({
    super.key,
    required this.exercise,
    required this.totalExercises,
    required this.currentExerciseIndex,
    required this.allExercises,
    this.initialWorkoutSeconds = 0,
    this.isFullWorkout = false,
    this.sessionId,
    this.workoutId,
    this.isPreviewMode = false,
  });

  @override
  State<ExerciseExecutionPage> createState() => _ExerciseExecutionPageState();
}

class _ExerciseExecutionPageState extends State<ExerciseExecutionPage> {
  final List<SeriesData> _series = [];
  int _completedSeries = 0;
  YoutubePlayerController? _youtubeController;
  Timer? _workoutTimer;
  int _workoutSeconds = 0;
  
  @override
  void initState() {
    super.initState();
    _workoutSeconds = widget.initialWorkoutSeconds;
    
    if (!widget.isPreviewMode) {
      print('🎬 Modo TREINO: Inicializando séries e timer');
      _initializeSeries();
      _startWorkoutTimer();
    } else {
      print('👁️ Modo PREVIEW: Pulando inicialização de séries e timer');
    }
    
    _initializeYoutubePlayer();
  }

  @override
  void dispose() {
    if (!widget.isPreviewMode) {
      for (var s in _series) {
        s.weightController.dispose();
        s.repsController.dispose();
      }
    }
    
    _youtubeController?.close();
    _workoutTimer?.cancel();
    super.dispose();
  }

  void _startWorkoutTimer() {
    _workoutTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (mounted) {
        setState(() {
          _workoutSeconds++;
        });
      }
    });
  }

  String _formatWorkoutTime() {
    final hours = _workoutSeconds ~/ 3600;
    final minutes = (_workoutSeconds % 3600) ~/ 60;
    final seconds = _workoutSeconds % 60;
    
    if (hours > 0) {
      return '${hours.toString().padLeft(2, '0')}:${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';
    }
    return '${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';
  }

  void _initializeYoutubePlayer() {
    String? videoUrl = widget.exercise.videoUrl;
    
    if ((videoUrl == null || videoUrl.isEmpty) && widget.exercise.imageUrl != null) {
      if (widget.exercise.imageUrl!.contains('youtube.com') || widget.exercise.imageUrl!.contains('youtu.be')) {
        videoUrl = widget.exercise.imageUrl;
      }
    }
    
    if (videoUrl != null && (videoUrl.contains('youtube.com') || videoUrl.contains('youtu.be'))) {
      final videoId = YoutubePlayerController.convertUrlToId(videoUrl);
      
      if (videoId != null) {
        _youtubeController = YoutubePlayerController.fromVideoId(
          videoId: videoId,
          autoPlay: false,
          params: const YoutubePlayerParams(
            showFullscreenButton: true,
            mute: false,
            showControls: true,
            loop: false,
            enableCaption: false,
            strictRelatedVideos: true,
          ),
        );
      }
    }
  }

  void _initializeSeries() {
    for (int i = 0; i < 4; i++) {
      _addSeries(i + 1);
    }
  }

  void _addSeries(int seriesNumber) {
    setState(() {
      final newSeries = SeriesData(
        number: seriesNumber,
        weight: 0.0,
        reps: 0,
        isCompleted: false,
        weightController: TextEditingController(text: '0.0'),
        repsController: TextEditingController(text: '0'),
      );
      _series.add(newSeries);
    });
  }

  void _removeSeries(int index) {
    if (_series.length <= 1) return;
    
    setState(() {
      final removedSeries = _series.removeAt(index);
      removedSeries.weightController.dispose();
      removedSeries.repsController.dispose();

      for (int i = index; i < _series.length; i++) {
        _series[i].number = i + 1;
      }
      
      if (removedSeries.isCompleted) {
        _completedSeries--;
      }
    });
  }

  void _completeSeries(int index) {
    final series = _series[index];
    series.weight = double.tryParse(series.weightController.text.replaceAll(',', '.')) ?? 0.0;
    series.reps = int.tryParse(series.repsController.text) ?? 0;

    if (series.weight <= 0.0 || series.reps <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Preencha peso e repetições (maior que zero) antes de concluir'),
          backgroundColor: AppColors.error,
        ),
      );
      return;
    }

    setState(() {
      _series[index].isCompleted = true;
      _completedSeries++;
    });

    if (index < _series.length - 1) {
      _goToRest();
    }
  }

  void _goToRest() {
    Navigator.of(context).push(
      PageRouteBuilder(
        opaque: false,
        barrierDismissible: false,
        barrierColor: Colors.black.withOpacity(0.5),
        pageBuilder: (context, animation, secondaryAnimation) {
          return RestPage(
            onRestComplete: () {
              Navigator.of(context).pop();
            },
          );
        },
        transitionsBuilder: (context, animation, secondaryAnimation, child) {
          return FadeTransition(opacity: animation, child: child);
        },
      ),
    );
  }

  void _goToNextExercise() {
    if (widget.currentExerciseIndex < widget.totalExercises) {
      final nextExercise = widget.allExercises[widget.currentExerciseIndex];
      
      Navigator.of(context).pop();
      Navigator.of(context).push(
        MaterialPageRoute(
          builder: (context) => ExerciseExecutionPage(
            exercise: nextExercise,
            totalExercises: widget.totalExercises,
            currentExerciseIndex: widget.currentExerciseIndex + 1,
            allExercises: widget.allExercises,
            initialWorkoutSeconds: _workoutSeconds,
            isFullWorkout: widget.isFullWorkout,
          ),
        ),
      );
    } else {
      _finishWorkout();
    }
  }

  Future<void> _finishWorkout() async {
    _workoutTimer?.cancel();
    
    if (widget.sessionId == null) {
      print('⚠️ Nenhuma sessão ativa (sessionId é null)');
      print('   Finalizando apenas localmente...');
      _showCompletionDialogAndExit();
      return;
    }

    try {
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (context) => const Center(
          child: CircularProgressIndicator(color: AppColors.primary),
        ),
      );

      print('🏁 Finalizando sessão ${widget.sessionId} no backend...');
      print('   Tempo total: ${_formatWorkoutTime()}');
      print('   Workout ID: ${widget.workoutId}');
      
      await ApiService.completeWorkoutSession(
        sessionId: widget.sessionId, 
        userRating: 5,
        caloriesBurned: null,
        notes: 'Treino completado - Tempo: ${_formatWorkoutTime()}',
      );
      
      print('✅ Sessão finalizada com sucesso no backend!');

      if (mounted) Navigator.pop(context);
      _showCompletionDialogAndExit();

    } catch (e) {
      if (mounted) Navigator.pop(context);
      
      print('❌ Erro ao finalizar sessão no backend: $e');
      
      if (mounted) {
        showDialog(
          context: context,
          builder: (context) => AlertDialog(
            backgroundColor: AppColors.surface,
            title: const Row(
              children: [
                Icon(Icons.warning_amber, color: Colors.orange),
                SizedBox(width: 12),
                Text('Erro ao Salvar', style: TextStyle(color: Colors.white)),
              ],
            ),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  'Não foi possível salvar o treino no servidor:\n$e',
                  style: const TextStyle(color: AppColors.textSecondary),
                ),
                const SizedBox(height: 16),
                const Text(
                  'Deseja finalizar mesmo assim?',
                  style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600),
                ),
              ],
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Tentar Novamente'),
              ),
              TextButton(
                onPressed: () {
                  Navigator.pop(context);
                  _showCompletionDialogAndExit();
                },
                child: const Text('Finalizar Localmente', style: TextStyle(color: AppColors.error)),
              ),
            ],
          ),
        );
      }
    }
  }

  void _showCompletionDialogAndExit() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        backgroundColor: AppColors.surface,
        title: const Text(
          'Treino Concluído!',
          style: TextStyle(color: Colors.white),
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
              'Parabéns! Você completou todos os exercícios.',
              style: TextStyle(color: AppColors.textSecondary),
            ),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppColors.primary.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Column(
                children: [
                  const Icon(Icons.timer, color: AppColors.primary, size: 32),
                  const SizedBox(height: 8),
                  Text(
                    'Tempo total: ${_formatWorkoutTime()}',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              Navigator.popUntil(context, (route) => route.isFirst);
            },
            child: const Text('Finalizar'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (widget.isPreviewMode) {
      return _buildPreviewMode();
    }
    
    return Scaffold(
  backgroundColor: AppColors.background,
  body: SafeArea(
    child: SingleChildScrollView(  // ✅ Adicione isto aqui
      child: Column(
        children: [
          _buildHeader(),
          _buildExerciseInfo(),
          _buildSeriesList(),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
            child: OutlinedButton.icon(
              icon: const Icon(Icons.add_circle_outline, color: AppColors.primary),
              label: const Text('Adicionar Série', style: TextStyle(color: AppColors.primary)),
              style: OutlinedButton.styleFrom(
                minimumSize: const Size(double.infinity, 50),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                side: const BorderSide(color: AppColors.primary, width: 1.5),
              ),
              onPressed: () => _addSeries(_series.length + 1),
            ),
          ),
          const SizedBox(height: 100),
        ],
      ),
    ),
  ),
  bottomNavigationBar: _buildBottomBar(),
);
  }

  Widget _buildPreviewMode() {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Column(
          children: [
            _buildPreviewHeader(),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      widget.exercise.name,
                      style: const TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 8),
                    
                    Row(
                      children: [
                        _buildInfoChip(Icons.fitness_center, widget.exercise.muscleGroup),
                        const SizedBox(width: 8),
                        _buildInfoChip(Icons.bar_chart, widget.exercise.difficulty),
                        const SizedBox(width: 8),
                        _buildInfoChip(Icons.build, widget.exercise.equipment),
                      ],
                    ),
                    
                    const SizedBox(height: 24),
                    
                    Container(
                      height: 220,
                      width: double.infinity,
                      decoration: BoxDecoration(
                        color: AppColors.surface,
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(16),
                        child: _buildExerciseMedia(),
                      ),
                    ),
                    
                    const SizedBox(height: 24),
                    
                    if (widget.exercise.description.isNotEmpty) ...[
                      const Text(
                        'Descrição',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                      const SizedBox(height: 12),
                      Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: AppColors.surface,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          widget.exercise.description,
                          style: const TextStyle(
                            fontSize: 14,
                            color: AppColors.textSecondary,
                            height: 1.5,
                          ),
                        ),
                      ),
                      const SizedBox(height: 24),
                    ],
                    
                    const Text(
                      'Informações',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 12),
                    _buildInfoRow('Grupo Muscular', widget.exercise.muscleGroup),
                    _buildInfoRow('Dificuldade', widget.exercise.difficulty),
                    _buildInfoRow('Equipamento', widget.exercise.equipment),
                    if (widget.exercise.series.isNotEmpty)
                      _buildInfoRow('Séries Recomendadas', widget.exercise.series),
                    
                    const SizedBox(height: 32),
                    
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: AppColors.primary.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: AppColors.primary.withOpacity(0.3)),
                      ),
                      child: Column(
                        children: [
                          const Icon(Icons.info_outline, color: AppColors.primary, size: 32),
                          const SizedBox(height: 12),
                          const Text(
                            'Esta é apenas uma visualização',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                            textAlign: TextAlign.center,
                          ),
                          const SizedBox(height: 8),
                          const Text(
                            'Para fazer o treino completo com cronômetro e registro de séries, use o botão "Iniciar Treino"',
                            style: TextStyle(
                              fontSize: 13,
                              color: AppColors.textSecondary,
                            ),
                            textAlign: TextAlign.center,
                          ),
                        ],
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

  Widget _buildPreviewHeader() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [AppColors.primary, AppColors.primary.withOpacity(0.7)],
        ),
      ),
      child: Row(
        children: [
          GestureDetector(
            onTap: () => Navigator.pop(context),
            child: Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.2),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Icon(Icons.arrow_back, color: Colors.white),
            ),
          ),
          const SizedBox(width: 16),
          const Expanded(
            child: Text(
              'Visualização',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.2),
              borderRadius: BorderRadius.circular(20),
            ),
            child: const Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.visibility, color: Colors.white, size: 16),
                SizedBox(width: 6),
                Text(
                  'Preview',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoChip(IconData icon, String label) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.primary.withOpacity(0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: AppColors.primary),
          const SizedBox(width: 6),
          Text(
            label,
            style: const TextStyle(
              fontSize: 12,
              color: AppColors.textPrimary,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        children: [
          Expanded(
            flex: 2,
            child: Text(
              label,
              style: const TextStyle(
                fontSize: 14,
                color: AppColors.textSecondary,
              ),
            ),
          ),
          Expanded(
            flex: 3,
            child: Text(
              value,
              style: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w600,
                color: Colors.white,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [AppColors.primary, AppColors.primary.withOpacity(0.7)],
        ),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              GestureDetector(
                onTap: () => _showExitDialog(),
                child: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(Icons.close, color: Colors.white),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.timer, color: Colors.white, size: 18),
                    const SizedBox(width: 8),
                    Text(_formatWorkoutTime(), style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
                  ],
                ),
              ),
              GestureDetector(
                onTap: () => _showOptionsMenu(),
                child: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(Icons.more_horiz, color: Colors.white),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          const Text('Treino em andamento', style: TextStyle(fontSize: 14, color: Colors.white70)),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.fitness_center, color: Colors.white, size: 20),
              const SizedBox(width: 8),
              Flexible(
                child: Text(
                  widget.exercise.name,
                  style: const TextStyle(fontSize: 16, color: Colors.white, fontWeight: FontWeight.w600),
                  textAlign: TextAlign.center,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildExerciseInfo() {
    return Container(
      margin: const EdgeInsets.all(20),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.primary.withOpacity(0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(widget.exercise.name, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.white)),
          const SizedBox(height: 8),
          Text('${widget.exercise.muscleGroup} - Exercício ${widget.currentExerciseIndex} de ${widget.totalExercises}', style: const TextStyle(fontSize: 14, color: AppColors.textSecondary)),
          const SizedBox(height: 16),
          Container(
            height: 180,
            width: double.infinity,
            decoration: BoxDecoration(color: AppColors.background, borderRadius: BorderRadius.circular(12)),
            child: ClipRRect(borderRadius: BorderRadius.circular(12), child: _buildExerciseMedia()),
          ),
          if (widget.exercise.description.isNotEmpty) ...[
            const SizedBox(height: 12),
            Text(widget.exercise.description, style: const TextStyle(fontSize: 13, color: AppColors.textSecondary)),
          ],
        ],
      ),
    );
  }

  Widget _buildExerciseMedia() {
    String? mediaUrl = widget.exercise.videoUrl;
    
    if ((mediaUrl == null || mediaUrl.isEmpty) && widget.exercise.imageUrl != null && (widget.exercise.imageUrl!.contains('youtube.com') || widget.exercise.imageUrl!.contains('youtu.be'))) {
      mediaUrl = widget.exercise.imageUrl;
    }
    
    if (mediaUrl == null || mediaUrl.isEmpty) {
      mediaUrl = widget.exercise.imageUrl;
    }
    
    if (mediaUrl == null || mediaUrl.isEmpty) {
      return _buildMediaPlaceholder();
    }
    
    if ((mediaUrl.contains('youtube.com') || mediaUrl.contains('youtu.be')) && _youtubeController != null) {
      return YoutubePlayer(controller: _youtubeController!, aspectRatio: 16 / 9);
    }
    
    return Image.network(
      mediaUrl,
      fit: BoxFit.cover,
      loadingBuilder: (context, child, loadingProgress) {
        if (loadingProgress == null) return child;
        return Center(child: CircularProgressIndicator(value: loadingProgress.expectedTotalBytes != null ? loadingProgress.cumulativeBytesLoaded / loadingProgress.expectedTotalBytes! : null, color: AppColors.primary));
      },
      errorBuilder: (context, error, stackTrace) => _buildMediaPlaceholder(error: true),
    );
  }

  Widget _buildMediaPlaceholder({bool error = false}) {
    return Container(
      color: AppColors.background,
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(error ? Icons.broken_image : Icons.fitness_center, size: 64, color: AppColors.textHint.withOpacity(0.3)),
          const SizedBox(height: 8),
          Text(error ? 'Erro ao carregar mídia' : 'Sem mídia disponível', style: const TextStyle(color: AppColors.textHint, fontSize: 12)),
        ],
      ),
    );
  }

  Widget _buildSeriesList() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Séries', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white)),
          const SizedBox(height: 16),
          ListView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: _series.length,
            itemBuilder: (context, index) => _buildSeriesItem(_series[index], index),
          ),
        ],
      ),
    );
  }

  Widget _buildSeriesItem(SeriesData series, int index) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: series.isCompleted ? AppColors.primary.withOpacity(0.1) : AppColors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: series.isCompleted ? AppColors.primary : AppColors.primary.withOpacity(0.2), width: series.isCompleted ? 2 : 1),
      ),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(color: series.isCompleted ? AppColors.primary : AppColors.background, shape: BoxShape.circle),
            child: Center(child: Text('${series.number}', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: series.isCompleted ? Colors.white : AppColors.primary))),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: _buildQuantityInputField(
              label: 'KG',
              controller: series.weightController,
              enabled: !series.isCompleted,
              isWeight: true,
              index: index,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: _buildQuantityInputField(
              label: 'REP',
              controller: series.repsController,
              enabled: !series.isCompleted,
              isWeight: false,
              index: index,
            ),
          ),
          const SizedBox(width: 12),
          GestureDetector(
            onTap: series.isCompleted ? null : () => _completeSeries(index),
            child: Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: series.isCompleted ? AppColors.primary : Colors.transparent,
                shape: BoxShape.circle,
                border: Border.all(color: series.isCompleted ? AppColors.primary : AppColors.textSecondary.withOpacity(0.5), width: 2),
              ),
              child: Center(child: series.isCompleted ? const Icon(Icons.check, color: Colors.white, size: 20) : Icon(Icons.check, color: AppColors.textSecondary.withOpacity(0.5), size: 20)),
            ),
          ),
          const SizedBox(width: 8),
          if (!series.isCompleted && _series.length > 1)
            GestureDetector(
              onTap: () => _removeSeries(index),
              child: Container(
                width: 32,
                height: 32,
                decoration: BoxDecoration(
                  color: AppColors.error.withOpacity(0.1),
                  shape: BoxShape.circle,
                  border: Border.all(color: AppColors.error.withOpacity(0.3), width: 1),
                ),
                child: const Icon(Icons.close, size: 18, color: AppColors.error),
              ),
            )
          else
            const SizedBox(width: 32),
        ],
      ),
    );
  }

  // 🔧 CORREÇÃO PRINCIPAL: Remover setState dos callbacks
  Widget _buildQuantityInputField({
    required String label,
    required TextEditingController controller,
    required bool enabled,
    required bool isWeight,
    required int index,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: TextStyle(fontSize: 10, color: enabled ? AppColors.textSecondary : AppColors.textHint, fontWeight: FontWeight.w500)),
        const SizedBox(height: 4),
        Container(
          height: 40,
          decoration: BoxDecoration(
            color: AppColors.background,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: enabled ? AppColors.primary.withOpacity(0.4) : AppColors.textHint.withOpacity(0.2), width: 1),
          ),
          child: Row(
            children: [
              GestureDetector(
                onTap: enabled ? () {
                  // ✅ Atualizar valor diretamente no controller, sem setState
                  if (isWeight) {
                    double currentValue = double.tryParse(controller.text.replaceAll(',', '.')) ?? 0.0;
                    double newValue = (currentValue - 1).clamp(0.0, double.infinity);
                    controller.text = newValue.toStringAsFixed(1);
                    _series[index].weight = newValue;
                  } else {
                    int currentValue = int.tryParse(controller.text) ?? 0;
                    int newValue = (currentValue - 1).clamp(0, 999);
                    controller.text = newValue.toString();
                    _series[index].reps = newValue;
                  }
                } : null,
                child: Container(width: 30, alignment: Alignment.center, child: Icon(Icons.remove, size: 16, color: enabled ? AppColors.primary : AppColors.textHint)),
              ),
              Expanded(
                child: TextFormField(
                  controller: controller,
                  enabled: enabled,
                  textAlign: TextAlign.center,
                  keyboardType: isWeight ? const TextInputType.numberWithOptions(decimal: true) : TextInputType.number,
                  inputFormatters: <TextInputFormatter>[
                    isWeight ? FilteringTextInputFormatter.allow(RegExp(r'^\d*[\.,]?\d*')) : FilteringTextInputFormatter.digitsOnly,
                  ],
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: enabled ? Colors.white : AppColors.textHint),
                  decoration: const InputDecoration(isDense: true, contentPadding: EdgeInsets.zero, border: InputBorder.none),
                  onChanged: (value) {
                    // ✅ Atualizar apenas o valor interno, sem setState
                    if (isWeight) {
                      _series[index].weight = double.tryParse(value.replaceAll(',', '.')) ?? 0.0;
                    } else {
                      _series[index].reps = int.tryParse(value) ?? 0;
                    }
                  },
                ),
              ),
              GestureDetector(
                onTap: enabled ? () {
                  // ✅ Atualizar valor diretamente no controller, sem setState
                  if (isWeight) {
                    double currentValue = double.tryParse(controller.text.replaceAll(',', '.')) ?? 0.0;
                    double newValue = currentValue + 1;
                    controller.text = newValue.toStringAsFixed(1);
                    _series[index].weight = newValue;
                  } else {
                    int currentValue = int.tryParse(controller.text) ?? 0;
                    int newValue = currentValue + 1;
                    controller.text = newValue.toString();
                    _series[index].reps = newValue;
                  }
                } : null,
                child: Container(width: 30, alignment: Alignment.center, child: Icon(Icons.add, size: 16, color: enabled ? AppColors.primary : AppColors.textHint)),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildBottomBar() {
    final allSeriesCompleted = _completedSeries == _series.length;
    final isLastExercise = widget.currentExerciseIndex == widget.totalExercises;
    
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.surface,
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.1), blurRadius: 10, offset: const Offset(0, -5))],
      ),
      child: SafeArea(
        child: SizedBox(
          width: double.infinity,
          child: ElevatedButton(
            onPressed: allSeriesCompleted ? _handleNextAction : null,
            style: ElevatedButton.styleFrom(
              backgroundColor: allSeriesCompleted ? AppColors.primary : AppColors.textHint,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 16),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
            child: Text(
              allSeriesCompleted ? (isLastExercise ? 'Finalizar Treino' : 'Próximo exercício') : 'Complete todas as séries',
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
            ),
          ),
        ),
      ),
    );
  }

  void _handleNextAction() {
    final isLastExercise = widget.currentExerciseIndex == widget.totalExercises;
    
    if (isLastExercise) {
      _checkPendingExercisesBeforeFinish();
    } else {
      _goToNextExercise();
    }
  }

  void _checkPendingExercisesBeforeFinish() {
    print('🔍 DEBUG - Verificando finalização:');
    print('   isFullWorkout: ${widget.isFullWorkout}');
    print('   currentExerciseIndex: ${widget.currentExerciseIndex}');
    print('   totalExercises: ${widget.totalExercises}');
    
    final isLastExerciseInFullWorkout = widget.isFullWorkout && widget.currentExerciseIndex >= widget.totalExercises;
    
    print('   isLastExerciseInFullWorkout: $isLastExerciseInFullWorkout');
    
    if (isLastExerciseInFullWorkout) {
      print('✅ Treino completo finalizado corretamente');
      _finishWorkout();
      return;
    }
    
    print('⚠️ Mostrando aviso de exercícios pendentes');
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppColors.surface,
        title: const Row(
          children: [
            Icon(Icons.warning_amber_rounded, color: Colors.orange, size: 28),
            SizedBox(width: 12),
            Text('Exercícios Pendentes', style: TextStyle(color: Colors.white, fontSize: 18)),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              widget.isFullWorkout
                ? 'Você está no exercício ${widget.currentExerciseIndex} de ${widget.totalExercises}.'
                : 'Você visualizou apenas 1 exercício dos ${widget.totalExercises} disponíveis.',
              style: const TextStyle(color: AppColors.textSecondary, fontSize: 14),
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.orange.withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.orange.withOpacity(0.3)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.info_outline, color: Colors.orange, size: 20),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      widget.isFullWorkout
                        ? 'Ainda faltam ${widget.totalExercises - widget.currentExerciseIndex} exercício(s)'
                        : 'Use o botão "Iniciar Treino" para fazer o treino completo',
                      style: const TextStyle(color: Colors.orange, fontSize: 12, fontWeight: FontWeight.w500),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            const Text(
              'Deseja finalizar mesmo assim?',
              style: TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w600),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Continuar Treino', style: TextStyle(color: AppColors.primary)),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              _finishWorkout();
            },
            child: const Text('Finalizar Assim Mesmo', style: TextStyle(color: AppColors.error)),
          ),
        ],
      ),
    );
  }

  void _showExitDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppColors.surface,
        title: const Text('Sair do treino?', style: TextStyle(color: Colors.white)),
        content: const Text('Você perderá o progresso do treino atual.', style: TextStyle(color: AppColors.textSecondary)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancelar')),
          TextButton(
            onPressed: () {
              _workoutTimer?.cancel();
              Navigator.pop(context);
              AppRouter.goBack();
            },
            child: const Text('Sair', style: TextStyle(color: AppColors.error)),
          ),
        ],
      ),
    );
  }

  void _showOptionsMenu() {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (context) => Container(
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(leading: const Icon(Icons.info_outline, color: AppColors.primary), title: const Text('Ver instruções'), onTap: () => Navigator.pop(context)),
            ListTile(leading: const Icon(Icons.swap_horiz, color: AppColors.primary), title: const Text('Substituir exercício'), onTap: () => Navigator.pop(context)),
            ListTile(
              leading: const Icon(Icons.skip_next, color: AppColors.primary),
              title: const Text('Pular exercício'),
              onTap: () {
                Navigator.pop(context);
                _goToNextExercise();
              }
            ),
          ],
        ),
      ),
    );
  }
}