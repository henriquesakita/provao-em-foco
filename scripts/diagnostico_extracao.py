import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from provao.extracao import extrair_tudo  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent / "data" / "raw"
questoes = extrair_tudo(RAIZ)

print("total", len(questoes))
print("por ano", Counter(q.ano for q in questoes))
print("sem gabarito", sum(1 for q in questoes if not q.gabarito))
print("menos de 5 alternativas", sum(1 for q in questoes if len(q.alternativas) < 5))
print("sem alternativas", sum(1 for q in questoes if not q.alternativas))

por = Counter((q.ano, q.serie, q.disciplina) for q in questoes)
for chave in sorted(por):
    print(chave, por[chave])

print("\n--- exemplos sem 5 alternativas ---")
for q in questoes:
    if len(q.alternativas) < 5:
        print(q.ano, q.serie, q.dia, q.numero, q.disciplina, repr(q.enunciado[:90]), list(q.alternativas))

print("\n--- exemplo completo ---")
q = next(q for q in questoes if q.ano == 2024 and q.serie == 1 and q.numero == 1)
print(q.disciplina, q.gabarito, q.pagina)
print(q.enunciado)
for k, v in q.alternativas.items():
    print(k, v)
