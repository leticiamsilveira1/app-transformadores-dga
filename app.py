
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Monitoramento de Transformadores",
    page_icon="⚡",
    layout="wide"
)

# ============================================================
# CARREGA A BASE
# ============================================================
@st.cache_data
def carregar_base():
    df = pd.read_csv("/content/data/base_motor.csv")
    return df

df = carregar_base()

# ============================================================
# TÍTULO
# ============================================================
st.title("⚡ Monitoramento de Gases em Transformadores")
st.markdown("---")

# ============================================================
# SIDEBAR — FILTROS
# ============================================================
st.sidebar.header("Filtros")

# Filtro de Transformador
transformadores = sorted(df["ID do Transformador"].unique())
transformador_sel = st.sidebar.selectbox("Transformador", transformadores)

df_tr = df[df["ID do Transformador"] == transformador_sel]

# Filtro de Gás (dinâmico — vem do CSV)
gases_disponiveis = sorted(df_tr["gas"].unique())
gas_sel = st.sidebar.selectbox("Gás", ["(Todos)"] + gases_disponiveis)

if gas_sel != "(Todos)":
    df_filtrado = df_tr[df_tr["gas"] == gas_sel]
else:
    df_filtrado = df_tr

# ============================================================
# MÉTRICAS RESUMO
# ============================================================
st.subheader(f"Transformador: {transformador_sel}")

col1, col2, col3 = st.columns(3)

total = len(df_filtrado)
criticos  = (df_filtrado["classificacao_final"] == "Crítico").sum()
atencao   = (df_filtrado["classificacao_final"] == "Atenção").sum()
estaveis  = (df_filtrado["classificacao_final"] == "Estável").sum()

col1.metric("Total de Registros", total)
col2.metric("⚠️ Atenção",  int(atencao))
col3.metric("🔴 Crítico",  int(criticos))

st.markdown("---")

# ============================================================
# GRÁFICO — EVOLUÇÃO DO GÁS AO LONGO DO TEMPO
# ============================================================
st.subheader("Evolução dos Gases ao Longo do Tempo")

if gas_sel == "(Todos)":
    for gas in gases_disponiveis:
        df_gas = df_tr[df_tr["gas"] == gas].sort_values("Data de Amostragem")
        if df_gas.empty:
            continue

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_gas["Data de Amostragem"],
            y=df_gas["x"],
            mode="lines+markers",
            name=gas,
            line=dict(color="royalblue")
        ))

        if "ucl_x" in df_gas.columns:
            fig.add_trace(go.Scatter(
                x=df_gas["Data de Amostragem"],
                y=df_gas["ucl_x"],
                mode="lines",
                name="UCL",
                line=dict(color="red", dash="dash")
            ))
            fig.add_trace(go.Scatter(
                x=df_gas["Data de Amostragem"],
                y=df_gas["lcl_x"],
                mode="lines",
                name="LCL",
                line=dict(color="red", dash="dash")
            ))

        fig.update_layout(
            title=f"Gás: {gas}",
            xaxis_title="Data",
            yaxis_title="Concentração (ppm)",
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)

else:
    df_gas = df_filtrado.sort_values("Data de Amostragem")
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_gas["Data de Amostragem"],
        y=df_gas["x"],
        mode="lines+markers",
        name=gas_sel,
        line=dict(color="royalblue")
    ))

    if "ucl_x" in df_gas.columns:
        fig.add_trace(go.Scatter(
            x=df_gas["Data de Amostragem"],
            y=df_gas["ucl_x"],
            mode="lines",
            name="UCL",
            line=dict(color="red", dash="dash")
        ))
        fig.add_trace(go.Scatter(
            x=df_gas["Data de Amostragem"],
            y=df_gas["lcl_x"],
            mode="lines",
            name="LCL",
            line=dict(color="red", dash="dash")
        ))

    if "ewma" in df_gas.columns:
        fig.add_trace(go.Scatter(
            x=df_gas["Data de Amostragem"],
            y=df_gas["ewma"],
            mode="lines",
            name="EWMA",
            line=dict(color="orange", dash="dot")
        ))

    fig.update_layout(
        title=f"Gás: {gas_sel}",
        xaxis_title="Data",
        yaxis_title="Concentração (ppm)",
        height=450
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ============================================================
# CLASSIFICAÇÃO FINAL
# ============================================================
st.subheader("Classificação Final por Gás")

resumo = (
    df_tr.groupby(["gas", "classificacao_final"])
    .size()
    .reset_index(name="count")
)

fig_class = px.bar(
    resumo,
    x="gas",
    y="count",
    color="classificacao_final",
    color_discrete_map={
        "Estável": "green",
        "Atenção": "orange",
        "Crítico": "red"
    },
    barmode="group",
    title="Distribuição das Classificações por Gás",
    labels={"gas": "Gás", "count": "Quantidade", "classificacao_final": "Classificação"}
)
fig_class.update_layout(height=400)
st.plotly_chart(fig_class, use_container_width=True)

st.markdown("---")

# ============================================================
# TABELA DE DADOS
# ============================================================
st.subheader("Dados Detalhados")

colunas_exibir = [
    "ID do Transformador", "Data de Amostragem", "gas", "x",
    "classificacao_final", "prioridade_acao",
    "sinal_cep", "sinal_ewma", "sinal_cusum", "sinal_iec",
    "total_sinais", "classificacao_tendencia"
]

colunas_validas = [c for c in colunas_exibir if c in df_filtrado.columns]
st.dataframe(df_filtrado[colunas_validas].sort_values("Data de Amostragem"), use_container_width=True)
