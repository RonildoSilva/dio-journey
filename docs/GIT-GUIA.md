# Guia Git — pegar só uma pasta e extrair projetos

Este repositório é um **monorepo**: todas as formações ficam aqui. Este guia mostra como:

1. [Clonar/baixar só uma pasta](#1-clonar-só-uma-pasta-sparse-checkout) (ex.: um desafio)
2. [Transformar uma pasta em repositório próprio, com histórico](#2-extrair-um-projeto-para-repositório-próprio-subtree-split) (portfólio)
3. [Manter o repo extraído atualizado](#3-manter-o-repositório-extraído-sincronizado)
4. [Trazer um repo externo para cá](#4-trazer-um-repositório-externo-para-o-monorepo-subtree-add)
5. [Para que servem as tags aqui](#5-tags-marcos-não-filtros)

Todos os comandos funcionam igual no **Linux (bash)** e no **Windows (PowerShell ou Git Bash)**.
Use sempre `/` nos caminhos, inclusive no Windows.

> No Windows, rode uma vez para evitar erro com caminhos longos:
> `git config --global core.longpaths true`

Nos exemplos, a pasta usada é:

```text
formacoes/flutter-specialist/02-linguagem-de-programacao-dart/07-desafio-criando-calculadora-imc-flutter
```

---

## 1. Clonar só uma pasta (sparse checkout)

Baixa **apenas** a pasta escolhida (e os arquivos da raiz), mas continua sendo um repositório git
completo: dá para commitar e dar push normalmente.

```bash
git clone --filter=blob:none --sparse https://github.com/RonildoSilva/dio-journey.git dio-imc
cd dio-imc
git sparse-checkout set formacoes/flutter-specialist/02-linguagem-de-programacao-dart/07-desafio-criando-calculadora-imc-flutter
```

- `--filter=blob:none`: não baixa o conteúdo dos arquivos que você não usar (clone leve).
- `--sparse`: começa só com os arquivos da raiz.

| Quero… | Comando |
|---|---|
| Adicionar outra pasta | `git sparse-checkout add formacoes/python-fundamentals` |
| Pegar a formação inteira | `git sparse-checkout set formacoes/flutter-specialist` |
| Ver o que está ativo | `git sparse-checkout list` |
| Voltar a ter o repo todo | `git sparse-checkout disable` |

### Só os arquivos, sem git

| Situação | Comando |
|---|---|
| Tenho Node.js | `npx degit RonildoSilva/dio-journey/formacoes/flutter-specialist/02-linguagem-de-programacao-dart/07-desafio-criando-calculadora-imc-flutter meu-imc` |
| Já tenho o repo local | `git archive --format=zip -o imc.zip HEAD:formacoes/flutter-specialist/02-linguagem-de-programacao-dart/07-desafio-criando-calculadora-imc-flutter` |
| Só navegador | cole o link da pasta do GitHub em https://download-directory.github.io |

---

## 2. Extrair um projeto para repositório próprio (subtree split)

Quando um desafio ficar bom para o portfólio, ele vira um repositório separado
**preservando todos os commits** daquela pasta. A pasta continua existindo no monorepo.

### Passo 1: criar uma branch só com a pasta (no monorepo)

```bash
git subtree split --prefix=formacoes/flutter-specialist/02-linguagem-de-programacao-dart/07-desafio-criando-calculadora-imc-flutter -b export/calculadora-imc
```

A branch `export/calculadora-imc` contém **só** o conteúdo daquela pasta, agora na raiz, com o
histórico dela.

### Passo 2: criar o repositório novo a partir dessa branch

**Opção A: repositório local primeiro**

```bash
cd ..
git init -b main calculadora-imc
cd calculadora-imc
git pull ../dio-journey export/calculadora-imc
```

**Opção B: direto para o GitHub** (crie antes um repo **vazio** `calculadora-imc` no GitHub)

```bash
git push https://github.com/RonildoSilva/calculadora-imc.git export/calculadora-imc:main
```

### Passo 3: limpar a branch temporária (no monorepo)

```bash
git branch -D export/calculadora-imc
```

> 💡 A pasta da formação tem seu próprio `.gitignore`, `.fvmrc` e `.devcontainer/` **acima** do
> desafio, e eles não vão junto no split. Depois de extrair, copie para o repo novo o que fizer sentido.

---

## 3. Manter o repositório extraído sincronizado

Continue desenvolvendo **no monorepo**. Para mandar as novidades ao repo separado:

```bash
# uma vez: cadastrar o remoto
git remote add imc https://github.com/RonildoSilva/calculadora-imc.git

# sempre que quiser publicar as mudanças daquela pasta
git subtree push --prefix=formacoes/flutter-specialist/02-linguagem-de-programacao-dart/07-desafio-criando-calculadora-imc-flutter imc main
```

Se alguém (ou você) commitar direto no repo separado, traga de volta com:

```bash
git subtree pull --prefix=formacoes/flutter-specialist/02-linguagem-de-programacao-dart/07-desafio-criando-calculadora-imc-flutter imc main
```

> O `subtree split` sempre gera os mesmos commits para o mesmo histórico, então o push é
> incremental. Se o repo ficar muito grande e o comando ficar lento, adicione `--rejoin` ao split.

---

## 4. Trazer um repositório externo para o monorepo (subtree add)

Por exemplo, um desafio que você já tinha feito em outro repo:

```bash
git subtree add --prefix=formacoes/flutter-specialist/02-linguagem-de-programacao-dart/07-desafio-criando-calculadora-imc-flutter https://github.com/RonildoSilva/repo-antigo.git main --squash
```

Sem `--squash`, o histórico inteiro do repo externo também vem.

---

## 5. Tags: marcos, não filtros

Uma tag aponta para **um commit do repositório inteiro**, não para uma pasta. Ela **não** serve para
clonar só um projeto (para isso use a seção 1). Aqui ela serve para marcar conquistas:

```bash
git tag -a flutter-specialist/concluida -m "Formação Flutter Specialist concluída"
git tag -a flutter-specialist/desafio-imc-v1 -m "Entrega do desafio IMC"
git tag -l "flutter-specialist/*"     # listar
git push origin --tags                # (quando for publicar)
```

E dá para combinar: clonar uma tag + só uma pasta.

```bash
git clone --filter=blob:none --sparse --branch flutter-specialist/desafio-imc-v1 https://github.com/RonildoSilva/dio-journey.git
```
