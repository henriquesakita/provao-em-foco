"""Testes da taxonomia de temas."""

from __future__ import annotations

import pandas as pd
import pytest

from provao.dados import carregar_questoes
from provao.taxonomia import REGRAS


@pytest.fixture(scope="module")
def questoes() -> pd.DataFrame:
    return carregar_questoes()


def test_temas_pertencem_a_taxonomia(questoes: pd.DataFrame) -> None:
    for disciplina, grupo in questoes.groupby("disciplina"):
        permitidos = {tema for tema, _ in REGRAS[disciplina]}
        assert set(grupo["tema"]).issubset(permitidos)


def test_todas_as_disciplinas_tem_regras() -> None:
    assert set(REGRAS) == {
        "Língua Portuguesa",
        "Língua Inglesa",
        "Matemática",
        "Biologia",
        "Física",
        "Química",
        "História",
        "Geografia",
        "Filosofia",
        "Sociologia",
    }


def test_tema_manual_de_durkheim(questoes: pd.DataFrame) -> None:
    linha = questoes[questoes["chave"] == "2023-3-2-41"]
    assert len(linha) == 1
    assert linha.iloc[0]["tema"] == "Indivíduo e identidade"


def test_literatura_domina_portugues(questoes: pd.DataFrame) -> None:
    lp = questoes[questoes["disciplina"] == "Língua Portuguesa"]
    contagem = lp["tema"].value_counts()
    assert contagem.index[0] == "Literatura"
    assert contagem.iloc[0] >= 50
