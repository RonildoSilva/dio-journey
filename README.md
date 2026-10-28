# 🚀 dio-journey

Minha jornada na [DIO](https://web.dio.me): formações, cursos, desafios de projeto e anotações,
tudo organizado em um só lugar.

## 📊 Formações

<!-- AUTO:START (gerado por dio.py - não edite dentro deste bloco) -->
| Formação | Stack | Progresso | Entregas |
|---|---|---|---|
| [Formação Flutter Specialist](formacoes/flutter-specialist/) | `flutter` | `█░░░░░░░░░` 3/53 (6%) | [0/9](formacoes/flutter-specialist/ENTREGAS.md) |
<!-- AUTO:END -->

> 🚀 = desafio de projeto · ✅ = concluído · ⬜ = pendente

## 🗂️ Estrutura

```text
dio-journey/
├── formacoes/
│   └── <formacao>/                  ← um ambiente isolado por formação
│       ├── README.md                ← progresso e conteúdo da formação
│       ├── AMBIENTE.md              ← como preparar o ambiente (Linux e Windows)
│       ├── .devcontainer/           ← ambiente em container (opcional)
│       ├── formacao.json            ← dados da formação (fonte da verdade)
│       └── NN-<modulo>/
│           └── NN-desafio-<nome>/   ← projeto do desafio (só desafios têm pasta)
├── docs/
│   └── GIT-GUIA.md                  ← clonar só uma pasta, subtree, tags
├── .agents/skills/dio-formacoes/    ← skill (Google/Gemini, Antigravity, Codex) + script
└── .claude/skills/dio-formacoes/    ← stub da mesma skill para o Claude Code
```

Cursos são vídeo-aulas da DIO: ficam listados na tabela do README da formação, sem pasta.
Só os desafios têm código, então só eles viram pasta (e são o que sobe para o GitHub e para a DIO).

## 🧪 Ambientes isolados

Cada formação tem sua stack com versão fixada (`.fvmrc`, `.python-version`, `.nvmrc`…) e um
**Dev Container** próprio, então linguagens e versões diferentes não se misturam. Tudo funciona em
**Linux e Windows**: veja o `AMBIENTE.md` de cada formação.

| Stack | Versão fixada em | Isolamento por projeto |
|---|---|---|
| Flutter/Dart | `.fvmrc` (FVM) | um projeto Flutter por pasta |
| Python | `.python-version` | `.venv` por projeto |
| Node.js | `.nvmrc` | `node_modules` por projeto |
| Java | wrapper `mvnw`/`gradlew` | por projeto |
| .NET | `global.json` | por projeto |

## 🔧 Automação

Requer só Python 3.8+ (Linux: `python3`, Windows: `py`).

```bash
# 1. cole o conteúdo da página da formação em _raw/<nome>.md e converta
python3 .agents/skills/dio-formacoes/scripts/dio.py parse _raw/flutter.md --slug flutter-specialist --stack flutter

# 2. gere/atualize pastas, READMEs e este índice
python3 .agents/skills/dio-formacoes/scripts/dio.py build

# 3. marque atividades concluídas (atualiza os READMEs)
python3 .agents/skills/dio-formacoes/scripts/dio.py marcar flutter-specialist "calculadora de imc"
```

## 🌿 Git

- Pegar só um projeto, extrair para repositório próprio (subtree) e uso de tags:
  **[docs/GIT-GUIA.md](docs/GIT-GUIA.md)**
- No Windows: `git config --global core.longpaths true`


