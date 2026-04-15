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


# =========================
# FORMATADOR
# =========================
def formatar_valor(x):
    if x is None or x == "":
        return ""
    try:
        return f"{float(x):.2f}".replace(".", ",")
    except Exception:
        return ""


# =========================
# CONFIG INICIAL
# =========================
st.set_page_config(page_title="Gerador Financeiro", layout="wide")
st.title("Gerador de Movimentações Financeiras")

params = {}
saldos_iniciais = {}


# =========================
# FUNÇÕES AUXILIARES UI
# =========================
def upload_bloco(titulo, key, loader_fn, param_key, sucesso_msg=None):
    st.header(titulo)
    file = st.file_uploader("", key=key)

    if file:
        r = loader_fn(file)
        params[param_key] = r[param_key]
        if sucesso_msg:
            st.success(sucesso_msg)
        st.dataframe(r["preview"])
        return True
    return False


# =========================
# UPLOADS
# =========================
with st.expander("Cadastros (Arquivos Base)", expanded=True):

    upload_bloco("Unidades", "upload_un", carregar_unidades, "cod_unidade")

    upload_bloco("Centro de Custo", "upload_cc", carregar_centro_custo, "cod_centro_custo")

    upload_bloco(
        "Tesouraria (Contas Bancárias)",
        "upload_tesouraria",
        carregar_tesouraria,
        "cod_tesouraria",
        "Contas bancárias carregadas com sucesso!"
    )

    st.header("Classificação Financeira")

    file_est = st.file_uploader("Estrutura", key="estrutura_cf")
    file_ext = st.file_uploader("Externo", key="externo_cf")

    if file_est and file_ext:
        r = carregar_classificacao(file_est, file_ext)
        params["classificacoes"] = r["classificacoes"]
        st.dataframe(r["preview"])

st.divider()
# =========================
# PARÂMETROS
# =========================
with st.expander("Parâmetros de Geração", expanded=True):

    col1, col2, col3 = st.columns(3)

    with col1:
        qtd = st.number_input(
            "Qtd. documentos",
            min_value=1,
            max_value=10000,
            value=20
        )

        with col2:
        qtd = st.number_input(
            "Casas decimais",
            min_value=2,
            max_value=6,
            value=2
        )

    with col3:
        datas = st.date_input(
            "Período liquidação",
            value=(date.today().replace(day=1), date.today())
        )

    if isinstance(datas, tuple):
        data_ini, data_fim = datas
    else:
        data_ini = data_fim = datas

    gerar_saldos_flag = st.checkbox("Gerar CSV de Saldos")

    if gerar_saldos_flag and "cod_tesouraria" in params:
        st.subheader("Saldos iniciais por conta")

        for conta in params["cod_tesouraria"]:
            saldos_iniciais[conta] = st.number_input(
                f"Conta {conta}",
                value=0.0,
                step=100.0,
                key=f"saldo_{conta}"
            )

st.divider()

# =========================
# RESULTADOS - MOVIMENTAÇÕES
# =========================
def exibir_movimentacoes(df):
    st.subheader("Movimentações")

    df_preview = df.copy()

    if "valor" in df_preview.columns:
        df_preview["valor"] = df_preview["valor"].astype(str).map(formatar_valor)

    st.dataframe(df_preview.head())

    st.download_button(
        "Baixar Movimentações",
        df.to_csv(index=False, sep=";", decimal=",").encode(),
        "movimentacoes.csv"
    )


# =========================
# RESULTADOS - SALDOS
# =========================
def exibir_saldos(df_saldos):
    st.subheader("Saldos")

    df_preview = df_saldos.copy()

    for col in ["saldo_final", "total_entrada", "total_saida"]:
        if col in df_preview.columns:
            df_preview[col] = df_preview[col].astype(str).map(formatar_valor)

    st.dataframe(df_preview.head())

    st.download_button(
        "Baixar Saldos",
        df_saldos.to_csv(index=False, sep=";", decimal=",").encode(),
        "saldos.csv"
    )


# =========================
# GERAR
# =========================
if st.button("🚀 Gerar CSV"):

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

    exibir_movimentacoes(df)

    if gerar_saldos_flag:
        exibir_saldos(df_saldos)

    st.rerun()


# =========================
# VISUALIZAÇÃO PÓS-GERAÇÃO
# =========================
if "df" in st.session_state:
    exibir_movimentacoes(st.session_state["df"])

if gerar_saldos_flag and "df_saldos" in st.session_state:
    exibir_saldos(st.session_state["df_saldos"])
