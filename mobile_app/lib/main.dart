import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'config/theme/app_theme.dart';
import 'screens/home_screen.dart';
import 'screens/onboarding_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  final prefs = await SharedPreferences.getInstance();
  final bool haVistoOnboarding = prefs.getBool('ha_visto_onboarding') ?? false;

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
      
      theme: AppTheme.light,
      
      home: mostrarOnboarding ? const OnboardingScreen() : const HomeScreen()
    );
  }
}