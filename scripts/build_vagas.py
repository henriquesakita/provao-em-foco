"""Gera o quadro de vagas 2027 a partir do edital de 2026."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from provao.vagas import carregar_vagas, extrair_vagas, salvar_vagas  # noqa: E402


def main() -> None:
    vagas = extrair_vagas()
    destino = salvar_vagas(vagas)
    print(f"Vagas: {len(vagas)} registros, {vagas['vagas_total'].sum()} vagas")
    print(
        vagas.groupby("instituicao")
        .agg(cursos=("curso", "size"), vagas=("vagas_total", "sum"))
        .to_string()
    )
    print()
    print(vagas.groupby("area_geral")["vagas_total"].sum().to_string())
    print(f"\nArquivo: {destino.name} ({destino.stat().st_size / 1024:.1f} KB)")
    conferencia = carregar_vagas()
    assert len(conferencia) == len(vagas)


if __name__ == "__main__":
    main()
