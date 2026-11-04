"""Testes dos dados processados do Provão Paulista."""

from __future__ import annotations

import pandas as pd
import pytest

from provao.dados import (
    agregar_disciplinas,
    agregar_temas,
    carregar_contextos,
    carregar_disciplinas,
    carregar_questoes,
    carregar_temas,
)


@pytest.fixture(scope="module")
def questoes() -> pd.DataFrame:
    return carregar_questoes()


def test_total_de_questoes(questoes: pd.DataFrame) -> None:
    assert len(questoes) == 810


def test_90_questoes_por_ano_e_serie(questoes: pd.DataFrame) -> None:
    contagem = questoes.groupby(["ano", "serie"]).size()
    assert len(contagem) == 9
    assert (contagem == 90).all()


def test_todos_os_gabaritos_preenchidos(questoes: pd.DataFrame) -> None:
    assert questoes["gabarito"].notna().all()
    assert set(questoes["gabarito"]).issubset({"A", "B", "C", "D", "E"})


def test_todas_as_questoes_classificadas(questoes: pd.DataFrame) -> None:
    assert questoes["tema"].notna().all()
    assert (questoes["tema"].str.len() > 0).all()


def test_dez_componentes(questoes: pd.DataFrame) -> None:
    assert questoes["disciplina"].nunique() == 10


def test_questoes_de_imagem_preservadas(questoes: pd.DataFrame) -> None:
    # Itens cujas alternativas são apenas imagens continuam no banco, com
    # indicação da página do caderno.
    sem_texto = questoes[questoes["alternativas_texto"].isna()]
    assert len(sem_texto) == 27
    assert (sem_texto["pagina"] > 0).all()


def test_apoio_visual_fora_do_simulado(questoes: pd.DataFrame) -> None:
    assert questoes["apoio_visual"].dtype == bool
    assert int(questoes["apoio_visual"].sum()) == 225
    assert questoes.loc[questoes["alternativas_texto"].isna(), "apoio_visual"].all()

    disponiveis = questoes[~questoes["apoio_visual"]]
    assert len(disponiveis) == 585
    assert disponiveis["alternativas_texto"].notna().all()
    assert (disponiveis["alternativas_texto"].str.len() > 0).all()


def test_chaves_unicas(questoes: pd.DataFrame) -> None:
    assert questoes["chave"].is_unique


def test_agregacoes_conferem(questoes: pd.DataFrame) -> None:
    temas = agregar_temas(questoes)
    assert temas["quantidade"].sum() == len(questoes)
    assert (temas["percentual"] <= 100).all()

    disciplinas = agregar_disciplinas(questoes)
    assert disciplinas["quantidade"].sum() == len(questoes)


def test_arquivos_agregados_carregam() -> None:
    assert len(carregar_temas()) > 0
    # Em 2023 há Filosofia e Sociologia na mesma edição; em 2024 e 2025 o
    # caderno alterna as duas disciplinas entre as séries.
    assert len(carregar_disciplinas()) == 86
    assert len(carregar_contextos()) == 810
