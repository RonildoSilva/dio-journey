# Ambiente — Flutter

Cada formação tem um ambiente **isolado**: a versão do Flutter fica fixa em
[`.fvmrc`](.fvmrc) e não interfere em outras formações nem no Flutter global.

Há duas formas de trabalhar. Escolha uma por máquina.

## Opção A — Nativo com FVM (recomendado para emulador/celular)

### 1. Instalar o FVM (uma vez por máquina)

| Linux | Windows (PowerShell) |
|---|---|
| `curl -fsSL https://fvm.app/install.sh \| bash` | `choco install fvm` ou `dart pub global activate fvm` |

> **Windows:** ative o *Modo de Desenvolvedor* (Configurações → Sistema → Para desenvolvedores),
> o FVM usa links simbólicos.

### 2. Instalar a versão desta formação

Dentro desta pasta:

```bash
fvm install        # lê o .fvmrc
fvm flutter doctor
```

O VS Code passa a usar `.fvm/flutter_sdk` automaticamente.
Use sempre `fvm flutter ...` (ou `fvm dart ...`) nesta formação.

### 3. Criar o projeto de um curso/desafio

Os nomes de pasta usam hífen, mas pacotes Dart exigem `snake_case`, então informe `--project-name`:

```bash
cd 02-linguagem-de-programacao-dart/07-desafio-criando-calculadora-imc-flutter
fvm flutter create --org br.com.ronildosilva --project-name calculadora_imc .
fvm flutter run
```

Para exercícios só em Dart (sem UI):

```bash
fvm dart create -t console --force .
fvm dart run
```

## Opção B — Dev Container (Docker)

Ambiente idêntico no Linux e no Windows, sem instalar Flutter na máquina.

1. Instale Docker (Linux) ou Docker Desktop com WSL2 (Windows), e a extensão
   **Dev Containers** do VS Code.
2. Abra **esta pasta da formação** no VS Code → `F1` → **Dev Containers: Reopen in Container**.

Limitações: não há emulador Android dentro do container. Use:

```bash
flutter run -d web-server --web-hostname 0.0.0.0 --web-port 8080   # abre em http://localhost:8080
flutter test
flutter build apk                                                   # instale o APK no celular
```

> **Windows:** clone o repositório **dentro do WSL** (`\\wsl$\...`) para o container ficar rápido.
