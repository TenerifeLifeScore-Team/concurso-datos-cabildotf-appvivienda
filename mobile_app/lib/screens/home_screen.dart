import 'package:flutter/material.dart';
import '../config/theme/app_colors.dart';
import '../services/api_services.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ApiService _apiService = ApiService();
  
  bool isLoading = true;
  String? errorMessage;
  
  // ESTRUCTURA DE DATOS NUEVA:
  // Macro -> { Grupo : [Items] }
  Map<String, Map<String, List<String>>>? arbolConfig;
  
  // Estado de la UI
  String? macroSeleccionada; // ¿Qué pestaña estamos viendo? ("Servicios", "Ocio"...)
  Map<String, double> sliderValues = {}; // Valores de los sliders (0-5)

  @override
  void initState() {
    super.initState();
    _cargarDatosIniciales();
  }

  Future<void> _cargarDatosIniciales() async {
    try {
      final datos = await _apiService.getCategories();
      
      // Inicializamos sliders a 3.0 si están vacíos
      final Map<String, double> iniciales = {};
      datos.forEach((macro, grupos) {
        grupos.forEach((grupo, items) {
          iniciales[grupo] = 3.0;
        });
      });

      // Ordenamos las macros para que siempre salgan en el mismo orden
      final primerMacro = datos.keys.toList()..sort();
      
      setState(() {
        arbolConfig = datos;
        sliderValues = iniciales;
        // Seleccionamos la primera pestaña por defecto
        macroSeleccionada = primerMacro.isNotEmpty ? primerMacro.first : null;
        isLoading = false;
      });
      
    } catch (e) {
      setState(() {
        errorMessage = "Error de conexión:\n$e";
        isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      resizeToAvoidBottomInset: false, // Evita que el teclado rompa el layout
      appBar: AppBar(
        title: const Text("Tenerife LifeScore 🇮🇨"),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              setState(() { isLoading = true; errorMessage = null; });
              _cargarDatosIniciales();
            },
          ),
        ],
      ),
      body: Stack(
        children: [
          // FONDO (MAPA)
          Positioned.fill(
            child: Container(
              color: AppColors.background,
              child: Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.map_outlined, size: 60, color: Colors.grey[300]),
                    const SizedBox(height: 10),
                    const Text("El mapa interactivo irá aquí"),
                  ],
                ),
              ),
            ),
          ),

          // PANEL DESLIZANTE
          DraggableScrollableSheet(
            initialChildSize: 0.5,
            minChildSize: 0.15,
            maxChildSize: 0.9,
            builder: (context, scrollController) {
              return Container(
                decoration: const BoxDecoration(
                  color: AppColors.surface,
                  borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
                  boxShadow: [
                    BoxShadow(color: Colors.black26, blurRadius: 15, spreadRadius: 2)
                  ],
                ),
                child: Column(
                  children: [
                    // 1. TIRADOR (Para arrastrar)
                    Center(
                      child: Container(
                        width: 40, height: 5,
                        margin: const EdgeInsets.symmetric(vertical: 10),
                        decoration: BoxDecoration(
                          color: Colors.grey[300], 
                          borderRadius: BorderRadius.circular(10)
                        ),
                      ),
                    ),

                    // 2. CONTENIDO PRINCIPAL (Con scroll)
                    Expanded(
                      child: _buildPanelBody(scrollController),
                    ),
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
    if (isLoading) return const Center(child: CircularProgressIndicator());
    if (errorMessage != null) return Center(child: Text(errorMessage!));
    if (arbolConfig == null) return const SizedBox();

    // Obtenemos las categorías (Tabs) ordenadas
    final macros = arbolConfig!.keys.toList()..sort();

    return ListView(
      controller: scrollController, // Importante para que el panel se deslice
      padding: EdgeInsets.zero,
      children: [
        
        // A. TÍTULO Y PESTAÑAS (Header)
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 0),
          child: const Text(
            "Personaliza tu búsqueda",
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
          ),
        ),
        const SizedBox(height: 15),

        // BARRA DE PESTAÑAS (Scroll Horizontal)
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
                  onSelected: (bool selected) {
                    if (selected) {
                      setState(() {
                        macroSeleccionada = macro;
                      });
                    }
                  },
                  // Estilos personalizados
                  selectedColor: AppColors.primary,
                  labelStyle: TextStyle(
                    color: isSelected ? Colors.white : Colors.black87,
                    fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                  ),
                  backgroundColor: Colors.grey[200],
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                  showCheckmark: false, // Quitamos el check ✅ para que parezca un botón
                  side: BorderSide.none,
                ),
              );
            }).toList(),
          ),
        ),
        
        const Divider(height: 30, thickness: 1),

        // B. LISTA DE SLIDERS (Del grupo seleccionado)
        if (macroSeleccionada != null)
          ..._buildSlidersList(macroSeleccionada!),
          
        // Espacio extra al final para que no se corte
        const SizedBox(height: 40),
      ],
    );
  }

  List<Widget> _buildSlidersList(String macro) {
    // Obtenemos los grupos de esa macro (ej: "Salud Vital", "Educación")
    final gruposMap = arbolConfig![macro]!;
    final gruposOrdenados = gruposMap.keys.toList()..sort();

    return gruposOrdenados.map((grupo) {
      final valor = sliderValues[grupo] ?? 3.0;
      final items = gruposMap[grupo]!; // Lista de ejemplos (Farmacias, Colegios...)
      
      // Texto descriptivo (ej: "Farmacias, Hospitales...")
      final descripcion = items.take(3).join(", ") + (items.length > 3 ? "..." : "");

      return Padding(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Encabezado del Slider
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(grupo, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 16)),
                      Text(descripcion, 
                        style: TextStyle(color: Colors.grey[600], fontSize: 12),
                        maxLines: 1, overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppColors.primary.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Text(
                    valor.toStringAsFixed(0),
                    style: const TextStyle(color: AppColors.primary, fontWeight: FontWeight.bold),
                  ),
                ),
              ],
            ),
            
            // El Slider
            Slider(
              value: valor,
              min: 0, max: 5, divisions: 5,
              label: valor.toStringAsFixed(0),
              onChanged: (v) {
                setState(() => sliderValues[grupo] = v);
              },
            ),
          ],
        ),
      );
    }).toList();
  }
}