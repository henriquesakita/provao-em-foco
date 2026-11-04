"""Construção e carga dos dados processados do Provão Paulista.

O pacote guarda apenas dados derivados de documentos públicos. Os PDFs
originais ficam em ``data/raw`` e não são versionados.
"""

from __future__ import annotations

import json
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
    "pagina",
    "caderno",
]


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
    return pd.read_csv(pasta / "questoes.csv.gz")


def carregar_contextos(pasta: Path | None = None) -> pd.DataFrame:
    pasta = pasta or PASTA_PROCESSADOS
    return pd.read_csv(pasta / "contextos.csv.gz")


def carregar_temas(pasta: Path | None = None) -> pd.DataFrame:
    pasta = pasta or PASTA_PROCESSADOS
    return pd.read_csv(pasta / "temas.csv.gz")


def carregar_disciplinas(pasta: Path | None = None) -> pd.DataFrame:
    pasta = pasta or PASTA_PROCESSADOS
    return pd.read_csv(pasta / "disciplinas.csv.gz")
