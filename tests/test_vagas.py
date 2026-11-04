"""Testes do quadro de vagas 2027."""

from __future__ import annotations

import pandas as pd
import pytest

from provao.vagas import EDITAL_PADRAO, carregar_historico_vagas, carregar_vagas

TOTAIS = {
    "USP": 1500,
    "UNESP": 929,
    "UNICAMP": 326,
    "UNIVESP": 3064,
    "FATEC": 7920,
}


@pytest.fixture(scope="module")
def vagas() -> pd.DataFrame:
    return carregar_vagas()


def test_total_publicado(vagas: pd.DataFrame) -> None:
    assert len(vagas) == 1835
    assert vagas["vagas_total"].sum() == 13739


def test_totais_por_instituicao(vagas: pd.DataFrame) -> None:
    soma = vagas.groupby("instituicao")["vagas_total"].sum().to_dict()
    assert soma == TOTAIS


def test_sem_municipio_vazio(vagas: pd.DataFrame) -> None:
    assert vagas["municipio"].notna().all()
    assert (vagas["municipio"].str.len() > 0).all()


def test_sem_area_desconhecida(vagas: pd.DataFrame) -> None:
    assert "Não informada" not in set(vagas["area_geral"])


def test_sao_paulo_unificado(vagas: pd.DataFrame) -> None:
    capital = vagas[vagas["municipio"] == "São Paulo"]
    assert capital["vagas_total"].sum() > 2500
    assert not vagas["municipio"].str.startswith("São Paulo/").any()


def test_historico_vagas_por_edicao() -> None:
    historico = carregar_historico_vagas()
    totais = historico.groupby("edicao")["vagas"].sum().to_dict()
    assert totais == {2023: 15369, 2024: 15380, 2025: 15717, 2026: 15819}
    assert set(historico["instituicao"]) == {"USP", "UNESP", "UNICAMP", "UNIVESP", "FATEC"}


def test_historico_confere_com_quadros_de_2026(vagas: pd.DataFrame) -> None:
    historico = carregar_historico_vagas()
    atual = historico[historico["edicao"] == 2026].set_index("instituicao")["vagas"]
    detalhado = vagas.groupby("instituicao")["vagas_total"].sum()
    for instituicao in ("USP", "UNESP", "UNICAMP", "UNIVESP"):
        assert atual[instituicao] == detalhado[instituicao]
    assert atual["FATEC"] == 10000
    assert detalhado["FATEC"] + 2080 == atual["FATEC"]


@pytest.mark.skipif(not EDITAL_PADRAO.exists(), reason="edital bruto não disponível")
def test_reextracao_confere_com_arquivo(vagas: pd.DataFrame) -> None:
    from provao.vagas import extrair_vagas

    novas = extrair_vagas()
    assert len(novas) == len(vagas)
    assert novas["vagas_total"].sum() == vagas["vagas_total"].sum()
