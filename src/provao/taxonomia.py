"""Taxonomia de temas por disciplina, baseada no Anexo VII do edital de 2026.

Os temas foram agrupados em macrotópicos para permitir comparação entre os
anos. A classificação das questões é feita por palavras-chave e revisada
manualmente nos casos ambíguos.
"""

from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

# Cada tema é uma tupla (nome, [(expressão regular, peso), ...]).
REGRAS: dict[str, list[tuple[str, list[tuple[str, int]]]]] = {
    "Língua Portuguesa": [
        (
            "Figuras de linguagem",
            [
                (r"figuras? de linguagem", 4),
                (r"met[aá]fora|meton[ií]mia|hip[eé]rbole|eufemismo|ant[ií]tese", 3),
                (r"sinestesia|personifica[cç][aã]o|prosopopeia|pleonasmo|ironia", 3),
                (r"ambiguidade|paradoxo|compara[cç][aã]o|catacrese|per[ií]frase", 2),
            ],
        ),
        (
            "Literatura",
            [
                (r"soneto|poema|poesia|verso|estrofe|rima|eu l[ií]rico", 3),
                (r"romantismo|barroco|arcadismo|realismo|modernismo|trovadorismo|parnasianismo", 4),
                (r"literatura|obra liter[aá]ria|romance|conto|cr[oô]nica|narrador|personagem|f[aá]bula|mito|can[cç][aã]o|letra", 2),
                (r"machado de assis|jos[eé] de alencar|mario quintana|vin[ií]cius de moraes", 3),
                (r"intertextualidade|par[oó]dia|pastiche|alus[aã]o", 2),
            ],
        ),
        (
            "Morfossintaxe",
            [
                (r"verbo|verbal|substantivo|adjetivo|pronome|adv[eé]rbio|preposi[cç][aã]o|conjun[cç][aã]o", 2),
                (r"concord[aâ]ncia|reg[eê]ncia|flex[aã]o|modo verbal|tempo verbal|voz verbal", 3),
                (r"prefixo|sufixo|forma[cç][aã]o de palavra|classe de palavra|morfologia", 3),
                (r"artigo|numeral|interjei[cç][aã]o|locu[cç][aã]o", 1),
            ],
        ),
        (
            "Sintaxe e coesão",
            [
                (r"ora[cç][aã]o|per[ií]odo|coordena[cç][aã]o|subordina[cç][aã]o", 3),
                (r"conectivo|coes[aã]o|coer[eê]ncia|refer[eê]ncia|retoma", 3),
                (r"sujeito|predicado|objeto direto|objeto indireto|adjunto|fun[cç][aã]o sint[aá]tica", 3),
                (r"discurso direto|discurso indireto|discurso indireto livre", 3),
            ],
        ),
        (
            "Variação e norma",
            [
                (r"variacao linguistica|variedade linguistica|norma culta|norma padrao|norma-padrao", 4),
                (r"linguagem formal|linguagem informal|oralidade|registro|g[ií]ria|preconceito lingu[ií]stico", 3),
                (r"ortografia|acentua[cç][aã]o|pontua[cç][aã]o|grafar|grafia|mai[uú]scula|min[uú]scula", 2),
                (r"ditado popular|prov[eé]rbio|frase feita", 3),
            ],
        ),
        (
            "Leitura e interpretação",
            [
                (r"tirinha|charge|cartum|quadrinho|meme|quadro", 2),
                (r"texto|trecho|par[aá]grafo|autor|leitor|sentido|ideia|prop[oó]sito", 1),
                (r"g[eê]nero textual|not[ií]cia|reportagem|artigo de opini[aã]o|an[uú]ncio", 2),
            ],
        ),
    ],
    "Língua Inglesa": [
        (
            "Vocabulário e expressões",
            [
                (r"significado|sentido|voc[aá]bulo|palavra|express[aã]o|termo", 3),
                (r"means|meaning|word|expression", 2),
            ],
        ),
        (
            "Referência e coesão",
            [
                (r"refere-se|referem-se|retoma|remete|pronome|refer[eê]ncia", 3),
            ],
        ),
        (
            "Relação imagem-texto",
            [
                (r"imagem|tirinha|charge|cartum|gr[aá]fico|infogr[aá]fico|figura", 3),
            ],
        ),
        (
            "Compreensão crítica",
            [
                (r"opini[aã]o|fato|cr[ií]tica|prop[oó]sito|inten[cç][aã]o|tom|ironia|argumento", 3),
                (r"autor|personagem|posicionamento", 2),
            ],
        ),
        (
            "Informação específica",
            [
                (r"de acordo com o texto|segundo o texto|o texto afirma|o texto informa|according to", 3),
                (r"qual|quem|quando|onde|como|por que", 1),
            ],
        ),
        (
            "Compreensão global",
            [
                (r"tema principal|ideia principal|objetivo|g[eê]nero|texto", 1),
            ],
        ),
    ],
    "Matemática": [
        (
            "Funções",
            [
                (r"fun[cç][aã]o|f\(x\)|gr[aá]fico da fun[cç][aã]o|par[aá]bola|exponencial|logaritmo", 3),
                (r"dom[ií]nio|imagem da fun[cç][aã]o|raiz da fun[cç][aã]o|coeficiente angular|custo fixo|custo vari[aá]vel|receita|lucro", 3),
                (r"reta|inclina[cç][aã]o|crescimento linear|taxa de varia[cç][aã]o|lan[cç]ado", 1),
            ],
        ),
        (
            "Geometria plana",
            [
                (r"tri[aâ]ngulo|pol[ií]gono|quadrado|ret[aâ]ngulo|c[ií]rculo|circunfer[eê]ncia", 3),
                (r"[aá]rea|per[ií]metro|teorema de pit[aá]goras|semelhan[cç]a|congru[eê]ncia|pintar|tinta|parede|planta baixa", 3),
                (r"[aâ]ngulo|diagonal|mediana|bissetriz|tangente", 2),
            ],
        ),
        (
            "Geometria espacial",
            [
                (r"volume|cilindro|cone|esfera|prisma|pir[aâ]mide|paralelep[ií]pedo|poliedro|cubo|caixa|caixinha|dimens[oõ]es", 4),
                (r"capacidade|corpo redondo|vistas ortogonais|aresta|face|v[eé]rtice", 2),
            ],
        ),
        (
            "Proporcionalidade e porcentagem",
            [
                (r"porcentagem|percentual|desconto|acr[eé]scimo|juros|taxa", 3),
                (r"propor[cç][aã]o|proporcional|raz[aã]o|regra de tr[eê]s|escala|receita", 3),
            ],
        ),
        (
            "Conjuntos e sequências",
            [
                (r"n[uú]mero|algarismo|inteiro|racional|real|nota[cç][aã]o cient[ií]fica|bilh[aã]o|milh[aã]o|reta dos n[uú]meros", 1),
                (r"sequ[eê]ncia|progress[aã]o|pa\b|pg\b|lei de forma[cç][aã]o|recorr[eê]ncia", 4),
            ],
        ),
        (
            "Análise combinatória",
            [
                (r"combinat[oó]ria|combina[cç][aã]o|arranjo|permuta[cç][aã]o|posi[cç][aã]o|posi[cç][oõ]es", 4),
                (r"de quantas maneiras|possibilidades|senha|sorteio|agrupamento|jogador|time|equipe", 2),
            ],
        ),
        (
            "Probabilidade",
            [
                (r"probabilidade|chance|aleat[oó]rio|evento|espa[cç]o amostral|fam[ií]lia|filho", 4),
                (r"dado|moeda|urna|sorteio", 2),
            ],
        ),
        (
            "Estatística e gráficos",
            [
                (r"m[eé]dia|mediana|moda|frequ[eê]ncia|amostra|pesquisa", 3),
                (r"gr[aá]fico|tabela|histograma|setores|barras", 2),
            ],
        ),
        (
            "Trigonometria",
            [
                (r"seno|cosseno|tangente|trigonometria|tri[aâ]ngulo ret[aâ]ngulo", 4),
                (r"teorema dos senos|teorema dos cossenos|arco|radiano", 3),
            ],
        ),
        (
            "Sistemas lineares",
            [
                (r"sistema linear|sistema de equa[cç][oõ]es|equa[cç][aã]o linear|quantidades de|estoque", 4),
            ],
        ),
        (
            "Equações e álgebra",
            [
                (r"equa[cç][aã]o|inequa[cç][aã]o|inc[oó]gnita|express[aã]o alg[eé]brica", 3),
                (r"valor de x|valores de x|resolver|raiz da equa|discriminante|bhaskara|intervalo|desigualdade", 2),
                (r"pot[eê]ncia|expoente|radical|logaritmo", 2),
            ],
        ),
        (
            "Medidas",
            [
                (r"unidade de medida|convers[aã]o|litro|metro|quilograma|cent[ií]metro|mililitro", 2),
            ],
        ),
    ],
    "Física": [
        (
            "Cinemática",
            [
                (r"velocidade|acelera[cç][aã]o|movimento|trajet[oó]ria|queda livre|mru|mruv", 3),
                (r"deslocamento|intervalo de tempo|gr[aá]fico.*velocidade", 2),
            ],
        ),
        (
            "Leis de Newton",
            [
                (r"for[cç]a|newton|atrito|tra[cç][aã]o|peso|normal|equil[ií]brio", 2),
                (r"in[eé]rcia|a[cç][aã]o e rea[cç][aã]o|din[aâ]mica|for[cç]a resultante", 3),
            ],
        ),
        (
            "Gravitação",
            [
                (r"gravita[cç][aã]o|kepler|[oó]rbita|sat[eé]lite|campo gravitacional", 4),
            ],
        ),
        (
            "Trabalho e energia",
            [
                (r"trabalho|energia|pot[eê]ncia|cin[eé]tica|potencial|conserva[cç][aã]o da energia", 3),
            ],
        ),
        (
            "Termologia e calorimetria",
            [
                (r"temperatura|calor|t[eé]rmica|dilata[cç][aã]o|calor espec[ií]fico|calor latente", 3),
                (r"term[oô]metro|escala celsius|fahrenheit|kelvin|equil[ií]brio t[eé]rmico", 3),
            ],
        ),
        (
            "Gases e termodinâmica",
            [
                (r"g[aá]s|press[aã]o|volume|termodin[aâ]mica|ciclo|entropia|m[aá]quina t[eé]rmica", 3),
            ],
        ),
        (
            "Óptica",
            [
                (r"luz|espelho|lente|refra[cç][aã]o|reflex[aã]o|refletid|imagem|sombra|pinhole", 3),
                (r"[oó]ptica|foco|centro de curvatura|dioptro", 3),
            ],
        ),
        (
            "Ondulatória",
            [
                (r"onda|som|frequ[eê]ncia|comprimento de onda|decibel|doppler|resson[aâ]ncia|corda|pulso", 3),
                (r"ultrassom|infrassom|espectro eletromagn[eé]tico", 3),
            ],
        ),
        (
            "Eletrostática",
            [
                (r"carga el[eé]trica|campo el[eé]trico|potencial el[eé]trico|coulomb|eletrost[aá]tica", 4),
            ],
        ),
        (
            "Eletrodinâmica",
            [
                (r"corrente el[eé]trica|resist[eê]ncia|tens[aã]o|circuito|ohm|pot[eê]ncia el[eé]trica", 4),
                (r"gerador|capacitor|efeito joule|quilowatt-hora", 3),
            ],
        ),
        (
            "Eletromagnetismo",
            [
                (r"[ií]m[aã]|campo magn[eé]tico|indu[cç][aã]o|faraday|eletromagnetismo", 4),
            ],
        ),
    ],
    "Química": [
        (
            "Materiais e propriedades",
            [
                (r"subst[aâ]ncia|mistura|separa[cç][aã]o|densidade|estado f[ií]sico|material", 2),
                (r"ponto de fus[aã]o|ponto de ebuli[cç][aã]o|solubilidade|pictograma|seguran[cç]a|m[eé]todo cient[ií]fico|experimento", 2),
            ],
        ),
        (
            "Transformações e estequiometria",
            [
                (r"rea[cç][aã]o qu[ií]mica|equa[cç][aã]o qu[ií]mica|balanceamento|estequiometria", 4),
                (r"mol|massa molar|lavoisier|proust|rendimento", 3),
            ],
        ),
        (
            "Funções inorgânicas",
            [
                (r"[aá]cido|base|sal|[oó]xido|neutraliza[cç][aã]o|indicador|ph", 3),
            ],
        ),
        (
            "Química e meio ambiente",
            [
                (r"atmosfera|chuva [aá]cida|efeito estufa|polui[cç][aã]o|tratamento de [aá]gua", 3),
                (r"meio ambiente|ambiental|emiss[aã]o de gases", 2),
            ],
        ),
        (
            "Estrutura atômica",
            [
                (r"[aá]tomo|modelo at[oô]mico|pr[oó]ton|el[eé]tron|n[eê]utron|tabela peri[oó]dica|is[oó]topo", 3),
            ],
        ),
        (
            "Ligações químicas",
            [
                (r"liga[cç][aã]o i[oô]nica|liga[cç][aã]o covalente|liga[cç][aã]o met[aá]lica|octeto", 4),
                (r"f[oó]rmula molecular|f[oó]rmula estrutural|geometria molecular", 2),
            ],
        ),
        (
            "Polaridade e interações",
            [
                (r"polaridade|intermolecular|dipolo|eletronegatividade", 4),
            ],
        ),
        (
            "Soluções",
            [
                (r"solu[cç][aã]o|concentra[cç][aã]o|molaridade|dilui[cç][aã]o|ppm|solubilidade", 3),
            ],
        ),
        (
            "Cinética e equilíbrio",
            [
                (r"cin[eé]tica|velocidade da rea[cç][aã]o|equil[ií]brio qu[ií]mico|constante de equil[ií]brio", 4),
                (r"catalisador|energia de ativa[cç][aã]o|colis[aã]o", 3),
            ],
        ),
        (
            "Termoquímica e eletroquímica",
            [
                (r"entalpia|exot[eé]rmica|endot[eé]rmica|termoqu[ií]mica|lei de hess", 4),
                (r"pilha|eletr[oó]lise|oxida[cç][aã]o|redu[cç][aã]o|potencial padr[aã]o", 4),
            ],
        ),
        (
            "Radioatividade",
            [
                (r"radioatividade|meia-vida|fiss[aã]o|fus[aã]o nuclear|radia[cç][aã]o", 4),
            ],
        ),
        (
            "Química orgânica",
            [
                (r"org[aâ]nica|carbono|hidrocarboneto|[aá]lcool|pol[ií]mero|isomeria|fun[cç][aã]o org[aâ]nica", 4),
                (r"petr[oó]leo|g[aá]s natural|carv[aã]o", 2),
            ],
        ),
    ],
    "Biologia": [
        (
            "Ecologia e meio ambiente",
            [
                (r"ecossistema|cadeia alimentar|popula[cç][aã]o|h[aá]bitat|nicho|bioma", 3),
                (r"ciclo biogeoqu[ií]mico|polui[cç][aã]o|sustentabilidade|conserva[cç][aã]o|desmatamento", 3),
                (r"biodiversidade|impacto ambiental|esp[eé]cie invasora|pl[aá]stico|res[ií]duo", 2),
            ],
        ),
        (
            "Citologia e metabolismo",
            [
                (r"c[eé]lula|membrana|organela|mitoc[oô]ndria|cloroplasto", 3),
                (r"mitose|meiose|fotoss[ií]ntese|respira[cç][aã]o celular|fermenta[cç][aã]o", 3),
                (r"dna|rna|s[ií]ntese proteica|transcri[cç][aã]o|tradu[cç][aã]o", 2),
            ],
        ),
        (
            "Genética e biotecnologia",
            [
                (r"gene|gen[eé]tica|heredograma|mendel|cromossomo|alelo|gen[oó]tipo|fen[oó]tipo", 4),
                (r"biotecnologia|transg[eê]nico|clonagem|dna recombinante|engenharia gen[eé]tica", 3),
            ],
        ),
        (
            "Classificação e diversidade",
            [
                (r"classifica[cç][aã]o|taxonomia|esp[eé]cie|v[ií]rus|bact[eé]ria|fungo|protozo[aá]rio", 3),
                (r"reino|filo|vertebrado|invertebrado", 2),
            ],
        ),
        (
            "Fisiologia e saúde",
            [
                (r"sistema (?:digest[oó]rio|respirat[oó]rio|circulat[oó]rio|nervoso|imunol[oó]gico|end[oó]crino)", 4),
                (r"digest[aã]o|horm[oô]nio|sangue|vacina|doen[cç]a|sa[uú]de|nutri[cç][aã]o|n[eé]fron|rim|ultraprocessado|alimento", 2),
                (r"antibi[oó]tico|v[ií]rus|epidemia|pandemia|saneamento", 2),
            ],
        ),
        (
            "Botânica e zoologia",
            [
                (r"planta|raiz|caule|folha|flor|semente|fotoss[ií]ntese", 2),
                (r"animal|inseto|ave|peixe|anf[ií]bio|r[eé]ptil|mam[ií]fero", 2),
            ],
        ),
        (
            "Evolução",
            [
                (r"evolu[cç][aã]o|darwin|lamarck|sele[cç][aã]o natural|filogenia|ancestral|especia[cç][aã]o", 4),
            ],
        ),
        (
            "Investigação científica",
            [
                (r"experimento|hip[oó]tese|m[eé]todo cient[ií]fico|vari[aá]vel|grupo controle", 4),
            ],
        ),
    ],
    "História": [
        (
            "Antiguidade Clássica",
            [
                (r"gr[eé]cia|grego|roma|romano|atenas|ateniense|esparta|helen[ií]stico", 3),
            ],
        ),
        (
            "Período Medieval",
            [
                (r"feudal|feudo|idade m[eé]dia|senhor feudal|servid[aã]o|cruzada", 3),
            ],
        ),
        (
            "Mundo Moderno",
            [
                (r"renascimento|estado moderno|mercantilismo|iluminismo|reforma|antigo regime|montesquieu", 3),
                (r"expans[aã]o mar[ií]tima|coloniza[cç][aã]o", 2),
            ],
        ),
        (
            "Brasil Colonial",
            [
                (r"brasil col[oô]nia|capitania|a[cç][uú]car|pau-brasil|ouro|revolta colonial|patriarcalismo", 3),
                (r"escravid[aã]o|ind[ií]gena|jesu[ií]ta|bandeirante", 2),
            ],
        ),
        (
            "Brasil Imperial",
            [
                (r"imp[eé]rio|d\. pedro|independ[eê]ncia do brasil|segundo reinado|aboli[cç][aã]o|imigra[cç][aã]o", 4),
            ],
        ),
        (
            "Brasil República",
            [
                (r"rep[uú]blica|vargas|estado novo|ditadura|constitui[cç][aã]o de 1988|redemocratiza[cç][aã]o", 4),
                (r"golpe de 1964|regime militar|primeira rep[uú]blica", 3),
            ],
        ),
        (
            "Mundo Contemporâneo",
            [
                (r"revolu[cç][aã]o francesa|revolu[cç][aã]o industrial|guerra mundial|nazismo|fascismo", 4),
                (r"guerra fria|globaliza[cç][aã]o|imperialismo|descoloniza[cç][aã]o|capitalismo|congo|colonialismo", 3),
                (r"uni[aã]o africana|[aá]frica|fascismo|nazismo|fascista|nazista|stalin|urss|uni[aã]o sovi[eé]tica", 2),
            ],
        ),
        (
            "Povos indígenas",
            [
                (r"ind[ií]gena|povos origin[aá]rios|resist[eê]ncia ind[ií]gena", 3),
            ],
        ),
        (
            "História e método",
            [
                (r"fonte hist[oó]rica|historiografia|documento|mem[oó]ria", 2),
            ],
        ),
    ],
    "Geografia": [
        (
            "Geopolítica e ordem mundial",
            [
                (r"geopol[ií]tica|ordem mundial|guerra fria|bloco econ[oô]mico|conflito|fronteira", 3),
            ],
        ),
        (
            "Globalização e economia",
            [
                (r"globaliza[cç][aã]o|ind[uú]stria|com[eé]rcio|transporte|energia|pib|rede|internet|tecnologia", 3),
                (r"divis[aã]o internacional do trabalho|desigualdade econ[oô]mica", 2),
            ],
        ),
        (
            "População e migração",
            [
                (r"popula[cç][aã]o|demografia|migra[cç][aã]o|densidade|idh|urbano|rural", 3),
            ],
        ),
        (
            "Urbanização",
            [
                (r"cidade|urbaniza[cç][aã]o|metr[oó]pole|favela|mobilidade|saneamento", 3),
            ],
        ),
        (
            "Espaço agrário",
            [
                (r"agricultura|agroneg[oó]cio|solo|planta[cç][aã]o|pecu[aá]ria|reforma agr[aá]ria", 3),
            ],
        ),
        (
            "Natureza e meio ambiente",
            [
                (r"relevo|bioma|vegeta[cç][aã]o|eros[aã]o|impacto ambiental|desmatamento|unidade de conserva[cç][aã]o", 3),
            ],
        ),
        (
            "Clima e mudanças climáticas",
            [
                (r"clima|temperatura|chuva|aquecimento global|efeito estufa|precipita[cç][aã]o", 3),
            ],
        ),
        (
            "Sociedade e cultura",
            [
                (r"g[eê]nero|machismo|mulher|direitos|identidade|cultura|manifesta[cç][aã]o|desigualdade social", 3),
            ],
        ),
        (
            "Cartografia",
            [
                (r"mapa|escala|coordenada|longitude|latitude|cartografia|proje[cç][aã]o", 4),
            ],
        ),
        (
            "Hidrografia e água",
            [
                (r"rio|bacia hidrogr[aá]fica|[aá]gua|aqu[ií]fero|hidrel[eé]trica", 3),
            ],
        ),
    ],
    "Filosofia": [
        (
            "Filosofia e visões de mundo",
            [
                (r"filosofia|filosofar|mito|cultura|vis[aã]o de mundo", 2),
            ],
        ),
        (
            "Epistemologia",
            [
                (r"conhecimento|senso comum|ci[eê]ncia|racionalismo|empirismo|descartes|verdade", 3),
                (r"epistemologia|m[eé]todo|ceticismo|d[uú]vida", 2),
            ],
        ),
        (
            "Ética e bioética",
            [
                (r"[eé]tica|moral|bio[eé]tica|valores|virtude|responsabilidade", 4),
                (r"alteredade|aleteridade|alteridade|empatia|intergeracional", 3),
            ],
        ),
        (
            "Filosofia política",
            [
                (r"pol[ií]tica|estado|contrato social|hobbes|locke|rousseau|poder|democracia", 3),
                (r"contratualismo|soberania|governo", 2),
            ],
        ),
        (
            "Direitos humanos e cidadania",
            [
                (r"direitos humanos|cidadania|igualdade|liberdade", 3),
            ],
        ),
        (
            "Estética e cultura",
            [
                (r"arte|est[eé]tica|belo|cultura|meme|ind[uú]stria cultural|televis[aã]o|m[ií]dia", 3),
            ],
        ),
    ],
    "Sociologia": [
        (
            "Indivíduo e identidade",
            [
                (r"identidade|socializa[cç][aã]o|indiv[ií]duo|preconceito|discrimina[cç][aã]o|g[eê]nero|ra[cç]a|identit[aá]rio", 3),
                (r"durkheim|weber|fato social|solidariedade|a[cç][aã]o social|anomia|burocracia|m[eé]todo sociol[oó]gico", 4),
            ],
        ),
        (
            "Trabalho e classes sociais",
            [
                (r"trabalho|classe social|marx|capitalismo|emprego|desigualdade|tecnologia", 3),
                (r"divis[aã]o do trabalho|mais-valia|aliena[cç][aã]o", 3),
            ],
        ),
        (
            "Cultura e consumo",
            [
                (r"cultura|ind[uú]stria cultural|consumo|m[ií]dia|etnocentrismo|relativismo", 3),
            ],
        ),
        (
            "Estado e política",
            [
                (r"estado|partido|democracia|representa[cç][aã]o|pol[ií]tica|cidadania", 3),
            ],
        ),
        (
            "Movimentos sociais",
            [
                (r"movimento social|protesto|participa[cç][aã]o|direitos", 3),
            ],
        ),
        (
            "Desigualdades e direitos",
            [
                (r"desigualdade|pobreza|direitos humanos|viol[eê]ncia|intoler[aâ]ncia", 3),
            ],
        ),
        (
            "Sociedade brasileira",
            [
                (r"brasil|brasileira|constitui[cç][aã]o|patriarcalismo", 2),
            ],
        ),
    ],
}


def _radical(token: str) -> str:
    """Redução leve de plural para aumentar a coincidência de palavras-chave."""
    token = re.sub(r"^[^\w]+|[^\w]+$", "", token, flags=re.UNICODE)
    if len(token) <= 3:
        return token
    if token.endswith("oes") or token.endswith("aes"):
        return token[:-3] + "ao"
    if token.endswith("ais"):
        return token[:-3] + "al"
    if token.endswith("eis"):
        return token[:-3] + "el"
    if token.endswith("ois"):
        return token[:-3] + "ol"
    if token.endswith("ns"):
        return token[:-1] + "m"
    if token.endswith("es") and len(token) > 4 and token[-3] in "rzsl":
        return token[:-2]
    if token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def _variantes(token: str) -> list[str]:
    """Formas possíveis de um token, para casar singular e plural."""
    token = re.sub(r"^[^\w]+|[^\w]+$", "", token, flags=re.UNICODE)
    if not token:
        return []
    variantes = [token]

    def adicionar(candidato: str) -> None:
        if candidato and candidato not in variantes:
            variantes.append(candidato)

    if token.endswith("oes") or token.endswith("aes"):
        adicionar(token[:-3] + "ao")
    if token.endswith("ais"):
        adicionar(token[:-3] + "al")
    if token.endswith("eis"):
        adicionar(token[:-3] + "el")
    if token.endswith("ois"):
        adicionar(token[:-3] + "ol")
    if token.endswith("ns"):
        adicionar(token[:-1] + "m")
    if token.endswith("es") and len(token) > 4:
        adicionar(token[:-2])
    if token.endswith("s") and not token.endswith("ss"):
        adicionar(token[:-1])
    return variantes


_META_REGEX = re.compile(r"[\[\](){}?*+|\\^$.]")


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"\s+", " ", texto).strip().lower()
    return " ".join(_radical(t) for t in texto.split())


def normalizar_padrao(padrao: str) -> str:
    """Normaliza um padrão sem destruir os operadores de regex."""
    padrao = unicodedata.normalize("NFKD", padrao)
    padrao = "".join(c for c in padrao if not unicodedata.combining(c))
    partes = []
    for token in padrao.split():
        if _META_REGEX.search(token):
            partes.append(token)
            continue
        variantes = _variantes(token)
        if len(variantes) == 1:
            partes.append(variantes[0])
        else:
            partes.append("(?:" + "|".join(variantes) + ")")
    return " ".join(partes).lower()


def _pontuar(regras, alvo: str) -> tuple[str, int]:
    melhor = ("", 0)
    for tema, padroes in regras:
        pontos = 0
        for padrao, peso in padroes:
            if re.search(normalizar_padrao(padrao), alvo):
                pontos += peso
        if pontos > melhor[1]:
            melhor = (tema, pontos)
    return melhor


# Temas usados quando nenhuma palavra-chave é encontrada.
PADRAO: dict[str, str] = {
    "Língua Portuguesa": "Leitura e interpretação",
    "Língua Inglesa": "Compreensão global",
}


@lru_cache(maxsize=1)
def _overrides() -> dict[str, str]:
    caminho = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "reference"
        / "temas_manuais.json"
    )
    if not caminho.exists():
        return {}
    return json.loads(caminho.read_text(encoding="utf-8"))


def classificar(
    disciplina: str,
    texto: str,
    alternativas: str = "",
    limite: int = 3,
    chave: str | None = None,
) -> tuple[str, int]:
    """Retorna (tema, pontuação). Tema vazio quando nada foi identificado.

    O enunciado tem prioridade. As alternativas só entram quando o enunciado
    sozinho não atinge ``limite`` pontos, evitando que palavras das opções
    distorçam o tema. Casos ambíguos podem ser fixados em
    ``data/reference/temas_manuais.json`` usando uma chave como ``2024-3-2-42``.
    """
    if chave and chave in _overrides():
        return _overrides()[chave], 100
    regras = REGRAS.get(disciplina, [])
    tema, pontos = _pontuar(regras, normalizar(texto))
    if pontos >= limite or not alternativas:
        return tema or PADRAO.get(disciplina, ""), pontos
    tema_alt, pontos_alt = _pontuar(regras, normalizar(texto + " " + alternativas))
    if pontos_alt > pontos:
        return tema_alt or PADRAO.get(disciplina, ""), pontos_alt
    return tema or PADRAO.get(disciplina, ""), pontos

