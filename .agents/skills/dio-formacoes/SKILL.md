---
name: dio-formacoes
description: Organiza formações, bootcamps, cursos e desafios de projeto da plataforma DIO (dio.me) no repositório dio-journey. Use quando o usuário colar o conteúdo de uma página de formação/bootcamp da DIO, pedir para adicionar ou atualizar uma formação, marcar cursos/desafios como concluídos, iniciar um desafio de projeto, criar o ambiente de uma stack, ou extrair um projeto para repositório próprio.
---

# DIO Formações

Mantém o monorepo `dio-journey` organizado: `formacoes/<slug>/` com um ambiente isolado por
formação, pastas por módulo e por desafio, READMEs com progresso e índice no README raiz.

Script: `.agents/skills/dio-formacoes/scripts/dio.py` (Python 3.8+, stdlib, Linux e Windows).

## Onde esta skill é lida

- **Fonte única:** `.agents/skills/dio-formacoes/` (este arquivo). Lida pelo Google (Gemini CLI e
  Antigravity) e pelo Codex. Edite só aqui.
- **Claude Code:** `.claude/skills/dio-formacoes/SKILL.md` é um stub que aponta para este arquivo.
  Não duplique regras lá.
Abaixo, `DIO` = `python3 .agents/skills/dio-formacoes/scripts/dio.py` (Windows: `py ...`).

## Regras

- **Nunca dar push** sem pedido explícito. Commit local pode.
- **Sempre atualizar o README**: rode `DIO build` depois de qualquer mudança e edite as seções
  manuais do `README.md` raiz quando mudar estrutura, stacks, automação ou guias.
- Comandos documentados sempre com versão Linux **e** Windows.
- Nunca editar dentro de `<!-- AUTO:START -->...<!-- AUTO:END -->`; mude o `formacao.json` e rode `build`.
- Nunca sobrescrever READMEs de atividades (contêm anotações do usuário).

## Fluxo 1: nova formação (usuário colou a página da DIO)

1. Salve o texto colado em `_raw/<slug>.md` (se ainda não estiver lá).
2. Defina a **stack** pelo conteúdo: `flutter`, `python`, `node`, `java`, `dotnet` ou `generic`.
   Se houver várias linguagens, use a predominante; se for ambíguo, pergunte ao usuário.
   Para uma stack nova, crie `templates/stacks/<stack>/` (veja "Nova stack").
3. Converta:
   ```bash
   DIO parse _raw/<slug>.md --slug <slug> --stack <stack> [--url <link da DIO>]
   ```
   O slug é curto, sem "formacao-" (ex.: `flutter-specialist`, `python-ai-backend`).
4. Confira o resumo impresso (módulos, atividades, desafios). Se faltou algo, abra o
   `formacao.json` e corrija à mão (o parser depende do layout da DIO).
5. `DIO build`.
6. Atualize o README raiz se necessário e faça um commit local:
   `git add -A && git commit -m "feat(<slug>): adiciona formação"`.

Colar a mesma página de novo (com progresso atualizado) roda o mesmo fluxo: o `parse` mescla os
dados sem perder pastas, status ou campos extras.

## Fluxo 2: progresso

- `DIO marcar <slug> "<parte do título ou pasta>"` marca como concluída (`--pendente` desfaz).
  Já roda o `build`.
- "Baixar Certificado" na página da DIO = concluído; o `parse` detecta isso.

## Fluxo 3: iniciar um desafio com código

1. Leia o `AMBIENTE.md` da formação e use o ambiente isolado dela (ex.: `fvm flutter ...`).
2. Crie o projeto **dentro da pasta do desafio** (ex.: `fvm flutter create --project-name
   calculadora_imc .`; nomes Dart em snake_case). Anotações de curso vão na seção "Minhas
   anotações" do README da formação, não em pasta nova.
3. Preencha o README da atividade (enunciado, solução, como executar).
4. Commit local: `feat(<slug>): desafio <nome>`.

## Fluxo 4: extrair projeto para repo próprio

Siga [docs/GIT-GUIA.md](../../../docs/GIT-GUIA.md) (seção 2: `git subtree split`). Só faça o
push quando o usuário pedir.

## Estrutura do formacao.json

```json
{
  "slug": "flutter-specialist", "stack": "flutter", "url": "", "raw": "flutter.md",
  "nome": "...", "nivel": "Intermediário", "horas": 71, "descricao": "...", "prerequisitos": "...",
  "modulos": [{
    "nome": "Linguagem de Programação Dart", "pasta": "02-linguagem-de-programacao-dart",
    "atividades": [{
      "titulo": "...", "tipo": "curso|desafio|desafio-codigo|complementar|avaliacao",
      "nivel": "Básico", "horas": 2, "status": "pendente|concluido", "pasta": "01-..."
    }]
  }]
}
```

- **Só desafios ganham pasta** (`desafio` e `desafio-codigo`): são o código que vai para o GitHub
  e para a DIO. Cursos (vídeo-aulas), materiais complementares e avaliação aparecem só na tabela
  do README da formação, sem pasta nem README próprio.
- Cada desafio tem um bloco AUTO com enunciado e entrega (preenchidos por `entregas` e `entregar`).
  Enunciado vem de `_raw/<slug>/entregas.md`, colado da página do desafio na DIO.
- `pasta` é gravada uma vez e não muda (links estáveis). Campos extras (ex.: `"repo"`) são preservados.
- Slugs ficam limitados a 40 caracteres por causa do limite de caminho no Windows.

## Nova stack

Crie `templates/stacks/<stack>/` contendo:
- `.devcontainer/devcontainer.json` (imagem oficial `mcr.microsoft.com/devcontainers/*` quando houver)
- `.gitignore` da stack
- arquivo de versão (`.tool-version` equivalente da stack)
- `AMBIENTE.md` com Opção A (nativo, tabela Linux × Windows) e Opção B (Dev Container)

O `build` copia esses arquivos para a formação **só se ainda não existirem** (o usuário pode
personalizar). Depois, atualize a tabela "Ambientes isolados" do README raiz.
