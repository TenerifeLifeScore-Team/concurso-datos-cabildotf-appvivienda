import 'package:flutter/material.dart';
import 'config/theme/app_theme.dart';
import 'screens/home_screen.dart';

void main() {
  runApp(const TenerifeLifeScoreApp());
}

class TenerifeLifeScoreApp extends StatelessWidget {
  const TenerifeLifeScoreApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Tenerife LifeScore',
      debugShowCheckedModeBanner: false, // Quitamos la etiqueta "DEBUG"
      
      // Aquí aplicamos nuestro tema personalizado
      theme: AppTheme.light,
      
      // De momento, una pantalla temporal vacía
      home: const HomeScreen()
    );
  }
}