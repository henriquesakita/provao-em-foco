import re
from pathlib import Path

TEXTO = Path("data/raw/2026/edital.txt").read_text(encoding="utf-8")
inicio = TEXTO.find("ANEXO VII")
fim = TEXTO.find("ANEXO VIII", inicio)
bloco = TEXTO[inicio : fim if fim > 0 else len(TEXTO)]

print("tamanho bloco", len(bloco), "fim anexo VIII", fim)

# mostra linhas que parecem títulos de série/disciplina
for linha in bloco.splitlines():
    s = linha.strip()
    if re.fullmatch(r"PROV[ÃA]O PAULISTA SERIADO (I{1,3}|III)", s, re.I) or re.fullmatch(
        r"[A-ZÁÂÃÀÉÊÍÓÔÕÚÇ][A-ZÁÂÃÀÉÊÍÓÔÕÚÇ\s\-]{3,45}", s
    ):
        print(repr(s))
