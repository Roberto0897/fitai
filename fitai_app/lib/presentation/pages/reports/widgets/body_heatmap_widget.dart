// Widget de Cards Redondos de Grupos Musculares - DESIGN PREMIUM
// Localização: lib/features/dashboard/reports/widgets/muscle_group_cards_widget.dart

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class MuscleGroupCardsWidget extends StatelessWidget {
  final Map<String, int> muscleGroupFrequency;

  const MuscleGroupCardsWidget({
    Key? key,
    required this.muscleGroupFrequency,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    if (muscleGroupFrequency.isEmpty) {
      return _buildEmptyState();
    }

    final sortedGroups = muscleGroupFrequency.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));

    final maxFrequency = sortedGroups.first.value;

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF2A2A2A),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF00BCD4), width: 1.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Grupos Musculares',
                style: GoogleFonts.jockeyOne(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.w500,
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: const Color(0xFF00BCD4).withOpacity(0.2),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  '${sortedGroups.length} grupos',
                  style: const TextStyle(
                    color: Color(0xFF00BCD4),
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          
          // Grid de Cards Redondos
          LayoutBuilder(
            builder: (context, constraints) {
              final cardWidth = (constraints.maxWidth - 24) / 3; // 3 colunas
              
              return Wrap(
                spacing: 12,
                runSpacing: 16,
                children: sortedGroups.map((entry) {
                  final percentage = (entry.value / maxFrequency * 100).toInt();
                  final muscleData = _getMuscleData(entry.key);
                  final isTopGroup = entry.value == maxFrequency;
                  
                  return SizedBox(
                    width: cardWidth,
                    child: _buildRoundMuscleCard(
                      name: entry.key,
                      count: entry.value,
                      percentage: percentage,
                      emoji: muscleData['emoji']!,
                      color: muscleData['color']!,
                      isTopGroup: isTopGroup,
                    ),
                  );
                }).toList(),
              );
            },
          ),
        ],
      ),
    );
  }

  Widget _buildRoundMuscleCard({
    required String name,
    required int count,
    required int percentage,
    required String emoji,
    required Color color,
    required bool isTopGroup,
  }) {
    return Column(
      children: [
        // Círculo com emoji e progresso
        Stack(
          alignment: Alignment.center,
          children: [
            // Anel de progresso
            SizedBox(
              width: 85,
              height: 85,
              child: CircularProgressIndicator(
                value: percentage / 100,
                strokeWidth: 6,
                backgroundColor: const Color(0xFF404040),
                valueColor: AlwaysStoppedAnimation<Color>(color),
              ),
            ),
            // Círculo interno com emoji
            Container(
              width: 70,
              height: 70,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: color.withOpacity(0.15),
                border: Border.all(
                  color: isTopGroup ? const Color(0xFFFFD700) : color.withOpacity(0.3),
                  width: isTopGroup ? 3 : 2,
                ),
              ),
              child: Center(
                child: Text(
                  emoji,
                  style: const TextStyle(fontSize: 32),
                ),
              ),
            ),
            // Badge de top
            if (isTopGroup)
              Positioned(
                top: 0,
                right: 0,
                child: Container(
                  padding: const EdgeInsets.all(4),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFFD700),
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFFFFD700).withOpacity(0.5),
                        blurRadius: 8,
                        spreadRadius: 2,
                      ),
                    ],
                  ),
                  child: const Text(
                    '👑',
                    style: TextStyle(fontSize: 12),
                  ),
                ),
              ),
          ],
        ),
        const SizedBox(height: 8),
        
        // Nome do músculo
        Text(
          name,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 12,
            fontWeight: FontWeight.w600,
          ),
          textAlign: TextAlign.center,
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
        ),
        const SizedBox(height: 4),
        
        // Contador
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
          decoration: BoxDecoration(
            color: color.withOpacity(0.2),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Text(
            '${count}x',
            style: TextStyle(
              color: color,
              fontSize: 13,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildEmptyState() {
    return Container(
      padding: const EdgeInsets.all(40),
      decoration: BoxDecoration(
        color: const Color(0xFF2A2A2A),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF00BCD4), width: 1.5),
      ),
      child: Center(
        child: Column(
          children: [
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: const Color(0xFF404040).withOpacity(0.3),
              ),
              child: const Center(
                child: Text(
                  '💪',
                  style: TextStyle(fontSize: 40),
                ),
              ),
            ),
            const SizedBox(height: 16),
            Text(
              'Nenhum grupo muscular',
              style: GoogleFonts.jockeyOne(
                color: const Color(0xFF9E9E9E),
                fontSize: 16,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Complete treinos para ver\nseus grupos trabalhados',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: const Color(0xFF666666),
                fontSize: 12,
              ),
            ),
          ],
        ),
      ),
    );
  }

  // 🎨 DADOS PERSONALIZADOS PARA CADA GRUPO MUSCULAR
  Map<String, dynamic> _getMuscleData(String muscleName) {
    final name = muscleName.toLowerCase();
    
    // PEITO
    if (name.contains('peito') || name.contains('peitoral') || name.contains('chest')) {
      return {
        'emoji': '💪',
        'color': const Color(0xFFE91E63), // Rosa/Vermelho
      };
    }
    
    // COSTAS
    if (name.contains('costa') || name.contains('dorsal') || name.contains('lat') || name.contains('back')) {
      return {
        'emoji': '🦸',
        'color': const Color(0xFF2196F3), // Azul
      };
    }
    
    // PERNAS / QUADRÍCEPS
    if (name.contains('perna') || name.contains('coxa') || name.contains('quadr') || name.contains('leg')) {
      return {
        'emoji': '🦵',
        'color': const Color(0xFF4CAF50), // Verde
      };
    }
    
    // OMBROS
    if (name.contains('ombro') || name.contains('deltoid') || name.contains('shoulder')) {
      return {
        'emoji': '🏋️',
        'color': const Color(0xFFFF9800), // Laranja
      };
    }
    
    // BÍCEPS
    if (name.contains('bíceps') || name.contains('biceps')) {
      return {
        'emoji': '💪',
        'color': const Color(0xFF9C27B0), // Roxo
      };
    }
    
    // TRÍCEPS
    if (name.contains('tríceps') || name.contains('triceps')) {
      return {
        'emoji': '🔥',
        'color': const Color(0xFFFF5722), // Vermelho/Laranja
      };
    }
    
    // ABDÔMEN
    if (name.contains('abdômen') || name.contains('abdominal') || name.contains('core') || name.contains('abs')) {
      return {
        'emoji': '🎯',
        'color': const Color(0xFFFFEB3B), // Amarelo
      };
    }
    
    // PANTURRILHA
    if (name.contains('panturrilha') || name.contains('calf')) {
      return {
        'emoji': '🚶',
        'color': const Color(0xFF8BC34A), // Verde claro
      };
    }
    
    // GLÚTEOS
    if (name.contains('glúteo') || name.contains('gluteo') || name.contains('glute')) {
      return {
        'emoji': '🍑',
        'color': const Color(0xFFE91E63), // Rosa
      };
    }
    
    // TRAPÉZIO
    if (name.contains('trapézio') || name.contains('trap')) {
      return {
        'emoji': '⛰️',
        'color': const Color(0xFF607D8B), // Cinza azulado
      };
    }
    
    // ANTEBRAÇO
    if (name.contains('antebraço') || name.contains('forearm')) {
      return {
        'emoji': '🤜',
        'color': const Color(0xFF795548), // Marrom
      };
    }
    
    // LOMBAR
    if (name.contains('lombar') || name.contains('lower back')) {
      return {
        'emoji': '🧘',
        'color': const Color(0xFF00BCD4), // Ciano
      };
    }
    
    // CARDIO / AERÓBICO
    if (name.contains('cardio') || name.contains('aeróbico') || name.contains('aerobic')) {
      return {
        'emoji': '❤️',
        'color': const Color(0xFFF44336), // Vermelho
      };
    }
    
    // CORPO INTEIRO / FULL BODY
    if (name.contains('corpo') || name.contains('inteiro') || name.contains('full') || name.contains('total')) {
      return {
        'emoji': '🧍',
        'color': const Color(0xFF00BCD4), // Ciano
      };
    }
    
    // FLEXIBILIDADE / ALONGAMENTO
    if (name.contains('flex') || name.contains('along') || name.contains('stretch')) {
      return {
        'emoji': '🧘‍♀️',
        'color': const Color(0xFF9C27B0), // Roxo
      };
    }
    
    // DEFAULT (Genérico)
    return {
      'emoji': '💪',
      'color': const Color(0xFF00BCD4), // Ciano padrão
    };
  }
}