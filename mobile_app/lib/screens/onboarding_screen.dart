import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../config/theme/app_colors.dart'; 
import 'home_screen.dart';

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final PageController _pageController = PageController();
  int _paginaActual = 0;

  final List<Map<String, dynamic>> _paginas = [
    {
      "titulo": "Bienvenido a Tenerife LifeScore",
      "texto": "Descubre tu zona ideal para vivir en Tenerife. Nuestra app evalúa cada rincón de la isla basándose en lo que realmente te importa para encontrar tu lugar perfecto.",
      "imagen": "assets/icons/icono_binario.png", 
    },
    {
      "titulo": "Explorar vs Mi Zona",
      "texto": "Usa la pestaña 'Explorar' para ver el mapa de calor interactivo de toda la isla. Cambia a 'Mi Zona' si prefieres buscar una dirección concreta y analizar todo su entorno.",
      "icono": Icons.map_rounded,
    },
    {
      "titulo": "Perfiles Rápidos",
      "texto": "¿Eres estudiante, vienes en familia o buscas salir de fiesta? Toca el icono de perfil arriba a la izquierda para cargar al instante los filtros ideales para tu estilo de vida.",
      "icono": Icons.people_alt_rounded,
    },
    {
      "titulo": "Ajusta a tu Medida",
      "texto": "Abre el menú de ajustes para usar los sliders y darle más importancia a los servicios que quieras. ¡Abre las tarjetas para afinar marcando o desmarcando servicios específicos!",
      "icono": Icons.tune_rounded,
    },
    {
      "titulo": "IA a tu servicio",
      "texto": "Toca cualquier hexágono en el mapa o analiza una ubicación en \"Mi Zona\" y nuestro asesor virtual analizará cientos de datos al instante para darte un resumen detallado de los pros y contras de esa zona.",
      "icono": Icons.auto_awesome_rounded,
    }
  ];

  Future<void> _finalizarOnboarding() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('ha_visto_onboarding', true);

    if (mounted) {
      if (Navigator.canPop(context)) {
        Navigator.pop(context);
      } else {
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
            Align(
              alignment: Alignment.topRight,
              child: TextButton(
                onPressed: _finalizarOnboarding,
                child: const Text("Saltar", style: TextStyle(color: Colors.grey, fontSize: 16)),
              ),
            ),

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
                        if (pagina.containsKey("imagen"))
                          Image.asset(pagina["imagen"], height: 130, color: AppColors.primary),
                          
                        if (pagina.containsKey("icono"))
                          Icon(pagina["icono"], size: 120, color: AppColors.primary),
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

            Padding(
              padding: const EdgeInsets.all(30.0),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: List.generate(
                      _paginas.length,
                      (index) => Container(
                        margin: const EdgeInsets.only(right: 8),
                        height: 10,
                        width: _paginaActual == index ? 25 : 10, 
                        decoration: BoxDecoration(
                          color: _paginaActual == index ? AppColors.primary : Colors.grey[300],
                          borderRadius: BorderRadius.circular(5),
                        ),
                      ),
                    ),
                  ),

                  ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(30)),
                      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                    ),
                    onPressed: () {
                      if (_paginaActual == _paginas.length - 1) {
                        _finalizarOnboarding();
                      } else {
                        _pageController.nextPage(
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