import json
import re
from pathlib import Path

TEXTO = Path("data/raw/2026/edital.txt").read_text(encoding="utf-8")
inicio = TEXTO.find("ANEXO VII")
fim = TEXTO.find("ANEXO VIII", inicio)
bloco = TEXTO[inicio:fim]

DISCIPLINAS = [
    "LÍNGUA PORTUGUESA",
    "LÍNGUA INGLESA",
    "MATEMÁTICA",
    "QUÍMICA",
    "FÍSICA",
    "BIOLOGIA",
    "HISTÓRIA",
    "GEOGRAFIA",
    "FILOSOFIA",
    "SOCIOLOGIA",
]

series = {}
partes = re.split(r"PROV[ÃA]O PAULISTA SERIADO (I{1,3})\b", bloco)
for i in range(1, len(partes), 2):
    romano = partes[i]
    corpo = partes[i + 1]
    marcas = [
        (m.start(), m.group(1))
        for m in re.finditer(rf"^({'|'.join(DISCIPLINAS)})\s*$", corpo, re.M)
    ]
    dados = {}
    for j, (pos, nome) in enumerate(marcas):
        fim_disc = marcas[j + 1][0] if j + 1 < len(marcas) else len(corpo)
        trecho = corpo[pos + len(nome) : fim_disc]
        topicos = []
        for linha in trecho.splitlines():
            m = re.match(r"^(\d+)\.\s*(.+)$", linha.strip())
            if m and not re.match(r"^\d", m.group(2)):
                topicos.append({"n": int(m.group(1)), "titulo": m.group(2).strip()})
        dados[nome.title()] = topicos
    series[romano] = dados

for romano, dados in series.items():
    print("=====", romano)
    for disc, topicos in dados.items():
        print(f"  {disc} ({len(topicos)})")
        for t in topicos:
            print(f"     {t['n']}. {t['titulo']}")

Path("data/reference/topicos_anexo_vii.json").write_text(
    json.dumps(series, ensure_ascii=False, indent=2), encoding="utf-8"
)
