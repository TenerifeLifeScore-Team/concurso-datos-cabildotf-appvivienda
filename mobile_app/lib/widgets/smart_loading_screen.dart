import 'dart:async';
import 'package:flutter/material.dart';
import '../config/theme/app_colors.dart';

class SmartLoadingScreen extends StatefulWidget {
  const SmartLoadingScreen({super.key});

  @override
  State<SmartLoadingScreen> createState() => _SmartLoadingScreenState();
}

class _SmartLoadingScreenState extends State<SmartLoadingScreen> {
  bool _showDelayedMessage = false;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    // Arrancamos el cronómetro independiente de 5 segundos
    _timer = Timer(const Duration(seconds: 5), () {
      if (mounted) {
        setState(() => _showDelayedMessage = true);
      }
    });
  }

  @override
  void dispose() {
    // Si la pantalla de carga desaparece antes de los 5s, matamos el cronómetro
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Positioned.fill(
      child: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,      // Empieza arriba
            end: Alignment.bottomRight,     // Termina abajo
            colors: [
              AppColors.terciary,             // Color normal arriba
              AppColors.cuaternary, // Un toque de tu color principal abajo
            ],
          ),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // --- Logo o Icono ---
            Container(
              padding: const EdgeInsets.all(20),
              child: Image.asset(
                'assets/icons/icono_binario.png', 
                width: 150, // Ajusta el tamaño como veas que queda mejor
                height: 150,
                fit: BoxFit.contain,
                color: Colors.white
              ),
            ),
            const SizedBox(height: 0),
            
            // --- Título ---
            const Text(
              "Tenerife LifeScore", 
              style: TextStyle(color: Colors.white, fontSize: 28, fontWeight: FontWeight.bold, letterSpacing: 1.2),
            ),
            const SizedBox(height: 40),
            
            // --- Rueda de carga ---
            const CircularProgressIndicator(color: Colors.white),
            const SizedBox(height: 30),

            // --- MENSAJE DINÁMICO (Aparece a los 5 segundos) ---
            AnimatedOpacity(
              opacity: _showDelayedMessage ? 1.0 : 0.0, // Animación suave
              duration: const Duration(milliseconds: 800),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 40),
                child: Column(
                  children: [
                    const Text(
                      "Despertando al servidor...",
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.white),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      "Como usamos un servidor gratuito, el primer arranque del día tarda un poquito. ¡Gracias por la paciencia! 🦦",
                      textAlign: TextAlign.center,
                      style: TextStyle(color: AppColors.textSecondary, fontSize: 14, height: 1.4),
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
}