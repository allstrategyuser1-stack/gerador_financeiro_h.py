import random
import uuid
from datetime import datetime, timedelta
import pandas as pd
import unicodedata


# =========================
# 🔧 NORMALIZAÇÃO
# =========================
def normalizar_texto(texto):
    return unicodedata.normalize("NFKD", str(texto))\
        .encode("ASCII", "ignore")\
        .decode()\
        .lower()\
        .strip()


def normalizar_colunas(df):
    df.columns = [normalizar_texto(col) for col in df.columns]
    return df


# =========================
# 📥 UNIDADES
# =========================
def carregar_unidades(file):

    df = pd.read_excel(file, dtype=str) if file.name.endswith("xlsx") else pd.read_csv(file, dtype=str)
    df = normalizar_colunas(df)

    col_codigo = next((c for c in df.columns if "codigo" in c), None)
    col_nome = next((c for c in df.columns if "nome" in c), None)
    col_analitico = next((c for c in df.columns if "analitico" in c), None)

    if not col_codigo:
        raise ValueError("Código não encontrado.")

    if col_analitico:
        df = df[df[col_analitico].str.upper() == "A"]

    df = df[df[col_codigo].notnull()]
    df[col_codigo] = df[col_codigo].astype(str).str.strip()

    return {
        "cod_unidade": df[col_codigo].unique().tolist(),
        "preview": df[[col_codigo, col_nome]].rename(columns={col_codigo: "Código", col_nome: "Nome"})
    }


# =========================
# 📥 CENTRO DE CUSTO
# =========================
def carregar_centro_custo(file):

    df = pd.read_excel(file, dtype=str) if file.name.endswith("xlsx") else pd.read_csv(file, dtype=str)
    df = normalizar_colunas(df)

    if not any("codigo" in c for c in df.columns):
        file.seek(0)
        df = pd.read_excel(file, dtype=str, skiprows=1)
        df = normalizar_colunas(df)

    col_codigo = next((c for c in df.columns if "codigo" in c), None)
    col_nome = next((
        c for c in df.columns
        if "nome centro de custo externo" in c
        or "centro de custo externo" in c
        or "nome" in c
    ), None)

    df = df[df[col_codigo].notnull()]
    df[col_codigo] = df[col_codigo].astype(str).str.strip()

    return {
        "cod_centro_custo": df[col_codigo].unique().tolist(),
        "preview": df[[col_codigo, col_nome]].rename(columns={col_codigo: "Código", col_nome: "Centro de custo externo"})
    }


# =========================
# 📥 TESOURARIA (CONTAS BANCÁRIAS)
# =========================
def carregar_tesouraria(file):

    try:
        df = pd.read_excel(file, dtype=str)
    except:
        file.seek(0)
        df = pd.read_csv(file, dtype=str)

    df = normalizar_colunas(df)

    # Cabeçalho duplo → ignora primeira linha
    if not any("codigo" in c for c in df.columns):
        file.seek(0)
        df = pd.read_excel(file, dtype=str, skiprows=1)
        df = normalizar_colunas(df)

    # Detectar colunas
    colunas_codigo = [c for c in df.columns if "codigo" in c]
    if not colunas_codigo:
        raise ValueError("Coluna de Código não encontrada.")
    col_codigo = colunas_codigo[-1]

    col_nome = next((
        c for c in df.columns
        if "nome conta externa" in c
        or "conta externa" in c
        or "nome" in c
    ), None)

    if not col_codigo:
        raise ValueError("Coluna de Código não encontrada.")

    if not col_nome:
        df["nome"] = ""
        col_nome = "nome"

    # Limpeza
    df = df[df[col_codigo].notnull()]
    df[col_codigo] = df[col_codigo].astype(str).str.strip()

    if df.empty:
        raise ValueError("Nenhuma conta bancária válida encontrada.")

    return {
        "cod_tesouraria": df[col_codigo].unique().tolist(),
        "preview": df[[col_codigo, col_nome]].rename(
            columns={
                col_codigo: "Código",
                col_nome: "Conta bancária"
            }
        )
    }


# =========================
# 📥 CLASSIFICAÇÃO
# =========================
def carregar_classificacao(estrutura_file, externo_file):

    # -------- estrutura --------
    df_est = pd.read_excel(estrutura_file, dtype=str)
    df_est = normalizar_colunas(df_est)

    col_est = next((c for c in df_est.columns if "estrutura" in c), None)
    col_nat = next((c for c in df_est.columns if "natureza" in c), None)
    col_ana = next((c for c in df_est.columns if "analitico" in c), None)

    df_est = df_est[df_est[col_ana].str.upper() == "A"]

    mapa = dict(zip(df_est[col_est], df_est[col_nat].str.upper()))

    # -------- externo --------
    df_ext = pd.read_excel(externo_file, dtype=str)
    df_ext = normalizar_colunas(df_ext)

    if not any("codigo" in c for c in df_ext.columns):
        externo_file.seek(0)
        df_ext = pd.read_excel(externo_file, dtype=str, skiprows=1)
        df_ext = normalizar_colunas(df_ext)

    col_est_ext = next((c for c in df_ext.columns if "estrutura" in c), None)
    col_codigo = next((c for c in df_ext.columns if "codigo" in c), None)
    col_nome = next((c for c in df_ext.columns if "nome" in c), None)

    resultado = {"E": [], "S": []}
    preview = []

    for _, row in df_ext.iterrows():
        estrutura = str(row[col_est_ext]).strip()
        codigo = str(row[col_codigo]).strip()
        nome = str(row[col_nome]).strip() if col_nome else ""

        natureza = mapa.get(estrutura)

        if natureza in ["E", "S"]:
            resultado[natureza].append(codigo)
            preview.append({
                "Código": codigo,
                "Nome": nome,
                "Natureza": natureza
            })

    return {
        "classificacoes": resultado,
        "preview": pd.DataFrame(preview)
    }


# =========================
# 🚀 GERAÇÃO
# =========================
def gerar_movimentacoes(qtd, decimais, data_inicio_liq, data_fim_liq, params=None):

    dados = []

    hoje = datetime.now()
    inicio_base = hoje - timedelta(days=365)

    inicio_liq = datetime.combine(data_inicio_liq, datetime.min.time())
    fim_liq = datetime.combine(data_fim_liq, datetime.min.time())

    if fim_liq > hoje:
        fim_liq = hoje

    for i in range(qtd):

        # -------------------------
        # Natureza
        # -------------------------
        natureza = random.choice(["E", "S"])

        # -------------------------
        # Valor
        # -------------------------
        valor_float = round(random.uniform(1, 100000), decimais)
        valor = f"{valor_float:.{decimais}f}".replace(".", ",")

        # -------------------------
        # Datas
        # -------------------------
        data_emissao = inicio_base + timedelta(days=random.randint(0, 365))
        data_vencimento = data_emissao + timedelta(days=random.randint(1, 60))

        if random.random() < 0.5:
            data_liquidacao = None
        else:
            data_liquidacao = inicio_liq + timedelta(
                days=random.randint(0, (fim_liq - inicio_liq).days)
            )

        # Ajustes de consistência
        if data_emissao > data_vencimento:
            data_emissao = data_vencimento

        if data_liquidacao and data_emissao > data_liquidacao:
            data_emissao = data_liquidacao

        data_inclusao = hoje

        # -------------------------
        # Unidade
        # -------------------------
        cod_unidade = (
            random.choice(params["cod_unidade"])
            if params and "cod_unidade" in params
            else ""
        )

        # -------------------------
        # Centro de custo
        # -------------------------
        cod_centro_custo = (
            random.choice(params["cod_centro_custo"])
            if params and "cod_centro_custo" in params
            else ""
        )

        # -------------------------
        # Tesouraria
        # -------------------------
        cod_tesouraria = (
            random.choice(params["cod_tesouraria"])
            if params and "cod_tesouraria" in params
            else ""
        )

        # -------------------------
        # Classificação
        # -------------------------
        if params and "classificacoes" in params:
            lista = params["classificacoes"].get(natureza, [])
            cod_classificacao = random.choice(lista) if lista else ""
        else:
            cod_classificacao = ""

        # -------------------------
        # Cliente / fornecedor
        # -------------------------
        if random.random() < 0.15:
            cod_cliente_fornec = f"CF{random.randint(1,5)}"
        else:
            if natureza == "E":
                cod_cliente_fornec = f"C{random.randint(1,50)}"
            else:
                cod_cliente_fornec = f"F{random.randint(1,50)}"

        # -------------------------
        # doc_edit
        # -------------------------
        if data_vencimento > hoje and not data_liquidacao:
            doc_edit = "S"
        else:
            doc_edit = "N"

        # -------------------------
        # REGISTRO COMPLETO
        # -------------------------
        registro = {
            "documento": f"DOC-{1000+i}",
            "natureza": natureza,
            "valor": valor,

            "cod_unidade": cod_unidade,
            "cod_centro_de_custo": cod_centro_custo,
            "cod_tesouraria": cod_tesouraria,
            "cod_tipo_de_documento": "",
            "cod_classificacao_financeira": cod_classificacao,
            "cod_projeto": "",

            "prev_s_doc": "N",
            "suspenso": "N",
            "pend_aprov": "N",

            "data_vencimento": data_vencimento.strftime("%Y-%m-%d"),
            "data_liquidacao": data_liquidacao.strftime("%Y-%m-%d") if data_liquidacao else "",
            "data_inclusao": data_inclusao.strftime("%Y-%m-%d"),

            "erp_origem": "STREAMLIT",
            "erp_uuid": str(uuid.uuid4()),

            "data_emissao": data_emissao.strftime("%Y-%m-%d"),

            "historico": f"Lancamento {'entrada' if natureza == 'E' else 'saida'} gerado automaticamente",

            "cod_cliente_fornec": cod_cliente_fornec,
            "doc_edit": doc_edit
        }

        dados.append(registro)

    return pd.DataFrame(dados)
