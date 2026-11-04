import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
REF = ROOT / "data" / "reference"

# Mapear nomes das provas para (ano, serie, dia)
# 2023: 1a/2a/3a-lc-cn = d1, mt-ch = d2
# 2024/2025: 1a/2a/3a-lc-cn = d1, mt-ch = d2

registros = []
for ano in [2023, 2024, 2025]:
    pasta = ROOT / "data" / "raw" / str(ano)
    for arq in pasta.glob("*.pdf"):
        if "gab" not in arq.name:
            continue
        nome = arq.name
        # série
        mserie = re.search(r"([123])[aªº]", nome)
        serie = int(mserie.group(1)) if mserie else None
        if "lc-cn" in nome:
            dia = 1
            disc_base = "lc-cn"
        elif "mt-ch" in nome:
            dia = 2
            disc_base = "mt-ch"
        elif "d1" in nome:
            dia = 1
        elif "d2" in nome:
            dia = 2
        else:
            continue
        gabs = {}
        import pymupdf

        d = pymupdf.open(arq)
        t = "\n".join(p.get_text() for p in d)
        d.close()
        for m in re.finditer(r"(\d{1,3})\s*[\-\:]\s*([A-E])", t):
            gabs[int(m.group(1))] = m.group(2)
        for m in re.finditer(r"^(\d{1,3})\s+([A-E])\s*$", t, re.M):
            gabs.setdefault(int(m.group(1)), m.group(2))
        gabs = dict(sorted(gabs.items()))
        base = nome.replace(f"-gab-d{dia}.pdf", ".pdf")
        base_path = pasta / base
        if not base_path.exists():
            for cand in pasta.glob("*.pdf"):
                if cand.name == nome:
                    continue
                if "gab" in cand.name:
                    continue
                if mserie and re.search(r"([123])[aªº]", cand.name) and mserie.group(1) in cand.name:
                    if dia == 1 and ("lc" in cand.name or "cn" in cand.name):
                        base_path = cand
                        break
                    if dia == 2 and ("mt" in cand.name or "ch" in cand.name):
                        base_path = cand
                        break
        if not base_path.exists():
            continue
        # extrair questões
        doc = pymupdf.open(base_path)
        texto = "\n".join(p.get_text() for p in doc)
        doc.close()
        texto = re.sub(r"[ \t]+", " ", texto)
        partes = re.split(r"QUEST[ÃA]O\s+(\d+)", texto)
        for i in range(1, len(partes), 2):
            num = int(partes[i])
            if num not in gabs:
                continue
            qtxt = re.sub(r"\s+", " ", partes[i + 1]).strip()
            # classificar simples
            tl = qtxt.lower()
            temas = []
            if re.search(r"tirinha|quadrinho|charge|cartum", tl):
                temas.append("interpretação de imagem")
            if re.search(r"poema|soneto|verso|rima", tl):
                temas.append("poesia")
            if re.search(r"crônica|conto|narrativa|romance", tl):
                temas.append("narrativa")
            if re.search(r"gramática|verbo|sujeito|concordância|regência", tl):
                temas.append("gramática")
            if re.search(r"figuras de linguagem|metáfora|hipérbole", tl):
                temas.append("figuras de linguagem")
            if re.search(r"equação|função|geometria|trigonometria|probabilidade", tl):
                temas.append("matemática")
            if re.search(r"revolução|coloniza|república|império|feudal", tl):
                temas.append("história")
            if re.search(r"globaliza|urbaniza|clima|popula|territó", tl):
                temas.append("geografia")
            if re.search(r"célula|genética|ecologia|evolução|biologia", tl):
                temas.append("biologia")
            if re.search(r"física|mecânica|eletricidade|energia|força", tl):
                temas.append("física")
            if re.search(r"química|átomo|reação|solução|orgânica", tl):
                temas.append("química")
            if re.search(r"sociologia|filosofia|ética|cidadania|direitos", tl):
                temas.append("ciências humanas/filosofia/sociologia")
            if re.search(r"inglês|english|text|choose", tl):
                temas.append("inglês")
            if not temas:
                temas.append("outros")
            registros.append(
                {
                    "ano": ano,
                    "serie": serie,
                    "dia": dia,
                    "disciplina_prova": disc_base,
                    "questao_num": num,
                    "gabarito": gabs[num],
                    "temas": "; ".join(sorted(set(temas))),
                    "prova": base_path.name,
                    "gabarito_arquivo": nome,
                }
            )

df = pd.DataFrame(registros)
PROC.mkdir(parents=True, exist_ok=True)
df.to_csv(PROC / "questoes_mapeadas.csv", index=False, encoding="utf-8-sig")
df.to_json(PROC / "questoes_mapeadas.json", orient="records", force_ascii=False, indent=2)

resumo = {
    "total": len(df),
    "por_ano": df.groupby("ano").size().to_dict(),
    "por_serie_dia": df.groupby(["serie", "dia"]).size().to_dict(),
    "por_disciplina_prova": df.groupby("disciplina_prova").size().to_dict(),
}
print(json.dumps(resumo, ensure_ascii=False))
