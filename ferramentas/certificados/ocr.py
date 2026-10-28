"""
ocr.py - lê os PDFs de dados/pdf/ (imagem única) com tesseract (idioma por) e extrai os campos
do certificado. Não baixa nada. Grava dados/ocr_certificados.json e atualiza o banco.

Campos: nome_aluno, data_pdf, curso e carga_horaria.
O título do curso vem da API (dados/certificados_api.json), que é a fonte correta. O OCR do título
serve só de conferência (curso_ocr_confere): a faixa vertical "Certification Program" e a borda
do certificado aparecem no OCR como letras soltas ("E", "é") no começo das linhas.
Requer: pdfimages (poppler-utils) e tesseract com o pacote de idioma por.
"""
import json
import re
import shutil
import sqlite3
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
DADOS = HERE / "dados"
PDFS = DADOS / "pdf"
SAIDA = DADOS / "ocr_certificados.json"
LISTA_API = DADOS / "certificados_api.json"
BANCO = DADOS / "certificados.db"

MESES = {"janeiro": 1, "fevereiro": 2, "março": 3, "marco": 3, "abril": 4, "maio": 5, "junho": 6,
         "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12}


def ocr_pdf(pdf):
    """Extrai a imagem da página 1 e roda o tesseract; devolve o texto."""
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "img"
        subprocess.run(["pdfimages", "-j", "-f", "1", "-l", "1", str(pdf), str(base)], check=True)
        imagens = sorted(Path(tmp).glob("img-*.jpg"))
        if not imagens:
            raise RuntimeError("PDF sem imagem")
        r = subprocess.run(["tesseract", str(imagens[0]), "-", "-l", "por", "--psm", "6"],
                           capture_output=True, text=True, check=True)
        return r.stdout


def escolher_nome(linhas):
    """Primeira linha com pelo menos duas palavras de 3+ letras; corta letras soltas no fim."""
    for l in linhas:
        palavras = [w for w in re.findall(r"[A-Za-zÀ-ÿ]+", l)]
        if len([w for w in palavras if len(w) >= 3]) >= 2 and not l.lower().startswith("em "):
            usadas = []
            for w in palavras:
                if len(w) < 2 and usadas:
                    break
                usadas.append(w)
            while usadas and len(usadas[-1]) < 3:  # sufixos curtos no fim são ruído do selo
                usadas.pop()
            return " ".join(usadas)
    return None


def extrair(texto):
    limpo = [l.strip() for l in texto.splitlines() if l.strip()]
    campos = {"nome_aluno": None, "data_pdf": None, "curso": None, "carga_horaria": None}
    for i, l in enumerate(limpo):
        if "Certificamos" in l and campos["nome_aluno"] is None:
            campos["nome_aluno"] = escolher_nome(limpo[i + 1:i + 4])
        m = re.search(r"em\s+(\d{1,2})\s+de\s+([A-Za-zçÇãé]+)\s+de\s+(\d{4})", l)
        if m and m.group(2).lower() in MESES:
            campos["data_pdf"] = datetime(int(m.group(3)), MESES[m.group(2).lower()], int(m.group(1))).date().isoformat()
            if "concluiu o curso" in l and i + 1 < len(limpo):
                campos["curso"] = " ".join(limpo[i + 1:i + 3]) if "com carga" not in limpo[i + 1] else limpo[i + 1]
            elif "concluiu o curso" in l:
                campos["curso"] = None
        m = re.search(r"carga horária de\s+(.+?)\.?$", l)
        if m:
            campos["carga_horaria"] = m.group(1).strip()
    return campos


def normalizar(t):
    import unicodedata
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def sem_ruido_inicial(texto):
    """Remove letras soltas no começo (ruído da borda do certificado)."""
    palavras = (texto or "").split()
    while palavras and len(palavras[0]) <= 2 and palavras[0] not in ("C#", "IA", "AI", "Go"):
        palavras.pop(0)
    return " ".join(palavras) or None


def main():
    import sys
    if not LISTA_API.exists():
        raise SystemExit("Sem dados/certificados_api.json: rode coleta.py e baixar.py antes.")
    resultado = {} if "--todos" in sys.argv or not SAIDA.exists() else json.loads(SAIDA.read_text(encoding="utf-8"))
    falhas, novos = [], []
    for pdf in sorted(PDFS.glob("*.pdf")):
        if pdf.stem in resultado:
            continue  # já lido; use --todos para reler
        try:
            resultado[pdf.stem] = extrair(ocr_pdf(pdf))
            novos.append(pdf.stem)
        except Exception as e:
            falhas.append((pdf.stem, type(e).__name__))
    titulos_api = {i["code"]: i["name"] for i in json.loads(LISTA_API.read_text(encoding="utf-8"))}
    for codigo in novos:  # só leituras novas: as antigas já têm o título da API
        v = resultado[codigo]
        bruto = v["curso"]
        lido = sem_ruido_inicial(bruto)
        v["curso"] = titulos_api.get(codigo, lido)
        alvo = normalizar(v["curso"])
        v["curso_ocr_confere"] = None if not bruto else (alvo in normalizar(bruto) or alvo in normalizar(lido))
    SAIDA.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding="utf-8")
    sem_campo = [k for k, v in resultado.items() if not v["nome_aluno"] or not v["carga_horaria"] or not v["data_pdf"]]
    print(f"lidos agora: {len(novos)} | total: {len(resultado)} | falhas: {len(falhas)} "
          f"| com campo faltando: {len(sem_campo)}")
    for codigo, erro in falhas:
        print("  falha:", codigo, erro)
    for codigo in sem_campo:
        print("  incompleto:", codigo, [k for k, v in resultado[codigo].items() if not v and k != "curso"])
    if BANCO.exists():
        con = sqlite3.connect(BANCO)
        for codigo, v in resultado.items():
            con.execute("UPDATE certificados SET nome_aluno = ?, carga_horaria = ? WHERE codigo = ?",
                        (v["nome_aluno"], v["carga_horaria"], codigo))
        con.commit()
        con.close()
        print("banco atualizado (nome_aluno e carga_horaria)")


if __name__ == "__main__":
    main()
