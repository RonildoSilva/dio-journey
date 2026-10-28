# Regras do projeto dio-journey

- **Sem push.** Nunca rodar `git push` (nem `subtree push`) sem pedido explícito do usuário.
  Commits locais são permitidos.
- **Sempre atualizar o README.** Toda alteração no repositório (formação nova, progresso, nova
  stack, mudança de estrutura ou de convenção) deve refletir no `README.md` raiz e no README da
  formação afetada. Rodar `dio.py build` atualiza os blocos AUTO. Seções fora do bloco AUTO devem
  ser editadas à mão quando a mudança afetar estrutura, stacks, automação ou guias.
- **Linux e Windows.** Todo comando documentado deve ter equivalente para as duas plataformas.
  Scripts de automação só em Python (biblioteca padrão), sem bash/PowerShell exclusivos.
- **Ambientes isolados por formação.** Nunca instalar dependências globais para uma formação.
- **Só desafios têm pasta.** Cursos, materiais complementares e avaliações aparecem só na tabela do
  README da formação. Pasta = código entregue (desafio); anotações de curso vão em "Minhas anotações".
- Para organizar formações da DIO, usar a skill `dio-formacoes` (fonte: `.agents/skills/dio-formacoes/`;
  Claude Code lê o stub em `.claude/skills/dio-formacoes/`).
- **Dados pessoais e segredos fora do git.** Nunca commitar certificados (PDF), banco SQLite pessoal,
  `_raw/`, senhas, tokens ou cookies. Nunca colar senha em conversa nem gravar senha no repositório.
  Login em sites: a sessão fica no perfil local do navegador (`ferramentas/`, ignorado), não em arquivo versionado.
- **Arquivos de segredo.** Não abrir nem exibir arquivos como `_raw/.secret*` sem um uso específico
  e combinado com o usuário. O conteúdo nunca vai para a resposta nem para um commit.
- **Instalações no host.** Instalar pacotes do sistema (`apt`, `snap`) ou executar scripts baixados da
  internet é feito pelo usuário, com `! <comando>`, salvo autorização explícita para aquela instalação.
- **Flutter.** Versão fixada em `.fvmrc` (hoje `3.47.8`). O FVM fica em `~/fvm/bin` e o PATH é gravado no
  `~/.bashrc` (documentado no README da formação). Usar sempre `fvm flutter ...`.
- **Entrega Flutter.** `android/gradle/wrapper/gradle-wrapper.jar`, `gradlew` e `gradlew.bat` são
  versionados. O `.gitignore` gerado pelo Flutter ignora esses arquivos, então é preciso corrigi-lo ao
  criar o projeto.
- **Ferramentas.** Utilitários auxiliares ficam na pasta `ferramentas/` (raiz do repo, ao lado de
  `formacoes/`). Cada um tem ambiente isolado e dependências próprias, nunca globais.
- **Downloads no DIO uma vez.** Capturas e downloads de páginas do DIO são feitos uma única vez, com retomada (pular o que já existe). Não reabrir páginas nem refazer passagens sem pedido do usuário.
- **Commits.** Só quando o usuário pedir. Cada commit segue o padrão `tipo(escopo): descrição` em português.
- Idioma: português do Brasil.
