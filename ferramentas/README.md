# 🧰 Ferramentas

Utilitários auxiliares do dio-journey. Ficam ao lado de `formacoes/`, e cada um tem o próprio
ambiente isolado (`.venv` ou equivalente) e as próprias dependências.

| Ferramenta | O que faz | Dados pessoais |
|---|---|---|
| [certificados/](certificados/) | Baixa os certificados da DIO e organiza em pastas e num banco SQLite | Sim: ficam fora do git |

Regras gerais:
- Nada de senha, token ou cookie em arquivo versionado. Login fica no perfil local do navegador.
- Dados gerados (PDFs, banco, perfil do navegador, `.venv`) ficam fora do git pelo `.gitignore` local.
