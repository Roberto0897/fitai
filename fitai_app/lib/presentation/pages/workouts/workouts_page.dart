import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/router/app_router.dart';
import '../../../service/api_service.dart';
import 'workout_detail_page.dart';
import 'create_workout_page.dart';


class WorkoutsPage extends StatefulWidget {
  const WorkoutsPage({super.key});

  @override
  State<WorkoutsPage> createState() => _WorkoutsPageState();
}

class _WorkoutsPageState extends State<WorkoutsPage> with TickerProviderStateMixin {
  late TabController _tabController;
  String _searchQuery = '';
  String _selectedCategory = 'Todos';
  String _selectedDifficulty = 'Todos';
  String _selectedMuscleGroup = 'Todos';

  // Estado para dados da API
  List<WorkoutModel> _allWorkouts = [];
  List<ExerciseModel> _allExercises = [];
  bool _isLoadingWorkouts = true;
  bool _isLoadingExercises = true;
  String? _errorMessage;

  final List<String> _categories = ['Todos', 'Força', 'Cardio', 'Flexibilidade', 'HIIT', 'Yoga'];
  final List<String> _difficulties = ['Todos', 'Iniciante', 'Intermediário', 'Avançado'];
  final List<String> _muscleGroups = ['Todos', 'Peito', 'Costas', 'Pernas', 'Ombros', 'Braços', 'Core'];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _tabController.addListener(() {
      setState(() {});
    });
    
    _loadWorkoutsFromAPI();
    _loadExercisesFromAPI();
  }

  Future<void> _loadWorkoutsFromAPI() async {
    setState(() {
      _isLoadingWorkouts = true;
      _errorMessage = null;
    });

    try {
      final response = await ApiService.getWorkouts();
      final workoutsList = response['workouts'] as List;
      
      setState(() {
        _allWorkouts = workoutsList.map((workout) {
          return WorkoutModel(
            id: workout['id'],
            name: workout['name'] ?? 'Sem nome',
            description: workout['description'] ?? '',
            duration: workout['estimated_duration'] ?? 0,
            exercises: 0,
            difficulty: _mapDifficulty(workout['difficulty_level']),
            category: _mapCategory(workout['workout_type']),
            calories: workout['calories_estimate'] ?? 0,
            isRecommended: workout['is_recommended'] ?? false,
          );
        }).toList();
        _isLoadingWorkouts = false;
      });
      
      print('✅ ${_allWorkouts.length} treinos carregados da API');
      
    } catch (e) {
      setState(() {
        _errorMessage = 'Erro ao carregar treinos: $e';
        _isLoadingWorkouts = false;
      });
      print('❌ Erro ao carregar treinos: $e');
    }
  }

  Future<void> _loadExercisesFromAPI() async {
    setState(() {
      _isLoadingExercises = true;
    });

    try {
      final response = await ApiService.getExercises();
      final exercisesList = response['exercises'] as List;
      
      setState(() {
        _allExercises = exercisesList.map((exercise) {
          print('🎥 Exercício: ${exercise['name']}');
          print('   video_url: ${exercise['video_url']}');
          print('   image_url: ${exercise['image_url']}');
          
          return ExerciseModel(
            id: exercise['id'],
            name: exercise['name'] ?? 'Sem nome',
            description: exercise['description'] ?? '',
            muscleGroup: _mapMuscleGroup(exercise['muscle_group']),
            difficulty: _mapDifficulty(exercise['difficulty_level']),
            equipment: exercise['equipment_needed'] ?? 'Não especificado',
            series: '3',
            videoUrl: exercise['video_url'],  // ✅ ADICIONADO
            imageUrl: exercise['image_url'],  // ✅ ADICIONADO
          );
        }).toList();
        _isLoadingExercises = false;
      });
      
      print('✅ ${_allExercises.length} exercícios carregados da API');
      
    } catch (e) {
      setState(() {
        _isLoadingExercises = false;
      });
      print('❌ Erro ao carregar exercícios: $e');
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

  String _mapCategory(String? type) {
    switch (type?.toLowerCase()) {
      case 'strength':
        return 'Força';
      case 'cardio':
        return 'Cardio';
      case 'flexibility':
        return 'Flexibilidade';
      case 'hiit':
        return 'HIIT';
      case 'yoga':
        return 'Yoga';
      default:
        return 'Força';
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
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            _buildHeader(),
            _buildTabs(),
            _buildFilters(),
            Expanded(
              child: TabBarView(
                controller: _tabController,
                children: [
                  _buildAllWorkouts(),
                  _buildRecommendedWorkouts(),
                  _buildMyWorkouts(),
                  _buildExercisesTab(),
                ],
              ),
            ),
          ],
        ),
      ),
      floatingActionButton: _tabController.index == 2
          ? FloatingActionButton.extended(
              onPressed: _createNewWorkout,
              backgroundColor: AppColors.primary,
              icon: const Icon(Icons.add),
              label: const Text('Criar Treino'),
            )
          : null,
    );
  }

  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              GestureDetector(
                onTap: () => AppRouter.goBack(),
                child: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: AppColors.surface,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(Icons.arrow_back, color: AppColors.primary),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Text(
                  'Treinos',
                  style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              GestureDetector(
                onTap: () {
                  _loadWorkoutsFromAPI();
                  _loadExercisesFromAPI();
                },
                child: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: AppColors.surface,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(Icons.refresh, color: AppColors.primary),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Container(
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(16),
            ),
            child: TextField(
              onChanged: (value) => setState(() => _searchQuery = value),
              decoration: InputDecoration(
                hintText: _tabController.index == 3 ? 'Buscar exercícios...' : 'Buscar treinos...',
                prefixIcon: const Icon(Icons.search, color: AppColors.textHint),
                border: InputBorder.none,
                contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTabs() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 20),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16),
      ),
      child: TabBar(
        controller: _tabController,
        indicatorColor: AppColors.primary,
        indicatorWeight: 3,
        labelColor: AppColors.primary,
        unselectedLabelColor: AppColors.textSecondary,
        isScrollable: true,
        tabAlignment: TabAlignment.start,
        tabs: const [
          Tab(text: 'Todos'),
          Tab(text: 'Recomendados FitAI'),
          Tab(text: 'Meus Treinos'),
          Tab(text: 'Exercícios'),
        ],
      ),
    );
  }

  Widget _buildFilters() {
    if (_tabController.index == 3) {
      return Container(
        padding: const EdgeInsets.all(20),
        child: Row(
          children: [
            Expanded(
              child: _FilterDropdown(
                label: 'Grupo Muscular',
                value: _selectedMuscleGroup,
                items: _muscleGroups,
                onChanged: (value) => setState(() => _selectedMuscleGroup = value!),
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: _FilterDropdown(
                label: 'Dificuldade',
                value: _selectedDifficulty,
                items: _difficulties,
                onChanged: (value) => setState(() => _selectedDifficulty = value!),
              ),
            ),
          ],
        ),
      );
    }
    
    return Container(
      padding: const EdgeInsets.all(20),
      child: Row(
        children: [
          Expanded(
            child: _FilterDropdown(
              label: 'Categoria',
              value: _selectedCategory,
              items: _categories,
              onChanged: (value) => setState(() => _selectedCategory = value!),
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: _FilterDropdown(
              label: 'Dificuldade',
              value: _selectedDifficulty,
              items: _difficulties,
              onChanged: (value) => setState(() => _selectedDifficulty = value!),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAllWorkouts() {
    if (_isLoadingWorkouts) {
      return const Center(
        child: CircularProgressIndicator(color: AppColors.primary),
      );
    }

    if (_errorMessage != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 64, color: Colors.red),
            const SizedBox(height: 16),
            Text(
              _errorMessage!,
              style: const TextStyle(color: AppColors.textPrimary),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _loadWorkoutsFromAPI,
              child: const Text('Tentar Novamente'),
            ),
          ],
        ),
      );
    }

    final workouts = _getFilteredWorkouts(_allWorkouts);
    
    if (workouts.isEmpty) {
      return _buildEmptyState(
        title: 'Nenhum treino encontrado',
        subtitle: 'Os treinos do Django aparecerão aqui',
      );
    }

    return RefreshIndicator(
      onRefresh: _loadWorkoutsFromAPI,
      color: AppColors.primary,
      child: ListView.builder(
        padding: const EdgeInsets.symmetric(horizontal: 20),
        itemCount: workouts.length,
        itemBuilder: (context, index) {
          return Padding(
            padding: const EdgeInsets.only(bottom: 16),
            child: WorkoutCard(
              workout: workouts[index],
              onTap: () => _openWorkoutDetail(workouts[index]),
            ),
          );
        },
      ),
    );
  }

  Widget _buildRecommendedWorkouts() {
    if (_isLoadingWorkouts) {
      return const Center(
        child: CircularProgressIndicator(color: AppColors.primary),
      );
    }

    final workouts = _getFilteredWorkouts(_getRecommendedWorkouts());
    
    if (workouts.isEmpty) {
      return _buildEmptyState(
        icon: Icons.psychology,
        title: 'Nenhuma recomendação disponível',
        subtitle: 'Marque treinos como recomendados no Django admin',
      );
    }

    return Column(
      children: [
        Container(
          margin: const EdgeInsets.fromLTRB(20, 0, 20, 16),
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [
                AppColors.primary.withValues(alpha: 0.1),
                AppColors.primary.withValues(alpha: 0.05),
              ],
            ),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: AppColors.primary.withValues(alpha: 0.3),
            ),
          ),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: AppColors.primary.withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(
                  Icons.psychology,
                  color: AppColors.primary,
                  size: 24,
                ),
              ),
              const SizedBox(width: 12),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Treinos FitAI',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        color: AppColors.primary,
                      ),
                    ),
                    SizedBox(height: 2),
                    Text(
                      'Treinos gerados pelo FitAI',
                      style: TextStyle(
                        fontSize: 12,
                        color: AppColors.textSecondary,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        
        Expanded(
          child: RefreshIndicator(
            onRefresh: _loadWorkoutsFromAPI,
            color: AppColors.primary,
            child: ListView.builder(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              itemCount: workouts.length,
              itemBuilder: (context, index) {
                return Padding(
                  padding: const EdgeInsets.only(bottom: 16),
                  child: WorkoutCard(
                    workout: workouts[index],
                    onTap: () => _openWorkoutDetail(workouts[index]),
                    isRecommended: true,
                  ),
                );
              },
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildMyWorkouts() {
    return FutureBuilder<Map<String, dynamic>>(
      future: ApiService.getMyWorkouts(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(
            child: CircularProgressIndicator(color: AppColors.primary),
          );
        }

        if (snapshot.hasError) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.error_outline, size: 64, color: Colors.red),
                const SizedBox(height: 16),
                Text(
                  'Erro ao carregar treinos: ${snapshot.error}',
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: AppColors.textSecondary),
                ),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: () {
                    setState(() {});
                  },
                  child: const Text('Tentar Novamente'),
                ),
              ],
            ),
          );
        }

        final data = snapshot.data;
        if (data == null || data['my_workouts'] == null) {
          return _buildEmptyMyWorkouts();
        }

        final myWorkouts = (data['my_workouts'] as List)
            .map((w) => WorkoutModel(
                  id: w['id'],
                  name: w['name'],
                  description: w['description'],
                  duration: w['estimated_duration'] ?? 30,
                  exercises: w['exercise_count'] ?? 0,
                  difficulty: _mapDifficulty(w['difficulty_level']),
                  category: _mapCategory(w['workout_type']),
                  calories: w['calories_estimate'] ?? 0,
                  isRecommended: false,
                ))
            .toList();

        if (myWorkouts.isEmpty) {
          return _buildEmptyMyWorkouts();
        }

        return RefreshIndicator(
          onRefresh: () async {
            setState(() {});
          },
          color: AppColors.primary,
          child: ListView.builder(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
            itemCount: myWorkouts.length,
            itemBuilder: (context, index) {
              final workout = myWorkouts[index];
              return Padding(
                padding: const EdgeInsets.only(bottom: 16),
                child: _MyWorkoutCard(
                  workout: workout,
                  onTap: () => _openWorkoutDetail(workout),
                  onEdit: () => _editWorkout(workout),
                  onDelete: () => _deleteWorkout(workout),
                ),
              );
            },
          ),
        );
      },
    );
  }

  Widget _buildEmptyMyWorkouts() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: AppColors.primary.withValues(alpha: 0.1),
              shape: BoxShape.circle,
            ),
            child: const Icon(
              Icons.add_circle_outline,
              size: 64,
              color: AppColors.primary,
            ),
          ),
          const SizedBox(height: 24),
          const Text(
            'Nenhum treino personalizado',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w600,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Crie treinos personalizados com\nseus exercícios favoritos',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 14,
              color: AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: _createNewWorkout,
            icon: const Icon(Icons.add),
            label: const Text('Criar Primeiro Treino'),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.primary,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _createNewWorkout() {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => const CreateWorkoutPage(),
      ),
    ).then((_) => setState(() {}));
  }

  void _editWorkout(WorkoutModel workout) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Funcionalidade de edição em desenvolvimento'),
        backgroundColor: AppColors.primary,
      ),
    );
  }

  Future<void> _deleteWorkout(WorkoutModel workout) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppColors.surface,
        title: const Text('Excluir Treino', style: TextStyle(color: Colors.white)),
        content: Text(
          'Tem certeza que deseja excluir "${workout.name}"?\nEsta ação não pode ser desfeita.',
          style: const TextStyle(color: AppColors.textSecondary),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancelar'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            style: TextButton.styleFrom(foregroundColor: AppColors.error),
            child: const Text('Excluir'),
          ),
        ],
      ),
    );

    if (confirmed != true) return;

    try {
      await ApiService.delete('/workouts/${workout.id}/delete/');
      
      if (!mounted) return;
      
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Treino "${workout.name}" excluído'),
          backgroundColor: AppColors.primary,
        ),
      );
      
      setState(() {});
      
    } catch (e) {
      if (!mounted) return;
      
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Erro ao excluir: $e'),
          backgroundColor: AppColors.error,
        ),
      );
    }
  }

  // ✅ ABA EXERCÍCIOS CORRIGIDA - SÓ VISUALIZAÇÃO
  Widget _buildExercisesTab() {
    if (_isLoadingExercises) {
      return const Center(
        child: CircularProgressIndicator(color: AppColors.primary),
      );
    }

    final exercises = _getFilteredExercises(_allExercises);
    
    if (exercises.isEmpty) {
      return _buildEmptyState(
        icon: Icons.search_off,
        title: 'Nenhum exercício encontrado',
        subtitle: 'Tente ajustar os filtros ou busca',
      );
    }

    return RefreshIndicator(
      onRefresh: _loadExercisesFromAPI,
      color: AppColors.primary,
      child: ListView.builder(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        itemCount: exercises.length,
        itemBuilder: (context, index) {
          return Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: _ExerciseListCard(
              exercise: exercises[index],
              onTap: () => _openExerciseDetail(exercises[index]),
            ),
          );
        },
      ),
    );
  }

  Widget _buildEmptyState({
    IconData? icon,
    String? title,
    String? subtitle,
  }) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            icon ?? Icons.search_off,
            size: 64,
            color: AppColors.textHint,
          ),
          const SizedBox(height: 16),
          Text(
            title ?? 'Nenhum treino encontrado',
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 8),
          Text(
            subtitle ?? 'Tente ajustar os filtros ou busca',
            textAlign: TextAlign.center,
            style: const TextStyle(color: AppColors.textSecondary),
          ),
        ],
      ),
    );
  }

  List<WorkoutModel> _getRecommendedWorkouts() {
    return _allWorkouts.where((workout) => workout.isRecommended).toList();
  }

  List<WorkoutModel> _getFilteredWorkouts(List<WorkoutModel> workouts) {
    return workouts.where((workout) {
      final matchesSearch = _searchQuery.isEmpty || 
          workout.name.toLowerCase().contains(_searchQuery.toLowerCase()) ||
          workout.description.toLowerCase().contains(_searchQuery.toLowerCase());
      
      final matchesCategory = _selectedCategory == 'Todos' || 
          workout.category == _selectedCategory;
      
      final matchesDifficulty = _selectedDifficulty == 'Todos' || 
          workout.difficulty == _selectedDifficulty;
      
      return matchesSearch && matchesCategory && matchesDifficulty;
    }).toList();
  }

  List<ExerciseModel> _getFilteredExercises(List<ExerciseModel> exercises) {
    return exercises.where((exercise) {
      final matchesSearch = _searchQuery.isEmpty || 
          exercise.name.toLowerCase().contains(_searchQuery.toLowerCase()) ||
          exercise.description.toLowerCase().contains(_searchQuery.toLowerCase());
      
      final matchesMuscleGroup = _selectedMuscleGroup == 'Todos' || 
          exercise.muscleGroup == _selectedMuscleGroup;
      
      final matchesDifficulty = _selectedDifficulty == 'Todos' || 
          exercise.difficulty == _selectedDifficulty;
      
      return matchesSearch && matchesMuscleGroup && matchesDifficulty;
    }).toList();
  }

  void _openWorkoutDetail(WorkoutModel workout) {
    print('🎯 Navegando para treino ID: ${workout.id} - ${workout.name}');
    
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => WorkoutDetailPage(workout: workout),
      ),
    );
  }

  // ✅ MÉTODO CORRIGIDO - Abre exercício para visualização
  void _openExerciseDetail(ExerciseModel exercise) {
    print('🎯 Abrindo exercício em PREVIEW MODE');
    print('   Exercise: ${exercise.name}');
    print('   isPreviewMode: true');
    
    AppRouter.goToExerciseExecution(
      exercise: exercise,
      totalExercises: 1,
      currentExerciseIndex: 1,
      allExercises: [exercise],
      initialWorkoutSeconds: 0,
      isFullWorkout: false,
      isPreviewMode: true, // ✅ CRÍTICO: Ativa modo visualização
    );
  }
}

// Widgets auxiliares

class _FilterDropdown extends StatelessWidget {
  final String label;
  final String value;
  final List<String> items;
  final ValueChanged<String?> onChanged;

  const _FilterDropdown({
    required this.label,
    required this.value,
    required this.items,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.card),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String>(
          value: value,
          isExpanded: true,
          icon: const Icon(Icons.keyboard_arrow_down, color: AppColors.primary),
          dropdownColor: AppColors.surface,
          items: items.map((item) {
            return DropdownMenuItem<String>(
              value: item,
              child: Text(item, style: const TextStyle(fontSize: 14)),
            );
          }).toList(),
          onChanged: onChanged,
        ),
      ),
    );
  }
}

class WorkoutCard extends StatelessWidget {
  final WorkoutModel workout;
  final VoidCallback onTap;
  final bool isRecommended;

  const WorkoutCard({
    super.key,
    required this.workout,
    required this.onTap,
    this.isRecommended = false,
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
            color: isRecommended ? AppColors.primary.withValues(alpha: 0.3) : AppColors.card,
            width: isRecommended ? 1 : 0.5,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              workout.name,
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: AppColors.textPrimary,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              workout.description,
              style: const TextStyle(
                fontSize: 14,
                color: AppColors.textSecondary,
              ),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                _buildChip(Icons.schedule, '${workout.duration} min'),
                const SizedBox(width: 8),
                _buildChip(Icons.local_fire_department, '${workout.calories} kcal'),
                const SizedBox(width: 8),
                _buildChip(Icons.bar_chart, workout.difficulty),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildChip(IconData icon, String label) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
         Icon(icon, size: 14, color: AppColors.primary),
          const SizedBox(width: 4),
          Text(
            label,
            style: const TextStyle(
              fontSize: 12,
              color: AppColors.textSecondary,
            ),
          ),
        ],
      ),
    );
  }
}

// Widget para card de treino personalizado
class _MyWorkoutCard extends StatelessWidget {
  final WorkoutModel workout;
  final VoidCallback onTap;
  final VoidCallback onEdit;
  final VoidCallback onDelete;

  const _MyWorkoutCard({
    required this.workout,
    required this.onTap,
    required this.onEdit,
    required this.onDelete,
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
            color: AppColors.primary.withValues(alpha: 0.3),
            width: 1,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: AppColors.primary.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(
                    Icons.star,
                    size: 16,
                    color: AppColors.primary,
                  ),
                ),
                const SizedBox(width: 8),
                const Text(
                  'MEU TREINO',
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                    color: AppColors.primary,
                    letterSpacing: 0.5,
                  ),
                ),
                const Spacer(),
                PopupMenuButton<String>(
                  icon: const Icon(Icons.more_vert, color: AppColors.textSecondary),
                  color: AppColors.surface,
                  onSelected: (value) {
                    if (value == 'edit') onEdit();
                    if (value == 'delete') onDelete();
                  },
                  itemBuilder: (context) => [
                    const PopupMenuItem(
                      value: 'edit',
                      child: Row(
                        children: [
                          Icon(Icons.edit, size: 18, color: AppColors.primary),
                          SizedBox(width: 8),
                          Text('Editar'),
                        ],
                      ),
                    ),
                    const PopupMenuItem(
                      value: 'delete',
                      child: Row(
                        children: [
                          Icon(Icons.delete, size: 18, color: AppColors.error),
                          SizedBox(width: 8),
                          Text('Excluir', style: TextStyle(color: AppColors.error)),
                        ],
                      ),
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              workout.name,
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: AppColors.textPrimary,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              workout.description,
              style: const TextStyle(
                fontSize: 14,
                color: AppColors.textSecondary,
              ),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                _buildChip(Icons.schedule, '${workout.duration} min'),
                const SizedBox(width: 8),
                _buildChip(Icons.fitness_center, '${workout.exercises} ex'),
                const SizedBox(width: 8),
                _buildChip(Icons.bar_chart, workout.difficulty),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildChip(IconData icon, String label) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: AppColors.primary),
          const SizedBox(width: 4),
          Text(
            label,
            style: const TextStyle(
              fontSize: 12,
              color: AppColors.textSecondary,
            ),
          ),
        ],
      ),
    );
  }
}

// ✅ WIDGET CORRIGIDO - Card de exercício sem botão de adicionar
class _ExerciseListCard extends StatelessWidget {
  final ExerciseModel exercise;
  final VoidCallback onTap;

  const _ExerciseListCard({
    required this.exercise,
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
          border: Border.all(color: AppColors.card, width: 0.5),
        ),
        child: Row(
          children: [
            // Ícone de grupo muscular
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.primary.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Icon(
                Icons.fitness_center,
                color: AppColors.primary,
                size: 24,
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
                    exercise.description,
                    style: const TextStyle(
                      fontSize: 12,
                      color: AppColors.textSecondary,
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      // Badge de grupo muscular
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: AppColors.primary.withValues(alpha: 0.2),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          exercise.muscleGroup,
                          style: const TextStyle(
                            fontSize: 10,
                            color: AppColors.primary,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      // Badge de equipamento
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: AppColors.card,
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Icon(
                              Icons.settings,
                              size: 10,
                              color: AppColors.textSecondary,
                            ),
                            const SizedBox(width: 4),
                            Text(
                              exercise.equipment,
                              style: const TextStyle(
                                fontSize: 10,
                                color: AppColors.textSecondary,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            
            const SizedBox(width: 12),
            
            // Ícone de "ver mais"
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

// Modelos
class WorkoutModel {
  final int id;
  final String name;
  final String description;
  final int duration;
  final int exercises;
  final String difficulty;
  final String category;
  final int calories;
  final String? imageUrl;
  final bool isRecommended;

  WorkoutModel({
    required this.id,
    required this.name,
    required this.description,
    required this.duration,
    required this.exercises,
    required this.difficulty,
    required this.category,
    required this.calories,
    this.imageUrl,
    this.isRecommended = false,
  });
}


