/// Calcula o IMC (índice de massa corporal): peso em kg dividido por altura em metros ao quadrado.
double calcularImc(double pesoKg, double alturaM) {
  if (pesoKg <= 0 || alturaM <= 0) {
    throw ArgumentError('Peso e altura devem ser maiores que zero.');
  }
  return pesoKg / (alturaM * alturaM);
}

/// Classificação da OMS para adultos.
String classificarImc(double imc) {
  if (imc < 18.5) return 'Abaixo do peso';
  if (imc < 25) return 'Peso normal';
  if (imc < 30) return 'Sobrepeso';
  if (imc < 35) return 'Obesidade grau I';
  if (imc < 40) return 'Obesidade grau II';
  return 'Obesidade grau III';
}

/// Converte o texto digitado (aceita vírgula ou ponto) em número, ou null se for inválido.
double? lerNumero(String texto) {
  final valor = double.tryParse(texto.trim().replaceAll(',', '.'));
  if (valor == null || valor <= 0) return null;
  return valor;
}
