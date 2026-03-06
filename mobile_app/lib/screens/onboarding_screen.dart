import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../config/theme/app_colors.dart'; // Ajusta la ruta a tus colores
import 'home_screen.dart'; // Ajusta la ruta a tu HomeScreen

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final PageController _pageController = PageController();
  int _paginaActual = 0;

  // INSTRUCCIONES
  final List<Map<String, dynamic>> _paginas = [
    {
      "titulo": "Bienvenido a LifeScore 🇮🇨",
      "texto": "Descubre tu zona ideal para vivir en Tenerife basándote en lo que realmente te importa.",
      "icono": Icons.travel_explore_rounded, // Cámbialo por "imagen": "assets/images/tu_foto.png" si usas fotos
    },
    {
      "titulo": "Ajusta tus Preferencias",
      "texto": "Abre el menú de ajustes y usa los sliders para darle más importancia a zonas verdes, ocio, transporte...",
      "icono": Icons.tune_rounded,
    },
    {
      "titulo": "IA a tu servicio",
      "texto": "Toca cualquier zona en el mapa y nuestro asesor virtual analizará los datos para darte un resumen al instante.",
      "icono": Icons.auto_awesome_rounded,
    }
  ];

  // Función que guarda que el usuario ya ha visto esto y lo manda a la app
  Future<void> _finalizarOnboarding() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('ha_visto_onboarding', true);

    if (mounted) {
      // Magia: Preguntamos si venimos del botón de Info o si acabamos de abrir la app
      if (Navigator.canPop(context)) {
        // Si venimos del botón de Info, simplemente "cerramos" las instrucciones
        Navigator.pop(context);
      } else {
        // Si es la primera vez que abrimos la app, cargamos el HomeScreen
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (context) => const HomeScreen()),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Column(
          children: [
            // --- BOTÓN DE SALTAR (Arriba a la derecha) ---
            Align(
              alignment: Alignment.topRight,
              child: TextButton(
                onPressed: _finalizarOnboarding,
                child: const Text("Saltar", style: TextStyle(color: Colors.grey, fontSize: 16)),
              ),
            ),

            // --- LAS PÁGINAS DESLIZABLES ---
            Expanded(
              child: PageView.builder(
                controller: _pageController,
                onPageChanged: (index) {
                  setState(() => _paginaActual = index);
                },
                itemCount: _paginas.length,
                itemBuilder: (context, index) {
                  final pagina = _paginas[index];
                  return Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 40),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        // Aquí pones tu icono o imagen
                        Icon(pagina["icono"], size: 120, color: AppColors.primary),
                        /* SI QUIERES USAR TUS IMÁGENES, QUITA EL ICON Y USA ESTO:
                           Image.asset(pagina["imagen"], height: 250),
                        */
                        const SizedBox(height: 40),
                        Text(
                          pagina["titulo"],
                          textAlign: TextAlign.center,
                          style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: 20),
                        Text(
                          pagina["texto"],
                          textAlign: TextAlign.center,
                          style: TextStyle(fontSize: 16, color: Colors.grey[600], height: 1.5),
                        ),
                      ],
                    ),
                  );
                },
              ),
            ),

            // --- CONTROLES INFERIORES (Puntitos y Botón Siguiente) ---
            Padding(
              padding: const EdgeInsets.all(30.0),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  // Los puntitos indicadores
                  Row(
                    children: List.generate(
                      _paginas.length,
                      (index) => Container(
                        margin: const EdgeInsets.only(right: 8),
                        height: 10,
                        width: _paginaActual == index ? 25 : 10, // Se alarga si es la página actual
                        decoration: BoxDecoration(
                          color: _paginaActual == index ? AppColors.primary : Colors.grey[300],
                          borderRadius: BorderRadius.circular(5),
                        ),
                      ),
                    ),
                  ),

                  // El botón de Siguiente / Empezar
                  ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(30)),
                      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                    ),
                    onPressed: () {
                      if (_paginaActual == _paginas.length - 1) {
                        _finalizarOnboarding(); // Si es la última, entramos a la app
                      } else {
                        _pageController.nextPage( // Si no, pasamos de página
                          duration: const Duration(milliseconds: 300),
                          curve: Curves.easeInOut,
                        );
                      }
                    },
                    child: Text(_paginaActual == _paginas.length - 1 ? "Empezar" : "Siguiente"),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}