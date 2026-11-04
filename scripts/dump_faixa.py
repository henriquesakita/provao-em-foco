import re
import sys

import pymupdf


def questoes(caminho):
    doc = pymupdf.open(caminho)
    texto = "\n".join(p.get_text() for p in doc)
    doc.close()
    texto = re.sub(r"[ \t]+", " ", texto)
    partes = re.split(r"QUEST[ÃA]O\s+(\d+)", texto)
    saida = {}
    for i in range(1, len(partes), 2):
        saida[int(partes[i])] = re.sub(r"\s+", " ", partes[i + 1]).strip()
    return saida


inicio = int(sys.argv[1])
fim = int(sys.argv[2])
for caminho in sys.argv[3:]:
    print("=====", caminho)
    qs = questoes(caminho)
    for numero in range(inicio, fim + 1):
        texto = qs.get(numero, "")
        print(f"{numero:02d}", texto[:150])
