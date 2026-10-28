"""
coleta.py - lista todos os certificados da conta (sessão salva em perfil/) e grava dados/certificados_api.json.

A própria página do DIO busca a lista em páginas de 12 itens conforme a rolagem; aqui apenas
observamos essas respostas no navegador logado. Não há token tratado neste script.
"""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
PERFIL = HERE / "perfil"
SAIDA = HERE / "dados" / "certificados_api.json"
PAGINA = "https://web.dio.me/certificates"


def coletar():
    itens_por_codigo = {}
    total = {"n": None}

    def ao_responder(resp):
        if "sms.dio.me/api" in resp.url and "/certificates/" in resp.url and resp.status == 200:
            corpo = resp.json()
            total["n"] = corpo.get("count", total["n"])
            for it in corpo.get("results", []):
                itens_por_codigo[it["code"]] = it

    with sync_playwright() as p:
        contexto = p.chromium.launch_persistent_context(str(PERFIL), channel="chrome", headless=False)
        pagina = contexto.pages[0] if contexto.pages else contexto.new_page()
        pagina.on("response", ao_responder)
        pagina.goto(PAGINA, wait_until="domcontentloaded")
        estavel = 0  # o DIO passa pelo auth.dio.me e volta: só conta quando fica estável
        for _ in range(120):
            estavel = estavel + 1 if pagina.url.startswith(PAGINA) else 0
            if estavel >= 5:
                break
            pagina.wait_for_timeout(1000)
        sem_novidade = 0
        while sem_novidade < 4:
            antes = len(itens_por_codigo)
            pagina.mouse.wheel(0, 6000)
            pagina.wait_for_timeout(2000)
            sem_novidade = 0 if len(itens_por_codigo) > antes else sem_novidade + 1
            if total["n"] and len(itens_por_codigo) >= total["n"]:
                break
        contexto.close()
    return total["n"], list(itens_por_codigo.values())


if __name__ == "__main__":
    total, itens = coletar()
    SAIDA.parent.mkdir(exist_ok=True)
    if not total or len(itens) < total:
        # sessão expirada ou página incompleta: nunca sobrescrever a lista boa com uma parcial
        print(f"coleta incompleta (DIO informou {total}, coletados {len(itens)}): nada gravado. "
              "Se a sessão expirou, rode login.py.")
        raise SystemExit(2)
    SAIDA.write_text(json.dumps(itens, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"total informado pelo DIO: {total} | coletados: {len(itens)} | salvo em dados/")
