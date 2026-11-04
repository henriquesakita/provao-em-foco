"""Carga das questões inéditas escritas para o painel."""

from __future__ import annotations

import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ARQUIVO_PADRAO = RAIZ / "data" / "reference" / "questoes_ineditas.json"

CAMPOS = {
    "id",
    "disciplina",
    "tema",
    "dificuldade",
    "enunciado",
    "alternativas",
    "gabarito",
    "comentario",
}


def carregar_ineditas(caminho: Path | None = None) -> list[dict]:
    caminho = caminho or ARQUIVO_PADRAO
    return json.loads(caminho.read_text(encoding="utf-8"))
