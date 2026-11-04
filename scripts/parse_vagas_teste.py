import re
import unicodedata
from pathlib import Path

TEXTO = Path("data/raw/2026/edital.txt")
AREAS = [
    "Ciências Humanas e Artes",
    "Ciências Biológicas e Saúde",
    "Ciências Exatas e Tecnológicas",
    "Ciências Agrárias",
    "Ciências Sociais Aplicadas",
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
]


def limpar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c)).strip().lower()


AREAS_NORM = {limpar(a): a for a in AREAS}
TURNOS_NORM = {limpar(t) for t in TURNOS}


def prefixos_de_area() -> list[tuple[str, str]]:
    """Prefixos que podem aparecer colados ao nome do curso no texto do PDF."""
    itens: set[str] = set()
    for area in AREAS:
        palavras = area.split()
        for n in range(1, len(palavras) + 1):
            itens.add(" ".join(palavras[:n]))
    return sorted(((limpar(p), p) for p in itens), key=lambda x: len(x[0]), reverse=True)


PREFIXOS_AREA = prefixos_de_area()


def separar_area_colada(linha: str) -> list[str]:
    base = limpar(linha)
    for chave, original in PREFIXOS_AREA:
        if chave == base:
            return [linha]
        if base.endswith(" " + chave):
            corte = len(linha) - len(original)
            esquerda = linha[:corte].strip()
            if esquerda:
                return [esquerda, original]
        if base.startswith(chave + " "):
            resto = linha[len(original) :].strip()
            if resto and limpar(resto).startswith(
                ("fatec", "faculdade", "instituto", "escola", "campus", "polo")
            ):
                return [original, resto]
    return [linha]


def eh_turno(linha: str) -> bool:
    base = limpar(linha)
    if base in TURNOS_NORM:
        return True
    return "semestre" in base and ("manha" in base or "tarde" in base or "noite" in base)


def area_do_prefixo(linhas: list[str]) -> tuple[int, int, str] | None:
    for inicio in range(len(linhas)):
        for fim in range(inicio + 1, len(linhas) + 1):
            combinado = " ".join(linhas[inicio:fim]).strip()
            chave = limpar(combinado)
            if chave in AREAS_NORM:
                return inicio, fim, AREAS_NORM[chave]
    return None


AREAS_POR_TERMO = {
    "odontologia": "Ciências Biológicas e Saúde",
    "medicina": "Ciências Biológicas e Saúde",
    "enfermagem": "Ciências Biológicas e Saúde",
    "farmácia": "Ciências Biológicas e Saúde",
    "fisioterapia": "Ciências Biológicas e Saúde",
    "nutrição": "Ciências Biológicas e Saúde",
    "biomedicina": "Ciências Biológicas e Saúde",
}


def inferir_area(nome: str) -> str:
    base = limpar(nome)
    for termo, area in AREAS_POR_TERMO.items():
        if termo in base:
            return area
    return "Não informada"


def repeticao_exata(texto: str) -> bool:
    return bool(re.fullmatch(r"(.+?)\s+\1", texto))


def linhas_do_anexo(rotulo: str, proximo: str | None) -> list[str]:
    texto = TEXTO.read_text(encoding="utf-8")
    inicio = texto.index(rotulo)
    fim = texto.index(proximo, inicio) if proximo else len(texto)
    secao = texto[inicio:fim]
    linhas = [linha.strip() for linha in secao.splitlines() if linha.strip()]
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
        resultado.extend(separar_area_colada(linha))
    return resultado


def extrair_anexo(rotulo: str, proximo: str | None, quantos_numeros: int):
    linhas = linhas_do_anexo(rotulo, proximo)
    marcador = "EP PPI" if quantos_numeros == 3 else "EP"
    try:
        inicio = linhas.index(marcador) + 1
    except ValueError:
        inicio = 0
    registros = []
    problemas = []
    i = inicio
    while i < len(linhas):
        codigo = linhas[i]
        if re.fullmatch(r"\d{1,7}(?:/\d+)+|\d{1,7}", codigo):
            inicio_corpo = i + 1
        elif codigo in {
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
        }:
            i += 1
            continue
        else:
            # uma linha de curso sem código (falha de extração do edital)
            codigo = ""
            inicio_corpo = i
        # encontra a cauda numérica
        j = inicio_corpo
        while j + quantos_numeros <= len(linhas):
            cauda = linhas[j : j + quantos_numeros]
            if all(re.fullmatch(r"\d+", n) for n in cauda) and not re.fullmatch(
                r"\d+", linhas[j - 1]
            ):
                break
            j += 1
        else:
            problemas.append((codigo, "sem cauda", linhas[i : i + 5]))
            break
        cauda = linhas[j : j + quantos_numeros]
        corpo = linhas[inicio_corpo:j]
        i = j + quantos_numeros

        if len(corpo) < 4:
            problemas.append((codigo, "corpo curto", corpo))
            continue
        municipio = corpo[-1]
        anterior = corpo[:-1]
        pos_turno = len(anterior) - 1
        while pos_turno > 0 and eh_turno(anterior[pos_turno - 1]):
            pos_turno -= 1
        turno = " ".join(anterior[pos_turno:])
        prefixo = anterior[:pos_turno]
        area = area_do_prefixo(prefixo)
        if not area:
            # Em uma linha da UNESP a área não foi extraída do PDF.
            nome = prefixo[0]
            if inferir_area(nome) == "Não informada":
                problemas.append((codigo, "sem area", prefixo[-4:]))
                continue
            nome_area = inferir_area(nome)
            campus = " ".join(prefixo[1:]).strip()
        else:
            pos_area, fim_area, nome_area = area
            nome = " ".join(prefixo[:pos_area])
            campus = " ".join(prefixo[fim_area:]).strip()
        campus = re.sub(r"\s*" + re.escape(nome_area) + r"\s*$", "", campus, flags=re.I).strip()
        if repeticao_exata(campus):
            campus = campus[: len(campus) // 2].strip()
        registros.append(
            {
                "codigo": codigo,
                "curso": nome,
                "area": nome_area,
                "campus": campus,
                "turno": turno,
                "municipio": municipio,
                "total": int(cauda[0]),
                "ep": int(cauda[1]) if len(cauda) > 1 else None,
                "ppi": int(cauda[2]) if len(cauda) > 2 else None,
            }
        )
    return registros, problemas


if __name__ == "__main__":
    casos = [
        ("ANEXO VIII", "ANEXO IX", 3, 1500),
        ("ANEXO IX", "ANEXO X", 3, 929),
        ("ANEXO X", "ANEXO XI", 3, 326),
        ("ANEXO XI", "ANEXO XII", 2, 3064),
        ("ANEXO XII", None, 2, 7920),
    ]
    for rotulo, proximo, nums, esperado in casos:
        registros, problemas = extrair_anexo(rotulo, proximo, nums)
        soma = sum(r["total"] for r in registros)
        print(
            f"{rotulo}: {len(registros)} cursos, {soma} vagas (esperado {esperado}), "
            f"{len(problemas)} problemas"
        )
        for p in problemas[:6]:
            print("   ", p)
        for r in registros[:2]:
            print("   ", r)
