import json
import re
from pathlib import Path

import fitz
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
REF = ROOT / "data" / "reference"
PROC.mkdir(parents=True, exist_ok=True)
REF.mkdir(parents=True, exist_ok=True)

DISCIPLINAS = {
    "lc": ["língua portuguesa", "português", "linguagens", "leitura", "interpretação"],
    "cn": ["ciências da natureza", "biologia", "física", "química"],
    "ch": ["ciências humanas", "história", "geografia", "sociologia", "filosofia"],
    "mt": ["matemática"],
}

def normaliza_texto(t):
    t = (t or "").lower()
    t = t.replace("–", "-").replace("—", "-")
    t = re.sub(r"\s+", " ", t)
    return t.strip()

def identificar_disciplina(texto):
    t = normaliza_texto(texto)
    if "matemática" in t or "matem" in t and "linguagens" not in t and "ciências humanas" not in t and "ciências da natureza" not in t:
        pass
    if re.search(r"\bmatem[aá]tica\b", t):
        if "ciências humanas" in t or "redação" in t:
            return "mt-ch"
        return "mt"
    if "ciências da natureza" in t and "linguagens" in t:
        return "lc-cn"
    if "linguagens" in t and "códigos" in t:
        return "lc"
    if "ciências humanas" in t and re.search(r"\bredação\b", t):
        return "mt-ch"
    if "ciências humanas" in t and "matemática" in t:
        return "mt-ch"
    if "ciências humanas" in t:
        return "ch"
    if "ciências da natureza" in t:
        return "cn"
    if "linguagens" in t:
        return "lc"
    return "outro"

def extrair_questoes(pdf_path):
    doc = fitz.open(pdf_path)
    linhas_todas = []
    for pagina in doc:
        texto = pagina.get_text("text")
        for linha in texto.splitlines():
            linha = linha.strip()
            if not linha:
                continue
            linhas_todas.append(linha)
    doc.close()
    bloco = []
    questoes = []
    qid = None
    for linha in linhas_todas:
        m = re.match(r"^QUEST[ÃA]O\s+(\d+)\b", linha)
        if m:
            if bloco and qid:
                questoes.append({"numero": int(qid), "texto": "\n".join(bloco)})
            qid = m.group(1)
            bloco = [linha]
            continue
        if qid and re.match(r"^[A-E]\)", linha):
            bloco.append(linha)
            continue
        if qid and re.match(r"^[A-E]\s", linha):
            bloco.append(linha)
            continue
        if qid and re.match(
            r"^(Língua|Matemática|Ciências|Para responder|Leia|Examine|Observe|"
            r"Analise|Assinale)\b",
            linha,
        ):
            bloco.append(linha)
            continue
        if qid and re.match(r"^\d+\.", linha) and not re.match(r"^QUEST", linha):
            bloco.append(linha)
            continue
        if qid:
            if len(linha) > 3 and not re.match(
                r"^(Confidencial|Saresp|Página|VERSÃO)\b", linha, re.I
            ):
                bloco.append(linha)
    if bloco and qid:
        questoes.append({"numero": int(qid), "texto": "\n".join(bloco)})
    return questoes

def mapear_gabarito(pdf_path):
    doc = fitz.open(pdf_path)
    gabaritos = {}
    for pagina in doc:
        texto = pagina.get_text("text")
        for linha in texto.splitlines():
            linha = linha.strip()
            m = re.match(r"^(\d{1,3})\s*[\-\:\.]\s*([A-E])\b", linha)
            if m:
                gabaritos[int(m.group(1))] = m.group(2)
                continue
            m2 = re.match(r"^(\d{1,3})\s+([A-E])\s*$", linha)
            if m2:
                gabaritos[int(m2.group(1))] = m2.group(2)
                continue
            m3 = re.findall(r"(\d{1,3})\s*[\-\:]\s*([A-E])", linha)
            for num, alt in m3:
                gabaritos[int(num)] = alt
    doc.close()
    return dict(sorted(gabaritos.items()))

def inferir_serie_e_disciplina_por_nome(arquivo):
    nome = arquivo.name.lower()
    serie = None
    if "1a" in nome or "1ª" in nome or "1 serie" in nome or "1º" in nome:
        serie = 1
    elif "2a" in nome or "2ª" in nome or "2º" in nome:
        serie = 2
    elif "3a" in nome or "3ª" in nome or "3º" in nome:
        serie = 3
    if "lc-cn" in nome or ("lc" in nome and "cn" in nome):
        disc = "lc-cn"
    elif "mt-ch" in nome:
        disc = "mt-ch"
    elif "lc" in nome and "cn" not in nome and "mt" not in nome and "ch" not in nome:
        disc = "lc"
    elif "mt" in nome and "ch" not in nome and "lc" not in nome:
        disc = "mt"
    elif "cn" in nome and "lc" not in nome:
        disc = "cn"
    elif "ch" in nome and "mt" not in nome:
        disc = "ch"
    else:
        disc = "outro"
    return serie, disc

def extrair_temas(questao_texto):
    t = questao_texto.lower()
    temas = []
    if re.search(r"tirinha|quadrinho|charge", t):
        temas.append("interpretação de imagem")
    if re.search(r"soneto|poema|verso|estrofe|rima", t):
        temas.append("gêneros poéticos")
    if re.search(r"crônica|conto|romance|narrativa", t):
        temas.append("gêneros narrativos")
    if re.search(r"artigo|reportagem|notícia", t):
        temas.append("gêneros jornalísticos")
    if re.search(r"funç[õa]es?|função sintática|sujeito|predicado|verbo", t):
        temas.append("gramática")
    if re.search(r"figuras de linguagem|metáfora|metonímia|antítese", t):
        temas.append("figuras de linguagem")
    if re.search(r"equação|funç[ãa]o|geometria|trigonometria|álgebra", t):
        temas.append("matemática")
    if re.search(r"revolução|independência|brasil colonial|república", t):
        temas.append("história do Brasil")
    if re.search(r"globalização|urbanização|clima|meio ambiente", t):
        temas.append("geografia")
    if re.search(r"célula|genética|ecologia|evolução", t):
        temas.append("biologia")
    if re.search(r"física|mecânica|eletricidade|óptica", t):
        temas.append("física")
    if re.search(r"química|átomo|ligações|orgânica|inorgânica", t):
        temas.append("química")
    if not temas:
        temas.append("outros")
    return temas

def main():
    registros = []
    for ano in [2023, 2024, 2025]:
        pasta = RAW / str(ano)
        if not pasta.exists():
            continue
        for arq in pasta.glob("*.pdf"):
            if "gab" not in arq.name:
                continue
            gabs = mapear_gabarito(arq)
            dia = None
            if "d1" in arq.name:
                dia = 1
            elif "d2" in arq.name:
                dia = 2
            serie, disc_gab = inferir_serie_e_disciplina_por_nome(arq)
            base_nome = arq.name.replace(f"-gab-d{dia}.pdf", ".pdf")
            base_path = pasta / base_nome
            if not base_path.exists():
                base_nome_alt = arq.name.replace("gab-d1", "lc-cn").replace("gab-d2", "mt-ch")
                if base_nome_alt.endswith(".pdf"):
                    cand = pasta / base_nome_alt
                    if cand.exists():
                        base_path = cand
            if not base_path.exists():
                continue
            questoes = extrair_questoes(base_path)
            serie_q, disc_q = inferir_serie_e_disciplina_por_nome(base_path)
            disc = disc_q if disc_q != "outro" else disc_gab
            serie_res = serie_q or serie
            for q in questoes:
                num = q["numero"]
                if num not in gabs:
                    continue
                temas = extrair_temas(q["texto"])
                registros.append({
                    "ano": ano,
                    "serie": serie_res,
                    "disciplina": disc,
                    "dia": dia,
                    "prova_arquivo": base_path.name,
                    "gabarito_arquivo": arq.name,
                    "questao_num": num,
                    "gabarito": gabs[num],
                    "temas": "; ".join(sorted(set(temas))),
                    "texto": q["texto"][:4000],
                })
    df = pd.DataFrame(registros)
    df.to_csv(PROC / "questoes_gabaritos.csv", index=False, encoding="utf-8-sig")
    df.to_json(PROC / "questoes_gabaritos.json", orient="records", force_ascii=False, indent=2)
    # Agregados
    temas_serie_disc = df.groupby(["ano", "serie", "disciplina", "temas"]).size().reset_index(name="quantidade")
    temas_serie_disc.to_csv(PROC / "temas_por_serie_disciplina.csv", index=False, encoding="utf-8-sig")
    por_disc = df.groupby(["ano", "disciplina"]).size().reset_index(name="quantidade")
    por_disc.to_csv(PROC / "quantidade_por_disciplina.csv", index=False, encoding="utf-8-sig")
    print(json.dumps({
        "total_registros": len(df),
        "anos": sorted(df["ano"].unique().tolist()),
        "series": sorted(df["serie"].dropna().unique().tolist()),
        "disciplinas": sorted(df["disciplina"].unique().tolist()),
    }, ensure_ascii=False))

if __name__ == "__main__":
    main()
