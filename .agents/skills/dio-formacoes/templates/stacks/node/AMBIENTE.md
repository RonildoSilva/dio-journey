# Ambiente — Node.js

Versão fixada em [`.nvmrc`](.nvmrc). Cada projeto tem seu próprio `node_modules`, então já fica isolado.

## Opção A — Nativo

| | Linux | Windows (PowerShell) |
|---|---|---|
| Gerenciador | [nvm](https://github.com/nvm-sh/nvm) ou [fnm](https://github.com/Schniz/fnm) | [fnm](https://github.com/Schniz/fnm): `winget install Schniz.fnm` |
| Usar a versão | `nvm install && nvm use` | `fnm install; fnm use` |
| Dependências | `npm ci` (ou `npm install`) | `npm ci` (ou `npm install`) |

> O fnm lê o `.nvmrc` nas duas plataformas.

## Opção B — Dev Container

Abra **esta pasta** no VS Code → `F1` → **Dev Containers: Reopen in Container**.
