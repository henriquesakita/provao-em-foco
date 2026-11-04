"""Gera os arquivos processados usados pelo aplicativo e pelos testes."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from provao.dados import (  # noqa: E402
    construir_contextos,
    construir_questoes,
    salvar_processados,
)


def main() -> None:
    questoes = construir_questoes()
    contextos = construir_contextos()
    destinos = salvar_processados(questoes, contextos)

    print(f"Questões: {len(questoes)}")
    print(questoes.groupby(["ano", "serie"]).size().to_string())
    print("\nSem tema:", int((questoes["tema"] == "").sum()))
    print("Sem gabarito:", int((questoes["gabarito"] == "").sum()))
    print("Sem alternativas em texto:", int((questoes["alternativas_texto"] == "").sum()))
    print("\nArquivos gerados:")
    for nome, caminho in destinos.items():
        tamanho = caminho.stat().st_size / 1024
        print(f"  {nome:12s} {caminho.name:24s} {tamanho:8.1f} KB")


if __name__ == "__main__":
    main()
