import re
from pathlib import Path

import pymupdf

raiz = Path(__file__).resolve().parent.parent / "data" / "raw"
casos = [(2023, 2, 1, 10, "lc-cn"), (2024, 2, 1, 17, "lc-cn"), (2023, 1, 2, 7, "mt-ch")]

for ano, serie, dia, numero, sufixo in casos:
    caminho = raiz / str(ano) / f"{ano}-{serie}a-{sufixo}.pdf"
    doc = pymupdf.open(caminho)
    texto = "\n".join(p.get_text() for p in doc)
    doc.close()
    partes = list(re.finditer(r"QUEST[ÃA]O\s+(\d+)", texto))
    for i, parte in enumerate(partes):
        if int(parte.group(1)) != numero:
            continue
        fim = partes[i + 1].start() if i + 1 < len(partes) else len(texto)
        print("=" * 80)
        print(ano, serie, dia, numero)
        print(texto[parte.start():fim][:1800])
        break
