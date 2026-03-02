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
          children: [
            if (isLoading)
              const LinearProgressIndicator()
            else if (data != null) ...[
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
              const Divider(),
              const Text("Desglose de servicios cercanos:", style: TextStyle(fontSize: 12, color: Colors.grey)),
              const SizedBox(height: 10),
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
              const Text("Mueve el mapa para escanear una zona"),
          ],
        ),
      ),
    );
  }
}