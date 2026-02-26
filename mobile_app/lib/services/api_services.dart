import 'dart:convert';
// import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:flutter/foundation.dart';

class ApiService {
  // CONFIGURACIÓN DE LA IP
  // Si estás en el emulador de Android, tu PC es 10.0.2.2
  // Si estás en iOS, tu PC es localhost
  // Si pruebas en un móvil físico, necesitas la IP local de tu PC (ej: 192.168.1.XX)
  static String get _baseUrl {
    const String miIpDelPc = "10.58.85.131"; 
  
  if (kIsWeb) return "http://localhost:8000";
  return "http://$miIpDelPc:8000";
  }

  /// Pide la configuración de categorías al Backend Python
  Future<Map<String, List<String>>> getCategories() async {
    try {
      final url = Uri.parse('$_baseUrl/config');
      print("📡 Llamando a: $url");
      
      final response = await http.get(url);

      if (response.statusCode == 200) {
        // Decodificamos el JSON que nos manda Python
        // Python manda algo tipo: {"Salud": ["Farmacias", "Hospitales"], ...}
        final Map<String, dynamic> decodedData = json.decode(utf8.decode(response.bodyBytes));
        
        // Lo convertimos a un Mapa tipado para Dart
        final Map<String, List<String>> result = {};
        decodedData.forEach((key, value) {
          result[key] = List<String>.from(value);
        });
        
        return result;
      } else {
        throw Exception('Error del servidor: ${response.statusCode}');
      }
    } catch (e) {
      print("❌ Error de conexión: $e");
      // Devolvemos un error vacío o lanzamos la excepción para que la UI lo sepa
      rethrow; 
    }
  }
}