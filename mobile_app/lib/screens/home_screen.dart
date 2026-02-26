import 'package:flutter/material.dart';
import '../config/theme/app_colors.dart';
import '../services/api_services.dart'; // Importamos nuestro "teléfono"

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ApiService _apiService = ApiService();
  
  // ESTADO DE LA APP
  bool isLoading = true;
  String? errorMessage;
  
  // Aquí guardamos lo que nos manda Python: { "Salud": ["Farmacia", ...], "Ocio": [...] }
  Map<String, List<String>>? categoriasConfig;
  
  // Aquí guardamos los valores de los sliders del usuario (0.0 a 5.0)
  Map<String, double> sliderValues = {};

  @override
  void initState() {
    super.initState();
    _cargarDatosIniciales();
  }

  // Función para llamar a la API al arrancar
  Future<void> _cargarDatosIniciales() async {
    try {
      // 1. Pedimos la config a Python
      final datos = await _apiService.getCategories();
      
      // 2. Inicializamos los sliders a 3.0 (valor medio)
      final Map<String, double> iniciales = {};
      datos.forEach((key, value) {
        iniciales[key] = 3.0;
      });

      // 3. Actualizamos la pantalla
      setState(() {
        categoriasConfig = datos;
        sliderValues = iniciales;
        isLoading = false;
      });
      
    } catch (e) {
      setState(() {
        errorMessage = "No pude conectar con el PC 😢\nRevisa la IP en api_service.dart\nError: $e";
        isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
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
          // CAPA 1: EL MAPA (Fondo)
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

          // CAPA 2: EL PANEL DESLIZANTE
          DraggableScrollableSheet(
            initialChildSize: 0.4,
            minChildSize: 0.1,
            maxChildSize: 0.85,
            builder: (context, scrollController) {
              return Container(
                decoration: const BoxDecoration(
                  color: AppColors.surface,
                  borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
                  boxShadow: [
                    BoxShadow(color: Colors.black26, blurRadius: 15, spreadRadius: 2)
                  ],
                ),
                child: _buildPanelContent(scrollController),
              );
            },
          ),
        ],
      ),
    );
  }

  // Contenido del panel (Gestión de estados: Cargando, Error o Lista)
  Widget _buildPanelContent(ScrollController scrollController) {
    // A. Si está cargando...
    if (isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    // B. Si hubo error...
    if (errorMessage != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.wifi_off, size: 40, color: Colors.red),
              const SizedBox(height: 10),
              Text(errorMessage!, textAlign: TextAlign.center),
              const SizedBox(height: 10),
              ElevatedButton(
                onPressed: _cargarDatosIniciales, 
                child: const Text("Reintentar")
              )
            ],
          ),
        ),
      );
    }

    // C. Si todo fue bien: ¡LISTA DE SLIDERS! 🎚️
    // Ordenamos las categorías alfabéticamente para que salgan bonitas
    final listaCategorias = categoriasConfig!.keys.toList()..sort();

    return ListView.separated(
      controller: scrollController,
      padding: const EdgeInsets.all(20),
      itemCount: listaCategorias.length + 1, // +1 para el título
      separatorBuilder: (_, __) => const SizedBox(height: 20),
      itemBuilder: (context, index) {
        
        // Cabecera
        if (index == 0) {
          return Center(
            child: Container(
              width: 40, height: 5,
              margin: const EdgeInsets.only(bottom: 10),
              decoration: BoxDecoration(color: Colors.grey[300], borderRadius: BorderRadius.circular(10)),
            ),
          );
        }

        // Sliders reales
        final categoria = listaCategorias[index - 1];
        final valor = sliderValues[categoria] ?? 3.0;

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  categoria, // Ej: "Salud", "Ocio"
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                ),
                Text(
                  valor.toStringAsFixed(0), // Ej: "3"
                  style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary),
                ),
              ],
            ),
            Slider(
              value: valor,
              min: 0,
              max: 5,
              divisions: 5,
              label: valor.toStringAsFixed(0),
              onChanged: (nuevoValor) {
                setState(() {
                  sliderValues[categoria] = nuevoValor;
                });
                // AQUÍ EN EL FUTURO LLAMAREMOS A _calcularMapa()
              },
            ),
          ],
        );
      },
    );
  }
}