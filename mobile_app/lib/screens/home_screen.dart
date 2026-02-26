import 'package:flutter/material.dart';
import '../config/theme/app_colors.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  // Aquí definiremos más adelante las variables para los sliders
  bool isLoading = false; // Lo pondremos a true cuando conectemos el backend

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      // Barra superior
      appBar: AppBar(
        title: const Text("Tenerife LifeScore 🇮🇨"),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              // TODO: Recargar datos
            },
          ),
        ],
      ),
      
      // Cuerpo: Usamos un Stack para poner el mapa debajo y los controles encima
      body: Stack(
        children: [
          // CAPA 1: El Mapa (Fondo)
          Positioned.fill(
            child: Container(
              color: AppColors.background,
              child: const Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.map, size: 50, color: Colors.grey),
                    SizedBox(height: 10),
                    Text("Aquí irá el Mapa"),
                  ],
                ),
              ),
            ),
          ),

          // CAPA 2: Panel de Control (Sliders)
          // Usamos un DraggableScrollableSheet para que sea deslizable como Google Maps
          DraggableScrollableSheet(
            initialChildSize: 0.3, // Empieza ocupando el 30% de la pantalla
            minChildSize: 0.1,     // Se puede bajar hasta el 10%
            maxChildSize: 0.8,     // Se puede subir hasta el 80%
            builder: (context, scrollController) {
              return Container(
                decoration: const BoxDecoration(
                  color: AppColors.surface,
                  borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black12,
                      blurRadius: 10,
                      spreadRadius: 2,
                    )
                  ],
                ),
                child: ListView(
                  controller: scrollController,
                  padding: const EdgeInsets.all(20),
                  children: [
                    // Tirador visual
                    Center(
                      child: Container(
                        width: 40,
                        height: 5,
                        margin: const EdgeInsets.only(bottom: 20),
                        decoration: BoxDecoration(
                          color: Colors.grey[300],
                          borderRadius: BorderRadius.circular(10),
                        ),
                      ),
                    ),
                    
                    const Text(
                      "Personaliza tu búsqueda",
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 20),
                    
                    // Aquí inyectaremos los sliders dinámicos luego
                    _buildPlaceholderSlider("Salud"),
                    _buildPlaceholderSlider("Ocio"),
                    _buildPlaceholderSlider("Naturaleza"),
                  ],
                ),
              );
            },
          ),
        ],
      ),
    );
  }

  // Widget auxiliar temporal para ver cómo queda
  Widget _buildPlaceholderSlider(String label) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label, style: const TextStyle(fontWeight: FontWeight.w500)),
            Text("3/5", style: TextStyle(color: AppColors.primary)),
          ],
        ),
        Slider(
          value: 3,
          min: 0,
          max: 5,
          divisions: 5,
          onChanged: (val) {}, // No hace nada todavía
        ),
        const SizedBox(height: 10),
      ],
    );
  }
}