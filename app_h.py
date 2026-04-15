import streamlit as st
from generator_h import (
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

# =========================
# GERAR SALDOS
# =========================
def gerar_saldos(df_mov, saldos_iniciais):
    df = df_mov.copy()

    # -------------------------
    # Normalização
    # -------------------------
    df = normalizar_colunas(df)

    df = df[df["data_liquidacao"].notnull() & (df["data_liquidacao"] != "")]

    # Converter valor
    df["valor"] = df["valor"].str.replace(",", ".").astype(float)

    # -------------------------
    # Agrupamento
    # -------------------------
    agrupado = df.groupby(
        ["cod_tesouraria", "data_liquidacao", "natureza"]
    )["valor"].sum().reset_index()

    # Pivot (E / S)
    pivot = agrupado.pivot_table(
        index=["cod_tesouraria", "data_liquidacao"],
        columns="natureza",
        values="valor",
        fill_value=0
    ).reset_index()

    pivot.columns.name = None

    # Garantir colunas
    if "E" not in pivot.columns:
        pivot["E"] = 0
    if "S" not in pivot.columns:
        pivot["S"] = 0

    pivot = pivot.rename(columns={
        "E": "total_entrada",
        "S": "total_saida"
    })

    # -------------------------
    # Ordenação
    # -------------------------
    pivot = pivot.sort_values(["cod_tesouraria", "data_liquidacao"])

    # -------------------------
    # Cálculo de saldo acumulado
    # -------------------------
    resultado = []

    for conta, grupo in pivot.groupby("cod_tesouraria"):

        saldo = saldos_iniciais.get(conta, 0)

        for _, row in grupo.iterrows():
            entrada = row["total_entrada"]
            saida = row["total_saida"]

            saldo = saldo + entrada - saida

            resultado.append({
                "SALDO_FINAL": round(saldo, 2),
                "TOTAL_ENTRADA": round(entrada, 2),
                "TOTAL_SAIDA": round(saida, 2),
                "DATA": row["data_liquidacao"],
                "COD_TESOURARIA": conta
            })

    return pd.DataFrame(resultado)
