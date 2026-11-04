import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from provao.extracao import extrair_tudo  # noqa: E402
from provao.taxonomia import classificar  # noqa: E402

questoes = extrair_tudo(Path(__file__).resolve().parent.parent / "data" / "raw")

resultado = {}
for q in questoes:
    chave = f"{q.ano}-{q.serie}-{q.dia}-{q.numero}"
    tema, pontos = classificar(
        q.disciplina, q.enunciado, " ".join(q.alternativas.values()), chave=chave
    )
    resultado[(q.ano, q.serie, q.dia, q.numero)] = (tema, pontos)

contagem = Counter((q.disciplina, resultado[(q.ano, q.serie, q.dia, q.numero)][0]) for q in questoes)
for chave in sorted(contagem):
    print(f"{chave[0]:18} {chave[1] or '(nao classificado)':40} {contagem[chave]}")

print("\n=== nao classificados ===")
nao = [q for q in questoes if resultado[(q.ano, q.serie, q.dia, q.numero)][0] == ""]
print("total", len(nao))
for q in nao:
    print(f"{q.ano} {q.serie}a d{q.dia} q{q.numero:02d} {q.disciplina}: {q.enunciado[:120]}")

print("\n=== pontuacao baixa (1-2) ===")
baixa = [q for q in questoes if 0 < resultado[(q.ano, q.serie, q.dia, q.numero)][1] <= 2]
print("total", len(baixa))
for q in baixa[:80]:
    tema, pontos = resultado[(q.ano, q.serie, q.dia, q.numero)]
    print(f"{q.ano} {q.serie}a d{q.dia} q{q.numero:02d} {q.disciplina} -> {tema} ({pontos}): {q.enunciado[:100]}")
