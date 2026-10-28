#!/usr/bin/env python3
"""
baixar.py - baixa os PDFs dos certificados listados em dados/certificados_api.json.

Cada PDF é baixado uma única vez: se dados/pdf/<codigo>.pdf já existe, é pulado.
Rodar de novo só baixa o que faltou (por exemplo, após uma falha de rede).

Uso (dentro desta pasta):
  .venv/bin/python baixar.py
No Windows: .venv\\Scripts\\python baixar.py
"""
import json
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
LISTA = HERE / "dados" / "certificados_api.json"
PASTA_PDF = HERE / "dados" / "pdf"
MODELO_URL = "https://hermes.dio.me/certificates/{codigo}.pdf"


def baixar_um(codigo):
    req = urllib.request.Request(MODELO_URL.format(codigo=codigo), headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        dados = r.read()
    if dados[:4] != b"%PDF":
        raise ValueError("resposta não é PDF")
    destino = PASTA_PDF / f"{codigo}.pdf"
    tmp = destino.with_suffix(".pdf.part")
    tmp.write_bytes(dados)
    tmp.replace(destino)  # só vira .pdf quando estiver completo


def main():
    itens = json.loads(LISTA.read_text(encoding="utf-8"))
    PASTA_PDF.mkdir(parents=True, exist_ok=True)
    baixados = pulados = 0
    falhas = []
    for it in itens:
        codigo = it["code"]
        if (PASTA_PDF / f"{codigo}.pdf").exists():
            pulados += 1
            continue
        try:
            baixar_um(codigo)
            baixados += 1
        except Exception as e:  # registra e segue para os próximos
            falhas.append((codigo, type(e).__name__))
    print(f"baixados: {baixados} | já existiam: {pulados} | falhas: {len(falhas)}")
    for codigo, erro in falhas:
        print(f"  falhou: {codigo} ({erro})")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
