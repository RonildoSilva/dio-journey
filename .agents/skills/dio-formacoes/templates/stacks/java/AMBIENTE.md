# Ambiente — Java

JDK 21 (Temurin). Prefira sempre o **wrapper** do projeto (`./mvnw` / `./gradlew`), que fixa a
versão do Maven/Gradle por projeto.

## Opção A — Nativo

| | Linux | Windows (PowerShell) |
|---|---|---|
| JDK | [SDKMAN](https://sdkman.io): `sdk install java 21-tem` | `winget install EclipseAdoptium.Temurin.21.JDK` |
| Build Maven | `./mvnw clean package` | `.\mvnw.cmd clean package` |
| Build Gradle | `./gradlew build` | `.\gradlew.bat build` |

## Opção B — Dev Container

Abra **esta pasta** no VS Code → `F1` → **Dev Containers: Reopen in Container**.
