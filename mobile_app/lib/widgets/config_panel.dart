import 'package:flutter/material.dart';
import '../config/theme/app_colors.dart';
import '../services/api_services.dart';
import 'group_card.dart';

class ConfigPanel extends StatelessWidget {
  final ScrollController scrollController;
  final Map<String, Map<String, List<ConfigItem>>>? arbolConfig;
  final String? macroSeleccionada;
  final Map<String, double> sliderValues;
  final Map<String, bool> checkValues;
  final String? errorMessage;
  
  final ValueChanged<String> onMacroChanged;
  final Function(String group, double value) onSliderChanged;
  final Function(double value) onSliderEnd;
  final Function(List<String> ids, bool value) onCheckChanged;
  
  final StateSetter? extraSetState;

  const ConfigPanel({
    super.key,
    required this.scrollController,
    required this.arbolConfig,
    required this.macroSeleccionada,
    required this.sliderValues,
    required this.checkValues,
    required this.onMacroChanged,
    required this.onSliderChanged,
    required this.onSliderEnd,
    required this.onCheckChanged,
    this.errorMessage,
    this.extraSetState,
  });

  @override
  Widget build(BuildContext context) {
    if (errorMessage != null) return Center(child: Text(errorMessage!));
    if (arbolConfig == null) return const SizedBox();

    final List<String> ordenDeseado = [
      "Servicios básicos",
      "Ocio y estilo de vida",
      "Restauración y socialización",
      "Consumo y vida diaria",
    ];

    final macros = arbolConfig!.keys.toList()
      ..sort((a, b) {
        int indexA = ordenDeseado.indexOf(a);
        int indexB = ordenDeseado.indexOf(b);
        if (indexA == -1) indexA = 999;
        if (indexB == -1) indexB = 999;
        return indexA.compareTo(indexB);
      });

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
                    onMacroChanged(macro);
                    if (extraSetState != null) extraSetState!(() {});
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
      return GroupCard(
        title: grupoKey,
        sliderValue: sliderValues[grupoKey] ?? 3.0,
        items: gruposMap[grupoKey]!,
        checkValues: checkValues,
        
        onSliderChanged: (val) {
          onSliderChanged(grupoKey, val);
          if (extraSetState != null) extraSetState!(() {});
        },
        onSliderEnd: onSliderEnd,
        onCheckChanged: (ids, val) {
          onCheckChanged(ids, val);
          if (extraSetState != null) extraSetState!(() {});
        },
      );
    }).toList();
  }
}