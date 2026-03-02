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
  Future<Map<String, Map<String, List<ConfigItem>>>> getCategories() async {
    try {
      final url = Uri.parse('$_baseUrl/config');
      print("📡 Llamando a: $url");
      
      final response = await http.get(url);

      if (response.statusCode == 200) {
        final Map<String, dynamic> decodedData = json.decode(utf8.decode(response.bodyBytes));
        final Map<String, Map<String, List<ConfigItem>>> result = {};
        
        decodedData.forEach((macroKey, gruposMap) {
          final Map<String, List<ConfigItem>> gruposTyped = {};
          
          (gruposMap as Map<String, dynamic>).forEach((grupoKey, itemsList) {
            // Mapeamos la lista de JSONs a lista de objetos ConfigItem
            final List<ConfigItem> items = (itemsList as List)
                .map((item) => ConfigItem.fromJson(item))
                .toList();
            gruposTyped[grupoKey] = items;
          });
          
          result[macroKey] = gruposTyped;
        });
        
        return result;
      } else {
        throw Exception('Error del servidor: ${response.statusCode}');
      }
    } catch (e) {
      print("❌ Error de conexión: $e");
      rethrow; 
    }
  }
  /// Envía las preferencias y recibe la lista de [hex_id, score, color]
  Future<List<Map<String, dynamic>>> calculateScores(
    Map<String, double> sliders, 
    Map<String, bool> checks
  ) async {
    try {
      final url = Uri.parse('$_baseUrl/calculate');
      final response = await http.post(
        url,
        headers: {"Content-Type": "application/json"},
        body: json.encode({
          "sliders": sliders,
          "checks": checks,
        }),
      );

      if (response.statusCode == 200) {
        return List<Map<String, dynamic>>.from(json.decode(utf8.decode(response.bodyBytes)));
      } else {
        throw Exception('Error en el cálculo: ${response.statusCode}');
      }
    } catch (e) {
      print("❌ Error al calcular scores: $e");
      rethrow;
    }
  }
  Future<Map<String, dynamic>> calculatePointScore({
    required double lat,
    required double lon,
    required Map<String, double> sliders,
    required Map<String, bool> checks,
  }) async {
    try {
      final url = Uri.parse('$_baseUrl/calculate-point');
      final response = await http.post(
        url,
        headers: {"Content-Type": "application/json"},
        body: json.encode({
          "lat": lat,
          "lon": lon,
          "sliders": sliders,
          "checks": checks,
        }),
      );

      if (response.statusCode == 200) {
        return json.decode(utf8.decode(response.bodyBytes));
      } else {
        throw Exception('Error en el radar: ${response.statusCode}');
      }
    } catch (e) {
      print("❌ Error en calculatePointScore: $e");
      rethrow;
    }
  }
  
  // Nuevo método solo para pedir el texto a la IA
  Future<String> getIaExplanation({
    required double lat,
    required double lon,
    required Map<String, double> sliders,
    required Map<String, bool> checks,
  }) async {
    final response = await http.post(
      Uri.parse('$_baseUrl/explain-point'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        "sliders": sliders,
        "checks": checks,
        "lat": lat,
        "lon": lon,
      }),
    );

    if (response.statusCode == 200) {
      return json.decode(utf8.decode(response.bodyBytes))['resumen_ia'];
    } else {
      return "No se pudo conectar con el asesor virtual.";
    }
  }
}

class ConfigItem {
  final String label;
  final List<String> ids;

  ConfigItem({required this.label, required this.ids});

  factory ConfigItem.fromJson(Map<String, dynamic> json) {
    return ConfigItem(
      label: json['label'],
      ids: List<String>.from(json['ids']),
    );
  }
}

