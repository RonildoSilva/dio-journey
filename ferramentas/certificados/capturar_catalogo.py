"""
Lista o catálogo /play por tipo de conteúdo (Curso, Bootcamp, Projetos, Masterclass),
uma passagem por tipo: clica no filtro, rola até o fim e guarda as respostas JSON do catálogo.
Salva em dados/catalogo_respostas.json (ignorado pelo git).
"""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
SAIDA = HERE / "dados" / "catalogo_respostas.json"
TIPOS = ["Curso", "Bootcamp", "Projetos", "Masterclass"]
capturas = []


def ao_responder(resp):
    if "sms.dio.me/api/play/catalog" in resp.url and resp.status == 200:
        try:
            capturas.append({"tipo_pagina": tipo_atual[0], "url": resp.url, "corpo": resp.json()})
        except Exception:
            pass


tipo_atual = ["?"]
with sync_playwright() as p:
    contexto = p.chromium.launch_persistent_context(str(HERE / "perfil"), channel="chrome", headless=False)
    pagina = contexto.pages[0] if contexto.pages else contexto.new_page()
    pagina.on("response", ao_responder)
    pagina.goto("https://web.dio.me/play", wait_until="domcontentloaded")
    estavel = 0
    for _ in range(120):
        estavel = estavel + 1 if pagina.url.startswith("https://web.dio.me/play") else 0
        if estavel >= 5:
            break
        pagina.wait_for_timeout(1000)
    for tipo in TIPOS:
        tipo_atual[0] = tipo
        try:
            pagina.get_by_role("button", name=f"{tipo} (", exact=False).first.click(timeout=8000)
        except Exception as e:
            print("nao achei filtro", tipo, type(e).__name__, flush=True)
            continue
        pagina.wait_for_timeout(3000)
        sem_novidade = 0
        antes = len(capturas)
        while sem_novidade < 3:
            n = len(capturas)
            pagina.mouse.wheel(0, 8000)
            pagina.wait_for_timeout(2000)
            sem_novidade = 0 if len(capturas) > n else sem_novidade + 1
        print(tipo, "respostas:", len(capturas) - antes, flush=True)
    contexto.close()

SAIDA.write_text(json.dumps(capturas, ensure_ascii=False), encoding="utf-8")
print("total respostas:", len(capturas), flush=True)
