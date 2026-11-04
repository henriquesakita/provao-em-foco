import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from provao.extracao import extrair_tudo  # noqa: E402

alvos = {
    (2023, 1, 1, 36),
    (2024, 3, 1, 4),
    (2024, 1, 2, 13),
    (2024, 3, 2, 25),
    (2025, 2, 2, 26),
    (2024, 3, 1, 41),
    (2025, 3, 2, 33),
    (2024, 1, 2, 35),
    (2024, 1, 2, 40),
    (2024, 1, 2, 37),
    (2023, 3, 2, 17),
    (2025, 3, 2, 17),
    (2023, 2, 2, 4),
}

questoes = extrair_tudo(Path(__file__).resolve().parent.parent / "data" / "raw")
for q in questoes:
    chave = (q.ano, q.serie, q.dia, q.numero)
    if chave in alvos:
        print("=" * 70)
        print(chave, q.disciplina)
        print(q.enunciado[:900])
        for k, v in q.alternativas.items():
            print(f"  ({k}) {v[:160]}")
