// Test básico de humo (Smoke Test) para verificar que la app arranca

import 'package:flutter_test/flutter_test.dart';
import 'package:TenerifeLifeScore/main.dart';

void main() {
  testWidgets('La app debería arrancar y mostrar el mensaje inicial', (WidgetTester tester) async {
    // 1. Cargar la app
    await tester.pumpWidget(const TenerifeLifeScoreApp());

    // 2. Verificar que aparece nuestro texto provisional
    // (Asegúrate de que este texto coincide con lo que pusimos en main.dart)
    expect(find.text('🏗️ Estructura lista'), findsOneWidget);
  });
}