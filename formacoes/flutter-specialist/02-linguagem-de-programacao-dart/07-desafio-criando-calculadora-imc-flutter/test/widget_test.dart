import 'package:calculadora_imc/main.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('calcula e mostra o IMC e a classificação', (tester) async {
    await tester.pumpWidget(const CalculadoraImcApp());

    await tester.enterText(find.widgetWithText(TextField, 'Peso (kg)'), '70');
    await tester.enterText(find.widgetWithText(TextField, 'Altura (m)'), '1,75');
    await tester.tap(find.text('Calcular'));
    await tester.pump();

    expect(find.text('22.9'), findsOneWidget);
    expect(find.text('Peso normal'), findsOneWidget);
  });

  testWidgets('mostra erro quando os campos são inválidos', (tester) async {
    await tester.pumpWidget(const CalculadoraImcApp());

    await tester.tap(find.text('Calcular'));
    await tester.pump();

    expect(find.textContaining('Informe peso (kg) e altura (m)'), findsOneWidget);
  });
}
