import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../config/theme/app_colors.dart';
import '../services/api_services.dart';

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
    setState(() => isCalculandoPunto = true);
    try {
      final resultado = await _apiService.calculatePointScore(
        lat: lat,
        lon: lon,
        sliders: sliderValues,
        checks: checkValues,
      );
      setState(() {
        datosPuntoEspecifico = resultado;
        isCalculandoPunto = false;
      });
    } catch (e) {
      setState(() => isCalculandoPunto = false);
      print("Error en radar: $e");
    }
  }

  void _abrirConfiguracionModal() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) {
        // 1. Envolvemos todo en StatefulBuilder para tener estado dentro del modal
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
                      
                      // 2. Pasamos el 'setModalState' y el 'scrollController'
                      Expanded(
                        child: _buildPanelBody(
                          scrollController, 
                          extraSetState: setModalState // <--- ESTO ES LA CLAVE
                        )
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
      // Al cerrar, si estamos en 'Mi Zona', recalculamos
      if (_tabSeleccionada == 1) {
        _obtenerScoreDePunto(
          _mapController.camera.center.latitude,
          _mapController.camera.center.longitude,
        );
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
          // CAPA DE FONDO (Solo visible si no hay TileLayer encima, para el modo Explorar)
          if (_tabSeleccionada == 0)
            Positioned.fill(
              child: Container(color: const Color(0xFFF5F7FA)),
            ),

          // MAPA INTERACTIVO
          FlutterMap(
            mapController: _mapController,
            options: MapOptions(
              initialCenter: const LatLng(28.1400, -16.5230),
              initialZoom: 9.4,
              onMapEvent: (event) {
                if (event is MapEventMoveEnd && _tabSeleccionada == 1) {
                  _obtenerScoreDePunto(
                    event.camera.center.latitude,
                    event.camera.center.longitude,
                  );
                }
              },
            ),
            children: [
              // 1. TILE LAYER CONDICIONAL
              // Solo mostramos el mapa de calles si estamos en "Mi Zona" (Tab 1)
              if (_tabSeleccionada == 1)
                TileLayer(
                  // Usamos CartoDB Positron porque es limpio y tiene nombres de calles
                  urlTemplate: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
                  subdomains: const ['a', 'b', 'c', 'd'],
                  userAgentPackageName: 'com.tenerifelifescore.app',
                ),

              // 2. CAPA DE HEXÁGONOS
              // Solo mostramos los colores si estamos en "Explorar" (Tab 0)
              if (_tabSeleccionada == 0) 
                PolygonLayer(polygons: poligonosADibujar),
            ],
          ),

          // CHINCHETA CENTRAL (MODO MI ZONA)
          if (_tabSeleccionada == 1)
            const IgnorePointer(
              child: Center(
                child: Padding(
                  padding: EdgeInsets.only(bottom: 40),
                  child: Icon(Icons.location_on, color: Colors.red, size: 50),
                ),
              ),
            ),

          // PANTALLA DE CARGA
          if (isLoading)
            Container(
              color: Colors.white70,
              child: const Center(child: CircularProgressIndicator()),
            ),

          // PANELES DESLIZANTES
          if (_tabSeleccionada == 0)
            DraggableScrollableSheet(
              initialChildSize: 0.4,
              minChildSize: 0.15,
              maxChildSize: 0.75,
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

          if (_tabSeleccionada == 1) _buildResumenZonaPunto(),
        ],
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _tabSeleccionada,
        selectedItemColor: AppColors.primary,
        onTap: (index) {
          setState(() => _tabSeleccionada = index);
          
          // Al cambiar de pestaña, recalculamos cosas si hace falta
          if (index == 1) {
            // Si pasamos a Mi Zona, hacemos un cálculo inicial en el centro actual
             _obtenerScoreDePunto(
              _mapController.camera.center.latitude,
              _mapController.camera.center.longitude,
            );
          }
        },
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.map), label: "Explorar"),
          BottomNavigationBarItem(icon: Icon(Icons.gps_fixed), label: "Mi Zona"),
        ],
      ),
    );
  }

  // ... (El resto de métodos _buildResumenZonaPunto, _buildPanelBody y _buildGroupList y la clase _GroupCard SE MANTIENEN IGUAL QUE ANTES) ...
  // COPIA AQUÍ ABAJO TUS MÉTODOS AUXILIARES QUE YA TENÍAS
  
  Widget _buildResumenZonaPunto() {
    return Align(
      alignment: Alignment.bottomCenter,
      child: Container(
        margin: const EdgeInsets.all(20),
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(20),
          boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 10)],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (isCalculandoPunto)
              const LinearProgressIndicator()
            else if (datosPuntoEspecifico != null) ...[
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text("LifeScore en este punto:", style: TextStyle(fontWeight: FontWeight.bold)),
                      Text(
                        "${datosPuntoEspecifico!['score']}/10",
                        style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: AppColors.primary),
                      ),
                    ],
                  ),
                  // --- BOTÓN NUEVO PARA EDITAR PERFIL ---
                  IconButton.filledTonal(
                    icon: const Icon(Icons.tune),
                    onPressed: _abrirConfiguracionModal, // <--- Nueva función
                    tooltip: "Ajustar mis preferencias",
                  ),
                ],
              ),
              const Divider(),
              const Text("Desglose de servicios cercanos:", style: TextStyle(fontSize: 12, color: Colors.grey)),
              const SizedBox(height: 10),
              SizedBox(
                height: 100,
                child: ListView(
                  shrinkWrap: true,
                  children: (datosPuntoEspecifico!['detalles'] as Map<String, dynamic>).entries.map((e) {
                    return Padding(
                      padding: const EdgeInsets.symmetric(vertical: 2),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(e.key, style: const TextStyle(fontSize: 13)),
                          Text(e.value.toStringAsFixed(2), style: const TextStyle(fontWeight: FontWeight.bold)),
                        ],
                      ),
                    );
                  }).toList(),
                ),
              ),
            ] else
              const Text("Mueve el mapa para escanear una zona"),
          ],
        ),
      ),
    );
  }

  // Añadimos el parámetro opcional {StateSetter? extraSetState}
  Widget _buildPanelBody(ScrollController scrollController, {StateSetter? extraSetState}) {
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
                  onSelected: (sel) {
                    // Aquí actualizamos tanto la pantalla principal como el modal
                    setState(() => macroSeleccionada = macro);
                    if (extraSetState != null) extraSetState(() => macroSeleccionada = macro);
                  },
                  selectedColor: AppColors.primary,
                  labelStyle: TextStyle(color: isSelected ? Colors.white : Colors.black87),
                  showCheckmark: false,
                ),
              );
            }).toList(),
          ),
        ),
        const Divider(height: 30, thickness: 1),
        
        // Pasamos el extraSetState hacia abajo
        if (macroSeleccionada != null) 
          ..._buildGroupList(macroSeleccionada!, extraSetState: extraSetState),
          
        const SizedBox(height: 40),
      ],
    );
  }

  // Añadimos el parámetro opcional {StateSetter? extraSetState}
  List<Widget> _buildGroupList(String macro, {StateSetter? extraSetState}) {
    final gruposMap = arbolConfig![macro]!;
    final gruposOrdenados = gruposMap.keys.toList()..sort();

    return gruposOrdenados.map((grupoKey) {
      return _GroupCard(
        title: grupoKey,
        sliderValue: sliderValues[grupoKey] ?? 3.0,
        items: gruposMap[grupoKey]!,
        checkValues: checkValues,
        onSliderChanged: (val) {
          // 1. Actualizamos el dato real
          sliderValues[grupoKey] = val;

          // 2. Si estamos en el modal, usamos su setState especial
          if (extraSetState != null) {
            extraSetState(() {}); 
          } 
          // 3. Siempre actualizamos el estado principal por si acaso
          setState(() {}); 
        },
        onSliderEnd: (val) {
          // Solo llamamos a la API si estamos en la pestaña principal
          // (Si estamos en el modal, se calcula al cerrar)
          if (_tabSeleccionada == 0) {
            _actualizarMapa();
          }
        },
        onCheckChanged: (idsAfectados, nuevoEstado) {
          // Misma lógica para los checkboxes
          for (var id in idsAfectados) {
            checkValues[id] = nuevoEstado;
          }
          
          if (extraSetState != null) extraSetState(() {});
          setState(() {});

          if (_tabSeleccionada == 0) _actualizarMapa();
        },
      );
    }).toList();
  }
}

class _GroupCard extends StatelessWidget {
  final String title;
  final double sliderValue;
  final List<ConfigItem> items;
  final Map<String, bool> checkValues;
  final ValueChanged<double> onSliderChanged;
  final ValueChanged<double> onSliderEnd;
  final Function(List<String>, bool) onCheckChanged;

  const _GroupCard({
    required this.title,
    required this.sliderValue,
    required this.items,
    required this.checkValues,
    required this.onSliderChanged,
    required this.onSliderEnd,
    required this.onCheckChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
      elevation: 0,
      color: AppColors.surface,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(15),
        side: BorderSide(color: Colors.grey.shade200),
      ),
      child: ExpansionTile(
        shape: const RoundedRectangleBorder(side: BorderSide(color: Colors.transparent)),
        collapsedShape: const RoundedRectangleBorder(side: BorderSide(color: Colors.transparent)),
        tilePadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        title: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Expanded(child: Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16))),
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
            onChangeEnd: onSliderEnd,
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