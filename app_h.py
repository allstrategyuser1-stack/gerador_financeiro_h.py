import streamlit as st
from generator import gerar_movimentacoes
from datetime import date

# Configuração da página
st.set_page_config(
    page_title="Gerador Financeiro",
    layout="wide"
)

# Estilo opcional
st.markdown("""
<style>
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 8px;
        height: 3em;
        font-size: 16px;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 Gerador de Movimentações Financeiras")

# =========================
# ⚙️ PARÂMETROS
# =========================
st.markdown("## ⚙️ Parâmetros")

col1, col2 = st.columns(2)

with col1:
    qtd = st.number_input(
        "Quantidade de registros",
        min_value=1,
        max_value=100000,
        value=100,
        step=100
    )

with col2:
    decimais = st.slider(
        "Casas decimais do valor",
        min_value=2,
        max_value=6,
        value=2
    )

# =========================
# 📅 INTERVALO DE LIQUIDAÇÃO
# =========================
st.markdown("## 📅 Intervalo de Liquidação")

data_inicio, data_fim = st.date_input(
    "Selecione o período de liquidação",
    value=(date.today().replace(day=1), date.today())
)

st.info("Este intervalo afeta apenas o campo data_liquidacao. As demais datas não são impactadas.")

# Validação
if data_inicio > data_fim:
    st.error("A data inicial não pode ser maior que a data final.")
    st.stop()

# =========================
# 🚀 AÇÃO
# =========================
st.markdown("## 🚀 Gerar Dados")

gerar = st.button("Gerar CSV", use_container_width=True)

# =========================
# 📤 RESULTADO
# =========================
if gerar:

    with st.spinner("Gerando dados..."):
        df = gerar_movimentacoes(qtd, decimais, data_inicio, data_fim)

    st.success("Arquivo gerado com sucesso!")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 🔍 Pré-visualização")
        st.dataframe(df.head(20), use_container_width=True)

    with col2:
        st.markdown("### 📥 Download")
        csv = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="⬇️ Baixar CSV",
            data=csv,
            file_name="movimentacoes.csv",
            mime="text/csv",
            use_container_width=True
        )
