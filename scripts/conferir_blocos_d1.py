import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from provao.extracao import extrair_tudo  # noqa: E402

questoes = extrair_tudo(Path(__file__).resolve().parent.parent / "data" / "raw")
for ano in (2024, 2025):
    for serie in (1, 2, 3):
        print("=" * 80)
        print(f"{ano} {serie}a dia 1 (25-48)")
        for q in questoes:
            if (q.ano, q.serie, q.dia) == (ano, serie, 1) and 25 <= q.numero <= 48:
                print(f"{q.numero:02d} [{q.disciplina}] {q.enunciado[:120].replace(chr(10), ' ')}")
