#!/usr/bin/env python3
"""
login.py - abre o Chrome com um perfil local para você entrar no DIO uma vez.

A senha nunca passa por este script: você digita no navegador. A sessão fica em
perfil/ (ignorado pelo git) e é reaproveitada pelos próximos scripts.

Uso (dentro desta pasta):
  .venv/bin/python login.py              # abre o navegador para você fazer login
  .venv/bin/python login.py --verificar  # testa se a sessão salva ainda vale (sem janela)

No Windows, troque .venv/bin/python por .venv\\Scripts\\python.
"""
import argparse
import sys
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
PERFIL = HERE / "perfil"
LOGIN_URL = "https://web.dio.me/"  # /login responde 404 direto; o login começa pelo botão "Entrar"
TESTE_URL = "https://web.dio.me/certificates"


def sessao_valida(pagina):
    """Logado = a página de certificados fica no próprio web.dio.me, sem ficar no auth.dio.me.

    O DIO faz um redirecionamento silencioso para o auth.dio.me por alguns segundos e depois
    devolve ao web.dio.me. Por isso a URL é lida depois de um tempo de espera, não logo após
    o carregamento (o networkidle chega antes do retorno).
    """
    pagina.goto(TESTE_URL, wait_until="domcontentloaded")
    estavel = 0  # segundos seguidos dentro de web.dio.me/certificates
    for _ in range(60):
        destino = urlparse(pagina.url)
        no_lugar = destino.netloc == "web.dio.me" and destino.path.startswith("/certificates")
        estavel = estavel + 1 if no_lugar else 0
        if estavel >= 5:
            return True
        pagina.wait_for_timeout(1000)
    return False


def abrir_para_login():
    PERFIL.mkdir(exist_ok=True)
    with sync_playwright() as p:
        contexto = p.chromium.launch_persistent_context(
            str(PERFIL), channel="chrome", headless=False,
        )
        pagina = contexto.pages[0] if contexto.pages else contexto.new_page()
        pagina.goto(LOGIN_URL)
        print("Na janela que abriu, clique em Entrar e faça login no DIO.")
        try:
            input("Quando estiver logado, pressione Enter aqui para salvar a sessão... ")
        except EOFError:
            contexto.close()
            print("Sem terminal interativo: rode este comando num terminal normal, não pelo '!'.")
            return 1
        ok = sessao_valida(pagina)
        contexto.close()
    if ok:
        print("OK: sessão salva em perfil/.")
        return 0
    print("Não consegui confirmar o login (a página de certificados redirecionou). "
          "Rode de novo e confirme que entrou.")
    return 1


def verificar():
    if not PERFIL.exists():
        print("Sem sessão salva. Rode: .venv/bin/python login.py")
        return 1
    with sync_playwright() as p:
        # Com headless o DIO manda a sessão para o login mesmo logada; a janela visível funciona.
        contexto = p.chromium.launch_persistent_context(
            str(PERFIL), channel="chrome", headless=False,
        )
        pagina = contexto.pages[0] if contexto.pages else contexto.new_page()
        ok = sessao_valida(pagina)
        contexto.close()
    if ok:
        print("Sessão válida.")
        return 0
    print("Sessão expirada ou inexistente. Rode: .venv/bin/python login.py")
    return 1


def main():
    p = argparse.ArgumentParser(description="Login manual no DIO com sessão salva")
    p.add_argument("--verificar", action="store_true", help="testa a sessão salva, sem abrir janela")
    args = p.parse_args()
    sys.exit(verificar() if args.verificar else abrir_para_login())


if __name__ == "__main__":
    main()
