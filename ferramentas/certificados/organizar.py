#!/usr/bin/env python3
"""
organizar.py - organiza os PDFs por formação e atualiza o bloco de certificados do README raiz.

Lê dados/certificados.db (rode banco.py antes). Não acessa a rede.

- dados/certificados/<formacao>/<codigo>.pdf  (um certificado pode estar em várias formações)
- dados/certificados/avulsos/<tipo>/<codigo>.pdf  (sem formação no repositório)
  Os PDFs são copiados de dados/pdf/ (original). Cópias que não valem mais são removidas.
- README raiz: bloco entre <!-- CERTIFICADOS:START --> e <!-- CERTIFICADOS:END -->,
  com resumo por formação e a lista de cada uma (sem nome do aluno; código e link do PDF).
- Avisa quando uma atividade tem certificado mas está "pendente" no formacao.json.

Uso (dentro desta pasta):
  .venv/bin/python organizar.py
No Windows: .venv\\Scripts\\python organizar.py
"""
import shutil
import sqlite3
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAIZ = HERE.parents[1]
DADOS = HERE / "dados"
BANCO = DADOS / "certificados.db"
PASTA = DADOS / "certificados"
README = RAIZ / "README.md"
INICIO = "<!-- CERTIFICADOS:START (gerado por ferramentas/certificados/organizar.py) -->"
FIM = "<!-- CERTIFICADOS:END -->"
ROTULO_TIPO = {"course": "cursos", "lab_projects": "projetos", "bootcamp": "bootcamps",
               "masterclass": "masterclasses", None: "outros"}
PERFIL_JSON = DADOS / "perfil_respostas.json"
PERFIL_INICIO = "<!-- PERFIL:START (gerado por ferramentas/certificados/organizar.py) -->"
PERFIL_FIM = "<!-- PERFIL:END -->"
# palavra que aparece nos títulos dos certificados/formações -> ícone do skillicons.dev
ICONES = [("flutter", "flutter"), ("flutter", "dart"), ("dart", "dart"), ("python", "py"), ("aws", "aws"), ("amazon", "aws"),
          ("unity", "unity"), ("git", "git"), ("github", "github"), ("azure", "azure"),
          ("kotlin", "kotlin"), ("linux", "linux"), ("docker", "docker"), ("java ", "java"),
          ("javascript", "js"), ("react", "react"), ("sql", "mysql")]


def organizar_pdfs(con):
    desejados = set()
    vinculos = con.execute("SELECT codigo, formacao_slug FROM certificado_formacao").fetchall()
    for codigo, slug in vinculos:
        desejados.add(PASTA / slug / f"{codigo}.pdf")
    com_formacao = {c for c, _ in vinculos}
    for codigo, tipo in con.execute("SELECT codigo, tipo_catalogo FROM certificados"):
        if codigo not in com_formacao:
            desejados.add(PASTA / "avulsos" / ROTULO_TIPO.get(tipo, "outros") / f"{codigo}.pdf")

    copiados = 0
    for destino in desejados:
        origem = DADOS / "pdf" / destino.name
        if origem.exists() and not destino.exists():
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(origem, destino)
            copiados += 1
    removidos = 0
    for antigo in PASTA.rglob("*.pdf") if PASTA.exists() else []:
        if antigo not in desejados:
            antigo.unlink()
            removidos += 1
    for pasta in sorted(PASTA.rglob("*"), reverse=True) if PASTA.exists() else []:
        if pasta.is_dir() and not any(pasta.iterdir()):
            pasta.rmdir()
    return len(desejados), copiados, removidos


def linha_certificado(codigo, curso, data, carga, url):
    return f"| {curso} | {data} | {carga or '-'} | [{codigo}]({url}) |"


def bloco_readme(con):
    total, horas = con.execute("SELECT COUNT(*), COALESCE(SUM(horas), 0) FROM certificados").fetchone()
    out = ["## 📜 Certificados", "",
           f"**{total} certificados** · **{horas} horas** de carga horária. "
           "Gerado por [ferramentas/certificados](ferramentas/certificados/) "
           "(PDFs e banco ficam fora do git).", "",
           "| Formação | Certificados | Horas | Atividades concluídas |", "|---|:-:|:-:|:-:|"]
    formacoes = con.execute("""
        SELECT f.slug, f.nome,
               (SELECT COUNT(DISTINCT v.codigo) FROM certificado_formacao v WHERE v.formacao_slug = f.slug),
               (SELECT COALESCE(SUM(c.horas), 0) FROM certificados c WHERE c.codigo IN
                    (SELECT codigo FROM certificado_formacao WHERE formacao_slug = f.slug)),
               (SELECT COUNT(*) FROM atividades a WHERE a.formacao_slug = f.slug AND a.status = 'concluido'),
               (SELECT COUNT(*) FROM atividades a WHERE a.formacao_slug = f.slug)
        FROM formacoes f ORDER BY f.nome""").fetchall()
    for slug, nome, n, h, feitas, todas in formacoes:
        out.append(f"| [{nome}](formacoes/{slug}/) | {n} | {h} | {feitas}/{todas} |")
    avulsos = con.execute("""SELECT COUNT(*), COALESCE(SUM(horas), 0) FROM certificados
                             WHERE codigo NOT IN (SELECT codigo FROM certificado_formacao)""").fetchone()
    out += [f"| _Avulsos (sem formação no repositório)_ | {avulsos[0]} | {avulsos[1]} | - |", ""]

    for slug, nome, n, *_ in formacoes:
        if not n:
            continue
        out += [f"<details><summary>{nome} ({n})</summary>", "",
                "| Curso | Concluído em | Carga | Código |", "|---|:-:|:-:|---|"]
        for linha in con.execute("""
                SELECT DISTINCT c.codigo, c.curso, c.data_conclusao, c.carga_horaria, c.url_pdf
                FROM certificados c JOIN certificado_formacao v ON v.codigo = c.codigo
                WHERE v.formacao_slug = ? ORDER BY c.data_conclusao""", (slug,)):
            out.append(linha_certificado(*linha))
        out += ["", "</details>", ""]

    por_tipo = defaultdict(list)
    for linha in con.execute("""SELECT codigo, curso, data_conclusao, carga_horaria, url_pdf, tipo_catalogo
                                FROM certificados WHERE codigo NOT IN (SELECT codigo FROM certificado_formacao)
                                ORDER BY data_conclusao"""):
        por_tipo[ROTULO_TIPO.get(linha[5], "outros")].append(linha[:5])
    if por_tipo:
        out += [f"<details><summary>Avulsos ({avulsos[0]})</summary>", ""]
        for tipo, linhas in sorted(por_tipo.items()):
            out += [f"**{tipo.capitalize()}** ({len(linhas)})", "",
                    "| Curso | Concluído em | Carga | Código |", "|---|:-:|:-:|---|"]
            out += [linha_certificado(*l) for l in linhas] + [""]
        out += ["</details>", ""]
    return "\n".join(out).rstrip()


def bloco_perfil(con):
    """Cabeçalho com nível, XP, horas, conquistas e tecnologias (dados de capturar_perfil.py)."""
    import json
    if not PERFIL_JSON.exists():
        return None
    caps = json.loads(PERFIL_JSON.read_text(encoding="utf-8"))

    def achar(cond):
        return next((c["corpo"] for c in caps if cond(c["url"])), None)

    usuario = achar(lambda u: "/api/users/" in u and u.rstrip("/").split("/")[-1].isidentifier()
                    and "/stats/" not in u and u.count("/") == 6) or {}
    meta = usuario.get("meta") or {}
    conquistas = achar(lambda u: u.endswith("/achievements/") and "/stats/" not in u) or []
    stats_skills = achar(lambda u: "/stats/skills/" in u) or {}
    nivel, xp, prox = meta.get("level"), meta.get("experience"), meta.get("experience_to_next")
    total, horas = con.execute("SELECT COUNT(*), COALESCE(SUM(horas), 0) FROM certificados").fetchone()
    n_form = con.execute("SELECT COUNT(*) FROM formacoes").fetchone()[0]
    usuario_dio = usuario.get("username") or ""

    pct = (xp / prox) if xp and prox else 0
    barra = "█" * round(pct * 10) + "░" * (10 - round(pct * 10))
    textos = " ".join(r[0] for r in con.execute("SELECT curso FROM certificados")).lower()
    textos += " " + " ".join(r[0] for r in con.execute("SELECT nome FROM formacoes")).lower()
    icones = []
    for palavra, icone in ICONES:
        if palavra in textos and icone not in icones:
            icones.append(icone)

    out = []
    if usuario.get("photo"):
        out += [f'<img src="{usuario["photo"]}" alt="avatar" width="96" align="right">', ""]
    out += [f"**{usuario.get('name', '')}** · [perfil na DIO](https://web.dio.me/users/{usuario_dio})", "",
            "| Nível | XP | Horas de estudo | Certificados | Conquistas | Skills | Formações aqui |",
            "|:-:|:-:|:-:|:-:|:-:|:-:|:-:|",
            f"| **{nivel}** | `{barra}` {xp} / {prox} ({pct:.0%}) | {horas}h | {total} | {len(conquistas)} "
            f"| {stats_skills.get('total_skills', '-')} | {n_form} |", ""]
    if icones:
        out += ["**Tecnologias estudadas** (pelos certificados e formações):", "",
                f'<img src="https://skillicons.dev/icons?i={",".join(icones)}" alt="{", ".join(icones)}">', ""]
    if conquistas:
        out += [f"<details><summary>Conquistas ({len(conquistas)})</summary>", "",
                " ".join(f'<img src="{c["badge"]}" alt="{c["name"]}" title="{c["name"]}" width="48">'
                         for c in conquistas if c.get("badge")), "", "</details>"]
    return "\n".join(out).rstrip()


def trocar_bloco(txt, inicio, fim, conteudo, antes_de=None, depois_da_linha_1=False):
    bloco = f"{inicio}\n{conteudo}\n{fim}"
    if inicio in txt and fim in txt:
        return txt.split(inicio, 1)[0] + bloco + txt.split(fim, 1)[1]
    if depois_da_linha_1:  # logo abaixo do título (# ...)
        primeira, _, resto = txt.partition("\n")
        return f"{primeira}\n\n{bloco}\n{resto}"
    if antes_de and antes_de in txt:
        return txt.replace(antes_de, bloco + "\n\n" + antes_de, 1)
    return txt.rstrip() + "\n\n" + bloco + "\n"


def atualizar_readme(conteudo, perfil=None):
    txt = README.read_text(encoding="utf-8")
    txt = trocar_bloco(txt, INICIO, FIM, conteudo, antes_de="## 🗂️ Estrutura")
    if perfil:
        txt = trocar_bloco(txt, PERFIL_INICIO, PERFIL_FIM, perfil, depois_da_linha_1=True)
    with open(README, "w", encoding="utf-8", newline="\n") as f:
        f.write(txt)


def pendentes_com_certificado(con):
    return con.execute("""
        SELECT DISTINCT v.formacao_slug, a.titulo FROM certificado_formacao v
        JOIN atividades a ON a.formacao_slug = v.formacao_slug AND a.modulo = v.modulo
        JOIN certificados c ON c.codigo = v.codigo
        WHERE a.status = 'pendente' AND a.titulo = (SELECT titulo FROM atividades a2
              WHERE a2.formacao_slug = v.formacao_slug AND a2.modulo = v.modulo AND a2.titulo = a.titulo)
          AND lower(a.titulo) = lower(c.curso)""").fetchall()


def main():
    if not BANCO.exists():
        raise SystemExit("Rode banco.py antes (dados/certificados.db não existe).")
    con = sqlite3.connect(BANCO)
    total, copiados, removidos = organizar_pdfs(con)
    atualizar_readme(bloco_readme(con), bloco_perfil(con))
    divergentes = pendentes_com_certificado(con)
    con.close()
    print(f"PDFs organizados: {total} (copiados agora: {copiados}, removidos: {removidos})")
    print("README.md: bloco de certificados atualizado")
    for slug, titulo in divergentes:
        print(f"  aviso: '{titulo}' tem certificado mas está pendente em formacoes/{slug} "
              f"(dio.py marcar {slug} \"{titulo[:30]}\")")


if __name__ == "__main__":
    main()
