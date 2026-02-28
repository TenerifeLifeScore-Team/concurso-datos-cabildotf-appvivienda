import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show rootBundle; // Para cargar el GeoJSON local
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../config/theme/app_colors.dart';
import '../services/api_services.dart'; // Asegúrate que el nombre del archivo sea api_service.dart (singular)

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ApiService _apiService = ApiService();
  final MapController _mapController = MapController();

  bool isLoading = true;
  String? errorMessage;

  // --- DATOS DEL MAPA Y CONFIG ---
  Map<String, Map<String, List<ConfigItem>>>? arbolConfig;
  List<Polygon> poligonosADibujar = [];
  dynamic geojsonRaw; // El esqueleto del grid

  // --- ESTADO UI ---
  String? macroSeleccionada;
  Map<String, double> sliderValues = {}; 
  Map<String, bool> checkValues = {}; 

  @override
  void initState() {
    super.initState();
    _inicializarTodo();
  }

  // 1. CARGA INICIAL: API + GEOJSON LOCAL
  Future<void> _inicializarTodo() async {
    try {
      // A. Cargar Config de la API
      final datos = await _apiService.getCategories();

      // B. Cargar Esqueleto del Mapa desde Assets
      final String response = await rootBundle.loadString('assets/data/grid_tenerife.geojson');
      geojsonRaw = json.decode(response);

      // C. Inicializar valores de Sliders y Checks
      final Map<String, double> inicialesSliders = {};
      final Map<String, bool> inicialesChecks = {};
      datos.forEach((macro, grupos) {
        grupos.forEach((grupo, items) {
          inicialesSliders[grupo] = 3.0;
          for (var item in items) {
            for (var id in item.ids) {
              inicialesChecks[id] = true;
            }
          }
        });
      });

      final primerMacro = datos.keys.toList()..sort();

      setState(() {
        arbolConfig = datos;
        sliderValues = inicialesSliders;
        checkValues = inicialesChecks;
        macroSeleccionada = primerMacro.isNotEmpty ? primerMacro.first : null;
      });

      // D. Pintar el mapa por primera vez
      await _actualizarMapa();

    } catch (e) {
      setState(() => errorMessage = "Error al iniciar: $e");
    } finally {
      setState(() => isLoading = false);
    }
  }

  // 2. FUNCIÓN PARA RE-CALCULAR EL MAPA
  Future<void> _actualizarMapa() async {
    try {
      // Llamada al endpoint /calculate de Python
      final resultados = await _apiService.calculateScores(sliderValues, checkValues);

      // Creamos un mapa de ID -> Color para buscar rápido
      final Map<String, String> nuevosColores = {};
      for (var res in resultados) {
        nuevosColores[res['hex_id']] = res['color'];
      }

      List<Polygon> nuevosPoligonos = [];

      // Recorremos el esqueleto local y le asignamos el color que nos dio Python
      for (var feature in geojsonRaw['features']) {
        final id = feature['properties']['hex_id'];
        final colorHex = nuevosColores[id] ?? "#CCCCCC"; 
        
        // Convertir Hex String a Color de Flutter
        final color = Color(int.parse(colorHex.replaceFirst('#', '0xFF')));

        // Extraer coordenadas: GeoJSON [Lon, Lat] -> Flutter [Lat, Lon]
        List<LatLng> points = [];
        var coords = feature['geometry']['coordinates'][0];
        for (var p in coords) {
          points.add(LatLng(p[1].toDouble(), p[0].toDouble()));
        }

        nuevosPoligonos.add(Polygon(
          points: points,
          color: color.withOpacity(1.0), // Transparencia para ver calles debajo
          borderStrokeWidth: 0.5,
          borderColor: Colors.white24,
          isFilled: true,
        ));
      }

      setState(() {
        poligonosADibujar = nuevosPoligonos;
      });
    } catch (e) {
      print("Error actualizando mapa: $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      resizeToAvoidBottomInset: false,
      appBar: AppBar(
        title: const Text("Tenerife LifeScore 🇮🇨"),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              setState(() => isLoading = true);
              _inicializarTodo();
            },
          ),
        ],
      ),
      body: Stack(
        children: [
          // CAPA 1: FONDO SÓLIDO + HEXÁGONOS 🗺️
            FlutterMap(
              mapController: _mapController,
              options: const MapOptions(
                initialCenter: LatLng(28.1400, -16.5230),
                initialZoom: 9.4,
              ),
              children: [
                // Hemos quitado el TileLayer (el mapa de satélite/ArcGIS)
                PolygonLayer(polygons: poligonosADibujar),
              ],
            ),

          // Pantalla de carga bloqueante al inicio
          if (isLoading)
            Container(
              color: Colors.white70,
              child: const Center(child: CircularProgressIndicator()),
            ),

          // CAPA 2: PANEL DE CONFIGURACIÓN
          DraggableScrollableSheet(
            initialChildSize: 0.4,
            minChildSize: 0.15,
            maxChildSize: 0.75, // Ajustado para que no tape todo el mapa
            builder: (context, scrollController) {
              return Container(
                decoration: const BoxDecoration(
                  color: AppColors.surface,
                  borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
                  boxShadow: [BoxShadow(color: Colors.black26, blurRadius: 15)],
                ),
                child: Column(
                  children: [
                    Center(child: Container(width: 40, height: 5, margin: const EdgeInsets.symmetric(vertical: 10), decoration: BoxDecoration(color: Colors.grey[300], borderRadius: BorderRadius.circular(10)))),
                    Expanded(child: _buildPanelBody(scrollController)),
                  ],
                ),
              );
            },
          ),
        ],
      ),
    );
  }

  Widget _buildPanelBody(ScrollController scrollController) {
    if (errorMessage != null) return Center(child: Text(errorMessage!));
    if (arbolConfig == null) return const SizedBox();

    final macros = arbolConfig!.keys.toList()..sort();

    return ListView(
      controller: scrollController,
      padding: EdgeInsets.zero,
      children: [
        const Padding(
          padding: EdgeInsets.symmetric(horizontal: 20),
          child: Text("Personaliza tu búsqueda", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
        ),
        const SizedBox(height: 15),
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Row(
            children: macros.map((macro) {
              final isSelected = macro == macroSeleccionada;
              return Padding(
                padding: const EdgeInsets.only(right: 10),
                child: ChoiceChip(
                  label: Text(macro),
                  selected: isSelected,
                  onSelected: (sel) => setState(() => macroSeleccionada = macro),
                  selectedColor: AppColors.primary,
                  labelStyle: TextStyle(color: isSelected ? Colors.white : Colors.black87),
                  showCheckmark: false,
                ),
              );
            }).toList(),
          ),
        ),
        const Divider(height: 30, thickness: 1),

        if (macroSeleccionada != null)
          ..._buildGroupList(macroSeleccionada!),
          
        const SizedBox(height: 40),
      ],
    );
  }

  List<Widget> _buildGroupList(String macro) {
    final gruposMap = arbolConfig![macro]!;
    final gruposOrdenados = gruposMap.keys.toList()..sort();

    return gruposOrdenados.map((grupoKey) {
      return _GroupCard(
        title: grupoKey,
        sliderValue: sliderValues[grupoKey] ?? 3.0,
        items: gruposMap[grupoKey]!,
        checkValues: checkValues,
        onSliderChanged: (val) {
          setState(() => sliderValues[grupoKey] = val);
          _actualizarMapa(); // Llamada a Python al mover el slider
        },
        onCheckChanged: (idsAfectados, nuevoEstado) {
          setState(() {
            for (var id in idsAfectados) {
              checkValues[id] = nuevoEstado;
            }
          });
          _actualizarMapa(); // Llamada a Python al tocar checkboxes
        },
      );
    }).toList();
  }
}

// --- WIDGET DE LA TARJETA (MANTENIENDO TUS MEJORAS) ---
class _GroupCard extends StatelessWidget {
  final String title;
  final double sliderValue;
  final List<ConfigItem> items;
  final Map<String, bool> checkValues;
  final ValueChanged<double> onSliderChanged;
  final Function(List<String>, bool) onCheckChanged;

  const _GroupCard({
    required this.title,
    required this.sliderValue,
    required this.items,
    required this.checkValues,
    required this.onSliderChanged,
    required this.onCheckChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
      elevation: 0, // Minimalista sin sombra
      color: AppColors.surface,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(15),
        side: BorderSide(color: Colors.grey.shade200), // Borde suave
      ),
      child: ExpansionTile(
        shape: const RoundedRectangleBorder(side: BorderSide(color: Colors.transparent)),
        collapsedShape: const RoundedRectangleBorder(side: BorderSide(color: Colors.transparent)),
        tilePadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        title: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Expanded(
              child: Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            ),
            const SizedBox(width: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: AppColors.primary.withOpacity(0.1),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(
                sliderValue.toStringAsFixed(0),
                style: const TextStyle(color: AppColors.primary, fontWeight: FontWeight.bold),
              ),
            ),
          ],
        ),
        subtitle: Padding(
          padding: const EdgeInsets.only(top: 8.0),
          child: Slider(
            value: sliderValue,
            min: 0, max: 5, divisions: 5,
            activeColor: AppColors.primary,
            inactiveColor: AppColors.primary.withOpacity(0.1),
            onChanged: onSliderChanged,
          ),
        ),
        children: [
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Align(
              alignment: Alignment.centerLeft,
              child: Text(
                "(Desmarca las que no necesites)",
                style: TextStyle(fontSize: 12, color: Colors.grey, fontStyle: FontStyle.italic),
              ),
            ),
          ),
          ...items.map((item) {
            final isChecked = item.ids.every((id) => checkValues[id] == true);
            return CheckboxListTile(
              title: Text(item.label, style: const TextStyle(fontSize: 14)),
              value: isChecked,
              dense: true,
              activeColor: AppColors.primary,
              controlAffinity: ListTileControlAffinity.leading,
              onChanged: (bool? val) {
                if (val != null) onCheckChanged(item.ids, val);
              },
            );
          }).toList(),
          const SizedBox(height: 10),
        ],
      ),
    );
  }
}