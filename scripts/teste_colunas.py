import re
import sys
from pathlib import Path

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from provao.extracao import BLOCOS, RUIDOS, _disciplina_do_item, _normalizar, _separar_alternativas


def texto_pagina(pagina) -> str:
    largura = pagina.rect.width
    meio = largura * 0.48
    blocos = []
    for bloco in pagina.get_text("blocks"):
        x0, y0, x1, y1, texto, *_ = bloco
        texto = texto.strip()
        if not texto:
            continue
        if y0 > pagina.rect.height - 40:
            continue
        if any(p.match(texto) for p in RUIDOS):
            continue
        largura_bloco = x1 - x0
        if largura_bloco > largura * 0.62:
            coluna = -1
        elif x0 >= meio:
            coluna = 1
        else:
            coluna = 0
        blocos.append((coluna, y0, x0, texto))
    blocos.sort(key=lambda b: (b[0], b[1], b[2]))
    return "\n".join(b[3] for b in blocos)


def extrair(ano, serie, dia, pasta):
    caderno = pasta / str(ano) / f"{ano}-{serie}a-{'lc-cn' if dia == 1 else 'mt-ch'}.pdf"
    doc = pymupdf.open(caderno)
    paginas = [texto_pagina(p) for p in doc]
    doc.close()
    texto = ""
    for conteudo in paginas:
        texto += conteudo + "\n\f\n"
    partes = list(re.finditer(r"QUEST[ÃA]O\s+(\d+)", texto))
    resultados = []
    for i, parte in enumerate(partes):
        numero = int(parte.group(1))
        if _disciplina_do_item(ano, serie, dia, numero) is None:
            continue
        fim = partes[i + 1].start() if i + 1 < len(partes) else len(texto)
        bloco = _normalizar(texto[parte.end():fim])
        enunciado, alternativas = _separar_alternativas(bloco)
        resultados.append((numero, alternativas, enunciado))
    return resultados


if __name__ == "__main__":
    raiz = Path(__file__).resolve().parent.parent / "data" / "raw"
    total = 0
    sem = []
    for ano in BLOCOS:
        for serie in BLOCOS[ano]:
            for dia in BLOCOS[ano][serie]:
                for numero, alternativas, _enunciado in extrair(ano, serie, dia, raiz):
                    total += 1
                    if len(alternativas) < 4:
                        sem.append((ano, serie, dia, numero, len(alternativas)))
    print("total", total, "sem alternativas", len(sem))
    print(sem[:60])
