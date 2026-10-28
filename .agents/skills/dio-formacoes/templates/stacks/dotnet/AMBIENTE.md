# Ambiente — .NET

SDK .NET 8. Para fixar a versão por formação, rode aqui: `dotnet new globaljson --sdk-version <versão>`.

## Opção A — Nativo

| | Linux | Windows (PowerShell) |
|---|---|---|
| SDK | [script oficial](https://learn.microsoft.com/dotnet/core/install/linux) ou gerenciador da distro | `winget install Microsoft.DotNet.SDK.8` |
| Novo projeto | `dotnet new console -o .` | `dotnet new console -o .` |
| Executar | `dotnet run` | `dotnet run` |

## Opção B — Dev Container

Abra **esta pasta** no VS Code → `F1` → **Dev Containers: Reopen in Container**.
