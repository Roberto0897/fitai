import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'core/theme/app_theme.dart';
import 'core/injection/injection.dart';
import 'core/router/app_router.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Configuração da orientação da tela
  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);
  
  // Configuração da status bar
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    statusBarIconBrightness: Brightness.light,
    systemNavigationBarColor: AppColors.background,
    systemNavigationBarIconBrightness: Brightness.light,
  ));
  
  // Inicialização do sistema de injeção de dependências
  try {
    await Injection.init();
    debugPrint('✅ FITAI: Dependências inicializadas com sucesso');
  } catch (e) {
    debugPrint('❌ FITAI: Erro ao inicializar dependências: $e');
  }
  
  // Log de inicialização
  debugPrint('🚀 FITAI: Aplicativo iniciando...');
  
  runApp(const FitAIApp());
}

class FitAIApp extends StatelessWidget {
  const FitAIApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'FITAI - Personal Trainer Inteligente',
      debugShowCheckedModeBanner: false,
      
      // Tema da aplicação
      theme: AppTheme.darkTheme,
      
      // Sistema de roteamento
      routerConfig: AppRouter.router,
    );
  }
}