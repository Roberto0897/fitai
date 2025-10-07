import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'core/theme/app_theme.dart';
import 'core/injection/injection.dart';
import 'core/router/app_router.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'firebase_options.dart';
import 'package:provider/provider.dart';
import 'providers/user_profile_provider.dart';
import 'providers/reports_provider.dart';
import 'package:fitai_app/service/chat_service.dart';
import 'providers/dashboard_provider.dart';


void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );
  
  FirebaseFirestore.instance.settings = const Settings(
    persistenceEnabled: true,
    cacheSizeBytes: Settings.CACHE_SIZE_UNLIMITED,
  );

  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);
  
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    statusBarIconBrightness: Brightness.light,
    systemNavigationBarColor: AppColors.background,
    systemNavigationBarIconBrightness: Brightness.light,
  ));
  
  try {
    await Injection.init();
    debugPrint('FITAI: Dependências inicializadas com sucesso');
  } catch (e) {
    debugPrint('FITAI: Erro ao inicializar dependências: $e');
  }
  
  debugPrint('FITAI: Aplicativo iniciando...');
  
  runApp(const FitAIApp());
}

class FitAIApp extends StatelessWidget {
  const FitAIApp({super.key});

  @override
  Widget build(BuildContext context) {
    // ADICIONAR MultiProvider aqui
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(
          create: (_) => UserProfileProvider(),
          lazy: false, // Carrega imediatamente
        ),
        ChangeNotifierProvider(
          create: (_) => ReportsProvider(), // ← ADICIONE ESTA LINHA
          lazy: false,
        ),
        ChangeNotifierProvider(
          create: (_) => ChatService(), // ← ADICIONE ESTA LINHA
          lazy: false,
        ),
         ChangeNotifierProvider(
          create: (_) => DashboardProvider(),
          lazy: false,
        ),
      ],
      child: MaterialApp.router(
        title: 'FITAI - Personal Trainer Inteligente',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.darkTheme,
        routerConfig: AppRouter.router,
      ),
    );
  }
}