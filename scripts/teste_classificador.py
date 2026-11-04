import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from provao.taxonomia import classificar, normalizar, normalizar_padrao  # noqa: E402

casos = [
    ("Matemática", "Para quais valores de x e y vale que 18x · 24y = 610?"),
    ("Matemática", "Em qual dos intervalos a seguir é verdade que ?"),
    (
        "Matemática",
        "Uma escola pretende lançar uma edição comemorativa de seu brasão. A equipe reduziu suas possibilidades a 5 opções de cores, 3 tipos de filtros e 4 tamanhos. De quantas maneiras distintas o brasão pode ser produzido a partir dessas combinações?",
    ),
    ("Matemática", "Um time de vôlei amador conta com 10 jogadores. O time que inicia a partida é formado por 6 jogadores."),
    ("Matemática", "Ana recebeu uma carta e quer guardá-la em uma caixinha que tem 7 cm de largura, 7 cm de comprimento e 2 cm de altura."),
]

for disciplina, texto in casos:
    print(classificar(disciplina, texto), "|", normalizar(texto)[:80])

print(normalizar_padrao("combina[cç][aã]o"))
print(normalizar_padrao("valores de x|valor de x"))
