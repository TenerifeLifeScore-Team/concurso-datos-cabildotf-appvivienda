import 'package:flutter/material.dart';
import '../config/theme/app_colors.dart';

class ResultCard extends StatelessWidget {
  final Map<String, dynamic>? data;
  final bool isLoading;
  final VoidCallback onTunePressed;

  const ResultCard({
    super.key,
    required this.data,
    required this.isLoading,
    required this.onTunePressed,
  });

  @override
  Widget build(BuildContext context) {
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
          crossAxisAlignment: CrossAxisAlignment.stretch, // Para que ocupe todo el ancho
          children: [
            if (isLoading)
              Column(
                children: const [
                  Text("Analizando zona con IA...", style: TextStyle(color: Colors.grey)),
                  SizedBox(height: 10),
                  LinearProgressIndicator(),
                ],
              )
            else if (data != null) ...[
              // 1. CABECERA: Puntuación y Botón Ajustes
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text("LifeScore en este punto:", style: TextStyle(fontWeight: FontWeight.bold)),
                      Text(
                        "${data!['score']}/10",
                        style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: AppColors.primary),
                      ),
                    ],
                  ),
                  IconButton.filledTonal(
                    icon: const Icon(Icons.tune),
                    onPressed: onTunePressed,
                    tooltip: "Ajustar mis preferencias",
                  ),
                ],
              ),
              
              const SizedBox(height: 15),

              // 2. RESUMEN IA (NUEVO BLOQUE) ✨
              if (data!.containsKey('resumen_ia')) 
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppColors.primary.withOpacity(0.1), // Fondo suave
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: AppColors.primary.withOpacity(0.3)),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.auto_awesome, size: 20, color: AppColors.primary), // Icono de IA
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          data!['resumen_ia'],
                          style: const TextStyle(fontSize: 14, fontStyle: FontStyle.italic, color: Colors.black87),
                        ),
                      ),
                    ],
                  ),
                ),

              const SizedBox(height: 15),
              const Divider(),
              const Text("Desglose de servicios cercanos:", style: TextStyle(fontSize: 12, color: Colors.grey)),
              const SizedBox(height: 10),
              
              // 3. LISTA DE DETALLES
              SizedBox(
                height: 100,
                child: ListView(
                  shrinkWrap: true,
                  children: (data!['detalles'] as Map<String, dynamic>).entries.map((e) {
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
              const Center(child: Text("Mueve el mapa para escanear una zona")),
          ],
        ),
      ),
    );
  }
}