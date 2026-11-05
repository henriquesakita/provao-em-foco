"""Construção e carga dos dados processados do Provão Paulista.

O pacote guarda apenas dados derivados de documentos públicos. Os PDFs
originais ficam em ``data/raw`` e não são versionados.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from provao.extracao import Questao, extrair_tudo
from provao.taxonomia import classificar

RAIZ = Path(__file__).resolve().parents[2]
PASTA_PROCESSADOS = RAIZ / "data" / "processed"

COLUNAS_QUESTOES = [
    "chave",
    "ano",
    "serie",
    "dia",
    "numero",
    "disciplina",
    "tema",
    "gabarito",
    "enunciado",
    "alternativas_json",
    "alternativas_texto",
    "apoio_visual",
    "pagina",
    "caderno",
]

# O texto extraído dos PDFs carrega hífens suaves e caracteres de largura zero
# no meio das palavras ("f\u00adigura", "t\u00adabela"). Sem limpá-los, a busca
# por apoio visual falha justamente nos itens que mais precisam ser barrados.
_MARCAS_INVISIVEIS = re.compile(r"[\u00ad\u200b\u200c\u200d\ufeff\u2060]")


def _normalizar_texto(valor: object) -> str:
    return _MARCAS_INVISIVEIS.sub("", str(valor))


# Questões que dependem de figura, gráfico, mapa, tira, tabela ou outro apoio
# visual do caderno não podem ser respondidas apenas com o texto extraído. O
# simulado usa esta marca para deixá-las de fora. A lista é deliberadamente
# ampla: excluir um item a mais é menos prejudicial do que exibir uma questão
# sem o material necessário. Ficam fora apenas expressões figuradas conhecidas,
# como "figura de linguagem", "figura do Estado", "quadro urbano",
# "Convenção-Quadro" e "tabela periódica".
_APOIO_VISUAL = re.compile(
    r"\b(?:"
    r"tiras?|tirinhas?"
    r"|quadrinhos?"
    r"|(?<![Cc]onven[cç][aã]o-)quadros?"
    r"(?!\s+(?:de\s+medalhas|urbano|cl[ií]nico|geral|negro|branco))"
    r"|cartaz(?:es)?"
    r"|pinturas?|esculturas?"
    r"|figuras?"
    r"(?!\s+(?:de\s+linguagem|da\s+linguagem|de\s+ret[oó]rica"
    r"|de\s+um\s+Estado|do\s+Estado|p[uú]blica|hist[oó]rica"
    r"|emblem[áa]tica|representativa|paterna|materna))"
    r"|gr[áa]ficos?|mapas?|esquemas?|diagramas?"
    r"|fotografias?|fotos?|ilustra[cç][aã]o|ilustra[cç][oõ]es"
    r"|infogr[áa]ficos?|histogramas?|maquetes?|fluxogramas?|pictogramas?"
    r"|charges?|cartu[mn]s?"
    r"|heredogramas?|cladogramas?"
    r"|tabelas?(?!\s+peri[oó]dicas?)"
    r")\b"
    r"|\bteias?\s+alimentar(?:es)?\b"
    r"|\b(?:examine|observe|veja|analise|considere)\s+(?:o|os|a|as)?\s*memes?\b"
    r"|\b(?:o|os)\s+meme(?:s)?\s+(?:apresentado|mostrado|acima|a seguir)\b"
    r"|\b(?:no|do)\s+meme\b"
    r"|\b(?:examine|observe|veja|analise|considere)\s+(?:o|os)\s+desenhos?\b"
    r"|\bdesenhos?\s+(?:a seguir|abaixo|acima|ao lado)\b"
    r"|\b(?:a|as)\s+imag(?:em|ens)\s+(?:mostra|mostram|retrata|retratam|apresenta"
    r"|apresentam|representa|representam|ilustra|ilustram|indica|indicam"
    r"|reproduz|reproduzem|exibe|exibem|destaca|destacam)\b"
    r"|\b(?:na|nas|nessa|nessas|nesta|nestas|desta|destas)\s+imag(?:em|ens)\b"
    r"|\b(?:observe|veja|analise|examine|considere)\s+(?:a|as)\s+imag(?:em|ens)\b"
    r"|\b(?:an[áa]lise|conte[úu]do)\s+d[ao]s?\s+imag(?:em|ens)\b"
    r"|\bimagem\s+(?:original|inserida|gerada|ampliada|a seguir|abaixo"
    r"|acima|ao lado|anterior)\b"
    r"|\bimagem\s+e\s+seu\s+conte[úu]do\b"
    r"|\ban[áa]lise\s+da\s+obra\b|\bc[ée]dula\s+simb[óo]lica\b"
    r"|\b(?:representa[cç][aã]o|pictograma|circuito|postagens?)"
    r"\s+(?:a seguir|abaixo|acima|ao lado)\b"
    r"|\b(?:conforme|de acordo com)\s+(?:a|o)\s+(?:representa[cç][aã]o"
    r"|processo representado)\b"
    r"|\bprocesso representado a seguir\b"
    r"|\bconforme\s+(?:as|os)\s+equa[cç][oõ]es\s+a seguir\b"
    r"|\b(?:[áa]rvores?)\s+(?:filogen[ée]ticas?|evolutivas?)\b",
    re.IGNORECASE,
)

# As alternativas também podem remeter a um apoio visual ("a foto a seguir foi
# registrada..."). Aqui a busca é mais estreita para não confundir figuras de
# linguagem com imagens do caderno.
_APOIO_VISUAL_ALTERNATIVAS = re.compile(
    r"\b(?:fotos?|fotografias?|imag(?:em|ens)|figuras?|gr[áa]ficos?|tabelas?"
    r"|tiras?|quadrinhos?|cartaz(?:es)?|mapas?|esquemas?|diagramas?"
    r"|charges?|cartu[mn]s?|pictogramas?|circuitos?|postagens?"
    r"|representa[cç][oõ]es?)\s+(?:a seguir|abaixo|acima|ao lado|anterior)\b",
    re.IGNORECASE,
)


def _tem_apoio_visual(enunciado: str, alternativas_texto: str) -> bool:
    if not isinstance(alternativas_texto, str) or not alternativas_texto.strip():
        return True
    if _APOIO_VISUAL.search(_normalizar_texto(enunciado)):
        return True
    return bool(
        _APOIO_VISUAL_ALTERNATIVAS.search(_normalizar_texto(alternativas_texto))
    )


def _chave(q: Questao) -> str:
    return f"{q.ano}-{q.serie}-{q.dia}-{q.numero}"


def _questao_para_linha(q: Questao) -> dict:
    alternativas_texto = " ".join(q.alternativas.values()).strip()
    tema, _ = classificar(
        q.disciplina,
        q.enunciado,
        alternativas_texto,
        chave=_chave(q),
    )
    return {
        "chave": _chave(q),
        "ano": q.ano,
        "serie": q.serie,
        "dia": q.dia,
        "numero": q.numero,
        "disciplina": q.disciplina,
        "tema": tema,
        "gabarito": q.gabarito,
        "enunciado": q.enunciado,
        "alternativas_json": json.dumps(q.alternativas, ensure_ascii=False),
        "alternativas_texto": alternativas_texto,
        "apoio_visual": _tem_apoio_visual(q.enunciado, alternativas_texto),
        "pagina": q.pagina,
        "caderno": q.caderno,
    }


def construir_questoes(raiz_bruta: Path | None = None) -> pd.DataFrame:
    """Extrai os cadernos, classifica os temas e devolve uma tabela única."""
    raiz_bruta = raiz_bruta or RAIZ / "data" / "raw"
    questoes = extrair_tudo(raiz_bruta)
    linhas = [_questao_para_linha(q) for q in questoes]
    df = pd.DataFrame(linhas, columns=COLUNAS_QUESTOES)
    return df.sort_values(["ano", "serie", "dia", "numero"]).reset_index(drop=True)


def construir_contextos(raiz_bruta: Path | None = None) -> pd.DataFrame:
    """Texto da página em que cada questão começa.

    Serve para consultar gráficos, charges e textos de apoio cuja imagem não
    é extraída do PDF. Guardamos o texto bruto da página, sem tentar recortar
    o trecho exato, para não atribuir material errado a uma questão.
    """
    raiz_bruta = raiz_bruta or RAIZ / "data" / "raw"
    questoes = extrair_tudo(raiz_bruta)
    linhas = [
        {
            "chave": _chave(q),
            "ano": q.ano,
            "serie": q.serie,
            "dia": q.dia,
            "numero": q.numero,
            "disciplina": q.disciplina,
            "pagina": q.pagina,
            "contexto_pagina": q.contexto_pagina,
        }
        for q in questoes
    ]
    return pd.DataFrame(linhas).sort_values(
        ["ano", "serie", "dia", "numero"]
    ).reset_index(drop=True)


def agregar_temas(df: pd.DataFrame) -> pd.DataFrame:
    """Conta temas por ano, série e disciplina, com percentual interno."""
    agrupado = (
        df.groupby(["ano", "serie", "disciplina", "tema"], as_index=False)
        .size()
        .rename(columns={"size": "quantidade"})
    )
    totais = agrupado.groupby(["ano", "serie", "disciplina"])["quantidade"].transform(
        "sum"
    )
    agrupado["total_disciplina"] = totais
    agrupado["percentual"] = (agrupado["quantidade"] / totais * 100).round(1)
    return agrupado.sort_values(
        ["ano", "serie", "disciplina", "quantidade", "tema"],
        ascending=[True, True, True, False, True],
    ).reset_index(drop=True)


def agregar_disciplinas(df: pd.DataFrame) -> pd.DataFrame:
    """Quantidade de questões por ano, série e disciplina."""
    return (
        df.groupby(["ano", "serie", "disciplina"], as_index=False)
        .size()
        .rename(columns={"size": "quantidade"})
        .sort_values(["ano", "serie", "disciplina"])
        .reset_index(drop=True)
    )


def salvar_processados(
    df_questoes: pd.DataFrame,
    df_contextos: pd.DataFrame,
    pasta: Path | None = None,
) -> dict[str, Path]:
    pasta = pasta or PASTA_PROCESSADOS
    pasta.mkdir(parents=True, exist_ok=True)

    destinos = {
        "questoes": pasta / "questoes.csv.gz",
        "contextos": pasta / "contextos.csv.gz",
        "temas": pasta / "temas.csv.gz",
        "disciplinas": pasta / "disciplinas.csv.gz",
    }
    df_questoes.to_csv(destinos["questoes"], index=False, compression="gzip")
    df_contextos.to_csv(destinos["contextos"], index=False, compression="gzip")
    agregar_temas(df_questoes).to_csv(
        destinos["temas"], index=False, compression="gzip"
    )
    agregar_disciplinas(df_questoes).to_csv(
        destinos["disciplinas"], index=False, compression="gzip"
    )
    return destinos


def carregar_questoes(pasta: Path | None = None) -> pd.DataFrame:
    pasta = pasta or PASTA_PROCESSADOS
    df = pd.read_csv(pasta / "questoes.csv.gz")
    # Recalcula a marca para que mudanças na regra valham mesmo sem regerar
    # todo o conjunto processado.
    df["apoio_visual"] = [
        _tem_apoio_visual(enunciado, alternativas)
        for enunciado, alternativas in zip(
            df["enunciado"], df["alternativas_texto"], strict=True
        )
    ]
    return df


def carregar_contextos(pasta: Path | None = None) -> pd.DataFrame:
    pasta = pasta or PASTA_PROCESSADOS
    return pd.read_csv(pasta / "contextos.csv.gz")


def carregar_temas(pasta: Path | None = None) -> pd.DataFrame:
    pasta = pasta or PASTA_PROCESSADOS
    return pd.read_csv(pasta / "temas.csv.gz")


def carregar_disciplinas(pasta: Path | None = None) -> pd.DataFrame:
    pasta = pasta or PASTA_PROCESSADOS
    return pd.read_csv(pasta / "disciplinas.csv.gz")
