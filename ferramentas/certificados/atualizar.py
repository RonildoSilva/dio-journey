#!/usr/bin/env python3
"""
atualizar.py - atualiza tudo de uma vez: perfil (XP, nível), certificados novos, PDFs, OCR,
banco, pastas, README raiz e as formações (dio.py build). Chamado pelo hook pre-push.

Etapas com rede (perfil e lista de certificados) só rodam se:
  - existe o .venv com Playwright e uma sessão salva em perfil/;
  - a última consulta ao DIO foi há mais de 30 minutos (evita visitas repetidas).
Sem rede, as etapas locais (banco, pastas, README, build) rodam do mesmo jeito.

Uso (de qualquer pasta):
  python3 ferramentas/certificados/atualizar.py [--offline] [--forcar] [--entregue SLUG/PASTA ...]
No Windows: py ferramentas\\certificados\\atualizar.py

  --offline   não acessa o DIO (só etapas locais)
  --forcar    ignora o intervalo de 30 minutos
  --entregue  marca desafios como entregues (ex.: flutter-specialist/04-desafio-subindo-...)
"""
import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAIZ = HERE.parents[1]
DADOS = HERE / "dados"
ESTADO = DADOS / "ultima_atualizacao.json"
DIO = RAIZ / ".agents" / "skills" / "dio-formacoes" / "scripts" / "dio.py"
INTERVALO = 30 * 60
VENV_PY = HERE / ".venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def rodar(rotulo, comando):
    print(f"→ {rotulo}", flush=True)
    r = subprocess.run(comando, cwd=HERE)
    if r.returncode:
        print(f"  {rotulo}: código {r.returncode} (seguindo com os dados que já existem)", flush=True)
    return r.returncode == 0


def resumo():
    """Fotografia para comparar antes/depois: nível, XP e quantidade de certificados."""
    nivel = xp = None
    perfil = DADOS / "perfil_respostas.json"
    if perfil.exists():
        for c in json.loads(perfil.read_text(encoding="utf-8")):
            meta = (c["corpo"].get("meta") or {}) if isinstance(c["corpo"], dict) else {}
            if meta.get("level"):
                nivel, xp = meta["level"], meta.get("experience")
                break
    lista = DADOS / "certificados_api.json"
    certs = len(json.loads(lista.read_text(encoding="utf-8"))) if lista.exists() else 0
    return {"nivel": nivel, "xp": xp, "certificados": certs}


def pode_usar_rede(args):
    if args.offline:
        return False, "modo --offline"
    if not VENV_PY.exists():
        return False, "sem .venv (veja ferramentas/certificados/README.md, 'Como preparar')"
    if not (HERE / "perfil").exists():
        return False, "sem sessão salva (rode login.py)"
    if ESTADO.exists() and not args.forcar:
        ultima = json.loads(ESTADO.read_text(encoding="utf-8")).get("rede", 0)
        if time.time() - ultima < INTERVALO:
            return False, f"última consulta há {int((time.time() - ultima) / 60)} min (intervalo de 30 min)"
    return True, ""


def main():
    ap = argparse.ArgumentParser(description="Atualiza perfil, certificados e README")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--forcar", action="store_true")
    ap.add_argument("--entregue", nargs="*", default=[])
    args = ap.parse_args()
    DADOS.mkdir(exist_ok=True)
    antes = resumo()

    usar_rede, motivo = pode_usar_rede(args)
    if usar_rede:
        perfil_ok = rodar("perfil (nível, XP, conquistas)", [str(VENV_PY), "capturar_perfil.py"])
        lista_ok = rodar("lista de certificados", [str(VENV_PY), "coleta.py"])
        if lista_ok:
            rodar("PDFs novos", [str(VENV_PY), "baixar.py"])
        if perfil_ok or lista_ok:
            ESTADO.write_text(json.dumps({"rede": time.time()}), encoding="utf-8")
    else:
        print(f"→ DIO não consultado: {motivo}", flush=True)

    if shutil.which("tesseract") and shutil.which("pdfimages"):
        rodar("OCR dos PDFs novos", [sys.executable, "ocr.py"])
    else:
        print("→ OCR pulado: instale tesseract-ocr (por) e poppler-utils", flush=True)

    for alvo in args.entregue:
        slug, _, pasta = alvo.partition("/")
        rodar(f"entrega {alvo}", [sys.executable, str(DIO), "entregar", slug, pasta])

    if (DADOS / "certificados_api.json").exists():
        rodar("banco", [sys.executable, "banco.py"])
        rodar("pastas e README", [sys.executable, "organizar.py"])
    rodar("formações (dio.py build)", [sys.executable, str(DIO), "build"])

    depois = resumo()
    print("\nResumo:", flush=True)
    for chave in ("nivel", "xp", "certificados"):
        a, d = antes[chave], depois[chave]
        print(f"  {chave}: {a} -> {d}" + ("  (novo!)" if a != d and a is not None else ""), flush=True)


if __name__ == "__main__":
    main()
