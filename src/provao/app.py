"""Painel do Provão em Foco.

Execute com:
    streamlit run app.py
"""

from __future__ import annotations

import html
import json
import random

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from provao.dados import (
    carregar_contextos,
    carregar_questoes,
)
from provao.ineditas import carregar_ineditas
from provao.ui import (
    CUSTOM_CSS,
    fmt_int,
    insight,
    render_footer,
    render_hero,
    section,
    style_fig,
)
from provao.vagas import carregar_vagas

FONTE_EXAM = "https://provaopaulistaseriado.vunesp.com.br/"
FONTE_EDITAL = "https://www.vunesp.com.br/SEED2602"

CORES = {
    "Língua Portuguesa": "#7c3aed",
    "Matemática": "#2563eb",
    "Biologia": "#059669",
    "Física": "#0891b2",
    "Química": "#d97706",
    "História": "#dc2626",
    "Geografia": "#65a30d",
    "Língua Inglesa": "#db2777",
    "Filosofia": "#9333ea",
    "Sociologia": "#0d9488",
}

DISCIPLINAS = list(CORES)


@st.cache_data(show_spinner=False)
def _questoes() -> pd.DataFrame:
    return carregar_questoes()


@st.cache_data(show_spinner=False)
def _contextos() -> pd.DataFrame:
    return carregar_contextos()


@st.cache_data(show_spinner=False)
def _vagas() -> pd.DataFrame:
    return carregar_vagas()


@st.cache_data(show_spinner=False)
def _ineditas() -> list[dict]:
    return carregar_ineditas()


def _html(texto: str) -> str:
    return html.escape(str(texto)).replace("\n", "<br>")


def _alternativas(linha: pd.Series) -> dict[str, str]:
    bruto = linha.get("alternativas_json")
    if not isinstance(bruto, str) or not bruto.strip():
        return {}
    try:
        dados = json.loads(bruto)
    except json.JSONDecodeError:
        return {}
    return {k: v for k, v in dados.items() if str(v).strip()}


def _filtrar(
    df: pd.DataFrame,
    anos: list[int] | None = None,
    series: list[int] | None = None,
    disciplinas: list[str] | None = None,
) -> pd.DataFrame:
    recorte = df
    if anos:
        recorte = recorte[recorte["ano"].isin(anos)]
    if series:
        recorte = recorte[recorte["serie"].isin(series)]
    if disciplinas:
        recorte = recorte[recorte["disciplina"].isin(disciplinas)]
    return recorte


def _top_temas(df: pd.DataFrame, n: int = 12) -> pd.DataFrame:
    contagem = (
        df.groupby(["tema", "disciplina"], as_index=False)
        .size()
        .rename(columns={"size": "quantidade"})
    )
    total = contagem.groupby("tema")["quantidade"].transform("sum")
    contagem["total"] = total
    contagem["percentual"] = (contagem["quantidade"] / contagem["total"] * 100).round(1)
    return contagem.sort_values(["total", "disciplina"], ascending=[False, True]).head(n)


# ---------------------------------------------------------------------------
# Abas
# ---------------------------------------------------------------------------


def aba_panorama(q: pd.DataFrame) -> None:
    section(
        "O que os cadernos revelam",
        "Três edições, três séries e 810 itens objetivos corrigidos por gabarito oficial.",
    )

    colunas = st.columns(4)
    colunas[0].metric("Questões analisadas", fmt_int(len(q)))
    colunas[1].metric("Edições", fmt_int(q["ano"].nunique()))
    colunas[2].metric("Cadernos", fmt_int(q.groupby(["ano", "serie"]).ngroups * 2))
    colunas[3].metric("Componentes", fmt_int(q["disciplina"].nunique()))

    insight(
        "Cada série responde a <strong>90 itens</strong>: 48 no primeiro dia e 42 no segundo. "
        "Língua Portuguesa e Matemática concentram <strong>20 itens cada</strong> no primeiro "
        "e no segundo dia, respectivamente. Nos demais componentes, a quantidade varia entre "
        "as edições — por isso a comparação de temas é feita dentro de cada disciplina."
    )

    section("Distribuição por componente")
    contagem = q.groupby("disciplina").size().sort_values().reset_index(name="questoes")
    fig = px.bar(
        contagem,
        x="questoes",
        y="disciplina",
        orientation="h",
        color="disciplina",
        color_discrete_map=CORES,
        labels={"questoes": "Questões", "disciplina": ""},
    )
    fig.update_traces(text="questoes", textposition="outside", cliponaxis=False)
    fig.update_layout(title="Questões por componente (2023–2025)", showlegend=False)
    st.plotly_chart(style_fig(fig, height=420, showlegend=False), width="stretch")

    section("Composição dos cadernos")
    comp = (
        q.groupby(["ano", "serie", "dia"]).size().reset_index(name="questoes")
    )
    comp["edicao"] = comp["ano"].astype(str) + " · " + comp["serie"].astype(str) + "ª série"
    comp["dia"] = comp["dia"].map({1: "Dia 1", 2: "Dia 2"})
    fig = px.bar(
        comp,
        x="edicao",
        y="questoes",
        color="dia",
        barmode="stack",
        color_discrete_map={"Dia 1": "#7c3aed", "Dia 2": "#f59e0b"},
        labels={"edicao": "", "questoes": "Questões", "dia": ""},
    )
    fig.update_layout(title="Itens por caderno e dia de aplicação")
    st.plotly_chart(style_fig(fig, height=380), width="stretch")

    section("Temas mais frequentes no conjunto")
    top = _top_temas(q, 14).sort_values("total")
    fig = px.bar(
        top,
        x="total",
        y="tema",
        orientation="h",
        color="disciplina",
        color_discrete_map=CORES,
        labels={"total": "Questões", "tema": "", "disciplina": ""},
    )
    fig.update_layout(title="Temas com mais itens nas três edições")
    st.plotly_chart(style_fig(fig, height=500), width="stretch")

    section("Cobertura por edição")
    tabela = (
        q.groupby(["ano", "serie"])
        .agg(
            questoes=("chave", "size"),
            componentes=("disciplina", "nunique"),
            temas=("tema", "nunique"),
        )
        .reset_index()
    )
    tabela.columns = ["Ano", "Série", "Questões", "Componentes", "Temas distintos"]
    st.dataframe(tabela, hide_index=True, width="stretch")


def aba_temas(q: pd.DataFrame) -> None:
    section(
        "Frequência de temas",
        "Filtre por edição, série e componente para comparar o peso de cada assunto.",
    )

    colunas = st.columns(3)
    anos = colunas[0].multiselect(
        "Edição", [2023, 2024, 2025], default=[2023, 2024, 2025], key="temas_ano"
    )
    series = colunas[1].multiselect("Série", [1, 2, 3], default=[1, 2, 3], key="temas_serie")
    disciplinas = colunas[2].multiselect(
        "Componente",
        DISCIPLINAS,
        default=["Língua Portuguesa", "Matemática"],
        key="temas_disciplina",
    )

    recorte = _filtrar(q, anos, series, disciplinas)
    if recorte.empty:
        st.info("Nenhuma questão corresponde aos filtros selecionados.")
        return

    colunas = st.columns(4)
    colunas[0].metric("Questões no recorte", fmt_int(len(recorte)))
    colunas[1].metric("Componentes", fmt_int(recorte["disciplina"].nunique()))
    colunas[2].metric("Temas distintos", fmt_int(recorte["tema"].nunique()))
    colunas[3].metric("Edições", fmt_int(recorte["ano"].nunique()))

    section("Temas mais cobrados no recorte")
    contagem = (
        recorte.groupby(["tema", "disciplina"], as_index=False)
        .size()
        .rename(columns={"size": "quantidade"})
    )
    contagem["percentual"] = (contagem["quantidade"] / len(recorte) * 100).round(1)
    contagem = contagem.sort_values("quantidade", ascending=False).head(15)
    contagem["rotulo"] = contagem.apply(
        lambda r: f"{r['tema']} ({r['percentual']:.0f}%)".replace(".", ","), axis=1
    )
    contagem = contagem.sort_values("quantidade")
    fig = px.bar(
        contagem,
        x="quantidade",
        y="rotulo",
        orientation="h",
        color="disciplina",
        color_discrete_map=CORES,
        labels={"quantidade": "Questões", "rotulo": "", "disciplina": ""},
    )
    fig.update_layout(title="15 temas mais frequentes")
    st.plotly_chart(style_fig(fig, height=520), width="stretch")

    if len(disciplinas) == 1:
        disciplina = disciplinas[0]
        section(f"Evolução dos temas em {disciplina}")
        dados = recorte.copy()
        anos_presentes = sorted(dados["ano"].unique())
        tabela = (
            dados.groupby(["tema", "ano"]).size().unstack(fill_value=0)
            .reindex(columns=anos_presentes, fill_value=0)
        )
        tabela["total"] = tabela.sum(axis=1)
        tabela = tabela.sort_values("total", ascending=False).head(12).drop(columns="total")
        percentual = tabela.div(tabela.sum(axis=0), axis=1) * 100
        fig = go.Figure(
            data=go.Heatmap(
                z=percentual.values,
                x=[str(a) for a in percentual.columns],
                y=percentual.index,
                colorscale="Purples",
                text=percentual.round(0).astype(int).astype(str) + "%",
                texttemplate="%{text}",
                hovertemplate="%{y}<br>%{x}: %{z:.1f}%<extra></extra>",
                colorbar=dict(title="% da disciplina"),
            )
        )
        fig.update_layout(title=f"Peso de cada tema dentro de {disciplina} (%)")
        st.plotly_chart(style_fig(fig, height=480, showlegend=False), width="stretch")

        section("Tabela de apoio")
        detalhe = (
            recorte.groupby(["tema", "ano"]).size().unstack(fill_value=0)
            .sort_values(by=list(anos_presentes), ascending=False)
        )
        detalhe.columns = [str(c) for c in detalhe.columns]
        detalhe["Total"] = detalhe.sum(axis=1)
        st.dataframe(detalhe, width="stretch")

    section("Temas por componente e série")
    cruzada = (
        recorte.groupby(["disciplina", "serie"]).size().reset_index(name="questoes")
    )
    fig = px.bar(
        cruzada,
        x="disciplina",
        y="questoes",
        color="serie",
        barmode="group",
        labels={"disciplina": "", "questoes": "Questões", "serie": "Série"},
        color_discrete_sequence=px.colors.sequential.Purples_r,
    )
    fig.update_layout(title="Questões por componente e série no recorte")
    st.plotly_chart(style_fig(fig, height=420), width="stretch")

    principais = recorte["tema"].value_counts().head(3)
    lista = ", ".join(
        f"<strong>{tema}</strong> ({fmt_int(n)})" for tema, n in principais.items()
    )
    insight(
        f"No recorte selecionado, os temas mais presentes são {lista}. "
        "A leitura por percentual ajuda a comparar componentes com números diferentes de itens."
    )


def _cartao_questao(linha: pd.Series, contexto: str | None = None) -> None:
    alternativas = _alternativas(linha)
    meta = (
        f"{linha['ano']} · {linha['serie']}ª série · Dia {linha['dia']} · "
        f"Questão {linha['numero']} · {linha['disciplina']}"
    )
    tags = (
        f'<span class="qtag">{_html(linha["tema"])}</span>'
        f'<span class="qtag gray">Gabarito {linha["gabarito"]}</span>'
    )
    corpo = (
        f'<div class="qbox"><div class="qmeta">{_html(meta)}</div>'
        f'<div style="margin:0.4rem 0 0.5rem 0">{tags}</div>'
        f'<div class="qstem">{_html(linha["enunciado"])}</div>'
    )
    if alternativas:
        for letra, texto in alternativas.items():
            corpo += (
                f'<div class="qalt"><strong>{letra})</strong> {_html(texto)}</div>'
            )
    else:
        corpo += (
            '<div class="qalt"><em>As alternativas deste item são apresentadas como '
            "imagem no caderno original. Consulte a página indicada abaixo.</em></div>"
        )
    corpo += "</div>"
    st.markdown(corpo, unsafe_allow_html=True)

    with st.expander("Gabarito, classificação e fonte"):
        st.write(f"**Gabarito:** {linha['gabarito']}")
        st.write(f"**Tema:** {linha['tema']}")
        st.write(
            f"**Fonte:** {linha['caderno']}, página {int(linha['pagina'])} "
            f"(questão {int(linha['numero'])})"
        )
        if contexto:
            st.caption("Texto extraído da página do caderno, para contexto:")
            st.text(contexto[:1800])


def aba_banco(q: pd.DataFrame) -> None:
    section(
        "Banco de questões",
        "Todos os itens objetivos das edições de 2023, 2024 e 2025, com gabarito e classificação.",
    )

    colunas = st.columns([1, 1, 1.4, 1.4])
    anos = colunas[0].multiselect(
        "Edição", [2023, 2024, 2025], default=[2023, 2024, 2025], key="banco_ano"
    )
    series = colunas[1].multiselect("Série", [1, 2, 3], default=[1, 2, 3], key="banco_serie")
    disciplinas = colunas[2].multiselect("Componente", DISCIPLINAS, key="banco_disciplina")
    busca = colunas[3].text_input(
        "Buscar no enunciado", placeholder="palavra ou expressão", key="banco_busca"
    )

    recorte = _filtrar(q, anos, series, disciplinas)
    if busca.strip():
        recorte = recorte[
            recorte["enunciado"].str.contains(busca.strip(), case=False, na=False)
        ]

    if recorte.empty:
        st.info("Nenhuma questão encontrada com esses filtros.")
        return

    st.caption(
        f"{fmt_int(len(recorte))} questões no recorte. "
        "Itens com alternativas apenas em imagem continuam disponíveis, com a página do caderno."
    )

    por_pagina = 8
    total_paginas = max(1, (len(recorte) + por_pagina - 1) // por_pagina)
    pagina = st.number_input(
        "Página", min_value=1, max_value=total_paginas, value=1, step=1, key="banco_pagina"
    )
    inicio = (int(pagina) - 1) * por_pagina
    fatia = recorte.iloc[inicio : inicio + por_pagina]

    contextos = _contextos().set_index("chave")
    for _, linha in fatia.iterrows():
        contexto = None
        if linha["chave"] in contextos.index:
            contexto = contextos.loc[linha["chave"], "contexto_pagina"]
        _cartao_questao(linha, contexto)

    st.download_button(
        "Baixar recorte em CSV",
        data=recorte.to_csv(index=False).encode("utf-8-sig"),
        file_name="questoes_provao_paulista.csv",
        mime="text/csv",
    )


def _sortear_simulado(
    base: pd.DataFrame, disciplinas: list[str], quantidade: int
) -> pd.DataFrame:
    candidatas = base[base["disciplina"].isin(disciplinas)]
    if candidatas.empty:
        return candidatas
    quantidade = min(quantidade, len(candidatas))
    rng = random.Random(st.session_state.get("simulado_seed", 0))
    indices = rng.sample(list(candidatas.index), quantidade)
    return candidatas.loc[indices].sort_values(["disciplina", "ano", "serie"])


def aba_simulado(q: pd.DataFrame) -> None:
    section(
        "Simulado",
        "Monte uma prova rápida com questões reais e confira o gabarito ao final.",
    )

    com_alternativas = q[q["alternativas_texto"].notna() & (q["alternativas_texto"] != "")]
    st.caption(
        f"{fmt_int(len(com_alternativas))} questões têm alternativas em texto e podem ser "
        "usadas no simulado. As demais dependem de imagens do caderno."
    )

    with st.form("configuracao_simulado"):
        colunas = st.columns([2, 1, 1])
        disciplinas = colunas[0].multiselect(
            "Componentes",
            DISCIPLINAS,
            default=["Língua Portuguesa", "Matemática", "Biologia"],
            key="simulado_disciplinas",
        )
        quantidade = colunas[1].slider("Questões", 5, 30, 10, 5, key="simulado_quantidade")
        gerar = colunas[2].form_submit_button(
            "Montar simulado", width="stretch", key="simulado_montar"
        )

    if gerar:
        if not disciplinas:
            st.warning("Selecione pelo menos um componente.")
        else:
            st.session_state["simulado_seed"] = st.session_state.get("simulado_seed", 0) + 1
            sorteio = _sortear_simulado(com_alternativas, disciplinas, quantidade)
            st.session_state["simulado_chaves"] = list(sorteio["chave"])
            st.session_state.pop("simulado_resultado", None)

    chaves = st.session_state.get("simulado_chaves", [])
    if not chaves:
        st.info("Escolha os componentes e a quantidade de questões para montar o simulado.")
        return

    selecionadas = q[q["chave"].isin(chaves)].copy()
    ordem = {chave: i for i, chave in enumerate(chaves)}
    selecionadas["ordem"] = selecionadas["chave"].map(ordem)
    selecionadas = selecionadas.sort_values("ordem")

    with st.form("respostas_simulado"):
        respostas: dict[str, str | None] = {}
        for posicao, (_, linha) in enumerate(selecionadas.iterrows(), start=1):
            alternativas = _alternativas(linha)
            st.markdown(
                f'<div class="qmeta">Questão {posicao} · {_html(linha["disciplina"])} · '
                f"{linha['ano']} · {linha['serie']}ª série</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="qstem">{_html(linha["enunciado"])}</div>',
                unsafe_allow_html=True,
            )
            opcoes = [f"{letra}) {texto}" for letra, texto in alternativas.items()]
            respostas[linha["chave"]] = st.radio(
                f"Resposta da questão {posicao}",
                opcoes,
                index=None,
                key=f"resposta_{linha['chave']}",
                label_visibility="collapsed",
            )
            st.divider()

        corrigir = st.form_submit_button(
            "Corrigir simulado", type="primary", key="simulado_corrigir"
        )

    if corrigir:
        acertos = 0
        detalhes = []
        for _, linha in selecionadas.iterrows():
            marcada = respostas.get(linha["chave"])
            letra = marcada[0] if marcada else None
            correta = linha["gabarito"]
            acertou = letra == correta
            acertos += int(acertou)
            detalhes.append(
                {
                    "chave": linha["chave"],
                    "numero": int(linha["numero"]),
                    "disciplina": linha["disciplina"],
                    "tema": linha["tema"],
                    "marcada": letra or "—",
                    "correta": correta,
                    "acertou": acertou,
                }
            )
        st.session_state["simulado_resultado"] = {
            "acertos": acertos,
            "total": len(selecionadas),
            "detalhes": detalhes,
        }

    resultado = st.session_state.get("simulado_resultado")
    if resultado:
        percentual = resultado["acertos"] / resultado["total"] * 100
        colunas = st.columns(3)
        colunas[0].metric("Acertos", f"{resultado['acertos']} de {resultado['total']}")
        colunas[1].metric("Aproveitamento", f"{percentual:.0f}%".replace(".", ","))
        colunas[2].metric("Questões em branco", sum(1 for d in resultado["detalhes"] if d["marcada"] == "—"))
        if percentual >= 60:
            st.success("Bom aproveitamento. Use os temas errados como prioridade de revisão.")
        else:
            st.warning("Vale revisar os temas das questões erradas antes de tentar novamente.")

        tabela = pd.DataFrame(resultado["detalhes"])
        tabela["acertou"] = tabela["acertou"].map({True: "Sim", False: "Não"})
        tabela = tabela.rename(
            columns={
                "numero": "Questão",
                "disciplina": "Componente",
                "tema": "Tema",
                "marcada": "Marcada",
                "correta": "Correta",
                "acertou": "Acertou",
            }
        )
        st.dataframe(
            tabela[["Questão", "Componente", "Tema", "Marcada", "Correta", "Acertou"]],
            hide_index=True,
            width="stretch",
        )


def aba_ineditas() -> None:
    section(
        "Questões inéditas",
        "Itens autorais escritos a partir dos temas recorrentes, com resolução comentada.",
    )

    questoes = _ineditas()
    disciplinas = sorted({q["disciplina"] for q in questoes})
    escolha = st.selectbox("Componente", ["Todos"] + disciplinas, key="ineditas_disciplina")
    if escolha != "Todos":
        questoes = [q for q in questoes if q["disciplina"] == escolha]

    st.caption(f"{len(questoes)} questões disponíveis neste filtro.")

    for questao in questoes:
        tags = (
            f'<span class="qtag">{_html(questao["disciplina"])}</span>'
            f'<span class="qtag gray">{_html(questao["tema"])}</span>'
            f'<span class="qtag gray">{_html(questao["dificuldade"])}</span>'
        )
        corpo = (
            f'<div class="qbox"><div style="margin-bottom:0.5rem">{tags}</div>'
            f'<div class="qstem">{_html(questao["enunciado"])}</div>'
        )
        for letra, texto in questao["alternativas"].items():
            corpo += f'<div class="qalt"><strong>{letra})</strong> {_html(texto)}</div>'
        corpo += "</div>"
        st.markdown(corpo, unsafe_allow_html=True)
        with st.expander("Ver gabarito e resolução comentada"):
            st.write(f"**Gabarito:** {questao['gabarito']}")
            st.write(questao["comentario"])


def aba_vagas(vagas: pd.DataFrame) -> None:
    section(
        "Vagas para ingresso em 2027",
        "Quadros publicados no edital do Provão Paulista Seriado 2026.",
    )

    colunas = st.columns(4)
    colunas[0].metric("Vagas nos quadros publicados", fmt_int(vagas["vagas_total"].sum()))
    colunas[1].metric("Ofertas de curso", fmt_int(len(vagas)))
    colunas[2].metric("Instituições", fmt_int(vagas["instituicao"].nunique()))
    colunas[3].metric("Municípios", fmt_int(vagas["municipio"].nunique()))

    insight(
        "Os Anexos VIII a XII somam <strong>13.739 vagas</strong>. O edital informa ainda "
        "<strong>2.080 vagas da FATEC para o 2º semestre de 2027</strong>, que não estão "
        "detalhadas por curso no Anexo XII. Com elas, o total divulgado chega a "
        "<strong>15.819 vagas</strong>. Os quadros abaixo refletem apenas as vagas publicadas "
        "por curso.",
        variant="warn",
    )

    section("Vagas por instituição")
    por_instituicao = (
        vagas.groupby("instituicao")["vagas_total"].sum().sort_values().reset_index()
    )
    fig = px.bar(
        por_instituicao,
        x="vagas_total",
        y="instituicao",
        orientation="h",
        color="instituicao",
        color_discrete_sequence=px.colors.sequential.Purples_r,
        labels={"vagas_total": "Vagas", "instituicao": ""},
    )
    fig.update_traces(text="vagas_total", textposition="outside", cliponaxis=False)
    fig.update_layout(title="Vagas publicadas por instituição", showlegend=False)
    st.plotly_chart(style_fig(fig, height=360, showlegend=False), width="stretch")

    colunas = st.columns(2)
    with colunas[0]:
        por_area = vagas.groupby("area_geral")["vagas_total"].sum().reset_index()
        fig = px.pie(
            por_area,
            names="area_geral",
            values="vagas_total",
            hole=0.55,
            color_discrete_sequence=["#7c3aed", "#2563eb", "#059669", "#f59e0b"],
        )
        fig.update_layout(title="Distribuição por área geral")
        st.plotly_chart(style_fig(fig, height=360), width="stretch")
    with colunas[1]:
        cidades = (
            vagas.groupby("municipio")["vagas_total"].sum().sort_values(ascending=False).head(12)
        ).reset_index()
        fig = px.bar(
            cidades,
            x="vagas_total",
            y="municipio",
            orientation="h",
            labels={"vagas_total": "Vagas", "municipio": ""},
            color_discrete_sequence=["#7c3aed"],
        )
        fig.update_layout(title="Municípios com mais vagas")
        st.plotly_chart(style_fig(fig, height=360, showlegend=False), width="stretch")

    section("Consultar ofertas")
    colunas = st.columns([1, 1, 1.3, 1.3])
    instituicoes = colunas[0].multiselect(
        "Instituição", sorted(vagas["instituicao"].unique()), key="vagas_instituicao"
    )
    areas = colunas[1].multiselect(
        "Área", sorted(vagas["area_geral"].unique()), key="vagas_area"
    )
    municipios = colunas[2].multiselect(
        "Município", sorted(vagas["municipio"].unique()), key="vagas_municipio"
    )
    busca = colunas[3].text_input(
        "Buscar curso", placeholder="nome do curso", key="vagas_busca"
    )

    recorte = vagas.copy()
    if instituicoes:
        recorte = recorte[recorte["instituicao"].isin(instituicoes)]
    if areas:
        recorte = recorte[recorte["area_geral"].isin(areas)]
    if municipios:
        recorte = recorte[recorte["municipio"].isin(municipios)]
    if busca.strip():
        recorte = recorte[
            recorte["curso"].str.contains(busca.strip(), case=False, na=False)
        ]

    st.caption(
        f"{fmt_int(len(recorte))} ofertas e {fmt_int(recorte['vagas_total'].sum())} vagas no recorte."
    )
    tabela = recorte[
        [
            "instituicao",
            "semestre",
            "curso",
            "area_geral",
            "campus",
            "turno",
            "municipio",
            "vagas_total",
        ]
    ].rename(
        columns={
            "instituicao": "Instituição",
            "semestre": "Semestre",
            "curso": "Curso",
            "area_geral": "Área",
            "campus": "Unidade",
            "turno": "Turno",
            "municipio": "Município",
            "vagas_total": "Vagas",
        }
    )
    st.dataframe(tabela, hide_index=True, width="stretch", height=460)

    st.download_button(
        "Baixar ofertas em CSV",
        data=recorte.to_csv(index=False).encode("utf-8-sig"),
        file_name="vagas_provao_paulista_2027.csv",
        mime="text/csv",
    )


def aba_metodo() -> None:
    section("Como o painel foi construído")

    st.markdown(
        """
        ### Fonte dos cadernos

        Os cadernos e os gabaritos oficiais foram baixados do site oficial do
        Provão Paulista Seriado, mantido pela Vunesp. Foram usadas as três
        edições disponíveis: 2023, 2024 e 2025, em todas as séries do ensino
        médio. O edital de 2026, que organiza o ingresso em 2027, foi lido da
        publicação oficial da Secretaria da Educação do Estado de São Paulo.

        ### Extração e conferência

        Cada caderno tem dois dias de aplicação e 90 itens. O texto foi extraído
        do PDF respeitando a ordem das colunas, porque os cadernos usam layout
        em duas colunas e a leitura linear embaralharia enunciados e
        alternativas. Os gabaritos foram vinculados item a item e conferidos
        contra os arquivos oficiais. O resultado fecha em **810 questões**,
        **90 por série em cada edição**, sem gabarito faltante.

        ### Classificação dos temas

        Os temas foram agrupados a partir do conteúdo programático do Anexo VII
        do edital. A classificação usa regras de palavras-chave no enunciado e,
        quando necessário, nas alternativas. Casos ambíguos foram revisados
        manualmente. Como toda classificação automática, os totais são uma
        aproximação: servem para orientar o estudo, não para substituir a
        leitura do programa oficial.

        ### Limitações

        - **27 questões** têm alternativas apenas em imagem. Elas permanecem no
          banco, com a página do caderno, mas não entram no simulado.
        - Em 2024 e 2025, Filosofia e Sociologia se alternam entre as séries;
          em 2023, as duas aparecem na mesma edição. A comparação por disciplina
          considera essa diferença.
        - As vagas de 2027 vêm dos quadros publicados. As 2.080 vagas da FATEC
          para o 2º semestre não estão detalhadas por curso no Anexo XII.
        - A UNIVESP oferece vagas no 2º semestre de 2027; as demais instituições,
          no 1º semestre.

        ### Reprodução

        ```bash
        python -m venv .venv
        .venv\\Scripts\\activate
        pip install -r requirements.txt
        streamlit run app.py
        ```

        Os dados processados ficam em `data/processed`. Para regerar as bases a
        partir dos PDFs e do edital, execute `scripts/build_dataset.py` e
        `scripts/build_vagas.py`.
        """
    )

    section("Links úteis")
    st.markdown(
        f"""
        - [Cadernos e gabaritos do Provão Paulista Seriado]({FONTE_EXAM})
        - [Edital 10/2026 e Anexos]({FONTE_EDITAL})
        - [Secretaria da Educação do Estado de São Paulo](https://www.educacao.sp.gov.br/)
        """
    )


def main() -> None:
    st.set_page_config(
        page_title="Provão em Foco",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    render_hero(
        kicker="Provão Paulista Seriado · 2023–2025",
        title="Provão em Foco",
        description=(
            "O que mais cai nas provas, como os temas se distribuem entre as séries "
            "e quais cursos oferecem vagas para o ingresso em 2027."
        ),
        source="Dados públicos da Vunesp e da Secretaria da Educação do Estado de São Paulo.",
    )

    q = _questoes()
    vagas = _vagas()

    abas = st.tabs(
        [
            "Panorama",
            "Temas",
            "Banco de questões",
            "Simulado",
            "Questões inéditas",
            "Vagas 2027",
            "Método e fontes",
        ]
    )
    with abas[0]:
        aba_panorama(q)
    with abas[1]:
        aba_temas(q)
    with abas[2]:
        aba_banco(q)
    with abas[3]:
        aba_simulado(q)
    with abas[4]:
        aba_ineditas()
    with abas[5]:
        aba_vagas(vagas)
    with abas[6]:
        aba_metodo()

    render_footer("Vunesp · Provão Paulista Seriado", FONTE_EXAM)


if __name__ == "__main__":
    main()

