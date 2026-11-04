import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from provao.extracao import extrair_tudo  # noqa: E402

questoes = extrair_tudo(Path(__file__).resolve().parent.parent / "data" / "raw")
for ano in (2023, 2024, 2025):
    for serie in (1, 2, 3):
        print("=" * 80)
        print(f"{ano} {serie}a dia 2")
        for q in questoes:
            if (q.ano, q.serie, q.dia) == (ano, serie, 2) and q.numero >= 33:
                print(f"{q.numero:02d} [{q.disciplina}] {q.enunciado[:150].replace(chr(10), ' ')}")
