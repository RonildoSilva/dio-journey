<!-- AUTO:START (gerado por dio.py - não edite dentro deste bloco) -->
# Criando uma Calculadora de IMC Com Flutter

| Formação | Módulo | Tipo | Nível | Carga | Status |
|---|---|---|---|---|:-:|
| [Formação Flutter Specialist](../../README.md) | Linguagem de Programação Dart | Desafio de projeto | Básico | 1h | ✅ |

## 📋 Enunciado

_Ainda não registrado: cole a página do desafio em `_raw/<formacao>/entregas.md` e rode `dio.py entregas`._

## 📦 Entrega

| Status | Data | Link enviado à DIO |
|:-:|:-:|---|
| 📦 Entregue | 2026-10-28 | [https://github.com/RonildoSilva/dio-journey/tree/main/formacoes/flutter-specialist/02-linguagem-de-programacao-dart/07-desafio-criando-calculadora-imc-flutter](https://github.com/RonildoSilva/dio-journey/tree/main/formacoes/flutter-specialist/02-linguagem-de-programacao-dart/07-desafio-criando-calculadora-imc-flutter) |

- Link desta pasta no GitHub (para enviar à DIO): `https://github.com/RonildoSilva/dio-journey/tree/main/formacoes/flutter-specialist/02-linguagem-de-programacao-dart/07-desafio-criando-calculadora-imc-flutter`
- Todas as entregas da formação: [ENTREGAS.md](../../ENTREGAS.md)
<!-- AUTO:END -->

## Solução

Aplicativo Flutter com uma tela que recebe peso (kg) e altura (m), calcula o IMC (peso dividido por altura ao quadrado) e mostra o valor com uma casa decimal e a classificação da OMS para adultos. Os campos aceitam vírgula ou ponto como separador decimal; entrada vazia, não numérica ou não positiva mostra uma mensagem de erro em vez de calcular.

A regra de cálculo e a classificação ficam em `lib/imc.dart`, separadas da interface (`lib/main.dart`), e são cobertas por `test/imc_test.dart`. `test/widget_test.dart` testa o fluxo da tela. Versão do Flutter fixada em `3.47.8` (`.fvmrc` da formação); `fvm flutter analyze` sem problemas e `fvm flutter test` com 7 testes passando.

## Como executar

Na pasta desta entrega, com o FVM instalado (passos na [formação](../../README.md#ambiente)):

**Linux**

```bash
fvm install
fvm flutter pub get
fvm flutter run
fvm flutter test
```

**Windows (PowerShell)**

```powershell
fvm install
fvm flutter pub get
fvm flutter run
fvm flutter test
```
