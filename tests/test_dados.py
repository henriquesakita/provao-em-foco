"""Testes dos dados processados do Provão Paulista."""

from __future__ import annotations

import pandas as pd
import pytest

from provao.dados import (
    _tem_apoio_visual,
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
    assert int(questoes["apoio_visual"].sum()) == 296
    assert questoes.loc[questoes["alternativas_texto"].isna(), "apoio_visual"].all()

    disponiveis = questoes[~questoes["apoio_visual"]]
    assert len(disponiveis) == 514
    assert disponiveis["alternativas_texto"].notna().all()
    assert (disponiveis["alternativas_texto"].str.len() > 0).all()


def test_simulado_sem_apoio_visual_explicito(questoes: pd.DataFrame) -> None:
    texto = questoes.loc[~questoes["apoio_visual"], "enunciado"].astype(str)
    proibidos = (
        r"\b(?:tiras?|tirinhas?|quadrinhos?|pictogramas?|cartazes?"
        r"|charges?|cartu[mn]s?)\b"
        r"|representa[cç][aã]o a seguir|circuito a seguir"
        r"|árvores? (?:filogen[ée]ticas?|evolutivas?)"
    )
    assert not texto.str.contains(proibidos, case=False, regex=True).any()


@pytest.mark.parametrize(
    "enunciado",
    [
        "Leia a tira e responda à questão.",
        "No terceiro quadrinho da tira, está indicada a sequência.",
        "Observe a figura do cogumelo comestível.",
        "A imagem mostra as aves conhecidas como tentilhões.",
        "Considere a tabela a seguir com os dados do experimento.",
        "Analise o heredograma a seguir.",
        "Observe a pintura de 1555.",
        "Examine o meme.",
        "Analise a teia alimentar.",
        "A estrutura está representada na f\u00adigura a seguir.",
        "A roleta posicionada como na imagem anterior.",
        "A representação a seguir é da reta dos números reais.",
        "Na embalagem, há o pictograma de segurança a seguir.",
        "Quatro lâmpadas foram usadas para construir o circuito a seguir.",
        "Leia as postagens a seguir.",
        "As conversões dependem do processo representado a seguir.",
        "De acordo com a representação, as lentes escurecem.",
        "O radioisótopo pode ser produzido conforme as equações a seguir.",
        "Observe a árvore filogenética dos vertebrados.",
    ],
)
def test_apoio_visual_detectado(enunciado: str) -> None:
    assert _tem_apoio_visual(enunciado, "alternativa") is True


@pytest.mark.parametrize(
    "enunciado",
    [
        "A figura de linguagem presente no verso é",
        "A figura do Estado garante a paz.",
        "No quadro urbano, o relógio mecânico marcava as horas.",
        "A Convenção-Quadro das Nações Unidas definiu regras.",
        "O quadro de medalhas das olimpíadas é ordenado pelo ouro.",
        "O elemento químico pertence à tabela periódica.",
        "A empresa produz 9 memes em 6 dias.",
        "Caramelo é o desenho mais vivo da esperança.",
        "O espelho côncavo conjuga uma imagem.",
        "A sua imagem no telhado capturou uma correnteza.",
        "O gerador está conectado a um circuito externo de 5,5 Ω.",
        "A representação do número em notação científica é",
        "A equação de reação é apresentada a seguir: TeCl4 + xNH4Cl.",
    ],
)
def test_apoio_visual_ignora_expressoes_figurativas(enunciado: str) -> None:
    assert _tem_apoio_visual(enunciado, "alternativa") is False


def test_apoio_visual_nas_alternativas() -> None:
    assert _tem_apoio_visual(
        "Texto sem referência visual.",
        "As amostras foram fervidas e a foto a seguir foi registrada.",
    )
    # Alternativas apenas com imagem continuam exigindo o caderno.
    assert _tem_apoio_visual("Texto sem referência visual.", None)


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
