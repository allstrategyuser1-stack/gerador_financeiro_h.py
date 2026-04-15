import streamlit as st
from generator import (
    gerar_movimentacoes,
    carregar_unidades,
    carregar_centro_custo,
    carregar_classificacao,
    carregar_tesouraria
)
from datetime import date

st.title("Gerador de Movimentações Financeiras")

params = {}

# =========================
# UNIDADES
# =========================
st.header("Unidades")
file_un = st.file_uploader("", key="upload_un")
if file_un:
    r = carregar_unidades(file_un)
    params["cod_unidade"] = r["cod_unidade"]
    st.dataframe(r["preview"])

# =========================
# CENTRO DE CUSTO
# =========================
st.header("Centro de Custo")
file_cc = st.file_uploader("", key="upload_cc")
if file_cc:
    r = carregar_centro_custo(file_cc)
    params["cod_centro_custo"] = r["cod_centro_custo"]
    st.dataframe(r["preview"])

# =========================
# TESOURARIA
# =========================
st.header("Tesouraria (Contas Bancárias)")
file_tes = st.file_uploader("", key="upload_tesouraria")
if file_tes:
    try:
        r = carregar_tesouraria(file_tes)
        params["cod_tesouraria"] = r["cod_tesouraria"]
        st.success("Contas bancárias carregadas com sucesso!")
        st.dataframe(r["preview"])
    except Exception as e:
        st.error(f"Erro tesouraria: {e}")
        st.stop()

# =========================
# CLASSIFICAÇÃO
# =========================
st.header("Classificação Financeira")

file_est = st.file_uploader("Estrutura")
file_ext = st.file_uploader("Externo")

if file_est and file_ext:
    r = carregar_classificacao(file_est, file_ext)
    params["classificacoes"] = r["classificacoes"]
    st.dataframe(r["preview"])

# =========================
# PARÂMETROS
# =========================
qtd = st.number_input("Quantidade de documentos desejada", 1, 10000, 20)
dec = st.slider("Quantidade de casas decimais no valor", 2, 6, 2)

data_ini, data_fim = st.date_input(
    "Período liquidação",
    value=(date.today().replace(day=1), date.today())
)

# =========================
# GERAR
# =========================
if st.button("Gerar CSV"):
    df = gerar_movimentacoes(qtd, dec, data_ini, data_fim, params)
    st.dataframe(df.head())

    st.download_button(
        "Baixar CSV",
        df.to_csv(index=False).encode(),
        "movimentacoes.csv"
    )
