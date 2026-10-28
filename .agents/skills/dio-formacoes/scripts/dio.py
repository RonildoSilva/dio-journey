#!/usr/bin/env python3
"""
dio.py - organiza as formações da DIO neste repositório.

Funciona em Linux e Windows (apenas biblioteca padrão, Python 3.8+).

Subcomandos:
  parse  RAW --slug SLUG --stack STACK [--nome NOME] [--url URL]
         Lê a página da formação na DIO e grava/atualiza formacoes/<SLUG>/formacao.json
         (preserva pastas e status já existentes). RAW pode ser o texto copiado (.md/.txt)
         ou a página salva pelo navegador (.html, "Salvar como" com a formação aberta).

  build  Gera/atualiza a estrutura: pastas de módulos e de desafios, READMEs,
         arquivos de ambiente da stack e o índice no README raiz.
         Cursos não têm pasta (só desafios têm código). Nunca sobrescreve
         anotações: só reescreve o bloco AUTO dos READMEs.

  marcar FORMACAO TERMO [--pendente]
         Marca uma atividade como concluída (ou pendente). TERMO pode ser
         parte do título ou da pasta.

  entregas FORMACAO RAW
         Lê o texto copiado das páginas de desafio (DESCRIÇÃO + título) e grava
         o enunciado em cada desafio. Gera ENTREGAS.md na formação.

  entregar FORMACAO TERMO [--link URL] [--data AAAA-MM-DD] [--pendente]
         Registra a entrega de um desafio (link padrão: pasta no GitHub) e
         marca a atividade como concluída.

Exemplos:
  python3 .agents/skills/dio-formacoes/scripts/dio.py parse _raw/flutter-specialist/pagina.md --slug flutter-specialist --stack flutter
  python  .agents/skills/dio-formacoes/scripts/dio.py build
  py      .agents/skills/dio-formacoes/scripts/dio.py marcar flutter-specialist "calculadora de imc"
  py      .agents/skills/dio-formacoes/scripts/dio.py entregas flutter-specialist _raw/flutter-specialist/entregas.md
  py      .agents/skills/dio-formacoes/scripts/dio.py entregar flutter-specialist "subindo"
"""
import argparse
import json
import re
import shutil
import sys
import unicodedata
from html.parser import HTMLParser
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_DIR / "templates" / "stacks"
DEFAULT_ROOT = SKILL_DIR.parents[2]  # <repo>/.agents/skills/dio-formacoes

AUTO_START = "<!-- AUTO:START (gerado por dio.py - não edite dentro deste bloco) -->"
AUTO_END = "<!-- AUTO:END -->"

SLUG_MAX = 40  # mantém caminhos curtos (limite de 260 chars no Windows)
NIVEIS = ("básico", "basico", "intermediário", "intermediario", "avançado", "avancado")
STATUS_CONCLUIDO = ("baixar certificado", "ver certificado", "concluído", "concluido", "revisar")
TIPOS = {
    "curso": "curso",
    "desafio de projeto": "desafio",
    "desafio de código": "desafio-codigo",
    "desafio de codigo": "desafio-codigo",
    "live": "live",
    "artigo": "artigo",
    "mentoria": "mentoria",
}
TIPOS_DESAFIO = ("desafio", "desafio-codigo")  # só desafios têm pasta (são o código entregue)
ROTULO_TIPO = {
    "curso": "Curso",
    "desafio": "Desafio de projeto",
    "desafio-codigo": "Desafio de código",
    "complementar": "Material complementar",
    "avaliacao": "Avaliação",
}


# --------------------------------------------------------------------------- utils
STOPWORDS = {
    "a", "o", "as", "os", "e", "de", "da", "do", "das", "dos", "em", "no", "na", "nos", "nas",
    "com", "para", "por", "um", "uma", "seu", "sua", "seus", "suas", "ao", "aos", "the", "of", "and",
}


def slugify(text, max_len=SLUG_MAX):
    t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "-", t.lower()).strip("-")
    if len(t) > max_len:  # primeiro remove palavras de ligação, depois corta
        t = "-".join(w for w in t.split("-") if w not in STOPWORDS) or t
    if len(t) > max_len:
        cut = t[:max_len]
        if t[max_len] != "-" and "-" in cut:
            cut = cut.rsplit("-", 1)[0]
        t = cut.strip("-")
    return t


def write_text(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path, data):
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def replace_auto(path, content, default_tail=""):
    """Reescreve apenas o bloco AUTO, preservando o resto do arquivo."""
    block = f"{AUTO_START}\n{content.rstrip()}\n{AUTO_END}"
    if path.exists():
        txt = path.read_text(encoding="utf-8")
        if AUTO_START in txt and AUTO_END in txt:
            pre = txt.split(AUTO_START, 1)[0]
            post = txt.split(AUTO_END, 1)[1]
            new = pre + block + post
        else:
            new = block + "\n\n" + txt
    else:
        new = block + "\n" + default_tail
    write_text(path, new)


def find_hours(line):
    m = re.search(r"(\d+)\s*hrs?\b", line, re.I)
    return int(m.group(1)) if m else None


def find_level(line):
    low = line.lower()
    for n in NIVEIS:
        if n in low:
            return {"basico": "Básico", "intermediario": "Intermediário", "avancado": "Avançado"}.get(
                n, n.capitalize()
            )
    return None


# --------------------------------------------------------------------------- parse
def classificar(tipo_raw, titulo):
    t = titulo.lower()
    if t.startswith("materiais complementares"):
        return "complementar"
    if t.startswith("avalie"):
        return "avaliacao"
    return TIPOS.get(tipo_raw.lower(), slugify(tipo_raw) or "outro")


class _TextoDaPagina(HTMLParser):
    """Converte a página salva em linhas de texto na ordem do documento, como o "copiar" do
    navegador: inclui o alt das imagens ("Imagem do bootcamp <título>") e ignora script/estilo/svg."""
    IGNORAR = {"script", "style", "svg", "noscript", "head"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.linhas, self._ignorando = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in self.IGNORAR:
            self._ignorando += 1
        elif tag == "img" and not self._ignorando:
            alt = dict(attrs).get("alt") or ""
            if alt.strip():
                self.linhas.append(alt.strip())

    def handle_endtag(self, tag):
        if tag in self.IGNORAR and self._ignorando:
            self._ignorando -= 1

    def handle_data(self, data):
        texto = re.sub(r"\s+", " ", data).strip()
        # linhas só com glifo de fonte de ícones (área de uso privado do Unicode) não são texto
        if not self._ignorando and texto and not all("" <= ch <= "" for ch in texto):
            self.linhas.append(texto)


def html_para_texto(html):
    p = _TextoDaPagina()
    p.feed(html)
    return "\n".join(p.linhas)


MARCAS_DEPOIS_DO_NOME = ("adicionar na lista", "matricular agora", "cancelar matrícula", "cancelar matricula")


def parse_raw(text):
    lines = [l.strip() for l in text.splitlines()]
    ne = [l for l in lines if l]

    # ---- cabeçalho
    nome, i_nome = None, 0
    # página salva: o nome vem logo antes de "Adicionar na lista"/"Matricular agora"
    for i, l in enumerate(ne):
        if l.lower() in MARCAS_DEPOIS_DO_NOME and i > 0:
            nome, i_nome = ne[i - 1], i - 1
            break
    for i, l in enumerate(ne):
        if nome is not None:
            break
        if l.lower() == "abrir menu pessoal" and i + 1 < len(ne):
            nome, i_nome = ne[i + 1], i + 1
            break
    if nome is None:
        for i, l in enumerate(ne):
            if l.lower().startswith(("formação", "formacao", "bootcamp")):
                nome, i_nome = l, i
                break

    try:
        i_cert = next(i for i, l in enumerate(ne) if l == "CERTIFICADO")
    except StopIteration:
        i_cert = 0
    header = ne[i_nome:i_cert] if i_cert > i_nome else ne[i_nome:i_nome + 30]

    nivel = next((find_level(l) for l in header if find_level(l) and len(l) < 25), None)
    horas = next((find_hours(l) for l in header if find_hours(l) and len(l) < 25), None)
    descricao = max((l for l in header if len(l) > 120), key=len, default="")
    prereq = next((l.split(":", 1)[1].strip() for l in header if "pré-requisitos" in l.lower() and ":" in l), "")

    # ---- atividades (somente após "CERTIFICADO", até o rodapé)
    end = len(ne)
    for i in range(i_cert, len(ne)):
        if ne[i].lower().startswith(("seu ultimo certificado", "seu último certificado")) or ne[i] == "Rooms":
            end = i
            break

    modulos, atual, i = [], None, i_cert
    while i < end:
        l = ne[i]
        if re.fullmatch(r"\d+\s+atividades?", l, re.I):
            atual = {"nome": ne[i - 1], "atividades": []}
            modulos.append(atual)
            i += 1
            continue
        if l.startswith("Imagem do bootcamp"):
            bloco = ne[i + 1:i + 9]  # tipo, título, nível, ícone, horas, status (+ folga)
            tipo_raw = bloco[0] if bloco else ""
            titulo = bloco[1] if len(bloco) > 1 else l.replace("Imagem do bootcamp", "").strip()
            nivel_a, horas_a, status_raw, consumed = None, None, "", 2
            for j, b in enumerate(bloco[2:], start=2):
                if nivel_a is None and find_level(b) and len(b) < 25:
                    nivel_a, consumed = find_level(b), j + 1
                elif horas_a is None and find_hours(b) and len(b) < 25:
                    horas_a, consumed = find_hours(b), j + 1
                    if j + 1 < len(bloco):
                        status_raw, consumed = bloco[j + 1], j + 2
                    break
            if atual is None:
                atual = {"nome": "Geral", "atividades": []}
                modulos.append(atual)
            atual["atividades"].append({
                "titulo": titulo,
                "tipo": classificar(tipo_raw, titulo),
                "nivel": nivel_a or "",
                "horas": horas_a,
                "status": "concluido" if status_raw.lower() in STATUS_CONCLUIDO else "pendente",
            })
            i += 1 + consumed
            continue
        i += 1

    return {
        "nome": nome or "Formação sem nome",
        "nivel": nivel or "",
        "horas": horas,
        "descricao": descricao,
        "prerequisitos": prereq,
        "modulos": modulos,
    }


def atribuir_pastas(data):
    for mi, mod in enumerate(data["modulos"], start=1):
        mod.setdefault("pasta", f"{mi:02d}-{slugify(mod['nome'])}")
        for ai, at in enumerate(mod["atividades"], start=1):
            if is_desafio(at):
                at.setdefault("pasta", f"{ai:02d}-desafio-{slugify(at['titulo'], SLUG_MAX - len('desafio-'))}")
            else:
                at.pop("pasta", None)  # pasta de curso antiga (cursos não têm pasta)


def merge(old, new):
    """Atualiza com dados novos da DIO sem perder pastas, status locais e campos extras."""
    antigos = {(m["nome"], a["titulo"]): a for m in old.get("modulos", []) for a in m["atividades"]}
    pastas_mod = {m["nome"]: m.get("pasta") for m in old.get("modulos", [])}
    for mod in new["modulos"]:
        if pastas_mod.get(mod["nome"]):
            mod["pasta"] = pastas_mod[mod["nome"]]
        for at in mod["atividades"]:
            prev = antigos.get((mod["nome"], at["titulo"]))
            if prev:
                status = "concluido" if "concluido" in (prev.get("status"), at["status"]) else "pendente"
                extra = {k: v for k, v in prev.items() if k not in at or k == "pasta"}
                at.update(extra)
                at["status"] = status
    for k, v in old.items():
        if k not in new or not new[k]:
            new[k] = v
    return new


def cmd_parse(args):
    root = Path(args.root)
    raw = Path(args.raw).read_text(encoding="utf-8", errors="replace")
    if Path(args.raw).suffix.lower() in (".html", ".htm"):
        raw = html_para_texto(raw)
    data = parse_raw(raw)
    if args.nome:
        data["nome"] = args.nome
    slug = args.slug or slugify(re.sub(r"^(forma[cç][aã]o|bootcamp)\s+", "", data["nome"], flags=re.I))
    out = root / "formacoes" / slug / "formacao.json"
    base = {"slug": slug, "stack": args.stack, "url": args.url or "", "raw": Path(args.raw).name}
    data = {**base, **data}
    if out.exists():
        old = read_json(out)
        data = merge(old, data)
        if args.stack:
            data["stack"] = args.stack
    if not data.get("stack"):
        sys.exit("Erro: informe --stack (ex.: flutter, python, node, java, dotnet, generic).")
    atribuir_pastas(data)
    write_json(out, data)

    total = sum(len(m["atividades"]) for m in data["modulos"])
    feitos = sum(a["status"] == "concluido" for m in data["modulos"] for a in m["atividades"])
    desafios = sum(a["tipo"] == "desafio" for m in data["modulos"] for a in m["atividades"])
    print(f"OK {out.relative_to(root)}")
    print(f"   {data['nome']} | {len(data['modulos'])} módulos | {total} atividades "
          f"| {desafios} desafios | {feitos} concluídas | stack={data['stack']}")


# --------------------------------------------------------------------------- build
def barra(feitos, total, largura=20):
    pct = (feitos / total) if total else 0
    cheio = round(pct * largura)
    return f"`{'█' * cheio}{'░' * (largura - cheio)}` {feitos}/{total} ({pct:.0%})"


def contar(data):
    ats = [a for m in data["modulos"] for a in m["atividades"]]
    return sum(a["status"] == "concluido" for a in ats), len(ats)


def copiar_stack(fdir, stack):
    src = TEMPLATES / stack
    if not src.is_dir():
        print(f"   aviso: template de stack '{stack}' não existe, usando 'generic'")
        src = TEMPLATES / "generic"
    for f in src.rglob("*"):
        if f.is_file():
            dest = fdir / f.relative_to(src)
            if not dest.exists():
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(f, dest)


REPO_URL_PADRAO = "https://github.com/RonildoSilva/dio-journey"
ROTULO_ENTREGA = {"pendente": "⏳ Pendente", "entregue": "📦 Entregue"}


def config(root):
    f = Path(root) / "dio.config.json"
    return read_json(f) if f.exists() else {}


def url_pasta(root, rel):
    cfg = config(root)
    return f"{cfg.get('repo_url', REPO_URL_PADRAO).rstrip('/')}/tree/{cfg.get('branch', 'main')}/{rel}"


def is_desafio(at):
    return at["tipo"] in TIPOS_DESAFIO


def entrega(at):
    return at.get("entrega") or {"status": "pendente", "link": "", "data": ""}


def md_link(url):
    return f"[{url}]({url})" if url.startswith("http") else (url or "-")


TAIL_DESAFIO = ("\n## Solução\n\n_O que foi feito, decisões e aprendizados._\n\n"
                "## Como executar\n\n```bash\n# comandos\n```\n")


def auto_desafio(root, data, mod, at, adir):
    e = entrega(at)
    horas = f"{at['horas']}h" if at.get("horas") else "-"
    rel = adir.relative_to(root).as_posix()
    out = [
        f"# {at['titulo']}", "",
        "| Formação | Módulo | Tipo | Nível | Carga | Status |", "|---|---|---|---|---|:-:|",
        f"| [{data['nome']}](../../README.md) | {mod['nome']} | {ROTULO_TIPO.get(at['tipo'], at['tipo'])} "
        f"| {at.get('nivel') or '-'} | {horas} | {'✅' if at['status'] == 'concluido' else '⬜'} |", "",
        "## 📋 Enunciado", "",
        at.get("enunciado") or "_Ainda não registrado: cole a página do desafio em "
        "`_raw/<formacao>/entregas.md` e rode `dio.py entregas`._", "",
        "## 📦 Entrega", "",
        "| Status | Data | Link enviado à DIO |", "|:-:|:-:|---|",
        f"| {ROTULO_ENTREGA[e['status']]} | {e.get('data') or '-'} | {md_link(e.get('link', ''))} |", "",
        f"- Link desta pasta no GitHub (para enviar à DIO): `{url_pasta(root, rel)}`",
        "- Todas as entregas da formação: [ENTREGAS.md](../../ENTREGAS.md)",
    ]
    return "\n".join(out)


def build_entregas(data, fdir):
    desafios = [(m, a) for m in data["modulos"] for a in m["atividades"] if is_desafio(a)]
    ent = sum(entrega(a)["status"] == "entregue" for _, a in desafios)
    out = [
        f"# 📦 Entregas: {data['nome']}", "",
        "Desafios de projeto da formação, enunciados e o que foi enviado à DIO. "
        "Voltar ao [README da formação](README.md).", "",
        barra(ent, len(desafios)), "",
        "| # | Desafio | Módulo | Entrega | Data | Link enviado |", "|:-:|---|---|:-:|:-:|---|",
    ]
    for n, (m, a) in enumerate(desafios, 1):
        e = entrega(a)
        out.append(f"| {n} | [{a['titulo']}]({m['pasta']}/{a['pasta']}/) | {m['nome']} "
                   f"| {ROTULO_ENTREGA[e['status']]} | {e.get('data') or '-'} | {md_link(e.get('link', ''))} |")
    out += ["", "## Enunciados", ""]
    for n, (m, a) in enumerate(desafios, 1):
        out += [f"### {n}. {a['titulo']}", "",
                f"📁 [{m['pasta']}/{a['pasta']}]({m['pasta']}/{a['pasta']}/) · {m['nome']}", "",
                a.get("enunciado") or "_Enunciado ainda não registrado._", ""]
    replace_auto(fdir / "ENTREGAS.md", "\n".join(out))
    return ent, len(desafios)


def build_formacao(root, fjson):
    data = read_json(fjson)
    fdir = fjson.parent
    atribuir_pastas(data)
    write_json(fjson, data)
    copiar_stack(fdir, data.get("stack") or "generic")

    feitos, total = contar(data)
    ent, tot_des = build_entregas(data, fdir)
    meta = " · ".join(x for x in [
        data.get("nivel"),
        f"{data['horas']}h" if data.get("horas") else "",
        f"stack `{data.get('stack')}`",
    ] if x)
    out = [f"# {data['nome']}", "", f"> {meta}", ""]
    if data.get("url"):
        out += [f"🔗 [Página na DIO]({data['url']})", ""]
    if data.get("descricao"):
        out += [data["descricao"], ""]
    if data.get("prerequisitos"):
        out += [f"**Pré-requisitos:** {data['prerequisitos']}", ""]
    out += ["## Progresso", "",
            "| | |", "|---|---|",
            f"| Atividades | {barra(feitos, total)} |",
            f"| Desafios entregues | {barra(ent, tot_des)} · [ver entregas](ENTREGAS.md) |", "",
            "## Ambiente", "",
            "Instale o FVM uma vez por máquina e depois a versão fixada pela formação (`.fvmrc`):", "",
            "| Passo | Linux | Windows (PowerShell) |", "|---|---|---|",
            "| 1. Instalar o FVM | `curl -fsSL https://fvm.app/install.sh \\| bash` | `choco install fvm` ou `dart pub global activate fvm` |",
            "| 2. Instalar a versão da formação (dentro desta pasta) | `fvm install` | `fvm install` |", "",
            "Se o terminal não encontrar o `fvm` depois do passo 1 (Linux), grave o caminho no `~/.bashrc` "
            "e recarregue o shell (feito uma vez por máquina):", "",
            "```bash", 'echo \'export PATH="$HOME/fvm/bin:$PATH"\' >> ~/.bashrc', "source ~/.bashrc", "```", "",
            "No Windows o `choco` ou o `dart pub global` já colocam o `fvm` no PATH. Se não achar, reabra o PowerShell.", "",
            "Depois, use sempre `fvm flutter ...`. Detalhes e Dev Container em [AMBIENTE.md](AMBIENTE.md).", "",
            "## Conteúdo", ""]

    for mod in data["modulos"]:
        mf, mt = sum(a["status"] == "concluido" for a in mod["atividades"]), len(mod["atividades"])
        out += [f"### {mod['nome']} ({mf}/{mt})", "",
                "| | Atividade | Tipo | Nível | Carga |", "|:-:|---|---|---|---|"]
        for at in mod["atividades"]:
            icone = "✅" if at["status"] == "concluido" else "⬜"
            titulo = at["titulo"]
            if is_desafio(at):
                adir = fdir / mod["pasta"] / at["pasta"]
                adir.mkdir(parents=True, exist_ok=True)
                replace_auto(adir / "README.md", auto_desafio(root, data, mod, at, adir), TAIL_DESAFIO)
                titulo = f"🚀 [{titulo}]({mod['pasta']}/{at['pasta']}/)"
                if entrega(at)["status"] == "entregue":
                    titulo += " · [📦](ENTREGAS.md)"
            horas = f"{at['horas']}h" if at.get("horas") else "-"
            out.append(f"| {icone} | {titulo} | {ROTULO_TIPO.get(at['tipo'], at['tipo'])} "
                       f"| {at.get('nivel') or '-'} | {horas} |")
        out.append("")

    replace_auto(fdir / "README.md", "\n".join(out), "\n## Minhas anotações\n\n- \n")
    return data, feitos, total, ent, tot_des


def cmd_build(args):
    root = Path(args.root)
    linhas = ["| Formação | Stack | Progresso | Entregas |", "|---|---|---|---|"]
    fjsons = sorted((root / "formacoes").glob("*/formacao.json"))
    for fjson in fjsons:
        data, feitos, total, ent, tot_des = build_formacao(root, fjson)
        rel = fjson.parent.relative_to(root).as_posix()
        linhas.append(f"| [{data['nome']}]({rel}/) | `{data.get('stack')}` | {barra(feitos, total, 10)} "
                      f"| [{ent}/{tot_des}]({rel}/ENTREGAS.md) |")
        print(f"OK {rel} (atividades {feitos}/{total}, entregas {ent}/{tot_des})")
    if not fjsons:
        linhas.append("| _nenhuma formação ainda_ | | | |")
    replace_auto(root / "README.md", "\n".join(linhas))
    print("OK README.md (índice)")


def carregar(root, slug):
    fjson = Path(root) / "formacoes" / slug / "formacao.json"
    if not fjson.exists():
        sys.exit(f"Formação não encontrada: {fjson}")
    return fjson, read_json(fjson)


def achar(data, termo):
    termo = termo.lower().strip("/\\")
    termo = termo.rsplit("/", 1)[-1] if "/" in termo else termo
    return [(m, a) for m in data["modulos"] for a in m["atividades"]
            if termo in a["titulo"].lower() or termo in (a.get("pasta") or "")]


def achar_um(data, termo):
    achados = achar(data, termo)
    if len(achados) != 1:
        print(f"{len(achados)} atividades encontradas para '{termo}':")
        for _, a in achados:
            print(f"  - {a['titulo']} [{a.get('pasta', '-')}]")
        sys.exit(1)
    return achados[0]


def cmd_marcar(args):
    fjson, data = carregar(args.root, args.formacao)
    _, at = achar_um(data, args.termo)
    at["status"] = "pendente" if args.pendente else "concluido"
    write_json(fjson, data)
    print(f"OK '{at['titulo']}' -> {at['status']}")
    cmd_build(args)


# --------------------------------------------------------------------------- entregas
def norm(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", t).strip()


def parse_entregas(text):
    """Extrai pares (título, enunciado) do texto copiado das páginas de desafio da DIO.

    Aceita a DESCRIÇÃO antes ou depois do bloco "Imagem do bootcamp <título>".
    """
    text = text.replace("\u200b", "").replace("\ufeff", "")
    lines = [l.rstrip() for l in text.splitlines()]
    is_desc = lambda l: norm(l) in ("descricao", "descricao do desafio")
    is_tit = lambda l: l.strip().startswith("Imagem do bootcamp")
    itens, pend, ultimo, i = [], None, None, 0
    while i < len(lines):
        l = lines[i].strip()
        if is_desc(l):
            buf, i = [], i + 1
            while i < len(lines) and not is_desc(lines[i]) and not is_tit(lines[i]):
                buf.append(lines[i].strip())
                i += 1
            desc = re.sub(r"\n{3,}", "\n\n", "\n".join(buf)).strip()
            proximo_e_titulo = i < len(lines) and is_tit(lines[i])
            if ultimo is not None and not ultimo["enunciado"] and not proximo_e_titulo:
                ultimo["enunciado"] = desc
            else:
                pend = desc
            continue
        if is_tit(l):
            ultimo = {"titulo": l.replace("Imagem do bootcamp", "", 1).strip(), "enunciado": pend or ""}
            pend = None
            itens.append(ultimo)
        i += 1
    return itens


def cmd_entregas(args):
    fjson, data = carregar(args.root, args.formacao)
    itens = parse_entregas(Path(args.raw).read_text(encoding="utf-8"))
    if not itens:
        sys.exit("Nenhum desafio encontrado (procuro por 'Imagem do bootcamp <título>' e 'DESCRIÇÃO').")
    todos = [(m, a) for m in data["modulos"] for a in m["atividades"]]
    for it in itens:
        alvo = [a for _, a in todos if norm(a["titulo"]) == norm(it["titulo"])] or \
               [a for _, a in todos if norm(it["titulo"]) in norm(a["titulo"])]
        if len(alvo) != 1:
            print(f"   aviso: não encontrei '{it['titulo']}' na formação ({len(alvo)} resultados)")
            continue
        at = alvo[0]
        if it["enunciado"]:
            at["enunciado"] = it["enunciado"]
        at.setdefault("entrega", entrega(at))
        print(f"OK enunciado: {at['titulo']}")
    write_json(fjson, data)
    cmd_build(args)


def cmd_entregar(args):
    from datetime import date
    root = Path(args.root)
    fjson, data = carregar(root, args.formacao)
    mod, at = achar_um(data, args.termo)
    if not is_desafio(at):
        sys.exit(f"'{at['titulo']}' não é um desafio.")
    if args.pendente:
        at["entrega"] = {"status": "pendente", "link": "", "data": ""}
    else:
        rel = (fjson.parent / mod["pasta"] / at["pasta"]).relative_to(root).as_posix()
        at["entrega"] = {"status": "entregue", "link": args.link or url_pasta(root, rel),
                         "data": args.data or date.today().isoformat()}
        at["status"] = "concluido"
    write_json(fjson, data)
    print(f"OK entrega '{at['titulo']}' -> {at['entrega']['status']} {at['entrega']['link']}")
    cmd_build(args)


def main():
    p = argparse.ArgumentParser(description="Organizador das formações DIO")
    p.add_argument("--root", default=str(DEFAULT_ROOT), help="raiz do repositório")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("parse", help="converte o texto copiado da DIO em formacao.json")
    sp.add_argument("raw")
    sp.add_argument("--slug")
    sp.add_argument("--stack")
    sp.add_argument("--nome")
    sp.add_argument("--url")
    sp.set_defaults(func=cmd_parse)

    sb = sub.add_parser("build", help="gera pastas, READMEs e índice")
    sb.set_defaults(func=cmd_build)

    sm = sub.add_parser("marcar", help="marca atividade como concluída/pendente")
    sm.add_argument("formacao")
    sm.add_argument("termo")
    sm.add_argument("--pendente", action="store_true")
    sm.set_defaults(func=cmd_marcar)

    se = sub.add_parser("entregas", help="registra enunciados dos desafios a partir do texto da DIO")
    se.add_argument("formacao")
    se.add_argument("raw")
    se.set_defaults(func=cmd_entregas)

    sg = sub.add_parser("entregar", help="registra a entrega de um desafio")
    sg.add_argument("formacao")
    sg.add_argument("termo")
    sg.add_argument("--link", help="link enviado à DIO (padrão: URL da pasta no GitHub)")
    sg.add_argument("--data", help="AAAA-MM-DD (padrão: hoje)")
    sg.add_argument("--pendente", action="store_true", help="desfaz a entrega")
    sg.set_defaults(func=cmd_entregar)

    args = p.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # console do Windows
    args.func(args)


if __name__ == "__main__":
    main()
