"""
Captura, numa única passagem, as respostas JSON que a página /play recebe (sessão logada).

section_type é parâmetro da URL (ex.: formation, course, bootcamp). Cada tipo gera um arquivo
próprio em dados/play_<tipo>_respostas.json.

Uso (dentro desta pasta):
  .venv/bin/python capturar_play.py                    # padrão: formation
  .venv/bin/python capturar_play.py --section-type course
"""
import argparse
import json
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
PLAY = "https://web.dio.me/play"
capturas = []


def ao_responder(resp):
    if "api" in resp.url and resp.status == 200 and "json" in resp.headers.get("content-type", ""):
        try:
            capturas.append({"url": resp.url, "corpo": resp.json()})
        except Exception:
            pass


args = argparse.ArgumentParser(description="Captura o catálogo /play por section_type")
args.add_argument("--section-type", default="formation", help="valor do parâmetro section_type da URL")
args = args.parse_args()
PAGINA = f"{PLAY}?section_type={args.section_type}"
SAIDA = HERE / "dados" / f"play_{args.section_type}_respostas.json"

with sync_playwright() as p:
    contexto = p.chromium.launch_persistent_context(str(HERE / "perfil"), channel="chrome", headless=False)
    pagina = contexto.pages[0] if contexto.pages else contexto.new_page()
    pagina.on("response", ao_responder)
    pagina.goto(PAGINA, wait_until="domcontentloaded")
    estavel = 0
    for _ in range(120):
        estavel = estavel + 1 if pagina.url.startswith("https://web.dio.me/play") else 0
        if estavel >= 5:
            break
        pagina.wait_for_timeout(1000)
    for _ in range(25):
        pagina.mouse.wheel(0, 5000)
        pagina.wait_for_timeout(1500)
    contexto.close()

SAIDA.parent.mkdir(exist_ok=True)
SAIDA.write_text(json.dumps(capturas, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"respostas JSON capturadas: {len(capturas)}")
for c in capturas:
    corpo = c["corpo"]
    chaves = list(corpo.keys())[:6] if isinstance(corpo, dict) else f"lista[{len(corpo)}]"
    print(" ", urlparse(c["url"]).netloc + urlparse(c["url"]).path[:70], "|", chaves)
