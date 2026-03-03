import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../config/theme/app_colors.dart';
import '../services/api_services.dart';
import '../widgets/config_panel.dart';
import '../widgets/result_card.dart';
import 'package:geolocator/geolocator.dart';
import 'package:http/http.dart' as http;

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
  List<Map<String, dynamic>> propiedadesHexagonos = []; // NUEVO: Para guardar municipio y centroide
  dynamic geojsonRaw;

  // --- ESTADO UI ---
  int _tabSeleccionada = 0; // 0: Explorar, 1: Mi Zona
  String? macroSeleccionada;
  Map<String, double> sliderValues = {};
  Map<String, bool> checkValues = {};

  // --- ESTADO RADAR (ZONA ESPECÍFICA) ---
  Map<String, dynamic>? datosPuntoEspecifico;
  bool isCalculandoPunto = false;
  LatLng? _ultimaPosicionMiZona;
  String? nombreZonaActual;

  // Controlador para el texto de búsqueda
  final TextEditingController _searchController = TextEditingController();
  
  // Para controlar si mostramos el botón de "Analizar"
  bool mostrarBotonAnalizar = true;

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
      List<Map<String, dynamic>> nuevasPropiedades = []; // NUEVO

      for (var feature in geojsonRaw['features']) {
        final props = feature['properties'];
        final id = props['hex_id'];
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
        nuevasPropiedades.add(props);
      }

      setState(() {
        poligonosADibujar = nuevosPoligonos;
        propiedadesHexagonos = nuevasPropiedades;
      });
    } catch (e) {
      print("Error actualizando mapa: $e");
    }
  }

  // ¿El punto está en el polígono?
  bool _isPointInPolygon(LatLng point, List<LatLng> polygonPoints) {
    bool isInside = false;
    int j = polygonPoints.length - 1;
    for (int i = 0; i < polygonPoints.length; i++) {
      if (((polygonPoints[i].latitude > point.latitude) != 
          (polygonPoints[j].latitude > point.latitude)) &&
          (point.longitude < (polygonPoints[j].longitude - polygonPoints[i].longitude) * (point.latitude - polygonPoints[i].latitude) / 
          (polygonPoints[j].latitude - polygonPoints[i].latitude) + polygonPoints[i].longitude)) {
        isInside = !isInside;
      }
      j = i;
    }
    return isInside;
  }

  // --- OBTENER BARRIO (NOMINATIM) ---
  Future<String> _obtenerBarrio(double lat, double lon) async {
    try {
      final url = Uri.parse('https://nominatim.openstreetmap.org/reverse?lat=$lat&lon=$lon&format=json&zoom=14&addressdetails=1');
      final response = await http.get(url, headers: {'User-Agent': 'com.tenerifelifescore.app'});

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final address = data['address'];
        if (address != null) {
          return address['suburb'] ?? address['neighbourhood'] ?? address['quarter'] ?? address['village'] ?? "Zona";
        }
      }
    } catch (e) { print("Error barrio: $e"); }
    return "Zona seleccionada";
  }

  // --- ANALIZAR HEXÁGONO (NUEVO) ---
  Future<void> _analizarHexagono(String centroidString, String municipio) async {
    final partes = centroidString.split(',');
    final lat = double.parse(partes[0].trim());
    final lon = double.parse(partes[1].trim());

    setState(() {
      isLoading = true;
      datosPuntoEspecifico = {'score': 0.0, 'detalles': {}}; 
      resumenIA = null;
      nombreZonaActual = "Buscando zona..."; 
      mostrarBotonAnalizar = false; 
    });

    final barrio = await _obtenerBarrio(lat, lon);

    setState(() {
      nombreZonaActual = barrio != "Zona" ? "$barrio ($municipio)" : "Zona en $municipio";
    });

    await _obtenerScoreDePunto(lat, lon);
    
    setState(() => isLoading = false);
  }

  // --- OBTENER SCORE GENERAL (API) ---
  Future<void> _obtenerScoreDePunto(double lat, double lon) async {
    setState(() {
      isCalculandoPunto = true;
      isLoadingIA = false;
      datosPuntoEspecifico = null;
      resumenIA = null;
    });

    try {
      final resultado = await _apiService.calculatePointScore(
        lat: lat, lon: lon, sliders: sliderValues, checks: checkValues,
      );

      setState(() {
        datosPuntoEspecifico = resultado;
        isCalculandoPunto = false; 
        isLoadingIA = true;
      });

      final textoIA = await _apiService.getIaExplanation(
        lat: lat, lon: lon, sliders: sliderValues, checks: checkValues,
      );

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

  // --- FUNCIONES DE UBICACIÓN Y BÚSQUEDA ---
  Future<void> _irAMiUbicacion() async {
    bool serviceEnabled;
    LocationPermission permission;

    // 1. Verificar si el GPS está encendido
    serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('El GPS está desactivado')));
      return;
    }

    // 2. Pedir permisos
    permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) return;
    }

    if (permission == LocationPermission.deniedForever) return;

    // 3. Obtener posición y mover mapa
    Position position = await Geolocator.getCurrentPosition();
    _mapController.move(LatLng(position.latitude, position.longitude), 15.0);
    setState(() => mostrarBotonAnalizar = true);
  }

  Future<void> _buscarDireccion(String query) async {
    if (query.isEmpty) return;
    
    // 1. Limpiamos cualquier resultado anterior para que no tape el mapa
    _cerrarTarjeta(); 
    setState(() => mostrarBotonAnalizar = false);
    final queryFinal = "$query, Tenerife"; 
    final url = Uri.parse('https://nominatim.openstreetmap.org/search?q=$queryFinal&format=json&limit=1');

    try {
      final response = await http.get(url, headers: {'User-Agent': 'com.tlife.app'});
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data.isNotEmpty) {
          final lat = double.parse(data[0]['lat']);
          final lon = double.parse(data[0]['lon']);
          
          _mapController.move(LatLng(lat, lon), 15.0);
          setState(() => mostrarBotonAnalizar = true);
          FocusScope.of(context).unfocus(); // Cerrar teclado
        } else {
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Dirección no encontrada')));
        }
      }
    } catch (e) {
      print("Error búsqueda: $e");
    }
  }

  void _analizarZonaActual() async {
    final centro = _mapController.camera.center;
    
    // Al analizar manualmente, buscamos también el nombre de la calle/barrio
    setState(() {
      mostrarBotonAnalizar = false;
      nombreZonaActual = "Calculando...";
    });

    final nombre = await _obtenerBarrio(centro.latitude, centro.longitude);
    setState(() => nombreZonaActual = nombre);

    _obtenerScoreDePunto(centro.latitude, centro.longitude);
  }
  
  void _cerrarTarjeta() {
    setState(() {
      datosPuntoEspecifico = null;
      resumenIA = null;
      nombreZonaActual = null;
      mostrarBotonAnalizar = true; 
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
                             } else {
                                _actualizarMapa();
                             }
                          },
                          onCheckChanged: (ids, val) {
                            setState(() {
                              for (var id in ids) { checkValues[id] = val; }
                            });
                            if (_tabSeleccionada == 1) {
                               _obtenerScoreDePunto(_mapController.camera.center.latitude, _mapController.camera.center.longitude);
                            } else {
                               _actualizarMapa();
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
    );
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
          if (_tabSeleccionada == 0)
            Positioned.fill(child: Container(color: const Color(0xFFF5F7FA))),

          FlutterMap(
            mapController: _mapController,
            options: MapOptions(
              initialCenter: const LatLng(28.1400, -16.5230), 
              initialZoom: 9.4,
              
              // --- NUEVO: DETECCIÓN DE CLICK PARA HEXÁGONOS ---
              onTap: (tapPosition, point) {
                if (_tabSeleccionada == 0) {
                  int indexTocado = -1;
                  for (int i = 0; i < poligonosADibujar.length; i++) {
                    if (_isPointInPolygon(point, poligonosADibujar[i].points)) {
                      indexTocado = i;
                      break;
                    }
                  }
                  if (indexTocado != -1) {
                    final props = propiedadesHexagonos[indexTocado];
                    _analizarHexagono(props['centroide'], props['municipio']);
                  } else {
                    _cerrarTarjeta();
                  }
                } else {
                   _cerrarTarjeta();
                }
              },

              onPositionChanged: (pos, hasGesture) {
                if (_tabSeleccionada == 1) {
                  _ultimaPosicionMiZona = pos.center;
                }
                if (hasGesture) {
                  if (!mostrarBotonAnalizar) {
                    setState(() {
                      mostrarBotonAnalizar = true;
                      datosPuntoEspecifico = null; 
                      resumenIA = null;
                      nombreZonaActual = null;
                    });
                  }
                }
              },
            ),
            children: [
              if (_tabSeleccionada == 1)
                TileLayer(
                  key: ValueKey("capa_calle_$_tabSeleccionada"), 
                  urlTemplate: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
                  subdomains: const ['a', 'b', 'c', 'd'],
                  userAgentPackageName: 'com.tenerifelifescore.app',
                  tileDisplay: const TileDisplay.instantaneous(), // Sin efecto borroso
                ),
              
              if (_tabSeleccionada == 0) 
                PolygonLayer(polygons: poligonosADibujar),
            ],
          ),

          if (_tabSeleccionada == 1)
            Positioned(
              top: 30, 
              left: 20,
              right: 20,
              child: Card(
                elevation: 4,
                shadowColor: Colors.black26,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 15),
                  child: Row(
                    children: [
                      const Icon(Icons.search, color: Colors.grey),
                      const SizedBox(width: 10),
                      Expanded(
                        child: TextField(
                          controller: _searchController,
                          decoration: const InputDecoration(
                            hintText: "Buscar calle o zona...",
                            border: InputBorder.none,
                          ),
                          textInputAction: TextInputAction.search,
                          onSubmitted: (val) => _buscarDireccion(val),
                        ),
                      ),
                      Container(width: 1, height: 24, color: Colors.grey[300]), 
                      IconButton(
                        icon: const Icon(Icons.my_location, color: AppColors.primary),
                        onPressed: _irAMiUbicacion,
                        tooltip: "Ir a mi ubicación",
                      ),
                    ],
                  ),
                ),
              ),
            ),

          if (_tabSeleccionada == 1)
            const IgnorePointer( 
              child: Center(
                child: Padding(
                  padding: EdgeInsets.only(bottom: 40), 
                  child: Icon(Icons.location_on, color: Colors.red, size: 50),
                ),
              ),
            ),

          if (_tabSeleccionada == 1 && mostrarBotonAnalizar && !isLoading)
            Positioned(
              bottom: 40,
              left: 60,
              right: 60,
              child: ElevatedButton.icon(
                onPressed: _analizarZonaActual,
                icon: const Icon(Icons.analytics_outlined, color: Colors.white),
                label: const Text(
                  "ANALIZAR AQUÍ", 
                  style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16)
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  elevation: 6,
                  shadowColor: AppColors.primary.withOpacity(0.5),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(30)),
                ),
              ),
            ),

          if (isLoading)
            Container(
              color: Colors.white.withOpacity(0.8),
              child: const Center(child: CircularProgressIndicator()),
            ),

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
                      // Tirador gris
                      Center(child: Container(width: 40, height: 5, margin: const EdgeInsets.symmetric(vertical: 10), decoration: BoxDecoration(color: Colors.grey[300], borderRadius: BorderRadius.circular(10)))),
                      Expanded(
                        child: ConfigPanel(
                          scrollController: scrollController,
                          arbolConfig: arbolConfig,
                          macroSeleccionada: macroSeleccionada,
                          sliderValues: sliderValues,
                          checkValues: checkValues,
                          errorMessage: errorMessage,
                          onMacroChanged: (val) => setState(() => macroSeleccionada = val),
                          onSliderChanged: (group, val) => setState(() => sliderValues[group] = val),
                          onSliderEnd: (val) => _actualizarMapa(),
                          onCheckChanged: (ids, val) {
                            setState(() {
                              for (var id in ids) { checkValues[id] = val; }
                            });
                            _actualizarMapa();
                          },
                        ),
                      ),
                    ],
                  ),
                );
              },
            ),

          // --- CAMBIO: La tarjeta ahora sale en AMBAS pestañas si hay datos ---
          if (datosPuntoEspecifico != null) 
            ResultCard(
              placeName: nombreZonaActual, // Pasamos el nombre
              score: datosPuntoEspecifico!['score'],
              iaSummary: resumenIA,
              isLoadingIA: isLoadingIA,
              onTunePressed: _abrirConfiguracionModal,
              onClosePressed: _cerrarTarjeta,
            ),
        ],
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _tabSeleccionada,
        selectedItemColor: AppColors.primary,
        onTap: (index) {
          setState(() => _tabSeleccionada = index);
          
          // TRUCO: Esperamos a que termine de repintar la pantalla (1 frame)
          WidgetsBinding.instance.addPostFrameCallback((_) {
            
          if (index == 0) {
              // MODO EXPLORAR: Lejano
              _mapController.move(
                const LatLng(28.1400, -16.5230), 
                9.4
              );
          } else if (index == 1) {
              // MODO MI ZONA: Santa Cruz o ultima posición usuario
            final destino = _ultimaPosicionMiZona ?? const LatLng(28.4636, -16.2518);
              
              _mapController.move(
                destino, 
                13.0 // Mantenemos un zoom cercano para ver calles
              );
              
              // IMPORTANTE:
              // He quitado el '_obtenerScoreDePunto' aquí.
              // Como me pediste antes que el cálculo fuera MANUAL (con botón),
              // al cambiar de pestaña solo movemos el mapa y mostramos el botón.
          setState(() {
               mostrarBotonAnalizar = true;
                datosPuntoEspecifico = null; // Limpiamos resultados viejos
               resumenIA = null;
              });
             }            
          });          
        },
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.map), label: "Explorar"),
          BottomNavigationBarItem(icon: Icon(Icons.gps_fixed), label: "Mi Zona"),
        ],
      ),
    );
  }
}