import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from provao.extracao import extrair_tudo  # noqa: E402

alvos = {
    (2023, 3, 2, 1),
    (2023, 3, 2, 3),
    (2023, 3, 2, 8),
    (2024, 1, 2, 2),
    (2024, 1, 2, 8),
    (2024, 1, 2, 14),
    (2024, 1, 2, 15),
    (2024, 1, 2, 18),
    (2023, 1, 1, 25),
    (2023, 2, 1, 25),
    (2024, 1, 1, 41),
    (2024, 3, 1, 41),
    (2024, 2, 2, 26),
    (2025, 3, 2, 14),
    (2024, 3, 2, 7),
}

questoes = extrair_tudo(Path(__file__).resolve().parent.parent / "data" / "raw")
for q in questoes:
    chave = (q.ano, q.serie, q.dia, q.numero)
    if chave in alvos:
        print("=" * 70)
        print(chave, q.disciplina)
        print(q.enunciado[:700])
        for k, v in q.alternativas.items():
            print(f"  ({k}) {v[:120]}")
