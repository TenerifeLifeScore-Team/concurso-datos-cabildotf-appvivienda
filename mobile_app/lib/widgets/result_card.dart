import 'package:flutter/material.dart';
import '../config/theme/app_colors.dart';

class ResultCard extends StatelessWidget {
  final String? placeName; // <--- NUEVO: Para mostrar el nombre de la calle o barrio
  final double score; 
  final String? iaSummary; 
  final bool isLoadingIA; 
  final VoidCallback onTunePressed;
  final Alignment positionAlignment;
  final VoidCallback onClosePressed; 

  const ResultCard({
    super.key,
    this.placeName, // Opcional, por si en algún momento no hay nombre
    required this.score,
    required this.iaSummary,
    required this.isLoadingIA,
    required this.onTunePressed,
    required this.onClosePressed,
    this.positionAlignment = Alignment.bottomCenter,  // Por defecto abajo
  });

  @override
  Widget build(BuildContext context) {
    // Definimos color según la nota para el círculo
    Color scoreColor = score >= 8 ? Colors.green : (score >= 5 ? Colors.orange : Colors.red);
    String scoreText = score >= 8 ? "¡Zona Excelente!" : (score >= 5 ? "Zona Aceptable" : "Zona Baja");

    return Align(
      alignment: positionAlignment, // <--- 1. Usamos la variable en lugar de dejarlo fijo
      child: Container(
        margin: EdgeInsets.only( // <--- 2. Hacemos el margen dinámico
          left: 20, 
          right: 20, 
          top: positionAlignment == Alignment.topCenter ? 25 : 20, 
          bottom: 20,
        ),
        padding: const EdgeInsets.fromLTRB(20, 15, 20, 20),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(24),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.15),
              blurRadius: 20,
              offset: const Offset(0, 10),
            )
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // --- 0. NOMBRE DE LA ZONA (NUEVO) ---
            if (placeName != null && placeName!.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(bottom: 15, left: 5),
                child: Row(
                  children: [
                    const Icon(Icons.place, size: 18, color: Colors.grey),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        placeName!,
                        style: const TextStyle(
                          fontSize: 15, 
                          fontWeight: FontWeight.w600,
                          color: Colors.black87,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis, // Si es muy largo, pone "..."
                      ),
                    ),
                  ],
                ),
              ),

            // --- 1. CABECERA (Score + Textos + Botones) ---
            Row(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                // Círculo con la nota
                Container(
                  width: 60,
                  height: 60,
                  decoration: BoxDecoration(
                    color: scoreColor.withOpacity(0.1),
                    shape: BoxShape.circle,
                    border: Border.all(color: scoreColor, width: 2),
                  ),
                  child: Center(
                    child: Text(
                      score.toStringAsFixed(1),
                      style: TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                        color: scoreColor,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 15),
                
                // Texto Principal
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        "LifeScore",
                        style: TextStyle(fontSize: 14, color: Colors.grey, fontWeight: FontWeight.w500),
                      ),
                      Text(
                        scoreText,
                        style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                ),

                // Botones de Acción
                Row(
                  children: [
                    IconButton(
                      icon: const Icon(Icons.tune_rounded, color: Colors.grey),
                      onPressed: onTunePressed,
                      tooltip: "Ajustar preferencias",
                    ),
                    IconButton(
                      icon: const Icon(Icons.close_rounded, color: Colors.black87),
                      onPressed: onClosePressed,
                      tooltip: "Cerrar",
                    ),
                  ],
                )
              ],
            ),

            const SizedBox(height: 20),

            // --- 2. CAJA DE INTELIGENCIA ARTIFICIAL ---
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFFF0F4FF), // Azul muy suave
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: const Color(0xFFD6E4FF)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.auto_awesome, size: 16, color: AppColors.primary),
                      const SizedBox(width: 8),
                      Text(
                        "Análisis Inteligente",
                        style: TextStyle(
                          fontSize: 12, 
                          fontWeight: FontWeight.bold, 
                          color: AppColors.primary,
                          letterSpacing: 0.5
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  
                  // CONTENIDO DINÁMICO (Cargando vs Texto)
                  if (isLoadingIA)
                    Row(
                      children: [
                        const SizedBox(
                          width: 15, 
                          height: 15, 
                          child: CircularProgressIndicator(strokeWidth: 2)
                        ),
                        const SizedBox(width: 10),
                        const Text(
                          "Consultando datos y analizando...", 
                          style: TextStyle(color: Colors.grey, fontSize: 13, fontStyle: FontStyle.italic)
                        ),
                      ],
                    )
                  else
                    Text(
                      iaSummary ?? "No se pudo conectar con el asesor virtual.",
                      style: const TextStyle(
                        fontSize: 14, 
                        color: Colors.black87, 
                        height: 1.4
                      ),
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