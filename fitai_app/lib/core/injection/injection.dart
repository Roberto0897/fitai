import 'package:flutter/foundation.dart';

class Injection {
  static Future<void> init() async {
    // Por enquanto, apenas um placeholder
    // Vamos expandir isso nas próximas etapas
    await Future.delayed(const Duration(milliseconds: 100));
    debugPrint('✅ Sistema de injeção inicializado');
  }
}