import streamlit as st
from generator_h import (
    gerar_movimentacoes,
    gerar_saldos,
    carregar_unidades,
    carregar_centro_custo,
    carregar_classificacao,
    carregar_tesouraria
)
from datetime import date

def formatar_valor(x):
    try:
        return f"{float(str(x).replace(',', '.')):.2f}".replace(".", ",")
    except:
        return ""

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

file_est = st.file_uploader("Estrutura", key="estrutura_cf")
file_ext = st.file_uploader("Externo", key="externo_cf")

if file_est and file_ext:
    r = carregar_classificacao(file_est, file_ext)
    params["classificacoes"] = r["classificacoes"]
    st.dataframe(r["preview"])

# =========================
# PARÂMETROS
# =========================
# QUANTIDADE DE DOCUMENTOS
qtd = st.number_input("Quantidade de documentos desejada", 1, 10000, 20)

# QUANTIDADE DE CASAS DECIMAIS NO VALOR
dec = st.slider("Quantidade de casas decimais no valor", 2, 6, 2)

# SELEÇÃO DE PERÍODO
datas = st.date_input(
    "Período liquidação",
    value=(date.today().replace(day=1), date.today())
)

if isinstance(datas, tuple):
    data_ini, data_fim = datas
else:
    data_ini = data_fim = datas

# FLAG SE GERA CSV DE SALDOS OU NÃO
gerar_saldos_flag = st.checkbox("Gerar CSV de Saldos")

# CAMPO PARA PREENCHER SALDOS INICIAIS DAS CONTAS
saldos_iniciais = {}

if gerar_saldos_flag and "cod_tesouraria" in params:
    st.subheader("Saldo inicial por conta")

    for conta in params["cod_tesouraria"]:
        saldo = st.number_input(
            f"Saldo inicial - Conta {conta}",
            value=0.0,
            step=100.0,
            key=f"saldo_{conta}"
        )
        saldos_iniciais[conta] = saldo

# =========================
# MOVIMENTAÇÕES
# =========================
if "df" in st.session_state:

    df = st.session_state["df"]

    st.subheader("Prévia Movimentações")

    df_preview = df.copy()

    if "valor" in df_preview.columns:
        df_preview["valor"] = (
            df_preview["valor"]
            .astype(str)
            .map(formatar_valor)
        )

    st.dataframe(df_preview.head())

    st.download_button(
        "Baixar CSV Movimentações",
        df.to_csv(index=False, sep=";", decimal=",").encode(),
        "movimentacoes.csv",
        key="download_mov"
    )

# =========================
# SALDOS
# =========================
if gerar_saldos_flag and "df_saldos" in st.session_state:

    df_saldos = st.session_state["df_saldos"]

    st.subheader("Prévia Saldos")

    df_saldos_preview = df_saldos.copy()

    for col in ["SALDO_FINAL", "TOTAL_ENTRADA", "TOTAL_SAIDA"]:
        if col in df_saldos_preview.columns:
            df_saldos_preview[col] = (
                df_saldos_preview[col]
                .astype(str)
                .map(formatar_valor)
            )

    st.dataframe(df_saldos_preview.head())

    st.download_button(
        "Baixar CSV Saldos",
        df_saldos.to_csv(index=False, sep=";", decimal=",").encode(),
        "saldos.csv",
        key="download_saldos"
    )

# =========================
# GERAR
# =========================
if st.button("Gerar CSV"):

    # LIMPA ESTADO ANTIGO
    st.session_state.pop("df", None)
    st.session_state.pop("df_saldos", None)

    df = gerar_movimentacoes(qtd, dec, data_ini, data_fim, params)
    st.session_state["df"] = df

    if gerar_saldos_flag:

        if not saldos_iniciais:
            st.error("Preencha os saldos iniciais.")
            st.stop()

        df_saldos = gerar_saldos(df, saldos_iniciais)
        st.session_state["df_saldos"] = df_saldos
    st.rerun()

    # PREVIEW CORRETO
    df_preview = df.copy()

    if "valor" in df_preview.columns:
        df_preview["valor"] = (
            df_preview["valor"]
            .astype(str)
            .map(formatar_valor)
        )

    st.subheader("Prévia Movimentações")
    st.dataframe(df_preview.head())

    st.download_button(
        "Baixar CSV Movimentações",
        df.to_csv(index=False, sep=";", decimal=",").encode(),
        "movimentacoes.csv"
    )
