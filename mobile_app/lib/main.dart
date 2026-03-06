import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'config/theme/app_theme.dart';
import 'screens/home_screen.dart';
import 'screens/onboarding_screen.dart';

void main() async {
  // 1. Obligatorio avisar a Flutter de que vamos a leer memoria antes de arrancar
  WidgetsFlutterBinding.ensureInitialized();
  
  // 2. Leemos la memoria
  final prefs = await SharedPreferences.getInstance();
  final bool haVistoOnboarding = prefs.getBool('ha_visto_onboarding') ?? false;

  // 3. Arrancamos la app pasándole el dato
  runApp(TenerifeLifeScoreApp(mostrarOnboarding: !haVistoOnboarding));
}

class TenerifeLifeScoreApp extends StatelessWidget {
  final bool mostrarOnboarding;

  const TenerifeLifeScoreApp({super.key, required this.mostrarOnboarding});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Tenerife LifeScore',
      debugShowCheckedModeBanner: false, 
      
      // Aquí aplicamos tu tema personalizado
      theme: AppTheme.light,
      
      // Si no ha visto el onboarding, se lo enseñamos. Si ya lo vio, al Home directo.
      home: mostrarOnboarding ? const OnboardingScreen() : const HomeScreen()
    );
  }
}