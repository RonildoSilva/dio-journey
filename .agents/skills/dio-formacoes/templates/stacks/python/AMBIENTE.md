# Ambiente — Python

Versão fixada em [`.python-version`](.python-version). **Cada projeto/desafio tem seu próprio `.venv`**,
assim as dependências de um não quebram outro.

## Opção A — Nativo

| | Linux | Windows (PowerShell) |
|---|---|---|
| Criar venv | `python3 -m venv .venv` | `py -3.12 -m venv .venv` |
| Ativar | `source .venv/bin/activate` | `.venv\Scripts\Activate.ps1` |
| Instalar deps | `pip install -r requirements.txt` | `pip install -r requirements.txt` |
| Salvar deps | `pip freeze > requirements.txt` | `pip freeze > requirements.txt` |

> **Windows:** se a ativação for bloqueada, rode uma vez:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

Alternativa moderna (Linux e Windows): [uv](https://docs.astral.sh/uv/), com `uv venv` e `uv pip install ...`.

## Opção B — Dev Container

Abra **esta pasta** no VS Code → `F1` → **Dev Containers: Reopen in Container**.
Requer Docker (Linux) ou Docker Desktop + WSL2 (Windows).
