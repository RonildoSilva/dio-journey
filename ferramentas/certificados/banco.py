#!/usr/bin/env python3
"""
banco.py - reconstrói dados/certificados.db do zero a partir dos dados locais (não acessa a rede).

Fontes:
  dados/certificados_api.json      lista de certificados (coleta.py)
  dados/ocr_certificados.json      nome e carga horária lidos do PDF (ocr.py), se existir
  dados/catalogo_respostas.json    catálogo por tipo (capturar_catalogo.py), se existir
  formacoes/*/formacao.json        formações do repositório (dio.py parse)

O vínculo certificado <-> formação é feito pelo título do curso (normalizado). Um certificado
pode pertencer a várias formações.

Uso (dentro desta pasta):
  .venv/bin/python banco.py
No Windows: .venv\\Scripts\\python banco.py
"""
import json
import re
import sqlite3
import unicodedata
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAIZ = HERE.parents[1]
DADOS = HERE / "dados"
BANCO = DADOS / "certificados.db"
SCHEMA = HERE / "schema.sql"


def normalizar(texto):
    t = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def ler_json(caminho, padrao):
    return json.loads(caminho.read_text(encoding="utf-8")) if caminho.exists() else padrao


def data_iso(texto):
    """'10/11/2025 19:30' -> '2025-11-10'."""
    return datetime.strptime(texto, "%d/%m/%Y %H:%M").date().isoformat()


def horas_de(carga):
    m = re.match(r"(\d+)", carga or "")
    return int(m.group(1)) if m else None


def tipos_do_catalogo():
    tipos = {}
    for c in ler_json(DADOS / "catalogo_respostas.json", []):
        corpo = c.get("corpo")
        for it in corpo.get("items", []) if isinstance(corpo, dict) else []:
            tipos.setdefault(normalizar(it.get("name")), it.get("section_type"))
    return tipos


def main():
    certificados = ler_json(DADOS / "certificados_api.json", [])
    ocr = ler_json(DADOS / "ocr_certificados.json", {})
    tipos = tipos_do_catalogo()

    if BANCO.exists():
        BANCO.unlink()  # o banco é derivado: sempre reconstruído
    con = sqlite3.connect(BANCO)
    con.executescript(SCHEMA.read_text(encoding="utf-8"))

    # formações e atividades do repositório
    por_titulo = {}  # titulo normalizado -> [(slug, modulo)]
    for fjson in sorted((RAIZ / "formacoes").glob("*/formacao.json")):
        f = json.loads(fjson.read_text(encoding="utf-8"))
        con.execute("INSERT INTO formacoes VALUES (?, ?, ?)", (f["slug"], f["nome"], f.get("url") or None))
        for m in f["modulos"]:
            for a in m["atividades"]:
                con.execute("INSERT OR IGNORE INTO atividades VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (f["slug"], m["nome"], a["titulo"], a["tipo"], a.get("nivel") or None,
                             a.get("horas"), a["status"]))
                por_titulo.setdefault(normalizar(a["titulo"]), []).append((f["slug"], m["nome"]))

    # certificados e vínculos
    vinculados = 0
    for it in certificados:
        codigo = it["code"]
        pdf = DADOS / "pdf" / f"{codigo}.pdf"
        lido = ocr.get(codigo, {})
        baixado = datetime.fromtimestamp(pdf.stat().st_mtime).strftime("%Y-%m-%d %H:%M") if pdf.exists() else ""
        con.execute(
            "INSERT INTO certificados VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (codigo, it["name"], lido.get("nome_aluno"), data_iso(it["created"]), lido.get("carga_horaria"),
             horas_de(lido.get("carga_horaria")), tipos.get(normalizar(it["name"])),
             f"https://hermes.dio.me/certificates/{codigo}.pdf", f"pdf/{codigo}.pdf", baixado),
        )
        destinos = por_titulo.get(normalizar(it["name"]), [])
        for slug, modulo in destinos:
            con.execute("INSERT OR IGNORE INTO certificado_formacao VALUES (?, ?, ?)", (codigo, slug, modulo))
        vinculados += bool(destinos)
    con.commit()

    n_form = con.execute("SELECT COUNT(*) FROM formacoes").fetchone()[0]
    n_ativ = con.execute("SELECT COUNT(*) FROM atividades").fetchone()[0]
    con.close()
    print(f"formações: {n_form} | atividades: {n_ativ} | certificados: {len(certificados)} "
          f"| ligados a formação: {vinculados} | avulsos: {len(certificados) - vinculados}")


if __name__ == "__main__":
    main()
