import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../config/theme/app_colors.dart';
import '../services/api_services.dart';

// Importamos nuestros nuevos widgets
import '../widgets/config_panel.dart';
import '../widgets/result_card.dart';

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
  String? resumenIA; // Variable separada para el texto
  bool isLoadingIA = false; // Estado de carga solo para el texto

  // --- DATOS DEL MAPA Y CONFIG ---
  Map<String, Map<String, List<ConfigItem>>>? arbolConfig;
  List<Polygon> poligonosADibujar = [];
  dynamic geojsonRaw;

  // --- ESTADO UI ---
  int _tabSeleccionada = 0; // 0: Explorar, 1: Mi Zona
  String? macroSeleccionada;
  Map<String, double> sliderValues = {};
  Map<String, bool> checkValues = {};

  // --- ESTADO RADAR (ZONA ESPECÍFICA) ---
  Map<String, dynamic>? datosPuntoEspecifico;
  bool isCalculandoPunto = false;

  @override
  void initState() {
    super.initState();
    _inicializarTodo();
  }

  Future<void> _inicializarTodo() async {
    try {
      final datos = await _apiService.getCategories();
      final String response = await rootBundle.loadString('assets/data/grid_tenerife.geojson');
      geojsonRaw = json.decode(response);

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

      await _actualizarMapa();
    } catch (e) {
      setState(() => errorMessage = "Error al iniciar: $e");
    } finally {
      setState(() => isLoading = false);
    }
  }

  Future<void> _actualizarMapa() async {
    try {
      final resultados = await _apiService.calculateScores(sliderValues, checkValues);
      final Map<String, String> nuevosColores = {};
      for (var res in resultados) {
        nuevosColores[res['hex_id']] = res['color'];
      }

      List<Polygon> nuevosPoligonos = [];
      for (var feature in geojsonRaw['features']) {
        final id = feature['properties']['hex_id'];
        final colorHex = nuevosColores[id] ?? "#CCCCCC";
        final color = Color(int.parse(colorHex.replaceFirst('#', '0xFF')));

        List<LatLng> points = [];
        var coords = feature['geometry']['coordinates'][0];
        for (var p in coords) {
          points.add(LatLng(p[1].toDouble(), p[0].toDouble()));
        }

        nuevosPoligonos.add(Polygon(
          points: points,
          color: color.withOpacity(1.0),
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

  Future<void> _obtenerScoreDePunto(double lat, double lon) async {
    // 1. Limpiamos datos anteriores para que no se mezclen
    setState(() {
      isCalculandoPunto = true; // Carga general (Score)
      isLoadingIA = false;
      datosPuntoEspecifico = null;
      resumenIA = null;
    });

    try {
      // 2. LLAMADA RÁPIDA: Obtenemos solo el Score
      final resultado = await _apiService.calculatePointScore(
        lat: lat,
        lon: lon,
        sliders: sliderValues,
        checks: checkValues,
      );

      // ¡PINTAMOS LA NOTA YA! El usuario ve el resultado en 0.1s
      setState(() {
        datosPuntoEspecifico = resultado;
        isCalculandoPunto = false; 
        
        // Activamos la carga secundaria
        isLoadingIA = true;
      });

      // 3. LLAMADA LENTA: Pedimos la explicación a la IA en segundo plano
      final textoIA = await _apiService.getIaExplanation(
        lat: lat,
        lon: lon,
        sliders: sliderValues,
        checks: checkValues,
      );

      // Cuando llegue la IA, actualizamos solo ese trocito
      if (mounted) {
        setState(() {
          resumenIA = textoIA;
          isLoadingIA = false;
        });
      }
    } catch (e) {
      setState(() {
        isCalculandoPunto = false;
        isLoadingIA = false;
      });
      print("Error: $e");
    }
  }

    void _cerrarTarjeta() {
    setState(() {
      datosPuntoEspecifico = null;
      resumenIA = null;
      // Opcional: Quitar la chincheta del mapa si quieres
      // _tabSeleccionada = 0; 
    });
  }

  void _abrirConfiguracionModal() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) {
        return StatefulBuilder(
          builder: (BuildContext context, StateSetter setModalState) {
            return DraggableScrollableSheet(
              initialChildSize: 0.6,
              minChildSize: 0.4,
              maxChildSize: 0.9,
              builder: (context, scrollController) {
                return Container(
                  decoration: const BoxDecoration(
                    color: AppColors.surface,
                    borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
                  ),
                  child: Column(
                    children: [
                      Center(child: Container(width: 40, height: 5, margin: const EdgeInsets.symmetric(vertical: 10), decoration: BoxDecoration(color: Colors.grey[300], borderRadius: BorderRadius.circular(10)))),
                      Expanded(
                        child: ConfigPanel(
                          scrollController: scrollController,
                          arbolConfig: arbolConfig,
                          macroSeleccionada: macroSeleccionada,
                          sliderValues: sliderValues,
                          checkValues: checkValues,
                          errorMessage: errorMessage,
                          extraSetState: setModalState,
                          
                          // LÓGICA DE ACTUALIZACIÓN
                          onMacroChanged: (val) => setState(() => macroSeleccionada = val),
                          onSliderChanged: (group, val) => setState(() => sliderValues[group] = val),
                          onSliderEnd: (val) {
                             if (_tabSeleccionada == 1) {
                                _obtenerScoreDePunto(_mapController.camera.center.latitude, _mapController.camera.center.longitude);
                             }
                          },
                          onCheckChanged: (ids, val) {
                            setState(() {
                              for (var id in ids) { checkValues[id] = val; }
                            });
                            if (_tabSeleccionada == 1) {
                               _obtenerScoreDePunto(_mapController.camera.center.latitude, _mapController.camera.center.longitude);
                            }
                          },
                        ),
                      ),
                    ],
                  ),
                );
              },
            );
          }
        );
      },
    ).whenComplete(() {
      if (_tabSeleccionada == 1) {
        _obtenerScoreDePunto(_mapController.camera.center.latitude, _mapController.camera.center.longitude);
      }
    });
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
          // CAPA FONDO
          if (_tabSeleccionada == 0)
            Positioned.fill(child: Container(color: const Color(0xFFF5F7FA))),

          // MAPA
          FlutterMap(
            mapController: _mapController,
            options: MapOptions(
              initialCenter: const LatLng(28.1400, -16.5230),
              initialZoom: 9.4,
              onMapEvent: (event) {
                if (event is MapEventMoveEnd && _tabSeleccionada == 1) {
                  _obtenerScoreDePunto(event.camera.center.latitude, event.camera.center.longitude);
                }
              },
            ),
            children: [
              if (_tabSeleccionada == 1)
                TileLayer(
                  urlTemplate: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
                  subdomains: const ['a', 'b', 'c', 'd'],
                  userAgentPackageName: 'com.tenerifelifescore.app',
                ),
              if (_tabSeleccionada == 0) 
                PolygonLayer(polygons: poligonosADibujar),
            ],
          ),

          // CHINCHETA
          if (_tabSeleccionada == 1)
            const IgnorePointer(
              child: Center(
                child: Padding(
                  padding: EdgeInsets.only(bottom: 40),
                  child: Icon(Icons.location_on, color: Colors.red, size: 50),
                ),
              ),
            ),

          // LOADING
          if (isLoading)
            Container(
              color: Colors.white70,
              child: const Center(child: CircularProgressIndicator()),
            ),

          // PANEL EXPLORAR (Draggable Sheet)
          if (_tabSeleccionada == 0)
            DraggableScrollableSheet(
              initialChildSize: 0.4,
              minChildSize: 0.15,
              maxChildSize: 0.60,
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
                      Expanded(
                        child: ConfigPanel(
                          scrollController: scrollController,
                          arbolConfig: arbolConfig,
                          macroSeleccionada: macroSeleccionada,
                          sliderValues: sliderValues,
                          checkValues: checkValues,
                          errorMessage: errorMessage,
                          
                          // LÓGICA DE ACTUALIZACIÓN (TAB 0)
                          onMacroChanged: (val) => setState(() => macroSeleccionada = val),
                          onSliderChanged: (group, val) => setState(() => sliderValues[group] = val),
                          onSliderEnd: (val) {
                             if (_tabSeleccionada == 0) _actualizarMapa();
                          },
                          onCheckChanged: (ids, val) {
                            setState(() {
                              for (var id in ids) { checkValues[id] = val; }
                            });
                            if (_tabSeleccionada == 0) _actualizarMapa();
                          },
                        ),
                      ),
                    ],
                  ),
                );
              },
            ),

          // TARJETA RESULTADO (Tab 1)
          if (_tabSeleccionada == 1 && datosPuntoEspecifico != null) // Solo si hay datos
              ResultCard(
                score: datosPuntoEspecifico!['score'], // Pasamos el dato limpio
                iaSummary: resumenIA,
                isLoadingIA: isLoadingIA,
                onTunePressed: _abrirConfiguracionModal,
                onClosePressed: _cerrarTarjeta, // <--- Conectamos la función de cerrar
              ),
        ],
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _tabSeleccionada,
        selectedItemColor: AppColors.primary,
        onTap: (index) {
          setState(() => _tabSeleccionada = index);
          if (index == 1) {
            _obtenerScoreDePunto(_mapController.camera.center.latitude, _mapController.camera.center.longitude);
          }
        },
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.map), label: "Explorar"),
          BottomNavigationBarItem(icon: Icon(Icons.gps_fixed), label: "Mi Zona"),
        ],
      ),
    );
  }
}