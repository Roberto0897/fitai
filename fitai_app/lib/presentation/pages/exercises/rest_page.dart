import 'dart:async';
import 'package:flutter/material.dart';

// Importa suas cores reais (AppColors)
import '../../../core/theme/app_theme.dart'; 

class RestPage extends StatefulWidget {
  // Função que será chamada para fechar esta tela e voltar ao exercício
  final VoidCallback onRestComplete;
  
  const RestPage({
    super.key,
    required this.onRestComplete,
  });

  @override
  State<RestPage> createState() => _RestPageState();
}

class _RestPageState extends State<RestPage> {
  // Tempo inicial de descanso em segundos (ex: 90s)
  int _secondsRemaining = 90;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _startTimer();
  }

  void _startTimer() {
    _timer?.cancel(); 
    
    // Inicia a contagem regressiva a cada segundo
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (!mounted) {
        _timer?.cancel();
        return;
      }
      
      if (_secondsRemaining > 0) {
        setState(() {
          _secondsRemaining--;
        });
      } else {
        // Tempo esgotado
        _timer?.cancel();
        widget.onRestComplete(); // Fecha a tela de descanso
      }
    });
  }

  void _addTime() {
    if (!mounted) return;
    setState(() {
      // Adiciona 30 segundos
      _secondsRemaining += 30; 
    });
  }

  void _skipRest() {
    _timer?.cancel();
    widget.onRestComplete(); // Fecha a tela de descanso imediatamente
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }
/*
  @override
  Widget build(BuildContext context) {
    // Usamos o AlertDialog para dar o efeito de modal centralizada
    return AlertDialog(
      // Fundo transparente para ver o conteúdo por trás (opcional, pode ser AppColors.background)
      backgroundColor: Colors.transparent, 
      contentPadding: EdgeInsets.zero,
      
      // Impede o fechamento acidental com o botão 'Voltar'
      content: WillPopScope(
        onWillPop: () async => false, 
        child: Container(
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            // Cor escura de fundo da modal, use AppColors.surface ou AppColors.background
            color: AppColors.surface, 
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppColors.primary, width: 2),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text(
                'Descanso',
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
              const SizedBox(height: 20),
              
              // Relógio
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.watch_later_outlined, size: 40, color: Colors.white),
                  const SizedBox(width: 10),
                  Text(
                    '${_secondsRemaining}s',
                    style: const TextStyle(
                      fontSize: 48,
                      fontWeight: FontWeight.w300,
                      color: Colors.white,
                    ),
                  ),
                ],
              ),
              
              const SizedBox(height: 20),
              
              // Botões de Ação
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  // Botão +30s
                  GestureDetector(
                    onTap: _addTime,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                      decoration: BoxDecoration(
                        // Cor de fundo leve e borda primária
                        color: AppColors.primary.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: AppColors.primary),
                      ),
                      child: const Text(
                        '+30s',
                        style: TextStyle(
                          color: AppColors.primary,
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 15),
                  
                  // Botão Pular/Avançar
                  GestureDetector(
                    onTap: _skipRest,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                      decoration: BoxDecoration(
                        color: AppColors.primary,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: const Row(
                        children: [
                          Text(
                            'PULAR',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          SizedBox(width: 8),
                          Icon(Icons.skip_next, color: Colors.white, size: 24),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }*/

  @override
Widget build(BuildContext context) {
  // Use um Scaffold com fundo transparente para que o PageRouteBuilder
  // possa exibir a tela anterior.
  return Scaffold(
    backgroundColor: Colors.transparent, 
    // Garante que não apareça barra de topo nem de navegação inferior
    body: Center(
      // Impede o fechamento acidental com o botão 'Voltar'
      child: WillPopScope(
        onWillPop: () async => false, 
        child: Container(
          // Largura máxima de um modal
          width: MediaQuery.of(context).size.width * 0.85, 
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            // Cor escura de fundo da modal
            color: AppColors.surface, 
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppColors.primary, width: 2),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text(
                'Descanso',
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
              const SizedBox(height: 20),
              
              // Relógio
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.watch_later_outlined, size: 40, color: Colors.white),
                  const SizedBox(width: 10),
                  Text(
                    '${_secondsRemaining}s',
                    style: const TextStyle(
                      fontSize: 48,
                      fontWeight: FontWeight.w300,
                      color: Colors.white,
                    ),
                  ),
                ],
              ),
              
              const SizedBox(height: 20),
              
              // Botões de Ação
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  // Botão +30s
                  GestureDetector(
                    onTap: _addTime,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                      decoration: BoxDecoration(
                        color: AppColors.primary.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: AppColors.primary),
                      ),
                      child: const Text(
                        '+30s',
                        style: TextStyle(
                          color: AppColors.primary,
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 15),
                  
                  // Botão Pular/Avançar
                  GestureDetector(
                    onTap: _skipRest,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                      decoration: BoxDecoration(
                        color: AppColors.primary,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: const Row(
                        children: [
                          Text(
                            'PULAR',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          SizedBox(width: 8),
                          Icon(Icons.skip_next, color: Colors.white, size: 24),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    ),
  );
}
}