#!/usr/bin/env python3
"""
pre_push.py - antes de cada push, atualiza perfil, certificados, README e entregas.

1. Descobre as pastas de desafio com código novo nos commits que estão subindo
   e as marca como entregues (dio.py entregar), se ainda não estiverem.
2. Roda ferramentas/certificados/atualizar.py.
3. Se algum arquivo gerado mudou, faz um commit só com esses arquivos e interrompe o push:
   rode `git push` de novo para enviar tudo junto (na segunda vez nada muda e o push segue).

Ativação (uma vez por clone):  git config core.hooksPath .githooks
Pular uma vez:                 git push --no-verify   (ou DIO_SEM_ATUALIZAR=1 git push)
Sem acessar o DIO:             DIO_OFFLINE=1 git push
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip())
ZERO = "0" * 40
DESAFIO = re.compile(r"^formacoes/([^/]+)/[^/]+/(\d\d-desafio-[^/]+)/(.+)$")
GERADOS = re.compile(r"^(README\.md|formacoes/[^/]+/(formacao\.json|README\.md|ENTREGAS\.md)"
                     r"|formacoes/[^/]+/[^/]+/\d\d-desafio-[^/]+/README\.md)$")


def git(*args):
    return subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True).stdout


def arquivos_enviados(entrada):
    arquivos = set()
    for linha in entrada.splitlines():
        partes = linha.split()
        if len(partes) != 4 or partes[1] == ZERO:  # remoção de branch
            continue
        local, remoto = partes[1], partes[3]
        faixa = [local, "--not", "--remotes"] if remoto == ZERO else [f"{remoto}..{local}"]
        arquivos |= {a for a in git("log", "--name-only", "--pretty=format:", *faixa).splitlines() if a}
    return arquivos


def desafios_entregues(arquivos):
    alvos = set()
    for a in arquivos:
        m = DESAFIO.match(a)
        if m and m.group(3) != "README.md":  # só conta código, não o README gerado
            alvos.add((m.group(1), m.group(2)))
    pendentes = []
    for slug, pasta in sorted(alvos):
        fjson = RAIZ / "formacoes" / slug / "formacao.json"
        dados = json.loads(fjson.read_text(encoding="utf-8")) if fjson.exists() else {"modulos": []}
        ja = any(at.get("pasta") == pasta and (at.get("entrega") or {}).get("status") == "entregue"
                 for m in dados["modulos"] for at in m["atividades"])
        if not ja:
            pendentes.append(f"{slug}/{pasta}")
    return pendentes


def sujos():
    return {l[3:] for l in git("status", "--porcelain", "--untracked-files=all").splitlines()}


def main():
    if os.environ.get("DIO_SEM_ATUALIZAR"):
        return 0
    entregues = desafios_entregues(arquivos_enviados(sys.stdin.read()))
    antes = sujos()
    comando = [sys.executable, str(RAIZ / "ferramentas" / "certificados" / "atualizar.py")]
    if os.environ.get("DIO_OFFLINE"):
        comando.append("--offline")
    if entregues:
        comando += ["--entregue", *entregues]
        print("[dio] desafios entregues neste push:", ", ".join(entregues), flush=True)
    subprocess.run(comando, cwd=RAIZ)

    # só arquivos gerados que estavam limpos antes: nunca leva junto trabalho em andamento
    mudaram = sorted(a for a in sujos() - antes if GERADOS.match(a))
    if not mudaram:
        return 0
    git("add", "--", *mudaram)
    git("commit", "-m", "chore(dio): atualiza perfil, certificados e entregas", "--", *mudaram)
    print("\n[dio] Atualizações commitadas:", *mudaram, sep="\n  ", flush=True)
    print("[dio] Push interrompido para incluir esse commit. Rode `git push` de novo.", flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
