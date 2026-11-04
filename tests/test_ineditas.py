"""Testes das questões inéditas."""

from __future__ import annotations

from collections import Counter

from provao.ineditas import CAMPOS, carregar_ineditas


def test_quantidade_e_campos() -> None:
    questoes = carregar_ineditas()
    assert len(questoes) >= 20
    for questao in questoes:
        assert set(questao) == CAMPOS
        assert all(str(questao[campo]).strip() for campo in CAMPOS)


def test_ids_unicos() -> None:
    ids = [q["id"] for q in carregar_ineditas()]
    assert len(ids) == len(set(ids))


def test_cinco_alternativas_e_gabarito_valido() -> None:
    for questao in carregar_ineditas():
        assert set(questao["alternativas"]) == {"A", "B", "C", "D", "E"}
        assert questao["gabarito"] in questao["alternativas"]


def test_cobertura_de_disciplinas() -> None:
    disciplinas = Counter(q["disciplina"] for q in carregar_ineditas())
    assert len(disciplinas) == 10
    assert min(disciplinas.values()) >= 2
