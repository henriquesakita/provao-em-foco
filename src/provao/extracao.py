"""Extração de questões e gabaritos dos cadernos do Provão Paulista / Saresp."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf

# ---------------------------------------------------------------------------
# Estrutura oficial observada nos cadernos
# ---------------------------------------------------------------------------
# Ano -> série -> dia -> lista de (disciplina, primeiro item, último item)
# A ordem dos itens foi conferida item a item no texto dos cadernos.
BLOCOS: dict[int, dict[int, dict[int, list[tuple[str, int, int]]]]] = {
    2023: {
        1: {
            1: [
                ("Língua Portuguesa", 1, 20),
                ("Língua Inglesa", 21, 24),
                ("Biologia", 25, 32),
                ("Física", 33, 40),
                ("Química", 41, 48),
            ],
            2: [
                ("Matemática", 1, 20),
                ("Geografia", 21, 27),
                ("História", 28, 34),
                ("Filosofia", 35, 38),
                ("Sociologia", 39, 42),
            ],
        },
        2: {
            1: [
                ("Língua Portuguesa", 1, 20),
                ("Língua Inglesa", 21, 24),
                ("Biologia", 25, 32),
                ("Física", 33, 40),
                ("Química", 41, 48),
            ],
            2: [
                ("Matemática", 1, 20),
                ("Geografia", 21, 27),
                ("História", 28, 34),
                ("Filosofia", 35, 38),
                ("Sociologia", 39, 42),
            ],
        },
        3: {
            1: [
                ("Língua Portuguesa", 1, 20),
                ("Língua Inglesa", 21, 24),
                ("Biologia", 25, 32),
                ("Física", 33, 40),
                ("Química", 41, 48),
            ],
            2: [
                ("Matemática", 1, 20),
                ("Geografia", 21, 27),
                ("História", 28, 34),
                ("Filosofia", 35, 38),
                ("Sociologia", 39, 42),
            ],
        },
    },
    2024: {
        1: {
            1: [
                ("Língua Portuguesa", 1, 18),
                ("Língua Inglesa", 19, 24),
                ("Física", 25, 32),
                ("Química", 33, 40),
                ("Biologia", 41, 48),
            ],
            2: [
                ("Matemática", 1, 18),
                ("História", 19, 26),
                ("Geografia", 27, 34),
                ("Filosofia", 35, 42),
            ],
        },
        2: {
            1: [
                ("Língua Portuguesa", 1, 18),
                ("Língua Inglesa", 19, 24),
                ("Física", 25, 32),
                ("Química", 33, 40),
                ("Biologia", 41, 48),
            ],
            2: [
                ("Matemática", 1, 18),
                ("História", 19, 26),
                ("Geografia", 27, 34),
                ("Sociologia", 35, 42),
            ],
        },
        3: {
            1: [
                ("Língua Portuguesa", 1, 18),
                ("Língua Inglesa", 19, 24),
                ("Física", 25, 32),
                ("Química", 33, 40),
                ("Biologia", 41, 48),
            ],
            2: [
                ("Matemática", 1, 18),
                ("História", 19, 26),
                ("Geografia", 27, 32),
                ("Sociologia", 33, 37),
                ("Filosofia", 38, 41),
                ("Sociologia", 42, 42),
            ],
        },
    },
    2025: {
        1: {
            1: [
                ("Língua Portuguesa", 1, 18),
                ("Língua Inglesa", 19, 24),
                ("Física", 25, 32),
                ("Química", 33, 40),
                ("Biologia", 41, 48),
            ],
            2: [
                ("Matemática", 1, 18),
                ("História", 19, 26),
                ("Geografia", 27, 34),
                ("Filosofia", 35, 42),
            ],
        },
        2: {
            1: [
                ("Língua Portuguesa", 1, 18),
                ("Língua Inglesa", 19, 24),
                ("Física", 25, 32),
                ("Química", 33, 40),
                ("Biologia", 41, 48),
            ],
            2: [
                ("Matemática", 1, 18),
                ("História", 19, 26),
                ("Geografia", 27, 34),
                ("Sociologia", 35, 42),
            ],
        },
        3: {
            1: [
                ("Língua Portuguesa", 1, 18),
                ("Língua Inglesa", 19, 24),
                ("Física", 25, 32),
                ("Química", 33, 40),
                ("Biologia", 41, 48),
            ],
            2: [
                ("Matemática", 1, 18),
                ("História", 19, 26),
                ("Geografia", 27, 34),
                ("Sociologia", 35, 37),
                ("Filosofia", 38, 42),
            ],
        },
    },
}

DISCIPLINAS = [
    "Língua Portuguesa",
    "Língua Inglesa",
    "Matemática",
    "Física",
    "Química",
    "Biologia",
    "História",
    "Geografia",
    "Filosofia",
    "Sociologia",
]

RUIDOS = [
    re.compile(r"^Confidencial até o momento da aplicação\.?$", re.I),
    re.compile(r"^Saresp\s*\d{4}\s*\|.*$", re.I),
    re.compile(r"^\d{1,3}$"),
    re.compile(r"^ASSINATURA DO ALUNO$", re.I),
    re.compile(r"^NOME DO ALUNO$", re.I),
    re.compile(r"^CÓDIGO\s*/\s*NOME DA D\.E\.$", re.I),
    re.compile(r"^CÓDIGO\s*/\s*MUNICÍPIO$", re.I),
    re.compile(r"^CÓDIGO\s*/\s*NOME DA ESCOLA$", re.I),
    re.compile(r"^ANO\s+PROVA\s+R\.A\.\s+TURMA\s+TURNO\s+SALA\s+VUNESP.*$", re.I),
    re.compile(r"^QUESTÃO\s+RESPOSTAS.*$", re.I),
    re.compile(r"^RESPOSTAS$", re.I),
]

CORTES = ("ASSINATURA DO ALUNO", "NOME DO ALUNO", "CÓDIGO / NOME DA ESCOLA")


@dataclass
class Questao:
    ano: int
    serie: int
    dia: int
    numero: int
    disciplina: str
    enunciado: str
    alternativas: dict[str, str] = field(default_factory=dict)
    gabarito: str = ""
    pagina: int = 0
    contexto_pagina: str = ""
    caderno: str = ""


def _limpar_linhas(texto: str) -> str:
    linhas = []
    for linha in texto.splitlines():
        limpa = linha.strip()
        if not limpa:
            continue
        if any(padrao.match(limpa) for padrao in RUIDOS):
            continue
        linhas.append(limpa)
    return "\n".join(linhas)


def _cortar_rodape(texto: str) -> str:
    posicoes = [texto.find(marca) for marca in CORTES if marca in texto]
    if posicoes:
        texto = texto[: min(posicoes)]
    return texto


def _juntar_hifenizacao(texto: str) -> str:
    """Recompõe palavras quebradas no fim da linha (ex.: 'lingua-\ngem')."""
    texto = re.sub(r"(?<=\w)-\n(?=[a-záéíóúâêôãõç])", "", texto)
    return texto


def _normalizar(texto: str) -> str:
    texto = _juntar_hifenizacao(_limpar_linhas(texto))
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{2,}", "\n", texto)
    return texto.strip()


def _texto_pagina(pagina: pymupdf.Page) -> str:
    """Reconstrói a leitura de páginas em duas colunas.

    Os cadernos usam duas colunas: o enunciado e o texto de apoio ficam à
    esquerda, e as alternativas podem ficar à direita. A extração linear do
    PDF embaralha essa ordem e fazia alternativas caírem no bloco da questão
    anterior. Ordenamos os blocos por coluna e depois por altura.
    """
    largura = pagina.rect.width
    altura = pagina.rect.height
    meio = largura * 0.48
    blocos: list[tuple[int, float, float, str]] = []
    for bloco in pagina.get_text("blocks"):
        x0, y0, x1, _y1, texto, *_ = bloco
        texto = texto.strip()
        if not texto or y0 > altura - 40:
            continue
        if any(padrao.match(texto) for padrao in RUIDOS):
            continue
        if x0 >= meio:
            coluna = 1
        else:
            coluna = 0
        blocos.append((coluna, y0, x0, texto))
    blocos.sort(key=lambda item: (item[0], item[1], item[2]))
    return "\n".join(item[3] for item in blocos)


# Início de um novo material de leitura que costuma aparecer depois das
# alternativas no mesmo bloco de texto extraído do PDF.
_NOVO_MATERIAL = re.compile(
    r"\n(?=(?:Para responder|Leia\b|Considere (?:o texto|a leitura|a figura|os textos|as informações)"
    r"|Examine\b|Observe\b|Analise\b|TEXTO\s+(?:I|II|III|1|2|3)\b|Texto\s+(?:I|II|III|1|2|3)\b"
    r"|O texto a seguir|A seguir,|CADERNO\b|REDAÇÃO\b|RASCUNHO\b|Classificação periódica\b"
    r"|A figura (?:a seguir|ilustra|mostra|representa)|O gráfico (?:a seguir|representa|mostra)"
    r"|A tabela (?:a seguir|indica|mostra|representa)|A imagem (?:a seguir|mostra|ilustra|representa)"
    r"|Disponível em\b))"
)

_MARCA_OPCAO = re.compile(r"(?m)^\s*\(?\s*([A-E])\s*\)\s*$")


def _limpar_alternativa(texto: str) -> str:
    texto = texto.strip()
    corte = _NOVO_MATERIAL.search(texto)
    if corte and corte.start() > 15:
        texto = texto[: corte.start()].strip()
    # alternativas cujas imagens foram separadas por quebra de página
    corte = _MARCA_OPCAO.search(texto)
    if corte and corte.start() > 20:
        texto = texto[: corte.start()].strip()
    return texto


def _separar_alternativas(bloco: str) -> tuple[str, dict[str, str]]:
    marcas = {}
    for letra in "ABCDE":
        m = re.search(rf"\(\s*{letra}\s*\)", bloco)
        if not m:
            m = re.search(rf"(?m)^\s*{letra}\s*\)", bloco)
        if m:
            marcas[letra] = m
    letras = [letra for letra in "ABCDE" if letra in marcas]
    if len(letras) < 4:
        return bloco.strip(), {}
    # só aceita se as letras estiverem em ordem crescente
    posicoes = [marcas[letra].start() for letra in letras]
    if posicoes != sorted(posicoes):
        return bloco.strip(), {}
    inicio = marcas[letras[0]].start()
    enunciado = bloco[:inicio].strip()
    alternativas: dict[str, str] = {}
    for i, letra in enumerate(letras):
        ini = marcas[letra].end()
        fim = marcas[letras[i + 1]].start() if i + 1 < len(letras) else len(bloco)
        alternativas[letra] = _limpar_alternativa(bloco[ini:fim])
    return enunciado, alternativas


def ler_gabarito(caminho: Path) -> dict[int, str]:
    doc = pymupdf.open(caminho)
    texto = "\n".join(p.get_text() for p in doc)
    doc.close()
    gabaritos: dict[int, str] = {}
    for m in re.finditer(r"(\d{1,3})\s*[-–:]\s*([A-E])\b", texto):
        gabaritos[int(m.group(1))] = m.group(2)
    for m in re.finditer(r"(?m)^\s*(\d{1,3})\s+([A-E])\s*$", texto):
        gabaritos.setdefault(int(m.group(1)), m.group(2))
    return dict(sorted(gabaritos.items()))


def _nome_caderno(ano: int, serie: int, dia: int) -> str:
    sufixo = "lc-cn" if dia == 1 else "mt-ch"
    return f"{ano}-{serie}a-{sufixo}.pdf"


def _nome_gabarito(ano: int, serie: int, dia: int) -> str:
    return f"{ano}-{serie}a-gab-d{dia}.pdf"


def _disciplina_do_item(ano: int, serie: int, dia: int, numero: int) -> str | None:
    for disciplina, primeiro, ultimo in BLOCOS[ano][serie][dia]:
        if primeiro <= numero <= ultimo:
            return disciplina
    return None


def extrair_caderno(ano: int, serie: int, dia: int, pasta: Path) -> list[Questao]:
    caderno = pasta / _nome_caderno(ano, serie, dia)
    gabarito = pasta / _nome_gabarito(ano, serie, dia)
    if not caderno.exists() or not gabarito.exists():
        raise FileNotFoundError(f"Arquivos ausentes para {ano} {serie}ª série dia {dia}")

    respostas = ler_gabarito(gabarito)
    doc = pymupdf.open(caderno)
    paginas = [_texto_pagina(pagina) for pagina in doc]
    doc.close()

    texto = ""
    marcas_pagina: list[tuple[int, int]] = []  # (posição no texto, página 1-based)
    for indice, conteudo in enumerate(paginas, start=1):
        marcas_pagina.append((len(texto), indice))
        texto += conteudo + "\n\f\n"

    partes = list(re.finditer(r"QUEST[ÃA]O\s+(\d+)", texto))
    questoes: list[Questao] = []
    for i, parte in enumerate(partes):
        numero = int(parte.group(1))
        disciplina = _disciplina_do_item(ano, serie, dia, numero)
        if disciplina is None:
            continue
        inicio = parte.end()
        fim = partes[i + 1].start() if i + 1 < len(partes) else len(texto)
        bloco = texto[inicio:fim]
        bloco = _cortar_rodape(bloco)
        bloco = _normalizar(bloco)
        if not bloco:
            continue
        # página onde o enunciado começa
        pagina = 1
        for posicao, indice in marcas_pagina:
            if posicao <= parte.start():
                pagina = indice
            else:
                break
        pagina_texto = _normalizar(paginas[pagina - 1]) if pagina <= len(paginas) else ""
        enunciado, alternativas = _separar_alternativas(bloco)
        questoes.append(
            Questao(
                ano=ano,
                serie=serie,
                dia=dia,
                numero=numero,
                disciplina=disciplina,
                enunciado=enunciado,
                alternativas=alternativas,
                gabarito=respostas.get(numero, ""),
                pagina=pagina,
                contexto_pagina=pagina_texto[:2500],
                caderno=caderno.name,
            )
        )
    return questoes


def extrair_tudo(raiz: Path) -> list[Questao]:
    questoes: list[Questao] = []
    for ano in sorted(BLOCOS):
        for serie in sorted(BLOCOS[ano]):
            for dia in sorted(BLOCOS[ano][serie]):
                questoes.extend(extrair_caderno(ano, serie, dia, raiz / str(ano)))
    return questoes
