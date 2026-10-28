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
- Idioma: português do Brasil.
