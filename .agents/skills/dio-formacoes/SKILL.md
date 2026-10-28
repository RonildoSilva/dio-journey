---
name: dio-formacoes
description: Organiza formações, bootcamps, cursos e desafios de projeto da plataforma DIO (dio.me) no repositório dio-journey. Use quando o usuário colar o conteúdo de uma página de formação/bootcamp da DIO, pedir para adicionar ou atualizar uma formação, marcar cursos/desafios como concluídos, iniciar um desafio de projeto, criar o ambiente de uma stack, extrair um projeto para repositório próprio, ou baixar e organizar os certificados da conta DIO (ferramentas/certificados).
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

1. Guarde a página em `_raw/<slug>/`. Preferível: **salvar a página** no navegador (Ctrl+S,
   "Página da Web, somente HTML") com a formação aberta e logado, como `pagina.html`. Alternativa:
   colar o texto copiado em `pagina.md`. A página salva traz o status real ("Baixar Certificado" = concluído).
2. Defina a **stack** pelo conteúdo: `flutter`, `python`, `node`, `java`, `dotnet` ou `generic`.
   Se houver várias linguagens, use a predominante; se for ambíguo, pergunte ao usuário.
   Para uma stack nova, crie `templates/stacks/<stack>/` (veja "Nova stack").
3. Converta:
   ```bash
   DIO parse _raw/<slug>/pagina.html --slug <slug> --stack <stack> [--url <link da DIO>]
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

## Fluxo 5: certificados da DIO (ferramentas/certificados)

Ferramenta fora do git: `ferramentas/certificados/` (ver o README da pasta). Dados pessoais
(PDFs, banco, sessão do navegador) ficam em `dados/` e `perfil/`, ambos ignorados.

Ordem de uso (cada passo roda **uma vez**; rodar de novo só baixa o que falta):
1. `login.py`: login manual no DIO, sessão salva em `perfil/`. Nunca guardar senha.
   `login.py --verificar` testa a sessão (abre janela; sem janela o DIO manda para o login).
2. `coleta.py`: lista os certificados rolando a página (rolagem infinita, 12 por página).
3. `baixar.py`: baixa os PDFs em `dados/pdf/<codigo>.pdf`, pulando os que já existem.
4. `banco.py`: monta `dados/certificados.db` a partir de `dados/certificados_api.json`.
5. `capturar_play.py --section-type <tipo>`: catálogo por tipo (`formation`, `course`, ...).
6. Estrutura das formações (módulos e cursos): **não** é capturada automaticamente. As páginas de
   formação redirecionam para o login de forma instável e carregam os módulos sob demanda. Use a
   página salva + `dio.py parse` (Fluxo 1); o vínculo certificado ↔ formação é feito pelo título.
7. `ocr.py`: lê nome, data e carga horária dos PDFs com tesseract (local, sem rede).
8. `capturar_perfil.py`: nível, XP e conquistas do perfil público (uma visita).
9. `banco.py` e depois `organizar.py`: banco (vínculo muitos-para-muitos certificado <-> formação),
   PDFs em `dados/certificados/<formação>/` e os blocos PERFIL e CERTIFICADOS do README raiz.

Aprendizados que valem para qualquer captura no DIO:
- **Redirecionamento silencioso:** a página passa pelo `auth.dio.me` por alguns segundos e volta
  para `web.dio.me`. Nunca ler a URL logo após o carregamento; esperar a URL assentar.
- **Headless não serve para checar sessão:** o DIO manda para o login. Usar janela visível.
- **Dados pela própria página:** capturar as respostas JSON que a página recebe (`page.on("response")`).
  Não extrair tokens do navegador nem chamar a API com credenciais tiradas do perfil.
- **Carregamento preguiçoso:** a lista de módulos de uma formação é pedida por módulo, quando
  aberto. Rolar a página não basta. Antes de confiar numa contagem, comparar com `track_activities`
  do catálogo (`courses`).
- **Catálogo completo por tipo:** `/play` com o filtro do tipo (Curso 758, Bootcamp 267,
  Projetos 257, Masterclass 105, Formação 73). O filtro de tipo é o parâmetro `section_type`.
- **PDF sem texto:** o certificado é uma imagem JPEG. Ler nome e carga horária exige OCR.
  Ferramentas: `pdfimages` (extrai a imagem) e `tesseract` com o pacote `por` (OCR, `ocr.py`).
- **Ferramentas do sistema usadas (citar no README e instalar em cada máquina):** Python 3.12+,
  Google Chrome, poppler-utils (`pdftotext`, `pdfimages`), tesseract-ocr com pacote `por`.
  Tabela completa com comandos Linux e Windows em `ferramentas/certificados/README.md`.

**Tudo de uma vez:** `atualizar.py` roda as etapas em ordem; o hook `.githooks/pre-push` o chama
a cada push (ativar com `git config core.hooksPath .githooks`). Coleta incompleta nunca
sobrescreve dados bons; consultas ao DIO respeitam intervalo de 30 minutos.

Não repetir downloads sem pedido. Antes de uma nova passagem, conferir o que já está salvo.
