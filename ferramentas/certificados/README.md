# 📜 Certificados DIO

Baixa os certificados da sua conta na DIO, organiza os PDFs por formação e grava um banco SQLite
local com os dados de cada certificado.

## Estrutura (ao rodar)

```text
ferramentas/certificados/
├── schema.sql                  ← estrutura do banco (versionado)
├── atualizar.py                ← roda tudo em ordem (usado pelo hook pre-push)
├── login.py                    ← login manual no DIO e verificação da sessão
├── coleta.py                   ← lista os certificados da conta (rolagem da página)
├── baixar.py                   ← baixa cada PDF uma única vez
├── banco.py                    ← monta o banco SQLite a partir dos dados coletados
├── ocr.py                      ← lê nome, data e carga horária dos PDFs (tesseract)
├── organizar.py                ← pastas por formação + blocos do README raiz (perfil e certificados)
├── capturar_perfil.py          ← nível, XP e conquistas do perfil público (uma visita)
├── capturar_play.py            ← lê o catálogo /play (formações) numa passagem
├── capturar_catalogo.py        ← lista o catálogo por tipo (curso, bootcamp, projetos, masterclass)
├── dados/                      ← ignorado pelo git (dados pessoais)
│   ├── certificados.db         ← banco SQLite
│   ├── certificados_api.json   ← lista de certificados (coleta.py)
│   ├── play_respostas.json     ← respostas do catálogo (capturar_play.py)
│   └── pdf/
│       └── HCXSQUZE.pdf        ← um PDF por código
├── perfil/                     ← ignorado pelo git (sessão do navegador)
└── .venv/                      ← ignorado pelo git (ambiente isolado)
```

## Dependências do sistema

Além do Python (3.12 usado aqui), estas ferramentas precisam estar instaladas. Algumas já estavam
nesta máquina; as que faltarem precisam ser instaladas em cada computador onde o projeto for clonado.

| Ferramenta | Para quê | Nesta máquina | Linux (Ubuntu/Debian) | Windows |
|---|---|---|---|---|
| Python 3.12+ | scripts e ambiente `.venv` | sim (3.12.3) | `sudo apt install python3 python3-venv` | `winget install Python.Python.3.12` |
| Google Chrome | Playwright abre o Chrome já instalado (`channel="chrome"`) | sim (155) | pacote `.deb` oficial do Google Chrome | instalador oficial do Chrome |
| poppler-utils (`pdftotext`, `pdfimages`) | extrair texto e imagens dos PDFs | sim | `sudo apt install poppler-utils` | `choco install poppler` |
| tesseract-ocr + pacote `por` | ler a imagem do certificado (nome, data e carga horária) | sim (5.3.4, idioma `por`) | `sudo apt install tesseract-ocr tesseract-ocr-por` | `choco install tesseract` (depois, o idioma `por`) |

O Playwright (`playwright==1.64.1`) fica dentro do `.venv` e não precisa de instalação global.
O tesseract é necessário para `ocr.py` (nome, data e carga horária a partir do PDF). Sem ele, esses campos ficam vazios.

## Organização

- **Pasta por formação:** `dados/certificados/<slug>/`, com o mesmo slug de `formacoes/<slug>/`.
- **Nome do arquivo:** o código do certificado (`<codigo>.pdf`), que é único na DIO.
- **Banco:** tabelas `formacoes` e `certificados` (veja `schema.sql`). A chave é o código.

## Privacidade

Os PDFs trazem o nome completo, e o repositório é público. Por isso:
- `dados/` e `perfil/` estão no `.gitignore` desta pasta.
- Só o resumo (formação, curso, data e código, com link para o certificado no DIO) vai para o README raiz.

## Como preparar (Linux e Windows)

Usa o Chrome já instalado na máquina (não baixa navegador extra). Dentro desta pasta:

**Linux**
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

**Windows (PowerShell)**
```powershell
py -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

Versão fixada em `requirements.txt`: `playwright==1.64.1`. Para testar a abertura do Chrome:

```bash
.venv/bin/python -c "from playwright.sync_api import sync_playwright as s; p=s().start(); b=p.chromium.launch(channel='chrome', headless=True); print(b.version); b.close(); p.stop()"
```

No Windows, troque `.venv/bin/python` por `.venv\Scripts\python`. Se o Chrome não estiver instalado, o `channel='chrome'` falha; nesse caso, instale o Chrome ou use `.venv/bin/playwright install chromium`.

## Login (uma vez)

Abre o Chrome numa janela para você entrar no DIO. A senha é digitada só no navegador: o script nunca a vê.

**Linux**
```bash
.venv/bin/python login.py
```

**Windows (PowerShell)**
```powershell
.venv\Scripts\python login.py
```

Quando estiver logado, volte ao terminal e pressione Enter. A sessão fica em `perfil/`.

Para conferir depois, sem abrir janela:

```bash
.venv/bin/python login.py --verificar       # Linux
.venv\Scripts\python login.py --verificar   # Windows
```

Se a sessão expirar, rode o `login.py` de novo.
