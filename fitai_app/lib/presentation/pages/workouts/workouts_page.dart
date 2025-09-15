import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/router/app_router.dart';

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

  final List<String> _categories = ['Todos', 'Força', 'Cardio', 'Flexibilidade', 'HIIT', 'Yoga'];
  final List<String> _difficulties = ['Todos', 'Iniciante', 'Intermediário', 'Avançado'];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
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
            // Header com busca
            _buildHeader(),
            
            // Tabs
            _buildTabs(),
            
            // Filtros
            _buildFilters(),
            
            // Lista de treinos
            Expanded(
              child: TabBarView(
                controller: _tabController,
                children: [
                  _buildAllWorkouts(),
                  _buildRecommendedWorkouts(),
                  _buildMyWorkouts(),
                ],
              ),
            ),
          ],
        ),
      ),
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
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: AppColors.surface,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(Icons.filter_list, color: AppColors.primary),
              ),
            ],
          ),
          const SizedBox(height: 16),
          
          // Barra de busca
          Container(
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(16),
            ),
            child: TextField(
              onChanged: (value) => setState(() => _searchQuery = value),
              decoration: const InputDecoration(
                hintText: 'Buscar treinos...',
                prefixIcon: Icon(Icons.search, color: AppColors.textHint),
                border: InputBorder.none,
                contentPadding: EdgeInsets.symmetric(horizontal: 20, vertical: 16),
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
        tabs: const [
          Tab(text: 'Todos'),
          Tab(text: 'Recomendados'),
          Tab(text: 'Meus Treinos'),
        ],
      ),
    );
  }

  Widget _buildFilters() {
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
    final workouts = _getFilteredWorkouts(_getAllWorkouts());
    
    if (workouts.isEmpty) {
      return _buildEmptyState();
    }

    return ListView.builder(
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
    );
  }

  Widget _buildRecommendedWorkouts() {
    final workouts = _getFilteredWorkouts(_getRecommendedWorkouts());
    
    if (workouts.isEmpty) {
      return _buildEmptyState();
    }

    return ListView.builder(
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
    );
  }

  Widget _buildMyWorkouts() {
    return const Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.fitness_center, size: 64, color: AppColors.textHint),
          SizedBox(height: 16),
          Text(
            'Seus treinos personalizados',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
          ),
          SizedBox(height: 8),
          Text(
            'Crie treinos personalizados ou\nsalve seus favoritos aqui',
            textAlign: TextAlign.center,
            style: TextStyle(color: AppColors.textSecondary),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return const Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.search_off, size: 64, color: AppColors.textHint),
          SizedBox(height: 16),
          Text(
            'Nenhum treino encontrado',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
          ),
          SizedBox(height: 8),
          Text(
            'Tente ajustar os filtros ou busca',
            style: TextStyle(color: AppColors.textSecondary),
          ),
        ],
      ),
    );
  }

  List<WorkoutModel> _getAllWorkouts() {
    return [
      WorkoutModel(
        id: 1,
        name: 'Full Body - Iniciante',
        description: 'Treino completo para iniciantes focado em todos os grupos musculares',
        duration: 45,
        exercises: 8,
        difficulty: 'Iniciante',
        category: 'Força',
        calories: 280,
        imageUrl: null,
        isRecommended: true,
      ),
      WorkoutModel(
        id: 2,
        name: 'Cardio HIIT Intenso',
        description: 'Treino intervalado de alta intensidade para queimar gordura',
        duration: 30,
        exercises: 6,
        difficulty: 'Intermediário',
        category: 'HIIT',
        calories: 350,
        imageUrl: null,
        isRecommended: true,
      ),
      WorkoutModel(
        id: 3,
        name: 'Força - Peito e Tríceps',
        description: 'Treino focado em peito e tríceps para desenvolvimento muscular',
        duration: 50,
        exercises: 10,
        difficulty: 'Avançado',
        category: 'Força',
        calories: 320,
        imageUrl: null,
      ),
      WorkoutModel(
        id: 4,
        name: 'Yoga Matinal',
        description: 'Sequência suave de yoga para começar o dia com energia',
        duration: 25,
        exercises: 12,
        difficulty: 'Iniciante',
        category: 'Yoga',
        calories: 120,
        imageUrl: null,
      ),
      WorkoutModel(
        id: 5,
        name: 'Core e Abdomen',
        description: 'Fortalecimento do core e abdominais para estabilidade',
        duration: 35,
        exercises: 8,
        difficulty: 'Intermediário',
        category: 'Força',
        calories: 200,
        imageUrl: null,
      ),
      WorkoutModel(
        id: 6,
        name: 'Flexibilidade Total',
        description: 'Alongamento completo para melhorar flexibilidade',
        duration: 40,
        exercises: 15,
        difficulty: 'Iniciante',
        category: 'Flexibilidade',
        calories: 100,
        imageUrl: null,
      ),
    ];
  }

  List<WorkoutModel> _getRecommendedWorkouts() {
    return _getAllWorkouts().where((workout) => workout.isRecommended).toList();
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

  void _openWorkoutDetail(WorkoutModel workout) {
    // TODO: Navegar para tela de detalhes
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Abrindo detalhes do treino: ${workout.name}'),
        backgroundColor: AppColors.primary,
      ),
    );
  }
}

// Widget para dropdown de filtros
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
              child: Text(
                item,
                style: const TextStyle(fontSize: 14),
              ),
            );
          }).toList(),
          onChanged: onChanged,
        ),
      ),
    );
  }
}

// Widget para card de treino
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
            Row(
              children: [
                // Thumbnail do treino
                Container(
                  width: 60,
                  height: 60,
                  decoration: BoxDecoration(
                    color: _getCategoryColor(workout.category).withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(
                    _getCategoryIcon(workout.category),
                    color: _getCategoryColor(workout.category),
                    size: 24,
                  ),
                ),
                const SizedBox(width: 16),
                
                // Informações principais
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              workout.name,
                              style: const TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                          if (isRecommended)
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(
                                color: AppColors.primary.withValues(alpha: 0.1),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: const Text(
                                'Recomendado',
                                style: TextStyle(
                                  fontSize: 10,
                                  color: AppColors.primary,
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            ),
                        ],
                      ),
                      const SizedBox(height: 4),
                      Text(
                        workout.description,
                        style: const TextStyle(
                          fontSize: 12,
                          color: AppColors.textSecondary,
                        ),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ),
                ),
              ],
            ),
            
            const SizedBox(height: 16),
            
            // Métricas do treino
            Row(
              children: [
                _MetricChip(
                  icon: Icons.schedule,
                  label: '${workout.duration} min',
                ),
                const SizedBox(width: 8),
                _MetricChip(
                  icon: Icons.fitness_center,
                  label: '${workout.exercises} exercícios',
                ),
                const SizedBox(width: 8),
                _MetricChip(
                  icon: Icons.local_fire_department,
                  label: '${workout.calories} cal',
                ),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: _getDifficultyColor(workout.difficulty).withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    workout.difficulty,
                    style: TextStyle(
                      fontSize: 10,
                      color: _getDifficultyColor(workout.difficulty),
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

  IconData _getCategoryIcon(String category) {
    switch (category.toLowerCase()) {
      case 'força':
        return Icons.fitness_center;
      case 'cardio':
        return Icons.directions_run;
      case 'hiit':
        return Icons.timer;
      case 'yoga':
        return Icons.self_improvement;
      case 'flexibilidade':
        return Icons.accessibility_new;
      default:
        return Icons.sports_gymnastics;
    }
  }

  Color _getCategoryColor(String category) {
    switch (category.toLowerCase()) {
      case 'força':
        return Colors.red;
      case 'cardio':
        return Colors.blue;
      case 'hiit':
        return Colors.orange;
      case 'yoga':
        return Colors.purple;
      case 'flexibilidade':
        return Colors.green;
      default:
        return AppColors.primary;
    }
  }

  Color _getDifficultyColor(String difficulty) {
    switch (difficulty.toLowerCase()) {
      case 'iniciante':
        return AppColors.success;
      case 'intermediário':
        return AppColors.warning;
      case 'avançado':
        return AppColors.error;
      default:
        return AppColors.primary;
    }
  }
}

// Widget para chips de métricas
class _MetricChip extends StatelessWidget {
  final IconData icon;
  final String label;

  const _MetricChip({required this.icon, required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 12, color: AppColors.textSecondary),
          const SizedBox(width: 4),
          Text(
            label,
            style: const TextStyle(
              fontSize: 10,
              color: AppColors.textSecondary,
            ),
          ),
        ],
      ),
    );
  }
}

// Model para os dados do treino
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