#!/usr/bin/env python3
"""
dio.py - organiza as formações da DIO neste repositório.

Funciona em Linux e Windows (apenas biblioteca padrão, Python 3.8+).

Subcomandos:
  parse  RAW --slug SLUG --stack STACK [--nome NOME] [--url URL]
         Lê o texto copiado da página da formação na DIO e grava/atualiza
         formacoes/<SLUG>/formacao.json (preserva pastas e status já existentes).

  build  Gera/atualiza a estrutura: pastas de módulos e atividades, READMEs,
         arquivos de ambiente da stack e o índice no README raiz.
         Nunca sobrescreve anotações: só reescreve o bloco AUTO dos READMEs.

  marcar FORMACAO TERMO [--pendente]
         Marca uma atividade como concluída (ou pendente). TERMO pode ser
         parte do título ou da pasta.

Exemplos:
  python3 .agents/skills/dio-formacoes/scripts/dio.py parse _raw/flutter.md --slug flutter-specialist --stack flutter
  python  .agents/skills/dio-formacoes/scripts/dio.py build
  py      .agents/skills/dio-formacoes/scripts/dio.py marcar flutter-specialist "calculadora de imc"
"""
import argparse
import json
import re
import shutil
import sys
import unicodedata
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
TIPOS_COM_PASTA = ("curso", "desafio", "desafio-codigo")
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


def parse_raw(text):
    lines = [l.strip() for l in text.splitlines()]
    ne = [l for l in lines if l]

    # ---- cabeçalho
    nome, i_nome = None, 0
    for i, l in enumerate(ne):
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
            bloco = ne[i + 1:i + 7]
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
            if at["tipo"] in TIPOS_COM_PASTA:
                prefixo = "desafio-" if at["tipo"].startswith("desafio") else ""
                at.setdefault("pasta", f"{ai:02d}-{prefixo}{slugify(at['titulo'], SLUG_MAX - len(prefixo))}")


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
    raw = Path(args.raw).read_text(encoding="utf-8")
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


def readme_atividade(data, mod, at):
    horas = f"{at['horas']}h" if at.get("horas") else "-"
    txt = (
        f"# {at['titulo']}\n\n"
        f"| Formação | Módulo | Tipo | Nível | Carga |\n|---|---|---|---|---|\n"
        f"| [{data['nome']}](../../README.md) | {mod['nome']} | {ROTULO_TIPO.get(at['tipo'], at['tipo'])} "
        f"| {at.get('nivel') or '-'} | {horas} |\n\n"
    )
    if at["tipo"].startswith("desafio"):
        txt += (
            "## Descrição do desafio\n\n_Cole aqui o enunciado da DIO._\n\n"
            "## Solução\n\n_O que foi feito, decisões e aprendizados._\n\n"
            "## Como executar\n\n```bash\n# comandos\n```\n\n"
            "## Entrega\n\n- Link enviado à DIO: \n"
        )
    else:
        txt += "## Anotações\n\n- \n\n## Código\n\nExercícios e exemplos do curso ficam nesta pasta.\n"
    return txt


def build_formacao(root, fjson):
    data = read_json(fjson)
    fdir = fjson.parent
    atribuir_pastas(data)
    write_json(fjson, data)
    copiar_stack(fdir, data.get("stack") or "generic")

    feitos, total = contar(data)
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
    out += ["## Progresso", "", barra(feitos, total), "",
            "## Ambiente", "", "Instruções para Linux e Windows em [AMBIENTE.md](AMBIENTE.md).", "",
            "## Conteúdo", ""]

    for mod in data["modulos"]:
        mf, mt = sum(a["status"] == "concluido" for a in mod["atividades"]), len(mod["atividades"])
        out += [f"### {mod['nome']} ({mf}/{mt})", "",
                "| | Atividade | Tipo | Nível | Carga |", "|:-:|---|---|---|---|"]
        for at in mod["atividades"]:
            icone = "✅" if at["status"] == "concluido" else "⬜"
            titulo = at["titulo"]
            if at.get("pasta"):
                titulo = f"[{titulo}]({mod['pasta']}/{at['pasta']}/)"
                adir = fdir / mod["pasta"] / at["pasta"]
                adir.mkdir(parents=True, exist_ok=True)
                readme = adir / "README.md"
                if not readme.exists():
                    write_text(readme, readme_atividade(data, mod, at))
            if at["tipo"] == "desafio":
                titulo = f"🚀 {titulo}"
            horas = f"{at['horas']}h" if at.get("horas") else "-"
            out.append(f"| {icone} | {titulo} | {ROTULO_TIPO.get(at['tipo'], at['tipo'])} "
                       f"| {at.get('nivel') or '-'} | {horas} |")
        out.append("")

    replace_auto(fdir / "README.md", "\n".join(out), "\n## Minhas anotações\n\n- \n")
    return data, feitos, total


def cmd_build(args):
    root = Path(args.root)
    linhas = ["| Formação | Stack | Progresso |", "|---|---|---|"]
    fjsons = sorted((root / "formacoes").glob("*/formacao.json"))
    for fjson in fjsons:
        data, feitos, total = build_formacao(root, fjson)
        rel = fjson.parent.relative_to(root).as_posix()
        linhas.append(f"| [{data['nome']}]({rel}/) | `{data.get('stack')}` | {barra(feitos, total, 10)} |")
        print(f"OK {rel} ({feitos}/{total})")
    if not fjsons:
        linhas.append("| _nenhuma formação ainda_ | | |")
    replace_auto(root / "README.md", "\n".join(linhas))
    print("OK README.md (índice)")


def cmd_marcar(args):
    root = Path(args.root)
    fjson = root / "formacoes" / args.formacao / "formacao.json"
    if not fjson.exists():
        sys.exit(f"Formação não encontrada: {fjson}")
    data = read_json(fjson)
    termo = args.termo.lower().strip("/\\")
    achados = [a for m in data["modulos"] for a in m["atividades"]
               if termo in a["titulo"].lower() or termo in (a.get("pasta") or "")]
    if len(achados) != 1:
        print(f"{len(achados)} atividades encontradas para '{args.termo}':")
        for a in achados:
            print(f"  - {a['titulo']} [{a.get('pasta', '-')}]")
        sys.exit(1)
    achados[0]["status"] = "pendente" if args.pendente else "concluido"
    write_json(fjson, data)
    print(f"OK '{achados[0]['titulo']}' -> {achados[0]['status']}")
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

    args = p.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # console do Windows
    args.func(args)


if __name__ == "__main__":
    main()
