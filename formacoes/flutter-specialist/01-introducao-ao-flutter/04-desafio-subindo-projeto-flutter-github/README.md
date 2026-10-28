<!-- AUTO:START (gerado por dio.py - não edite dentro deste bloco) -->
# Subindo o Seu Projeto Flutter no GitHub

| Formação | Módulo | Tipo | Nível | Carga | Status |
|---|---|---|---|---|:-:|
| [Formação Flutter Specialist](../../README.md) | Introdução ao Flutter | Desafio de projeto | Básico | 1h | ⬜ |

## 📋 Enunciado

Chegou a sua hora de colocar a mão na massa e assumir o protagonismo. Neste primeiro módulo você conheceu o Flutter e preparou todo o ambiente para o desenvolvimento. Isso será imprescindível para os próximos módulos. Sendo assim, os seus objetivos neste Desafio são: Instalar o Flutter, configurar o Ambiente, criar um projeto e, por fim, subir o seu projeto do GitHub.

## 📦 Entrega

| Status | Data | Link enviado à DIO |
|:-:|:-:|---|
| ⏳ Pendente | - | - |

- Link desta pasta no GitHub (para enviar à DIO): `https://github.com/RonildoSilva/dio-journey/tree/main/formacoes/flutter-specialist/01-introducao-ao-flutter/04-desafio-subindo-projeto-flutter-github`
- Todas as entregas da formação: [ENTREGAS.md](../../ENTREGAS.md)
<!-- AUTO:END -->

## Solução

_O que foi feito, decisões e aprendizados._

## Como executar

Flutter 3.47.8 (Dart 3.13.7), fixado em `.fvmrc` da formação. Com FVM instalado, dentro da pasta do projeto:

```bash
fvm flutter pub get
fvm flutter run -d chrome    # sem dependências extras (precisa do Chrome instalado)
fvm flutter test
```

Para rodar como app desktop no Linux (`fvm flutter run -d linux`), instale antes as dependências de build:

```bash
sudo apt install cmake ninja-build clang pkg-config libgtk-3-dev
```

Se o `fvm` não for encontrado no Linux, grave o caminho do instalador no `~/.bashrc` e recarregue o shell (uma vez por máquina):

```bash
echo 'export PATH="$HOME/fvm/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

No Windows, os mesmos comandos funcionam no PowerShell.
