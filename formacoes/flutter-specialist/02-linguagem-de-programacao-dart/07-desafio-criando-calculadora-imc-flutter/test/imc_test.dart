import 'package:calculadora_imc/imc.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('calcularImc', () {
    test('divide o peso pela altura ao quadrado', () {
      expect(calcularImc(70, 1.75), closeTo(22.86, 0.01));
    });

    test('lança erro para peso ou altura não positivos', () {
      expect(() => calcularImc(0, 1.75), throwsArgumentError);
      expect(() => calcularImc(70, 0), throwsArgumentError);
    });
  });

  group('classificarImc', () {
    test('usa as faixas da OMS', () {
      expect(classificarImc(17), 'Abaixo do peso');
      expect(classificarImc(18.5), 'Peso normal');
      expect(classificarImc(24.9), 'Peso normal');
      expect(classificarImc(25), 'Sobrepeso');
      expect(classificarImc(30), 'Obesidade grau I');
      expect(classificarImc(35), 'Obesidade grau II');
      expect(classificarImc(40), 'Obesidade grau III');
    });
  });

  group('lerNumero', () {
    test('aceita vírgula e ponto como separador decimal', () {
      expect(lerNumero('1,75'), 1.75);
      expect(lerNumero(' 70 '), 70);
    });

    test('retorna null para texto inválido ou não positivo', () {
      expect(lerNumero(''), isNull);
      expect(lerNumero('abc'), isNull);
      expect(lerNumero('-1'), isNull);
      expect(lerNumero('0'), isNull);
    });
  });
}
