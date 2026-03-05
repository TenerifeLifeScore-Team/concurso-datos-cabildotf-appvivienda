import 'package:flutter/material.dart';

class AppColors {
  // Colores principales de marca
  static const Color primary = Color(0xFF3c7ce3);
  static const Color secondary = Color(0xFF32C850);
  static const Color terciary = Color(0xFF5ac7fe); 
  static const Color cuaternary = Color(0xFF1413bf); 
  
  // Gradiente del LifeScore (Extraídos de tu utils.py)
  static const Color scoreCritical = Color(0xFFFF3C3C); // Rojo [255, 60, 60]
  static const Color scoreLow = Color(0xFFFFA000);      // Naranja [255, 160, 0]
  static const Color scoreMedium = Color(0xFFFFDC00);   // Amarillo [255, 220, 0]
  static const Color scoreHigh = Color(0xFF32C850);     // Verde [50, 200, 80]
  static const Color scoreTop = Color(0xFF006EFF);      // Azul [0, 110, 255]

  // Colores de UI neutros
  static const Color background = Color(0xFFF5F7FA);
  static const Color surface = Colors.white;
  static const Color textPrimary = Color(0xFF1A1A1A);
  static const Color textSecondary = Color.fromARGB(255, 200, 200, 200);
}