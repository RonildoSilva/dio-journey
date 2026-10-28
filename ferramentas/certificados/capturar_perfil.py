"""
capturar_perfil.py - visita UMA vez a página pública de conquistas do perfil e salva as respostas
JSON que ela recebe em dados/perfil_respostas.json (nível, XP, conquistas...).

Uso (dentro desta pasta):
  .venv/bin/python capturar_perfil.py [--usuario ronildo_comp]
"""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
SAIDA = HERE / "dados" / "perfil_respostas.json"

args = argparse.ArgumentParser(description="Captura os dados públicos do perfil DIO")
args.add_argument("--usuario", default="ronildo_comp")
args = args.parse_args()
URL = f"https://web.dio.me/users/{args.usuario}?tab=achievements"
capturas = []


def ao_responder(resp):
    if "sms.dio.me/api" in resp.url and resp.status == 200 and "json" in resp.headers.get("content-type", ""):
        try:
            capturas.append({"url": resp.url, "corpo": resp.json()})
        except Exception:
            pass


with sync_playwright() as p:
    contexto = p.chromium.launch_persistent_context(str(HERE / "perfil"), channel="chrome", headless=False)
    pagina = contexto.pages[0] if contexto.pages else contexto.new_page()
    pagina.on("response", ao_responder)
    pagina.goto(URL, wait_until="domcontentloaded")
    estavel = 0
    for _ in range(120):
        estavel = estavel + 1 if pagina.url.startswith(f"https://web.dio.me/users/{args.usuario}") else 0
        if estavel >= 6:
            break
        pagina.wait_for_timeout(1000)
    pagina.wait_for_timeout(4000)
    print("pagina final:", pagina.url[:70], flush=True)
    contexto.close()

tem_meta = any(isinstance(c["corpo"], dict) and (c["corpo"].get("meta") or {}).get("level") for c in capturas)
if not tem_meta:
    print("perfil sem nível/XP (sessão expirada ou página não carregou): nada gravado.", flush=True)
    raise SystemExit(2)
SAIDA.write_text(json.dumps(capturas, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"respostas JSON capturadas: {len(capturas)}", flush=True)
