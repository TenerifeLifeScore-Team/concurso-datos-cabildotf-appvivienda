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
  
  // DATOS: Macro -> { Grupo : [ConfigItem] }
  Map<String, Map<String, List<ConfigItem>>>? arbolConfig;
  
  // ESTADO UI
  String? macroSeleccionada;
  Map<String, double> sliderValues = {}; // Sliders (0-5)
  
  // ESTADO CHECKBOXES (ID interno -> true/false)
  // Guardamos cada ID individualmente para enviarlo fácil a Python
  Map<String, bool> checkValues = {}; 

  @override
  void initState() {
    super.initState();
    _cargarDatosIniciales();
  }

  Future<void> _cargarDatosIniciales() async {
    try {
      final datos = await _apiService.getCategories();
      
      final Map<String, double> inicialesSliders = {};
      final Map<String, bool> inicialesChecks = {};
      
      // Recorremos todo para inicializar valores
      datos.forEach((macro, grupos) {
        grupos.forEach((grupo, items) {
          inicialesSliders[grupo] = 3.0; // Slider al medio
          
          for (var item in items) {
            // Activamos por defecto todos los IDs internos de este item
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
    // ... (El Scaffold, AppBar y Stack son idénticos al anterior, no cambian) ...
    // COPIA AQUÍ LA PARTE DEL SCAFFOLD QUE YA TENÍAS HASTA EL _buildPanelBody
    return Scaffold(
      resizeToAvoidBottomInset: false,
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
          Positioned.fill(
            child: Container(color: AppColors.background), // Placeholder mapa
          ),
          DraggableScrollableSheet(
            initialChildSize: 0.5,
            minChildSize: 0.15,
            maxChildSize: 0.8,
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
    if (isLoading) return const Center(child: CircularProgressIndicator());
    if (errorMessage != null) return Center(child: Text(errorMessage!));
    if (arbolConfig == null) return const SizedBox();

    final macros = arbolConfig!.keys.toList()..sort();

    return ListView(
      controller: scrollController,
      padding: EdgeInsets.zero,
      children: [
        // TITULO Y TABS
        const Padding(
          padding: EdgeInsets.symmetric(horizontal: 20, vertical: 0),
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

        // LISTA DE GRUPOS (Sliders + Expander)
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
      final valorSlider = sliderValues[grupoKey] ?? 3.0;
      final itemsConfig = gruposMap[grupoKey]!; // Lista de objetos ConfigItem (Farmacia, Hospital...)
      
      // Creamos un widget personalizado para mantener limpio el código
      return _GroupCard(
        title: grupoKey,
        sliderValue: valorSlider,
        items: itemsConfig,
        checkValues: checkValues,
        onSliderChanged: (val) => setState(() => sliderValues[grupoKey] = val),
        onCheckChanged: (idsAfectados, nuevoEstado) {
          setState(() {
            for (var id in idsAfectados) {
              checkValues[id] = nuevoEstado;
            }
          });
        },
      );
    }).toList();
  }
}

// WIDGET AISLADO PARA LA TARJETA DEL GRUPO (Slider + Expander)
// ... Todo el código anterior de HomeScreen permanece igual ...

// WIDGET AISLADO PARA LA TARJETA DEL GRUPO (Slider + Expander)
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
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
      child: ExpansionTile(
        // Quitamos bordes raros
        shape: const RoundedRectangleBorder(side: BorderSide(color: Colors.transparent)),
        collapsedShape: const RoundedRectangleBorder(side: BorderSide(color: Colors.transparent)),
        tilePadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        
        // CABECERA
        title: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Expanded( // <--- Envolvemos el texto en Expanded
              child: Text(
                title, 
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
              ),
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
        // Subtítulo: Ahora solo contiene el Slider
        subtitle: Padding(
          padding: const EdgeInsets.only(top: 8.0),
          child: Slider(
            value: sliderValue,
            min: 0, 
            max: 5, 
            divisions: 5,
            onChanged: onSliderChanged,
          ),
        ),
        
        // CONTENIDO EXPANDIDO
        children: [
          // Pequeño texto de ayuda al expandir
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
          
          // Lista de checkboxes agrupados
          ...items.map((item) {
            final isChecked = item.ids.every((id) => checkValues[id] == true);
            
            return CheckboxListTile(
              title: Text(item.label, style: const TextStyle(fontSize: 14)),
              value: isChecked,
              dense: true,
              activeColor: AppColors.primary,
              controlAffinity: ListTileControlAffinity.leading,
              onChanged: (bool? val) {
                if (val != null) {
                  onCheckChanged(item.ids, val);
                }
              },
            );
          }).toList(),
          
          // Un poco de aire al final
          const SizedBox(height: 10),
        ],
      ),
    );
  }
}