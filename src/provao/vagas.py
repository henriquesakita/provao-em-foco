"""Leitura dos quadros de vagas do edital do Provão Paulista 2026.

O edital de 2026 (Anexos VIII a XII) publica as vagas para ingresso em 2027.
Os quadros são extraídos do texto do PDF, que dispõe cada célula em uma linha.
O parser reconstrói cada registro a partir do fim: os números fecham a linha
(total e cotas), o município pode ocupar mais de uma linha e o turno é o bloco
de linhas imediatamente anterior. Os totais por instituição são conferidos
contra o próprio edital.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
EDITAL_PADRAO = RAIZ / "data" / "raw" / "2026" / "edital.txt"
HISTORICO_PADRAO = RAIZ / "data" / "reference" / "vagas_historico.json"

AREAS = [
    "Ciências Humanas e Artes",
    "Ciências Biológicas e Saúde",
    "Ciências Exatas e Tecnológicas",
    "Ciências Agrárias",
    "Ciências Sociais Aplicadas",
    "Humanas/Exatas",
    "Humanas",
    "Exatas",
    "Biológicas",
]

TURNOS = [
    "Integral",
    "Noturno",
    "Matutino",
    "Vespertino",
    "Vespertino/Noturno",
    "Diurno",
    "Manhã",
    "Tarde",
    "Noite",
    "EaD",
    "Lic. Noturno",
]

# (rótulo do anexo, próximo anexo, quantos números fecham a linha, instituição,
#  semestre de ingresso, total publicado no edital)
ANEXOS = [
    ("ANEXO VIII", "ANEXO IX", 3, "USP", "1º semestre de 2027", 1500),
    ("ANEXO IX", "ANEXO X", 3, "UNESP", "1º semestre de 2027", 929),
    ("ANEXO X", "ANEXO XI", 3, "UNICAMP", "1º semestre de 2027", 326),
    ("ANEXO XI", "ANEXO XII", 2, "UNIVESP", "2º semestre de 2027", 3064),
    ("ANEXO XII", None, 2, "FATEC", "1º semestre de 2027", 7920),
]

AREAS_POR_TERMO = {
    "odontologia": "Ciências Biológicas e Saúde",
    "medicina": "Ciências Biológicas e Saúde",
    "enfermagem": "Ciências Biológicas e Saúde",
    "farmácia": "Ciências Biológicas e Saúde",
    "fisioterapia": "Ciências Biológicas e Saúde",
    "nutrição": "Ciências Biológicas e Saúde",
    "biomedicina": "Ciências Biológicas e Saúde",
}

CABECALHOS = {
    "Código",
    "Código do",
    "curso",
    "Nome do Curso",
    "Área",
    "Turno",
    "Município",
    "Total de",
    "Total de vagas",
    "vagas",
    "Provão",
    "Paulista",
    "2027-1",
    "2027-2",
    "EP",
    "PPI",
}

# Palavras que aparecem em turnos, inclusive nos casos em que o PDF quebra a
# frase em várias linhas (ex.: "Noite (Práticas laboratoriais a partir do 4º
# semestre diurno)").
_TOKENS_TURNO = re.compile(
    r"\b(?:integral|noturno|matutino|vespertino|diurno|manha|tarde|noite|ead|"
    r"ano|anos|semestre|semestral|praticas|laboratoriais|partir)\b"
)

COLUNAS = [
    "instituicao",
    "semestre",
    "codigo",
    "curso",
    "area",
    "area_geral",
    "campus",
    "turno",
    "turno_base",
    "municipio",
    "municipio_chave",
    "vagas_total",
    "vagas_ep",
    "vagas_ppi",
]


def _limpar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c)).strip().lower()


def _chave_area(texto: str) -> str:
    """Normaliza rótulos de área, inclusive os que o PDF quebrou com barra."""
    base = _limpar(texto).replace("/", " ")
    return re.sub(r"\s+", " ", base).strip()


AREAS_NORM = {_chave_area(a): a for a in AREAS}
TURNOS_NORM = {_limpar(t) for t in TURNOS}


def _prefixos_de_area() -> list[tuple[str, str]]:
    itens: set[str] = set()
    for area in AREAS:
        palavras = area.replace("/", " ").split()
        for n in range(1, len(palavras) + 1):
            itens.add(" ".join(palavras[:n]))
    return sorted(((_chave_area(p), p) for p in itens), key=lambda x: len(x[0]), reverse=True)


_PREFIXOS_AREA = _prefixos_de_area()


def _separar_area_colada(linha: str) -> list[str]:
    """Separa rótulos de área que o PDF grudou no nome ou no campus."""
    base = _limpar(linha)
    for chave, original in _PREFIXOS_AREA:
        if chave == base:
            return [linha]
        if base.endswith(" " + chave):
            corte = len(linha) - len(original)
            esquerda = linha[:corte].strip()
            if esquerda:
                return [esquerda, original]
        if base.startswith(chave + " "):
            resto = linha[len(original) :].strip()
            if resto and _limpar(resto).startswith(
                ("fatec", "faculdade", "instituto", "escola", "campus", "polo")
            ):
                return [original, resto]
    return [linha]


def _eh_turno(linha: str) -> bool:
    base = _limpar(linha)
    if not base:
        return False
    if base in TURNOS_NORM:
        return True
    # linhas curtas com vocabulário de turno, como "3º ano Noite"
    if len(base) <= 70 and _TOKENS_TURNO.search(base):
        # evita confundir nomes de campus/município com turno
        if base.startswith(("fatec", "faculdade", "instituto", "escola", "polo", "campus")):
            return False
        return True
    return False


def _area_do_prefixo(linhas: list[str]) -> tuple[int, int, str] | None:
    for inicio in range(len(linhas)):
        for fim in range(inicio + 1, len(linhas) + 1):
            chave = _chave_area(" ".join(linhas[inicio:fim]))
            if chave in AREAS_NORM:
                return inicio, fim, AREAS_NORM[chave]
    return None


def _inferir_area(nome: str) -> str:
    base = _limpar(nome)
    for termo, area in AREAS_POR_TERMO.items():
        if termo in base:
            return area
    return "Não informada"


def _area_geral(area: str) -> str:
    base = _chave_area(area)
    if base in {"humanas", "ciencias humanas e artes"}:
        return "Humanas"
    if base in {"exatas", "ciencias exatas e tecnologicas"}:
        return "Exatas"
    if base in {"biologicas", "ciencias biologicas e saude", "ciencias agrarias"}:
        return "Biológicas e Saúde"
    if base == "humanas exatas":
        return "Humanas e Exatas"
    return "Não informada"


def _turno_base(turno: str) -> str:
    base = _limpar(turno)
    if "ead" in base:
        return "EaD"
    achados = [
        nome
        for chave, nome in (
            ("integral", "Integral"),
            ("matutino", "Manhã"),
            ("manha", "Manhã"),
            ("vespertino", "Tarde"),
            ("tarde", "Tarde"),
            ("noturno", "Noite"),
            ("noite", "Noite"),
            ("diurno", "Diurno"),
        )
        if chave in base
    ]
    distintos = list(dict.fromkeys(achados))
    if len(distintos) == 1:
        return distintos[0]
    if len(distintos) > 1:
        return "Misto"
    return "Não informado"


def _linhas_do_anexo(texto: str, rotulo: str, proximo: str | None) -> list[str]:
    inicio = texto.index(rotulo)
    fim = texto.index(proximo, inicio) if proximo else len(texto)
    linhas = [linha.strip() for linha in texto[inicio:fim].splitlines() if linha.strip()]
    limpas = [
        linha
        for linha in linhas
        if not re.fullmatch(r"\d{1,3}/\d{1,3}", linha)
        and "Documento assinado" not in linha
        and "Este documento pode ser verificado" not in linha
        and "doe.sp.gov.br/autenticidade" not in linha
    ]
    resultado: list[str] = []
    for linha in limpas:
        resultado.extend(_separar_area_colada(linha))
    # Rótulos de área que o PDF quebrou como "Humanas/" + "Exatas".
    juntadas: list[str] = []
    for linha in resultado:
        if juntadas and juntadas[-1].endswith("/"):
            juntadas[-1] = juntadas[-1] + linha
        else:
            juntadas.append(linha)
    return juntadas


def _extrair_anexo(
    texto: str,
    rotulo: str,
    proximo: str | None,
    quantos_numeros: int,
    instituicao: str,
    semestre: str,
) -> tuple[list[dict], list[tuple[str, str]]]:
    linhas = _linhas_do_anexo(texto, rotulo, proximo)
    marcador = "EP PPI" if quantos_numeros == 3 else "EP"
    try:
        inicio = linhas.index(marcador) + 1
    except ValueError:
        inicio = 0

    registros: list[dict] = []
    problemas: list[tuple[str, str]] = []
    i = inicio
    while i < len(linhas):
        codigo = linhas[i]
        if re.fullmatch(r"\d{1,7}(?:/\d+)+|\d{1,7}", codigo):
            inicio_corpo = i + 1
        elif codigo in CABECALHOS:
            i += 1
            continue
        else:
            # Uma linha da FATEC ficou sem código no PDF.
            codigo = ""
            inicio_corpo = i

        j = inicio_corpo
        while j + quantos_numeros <= len(linhas):
            cauda = linhas[j : j + quantos_numeros]
            if all(re.fullmatch(r"\d+", n) for n in cauda) and not re.fullmatch(
                r"\d+", linhas[j - 1]
            ):
                break
            j += 1
        else:
            problemas.append((codigo, "sem cauda numérica"))
            break

        cauda = linhas[j : j + quantos_numeros]
        corpo = linhas[inicio_corpo:j]
        i = j + quantos_numeros

        if len(corpo) < 4:
            problemas.append((codigo, "corpo curto"))
            continue

        # O município pode ocupar várias linhas; o turno é o bloco anterior.
        fim_municipio = len(corpo)
        fim_turno = fim_municipio - 1
        while fim_turno > 0 and not _eh_turno(corpo[fim_turno]):
            fim_turno -= 1
        if not _eh_turno(corpo[fim_turno]):
            problemas.append((codigo, "sem turno"))
            continue
        municipio = " ".join(corpo[fim_turno + 1 : fim_municipio]).strip()
        if not municipio:
            problemas.append((codigo, "sem município"))
            continue

        # O turno também pode ocupar várias linhas.
        inicio_turno = fim_turno
        while inicio_turno > 0 and _eh_turno(corpo[inicio_turno - 1]):
            inicio_turno -= 1
        turno = " ".join(corpo[inicio_turno : fim_turno + 1]).strip()
        prefixo = corpo[:inicio_turno]

        area = _area_do_prefixo(prefixo)
        if not area:
            nome = prefixo[0]
            nome_area = _inferir_area(nome)
            if nome_area == "Não informada":
                problemas.append((codigo, "sem área"))
                continue
            campus = " ".join(prefixo[1:]).strip()
        else:
            pos_area, fim_area, nome_area = area
            nome = " ".join(prefixo[:pos_area])
            campus = " ".join(prefixo[fim_area:]).strip()

        campus = re.sub(
            r"\s*" + re.escape(nome_area) + r"\s*$", "", campus, flags=re.I
        ).strip()
        # Corrige campus duplicado pela extração de uma linha da UNESP.
        if re.fullmatch(r"(.+?)\s+\1", campus):
            campus = campus[: len(campus) // 2].strip()

        registros.append(
            {
                "instituicao": instituicao,
                "semestre": semestre,
                "codigo": codigo,
                "curso": nome,
                "area": nome_area,
                "area_geral": _area_geral(nome_area),
                "campus": campus,
                "turno": turno,
                "turno_base": _turno_base(turno),
                "municipio": municipio,
                "municipio_chave": _limpar(municipio),
                "vagas_total": int(cauda[0]),
                "vagas_ep": int(cauda[1]) if len(cauda) > 1 else None,
                "vagas_ppi": int(cauda[2]) if len(cauda) > 2 else None,
            }
        )
    return registros, problemas


def _canonicalizar_municipios(df: pd.DataFrame) -> pd.DataFrame:
    """Unifica grafias com e sem acento do mesmo município.

    O texto do edital mistura, por exemplo, "São Paulo" e "Sao Paulo". Para
    contar vagas por município escolhemos a grafia mais acentuada de cada
    chave, que costuma ser a forma oficial. Também agrupamos as localidades
    da capital (Butantã, Ipiranga, Itaquera etc.) no município de São Paulo.
    """

    def acentos(texto: str) -> int:
        return sum(1 for c in texto if ord(c) > 127)

    escolhas: dict[str, str] = {}
    for chave, grupo in df.groupby("municipio_chave", dropna=False):
        candidatos = grupo["municipio"].dropna().unique()
        if len(candidatos) == 1:
            escolhas[str(chave)] = candidatos[0]
            continue
        escolhas[str(chave)] = max(candidatos, key=lambda m: (acentos(m), len(m)))

    def oficial(chave: str) -> str:
        # Localidades da capital aparecem como "São Paulo/Butantã",
        # "São Paulo - Itaquera", "São Paulo/Leste" etc.
        if chave == "sao paulo" or re.match(
            r"^sao paulo(?:/| - | -$)", chave
        ):
            return "São Paulo"
        return escolhas.get(chave, chave)

    df = df.copy()
    df["municipio"] = df["municipio_chave"].map(oficial)
    df["municipio_chave"] = df["municipio"].map(_limpar)
    return df


def extrair_vagas(edital: Path | None = None) -> pd.DataFrame:
    """Devolve o quadro de vagas publicado no edital, com validação de totais."""
    edital = edital or EDITAL_PADRAO
    texto = edital.read_text(encoding="utf-8")
    registros: list[dict] = []
    for rotulo, proximo, numeros, instituicao, semestre, esperado in ANEXOS:
        linhas, problemas = _extrair_anexo(
            texto, rotulo, proximo, numeros, instituicao, semestre
        )
        soma = sum(r["vagas_total"] for r in linhas)
        if soma != esperado:
            raise ValueError(
                f"{instituicao}: {soma} vagas encontradas, esperado {esperado}"
            )
        if problemas:
            raise ValueError(f"{instituicao}: registros não interpretados: {problemas}")
        registros.extend(linhas)
    df = pd.DataFrame(registros, columns=COLUNAS)
    df = _canonicalizar_municipios(df)
    return df.sort_values(
        ["instituicao", "curso", "municipio", "turno"]
    ).reset_index(drop=True)


def salvar_vagas(df: pd.DataFrame, destino: Path | None = None) -> Path:
    destino = destino or RAIZ / "data" / "processed" / "vagas_2027.csv.gz"
    destino.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(destino, index=False, compression="gzip")
    return destino


def carregar_vagas(caminho: Path | None = None) -> pd.DataFrame:
    caminho = caminho or RAIZ / "data" / "processed" / "vagas_2027.csv.gz"
    return pd.read_csv(caminho)


def carregar_historico_vagas(caminho: Path | None = None) -> pd.DataFrame:
    """Devolve o total divulgado por instituição em cada edição.

    Os números seguem o dispositivo que abre a seção de vagas de cada edital,
    e não a soma dos quadros por curso: parte das vagas da FATEC é divulgada
    apenas como total semestral.
    """
    caminho = caminho or HISTORICO_PADRAO
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    registros = [
        {
            "edicao": edicao["edicao"],
            "ingresso": edicao["ingresso"],
            "instituicao": instituicao,
            "vagas": vagas,
        }
        for edicao in dados["edicoes"]
        for instituicao, vagas in edicao["instituicoes"].items()
    ]
    return pd.DataFrame(registros, columns=["edicao", "ingresso", "instituicao", "vagas"])
