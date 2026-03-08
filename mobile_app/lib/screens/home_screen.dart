import 'dart:convert';
import 'dart:async';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:geolocator/geolocator.dart';
import 'package:http/http.dart' as http;
import '../data/user_profiles.dart';
import '../config/theme/app_colors.dart';
import '../services/api_services.dart';
import '../widgets/config_panel.dart';
import '../widgets/result_card.dart';
import '../widgets/smart_loading_screen.dart';
import '../screens/onboarding_screen.dart';

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
  String? resumenIA;
  bool isLoadingIA = false;
  bool _mostrarAjustes = false;

  // --- DATOS DEL MAPA Y CONFIG ---
  Map<String, Map<String, List<ConfigItem>>>? arbolConfig;
  List<Polygon> poligonosADibujar = [];
  List<Map<String, dynamic>> propiedadesHexagonos = [];
  dynamic geojsonRaw;
  Map<String, double> scoresHexagonos = {};
  int _indexSeleccionado = -1;

  // --- ESTADO UI ---
  int _tabSeleccionada = 0; // 0: Explorar, 1: Mi Zona
  String? macroSeleccionada;
  Map<String, double> sliderValues = {};
  Map<String, bool> checkValues = {};

  // --- MI ZONA ---
  Map<String, dynamic>? datosPuntoEspecifico;
  bool isCalculandoPunto = false;
  LatLng? _ultimaPosicionMiZona;
  String? nombreZonaActual;
  bool _callesListas = false;

  // Controlador para el texto de búsqueda
  final TextEditingController _searchController = TextEditingController();
  
  // Para controlar si mostramos el botón de "Analizar"
  bool mostrarBotonAnalizar = true;

  // Variables para el internet
  bool _hayInternet = true;
  StreamSubscription? _suscripcionInternet;

  @override
  void initState() {
    _suscripcionInternet = Connectivity().onConnectivityChanged.listen((List<ConnectivityResult> result) {
      if (mounted) {
        setState(() {
          _hayInternet = !result.every((r) => r == ConnectivityResult.none);
        });
      }
    });

    super.initState();
    _inicializarTodo();
  }

  @override
  void dispose() {
    _suscripcionInternet?.cancel(); // Apagamos el escuchador
    super.dispose();
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

      setState(() {
        arbolConfig = datos;
        sliderValues = inicialesSliders;
        checkValues = inicialesChecks;
        String pestanaPorDefecto = "Servicios básicos"; 
        
        macroSeleccionada = datos.containsKey(pestanaPorDefecto) ? pestanaPorDefecto : datos.keys.first;
      });

      await _actualizarMapa();
    } catch (e) {
      setState(() => errorMessage = "Error al iniciar: $e");
    } finally {
      setState(() => isLoading = false);
    }
  }

  void _aplicarPerfil(UserProfile perfil) {
    setState(() {
      perfil.sliders.forEach((key, value) {
        if (sliderValues.containsKey(key)) {
          sliderValues[key] = value;
        }
      });

      checkValues.updateAll((key, val) => false);

      for (var checkId in perfil.checksMarcados) {
        if (checkValues.containsKey(checkId)) {
          checkValues[checkId] = true;
        } else {
          print("⚠️ Ojo: El checkbox '$checkId' no existe en la app.");
        }
      }
    });

    _actualizarMapa();

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Cargando perfil: ${perfil.icono} ${perfil.nombre}...'),
        backgroundColor: AppColors.primary,
        duration: const Duration(seconds: 2),
      ),
    );
  }

  void _abrirMenuPerfiles() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent, 
      isScrollControlled: true,
      builder: (context) {
        return Container(
          height: MediaQuery.of(context).size.height * 0.5, 
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
          ),
          child: Column(
            children: [
              Container(
                width: 40, 
                height: 5,
                margin: const EdgeInsets.only(top: 12, bottom: 20),
                decoration: BoxDecoration(
                  color: Colors.grey[300], 
                  borderRadius: BorderRadius.circular(10)
                ),
              ),
              
              const Text(
                "Elige tu perfil", 
                style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              const Padding(
                padding: EdgeInsets.symmetric(horizontal: 20),
                child: Text(
                  "Cargaremos los filtros ideales para ti al instante.",
                  textAlign: TextAlign.center,
                  style: TextStyle(color: Colors.grey, fontSize: 14),
                ),
              ),
              const SizedBox(height: 20),
              
              ListTile(
                contentPadding: const EdgeInsets.symmetric(horizontal: 25, vertical: 0),
                leading: const Text("🌍", style: TextStyle(fontSize: 32)),
                title: const Text("Perfil por defecto", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                subtitle: const Text("Todos los filtros equilibrados", style: TextStyle(fontSize: 12)),
                trailing: const Icon(Icons.arrow_forward_ios, size: 16, color: Colors.grey),
                onTap: () {
                  Navigator.pop(context); 
                  _aplicarPerfilPorDefecto();
                },
              ),
              
              const Divider(height: 1, indent: 25, endIndent: 25),

              Expanded(
                child: ListView.separated(
                  itemCount: perfilesPredefinidos.length,
                  separatorBuilder: (context, index) => const Divider(height: 1, indent: 25, endIndent: 25,),
                  itemBuilder: (context, index) {
                    String key = perfilesPredefinidos.keys.elementAt(index);
                    UserProfile perfil = perfilesPredefinidos[key]!;
                    
                    return ListTile(
                      contentPadding: const EdgeInsets.symmetric(horizontal: 25, vertical: 5),
                      leading: Text(perfil.icono, style: const TextStyle(fontSize: 32)),
                      title: Text(perfil.nombre, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                      trailing: const Icon(Icons.arrow_forward_ios, size: 16, color: Colors.grey),
                      onTap: () {
                        Navigator.pop(context);
                        _aplicarPerfil(perfil);
                      },
                    );
                  },
                ),
              ),
            ],
          ),
        );
      }
    );
  }

  void _aplicarPerfilPorDefecto() {
    setState(() {
      sliderValues.updateAll((key, val) => 3.0);
      
      checkValues.updateAll((key, val) => true);
    });

    _actualizarMapa();

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Cargando perfil: 🌍 Por Defecto...'),
        backgroundColor: AppColors.primary,
        duration: Duration(seconds: 2),
      ),
    );
  }

  Future<void> _actualizarMapa() async {
    try {
      final resultados = await _apiService.calculateScores(sliderValues, checkValues);
      final Map<String, String> nuevosColores = {};
      final Map<String, double> nuevosScores = {};

      for (var res in resultados) {
        nuevosColores[res['hex_id']] = res['color'];
        if (res['score_final'] != null) {
          nuevosScores[res['hex_id']] = (res['score_final'] as num).toDouble();
        }
      }

      List<Polygon> nuevosPoligonos = [];
      List<Map<String, dynamic>> nuevasPropiedades = [];

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
        scoresHexagonos = nuevosScores;
      });
    } catch (e) {
      print("Error actualizando mapa: $e");
    }
  }

  void _refrescarBordes() {
    if (poligonosADibujar.isEmpty) return;

    List<Polygon> poligonosRepintados = [];
    Polygon? poligonoDestacado;

    for (int i = 0; i < poligonosADibujar.length; i++) {
      final poly = poligonosADibujar[i];
      final bool isSelected = (i == _indexSeleccionado);

      final nuevoPoly = Polygon(
        points: poly.points,
        color: poly.color, 
        borderStrokeWidth: isSelected ? 3.0 : 0.5, 
        borderColor: isSelected ? Colors.black : Colors.white24,
        isFilled: true,
      );

      if (isSelected) {
        poligonoDestacado = nuevoPoly;
      } else {
        poligonosRepintados.add(nuevoPoly);
      }
    }

    if (poligonoDestacado != null) {
      poligonosRepintados.add(poligonoDestacado);
    }

    setState(() {
      poligonosADibujar = poligonosRepintados;
    });
  }

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

  Future<String> _obtenerNombreZona(double lat, double lon, {String? municipioGeoJson}) async {
    try {
      final url = Uri.parse('https://nominatim.openstreetmap.org/reverse?lat=$lat&lon=$lon&format=json&zoom=14&addressdetails=1');
      final response = await http.get(url, headers: {'User-Agent': 'com.tenerifelifescore.app'});

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final address = data['address'];
        
        if (address != null) {
          String barrio = address['suburb'] ?? address['neighbourhood'] ?? address['quarter'] ?? address['village'] ?? "Zona";
          
          String municipio = municipioGeoJson ?? address['city'] ?? address['town'] ?? address['municipality'] ?? "Tenerife";
          
          if (barrio != "Zona" && barrio != municipio) {
            return "$barrio ($municipio)";
          } else {
            return "Zona en $municipio";
          }
        }
      }
    } catch (e) { print("Error Nominatim: $e"); }
    return "Zona seleccionada";
  }

  Future<void> _analizarHexagono(String hexId, String centroidString, String municipio) async {
    final partes = centroidString.split(',');
    final lat = double.parse(partes[0].trim());
    final lon = double.parse(partes[1].trim());

    double latAjustada = lat - 0.06; 
    
    _mapController.move(LatLng(latAjustada, lon), 11.5);

    double notaDelHexagono = scoresHexagonos[hexId] ?? 0.0;

    setState(() {
      isLoading = false;
      datosPuntoEspecifico = {'score': notaDelHexagono}; 
      resumenIA = null;
      isLoadingIA = true;
      nombreZonaActual = "Buscando zona..."; 
    });

    final nombreFormateado = await _obtenerNombreZona(lat, lon, municipioGeoJson: municipio);

    if (mounted) {
      setState(() {
        nombreZonaActual = nombreFormateado;
      });
    }

    try {
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
      if (mounted) {
        setState(() {
          resumenIA = "No se pudo conectar con el asesor virtual.";
          isLoadingIA = false;
        });
      }
    }
  }

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

  Future<void> _irAMiUbicacion() async {
    bool serviceEnabled;
    LocationPermission permission;

    serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('El GPS está desactivado')));
      return;
    }

    permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) return;
    }

    if (permission == LocationPermission.deniedForever) return;

    Position position = await Geolocator.getCurrentPosition();
    _mapController.move(LatLng(position.latitude, position.longitude), 15.0);
    setState(() => mostrarBotonAnalizar = true);
  }

  Future<void> _buscarDireccion(String query) async {
    if (query.isEmpty) return;
    
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
          FocusScope.of(context).unfocus();
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
    
    setState(() {
      mostrarBotonAnalizar = false;
      nombreZonaActual = "Calculando...";
    });

    final nombreFormateado = await _obtenerNombreZona(centro.latitude, centro.longitude);
    setState(() => nombreZonaActual = nombreFormateado);

    _obtenerScoreDePunto(centro.latitude, centro.longitude);
  }
  
  void _cerrarTarjeta() {
    setState(() {
      _indexSeleccionado = -1;
      datosPuntoEspecifico = null;
      resumenIA = null;
      nombreZonaActual = null;
      mostrarBotonAnalizar = true; 
    });
    _refrescarBordes();
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
    if (isLoading) {
      return const Scaffold(
        body: SmartLoadingScreen(),
      );
    }
    return Scaffold(
      resizeToAvoidBottomInset: false,
      body: Stack(
        children: [
          if (_tabSeleccionada == 0)
            Positioned.fill(child: Container(color: const Color(0xFFF5F7FA))),

          Semantics(
            label: "Mapa interactivo de Tenerife. Mueve el mapa y pulsa en las zonas para ver su puntuación.",
            child: FlutterMap(
              mapController: _mapController,
              options: MapOptions(
                initialCenter: const LatLng(28.2600, -16.5230), 
                initialZoom: 9.4,
                
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
                      _indexSeleccionado = indexTocado;
                      _refrescarBordes(); 
                      
                      final props = propiedadesHexagonos[indexTocado];
                      _analizarHexagono(props['hex_id'], props['centroide'], props['municipio']);
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
                if (_tabSeleccionada == 1 && _callesListas)
                  TileLayer(
                    key: ValueKey("capa_calle_$_tabSeleccionada"), 
                    urlTemplate: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
                    subdomains: const ['a', 'b', 'c', 'd'],
                    userAgentPackageName: 'com.tenerifelifescore.app',
                    tileDisplay: const TileDisplay.instantaneous(),
                  ),
                
                if (_tabSeleccionada == 0) 
                  PolygonLayer(polygons: poligonosADibujar),
              ],
            ),
          ),
          Positioned(
            top: 50,
            left: 15,
            right: 15,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.center, 
              children: [
                
                FloatingActionButton(
                  heroTag: "btn_perfiles",
                  tooltip: "Abrir menú de perfiles de usuario",
                  backgroundColor: Colors.white,
                  elevation: 4,
                  onPressed: () {
                    _cerrarTarjeta();

                    setState(() {
                      _mostrarAjustes = false; 
                    });

                    _abrirMenuPerfiles();
                  },
                  child: const Icon(Icons.groups_3, color: AppColors.primary, size: 32),
                ),

                const SizedBox(width: 10), 

                Expanded(
                  child: AnimatedSwitcher(
                    duration: const Duration(milliseconds: 500),
                    child: _tabSeleccionada == 1 
                    ? Card(
                        key: const ValueKey("barra_busqueda"), 
                        color: Colors.white,
                        surfaceTintColor: Colors.transparent,
                        elevation: 4,
                        margin: EdgeInsets.zero, 
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(30)), 
                        child: Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 4),
                          child: Row(
                            children: [
                              const Icon(Icons.search, color: Colors.grey),
                              const SizedBox(width: 10),
                              Expanded(
                                child: TextField(
                                  controller: _searchController,
                                  decoration: const InputDecoration(
                                    hintText: "Buscar zona...",
                                    border: InputBorder.none,
                                    isDense: true, 
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
                                padding: EdgeInsets.zero, 
                                constraints: const BoxConstraints(), 
                              ),
                            ],
                          ),
                        ),
                      )
                    : const SizedBox.shrink(key: ValueKey("hueco_vacio")),
                  ),
                ),

                const SizedBox(width: 10), 

                FloatingActionButton(
                  heroTag: "btn_ajustes",
                  tooltip: _mostrarAjustes ? "Cerrar ajustes" : "Abrir ajustes de filtros",
                  backgroundColor: _mostrarAjustes ? AppColors.primary : Colors.white,
                  elevation: 4,
                  onPressed: () {
                    _cerrarTarjeta();

                    setState(() {
                      _mostrarAjustes = !_mostrarAjustes;
                    });
                  },
                  child: Icon(
                    Icons.tune, 
                    color: _mostrarAjustes ? Colors.white : AppColors.primary,
                    size: 30,
                  ),
                ),
              ],
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
              bottom: 30,
              left: 80,
              right: 80,
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
                  elevation: 4,
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

          AnimatedPositioned(
            duration: const Duration(milliseconds: 400),
            curve: Curves.easeOutExpo, 
            top: _mostrarAjustes ? 0 : MediaQuery.of(context).size.height,
            bottom: _mostrarAjustes ? 0 : -MediaQuery.of(context).size.height,
            left: 0,
            right: 0,
            child: DraggableScrollableSheet(
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
          ),

          if (_tabSeleccionada == 0 && !_mostrarAjustes) 
            Positioned(
              bottom: 30,
              left: 15,
              right: 15,
              child: Semantics( 
                label: "Puntuación LifeScore. Leyenda de puntuación: de 0 a 10. El 0 es rojo, indicando la puntuación más baja, y el 10 es azul, indicando la puntuación máxima.",
                child: IgnorePointer( 
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 12),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.95), 
                      borderRadius: BorderRadius.circular(20),
                      boxShadow: const [
                        BoxShadow(color: Colors.black12, blurRadius: 10, offset: Offset(0, 4))
                      ],
                    ),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          "Puntuación LifeScore", 
                          style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.grey[800])
                        ),
                        const SizedBox(height: 8),
                        
                        Container(
                          height: 12,
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(10),
                            gradient: const LinearGradient(
                              colors: [
                                AppColors.scoreCritical, // Rojo (0)
                                AppColors.scoreLow,      // Naranja (1.5)
                                AppColors.scoreMedium,   // Amarillo (4.0)
                                AppColors.scoreHigh,     // Verde (7.0)
                                AppColors.scoreTop,      // Azul (10)
                              ],
                              stops: [0.0, 0.15, 0.40, 0.70, 1.0], 
                            ),
                          ),
                        ),
                        const SizedBox(height: 6),
                        
                        const SizedBox(
                          height: 16,
                          child: Stack(
                            children: [
                              Align(alignment: Alignment(-1.0, 0), child: Text("0", style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold))),
                              Align(alignment: Alignment(-0.6, 0), child: Text("2", style: TextStyle(fontSize: 10, color: Colors.grey))),
                              Align(alignment: Alignment(-0.2, 0), child: Text("4", style: TextStyle(fontSize: 10, color: Colors.grey))),
                              Align(alignment: Alignment(0.2, 0), child: Text("6", style: TextStyle(fontSize: 10, color: Colors.grey))),
                              Align(alignment: Alignment(0.6, 0), child: Text("8", style: TextStyle(fontSize: 10, color: Colors.grey))),
                              Align(alignment: Alignment(1.0, 0), child: Text("10", style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold))),
                            ],
                          ),
                        )
                      ],
                    ),
                  ),
                ),
              ),
            ),
          
          Positioned(
            top: 110, 
            right: 15,
            child: FloatingActionButton.small( 
              heroTag: "btn_info",
              tooltip: "Ver instrucciones y ayuda",
              backgroundColor: Colors.white,
              elevation: 4,
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => const OnboardingScreen()),
                );
              },
              child: const Icon(Icons.help_outline, color: AppColors.primary, size: 24),
            ),
          ),

          AnimatedSwitcher(
            duration: const Duration(milliseconds: 300),
            switchInCurve: Curves.easeOut,
            switchOutCurve: Curves.easeIn,
            child: datosPuntoEspecifico != null 
              ? ResultCard(
                  key: const ValueKey("tarjeta_resultados"),
                  placeName: nombreZonaActual,
                  score: datosPuntoEspecifico!['score'],
                  iaSummary: resumenIA,
                  isLoadingIA: isLoadingIA,
                  positionAlignment: Alignment.bottomCenter,
                  onTunePressed: _abrirConfiguracionModal,
                  onClosePressed: _cerrarTarjeta,
                )
              : const SizedBox.shrink(key: ValueKey("tarjeta_vacia")), 
          ),
            
          if (!_hayInternet)
            Container(
              width: double.infinity,
              height: double.infinity,
              color: Colors.white,
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.wifi_off_rounded, size: 100, color: Colors.grey),
                  const SizedBox(height: 24),
                  const Text(
                    "¡Vaya! Sin conexión", 
                    style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: Colors.black87)
                  ),
                  const SizedBox(height: 12),
                  const Padding(
                    padding: EdgeInsets.symmetric(horizontal: 40),
                    child: Text(
                      "Tenerife LifeScore necesita internet para conectarse con nuestra IA y descargar los datos del mapa.\n\nRevisa tu conexión Wi-Fi o datos móviles para continuar descubriendo la isla.",
                      textAlign: TextAlign.center,
                      style: TextStyle(fontSize: 16, color: Colors.black54, height: 1.5),
                    ),
                  ),
                  const SizedBox(height: 40),
                  ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(30)),
                    ),
                    onPressed: () {},
                    icon: const Icon(Icons.refresh),
                    label: const Text("Buscando red..."),
                  )
                ],
              ),
            ),
        ],
      ),
      
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _tabSeleccionada,
        selectedItemColor: AppColors.primary,
        onTap: (index) {          
          setState(() {
            _tabSeleccionada = index;
            _callesListas = false;

            datosPuntoEspecifico = null; 
            resumenIA = null;
            nombreZonaActual = null;
            
            if (index == 1) mostrarBotonAnalizar = true;
          });
          
          WidgetsBinding.instance.addPostFrameCallback((_) {
            if (index == 0) {
              _mapController.move(const LatLng(28.2600, -16.5230), 9.4);
            } else if (index == 1) {
              final destino = _ultimaPosicionMiZona ?? const LatLng(28.4636, -16.2518);
              _mapController.move(destino, 13.0);
            }

            if (mounted) {
              setState(() {
                _callesListas = true;
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