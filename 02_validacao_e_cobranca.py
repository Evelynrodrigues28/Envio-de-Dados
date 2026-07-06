"""
02_validacao_e_cobranca.py
==========================
Executa a validacao dos dados de sell-out e identifica distribuidores em atraso.
Gera os payloads de e-mail de cobranca prontos para envio.

Pre-requisitos:
  - Executar '01_setup_dados_simulados.py' antes
  - Python 3.8+
  - Pacotes: pandas, openpyxl  (pip install -r requirements.txt)
  - Databricks (opcional): Runtime 13.x+ com Unity Catalog

Uso:
  Funciona em Databricks, VSCode, terminal ou qualquer ambiente Python padrao.
  Gera o arquivo de payloads em TMP_DIR/payloads_cobranca.json
"""

import pandas as pd
from pandas.tseries.offsets import BDay
from datetime import date
import json
import os
import tempfile

# =============================================================================
# CONFIGURACOES — devem ser as mesmas do script 01
# =============================================================================
CATALOG = "catalog_exemplo"
SCHEMA  = "sell_out"
TABELA  = "fato_sellout"

TMP_DIR              = tempfile.gettempdir()
CAMINHO_CONFIG       = os.path.join(TMP_DIR, "config_distribuidores.xlsx")
CAMINHO_LOCAL_TABELA = os.path.join(TMP_DIR, "fato_sellout.csv")       # fallback local
CAMINHO_PAYLOADS     = os.path.join(TMP_DIR, "payloads_cobranca.json")

SLA_DIAS_UTEIS = 3
EXCECOES_D3    = ["D07", "D08"]
MODO           = "Teste"
EMAIL_TESTE    = "analista.teste@empresa.com"

# ---------------------------------------------------------------------------
# Deteccao de ambiente
# ---------------------------------------------------------------------------
def _get_spark():
    """Retorna SparkSession se disponivel, senao None."""
    try:
        from pyspark.sql import SparkSession
        return SparkSession.builder.getOrCreate()
    except Exception:
        return None

spark      = _get_spark()
USAR_SPARK = spark is not None
print(f"Ambiente detectado: {'Databricks / PySpark' if USAR_SPARK else 'Local (pandas — sem Spark)'}")
print()

# =============================================================================
# PASSO 1: Carregar planilha de configuracao
# =============================================================================
print("=" * 60)
print("PASSO 1: Carregando planilha de configuracao...")
print("=" * 60)

df_config = pd.read_excel(CAMINHO_CONFIG, sheet_name="Distribuidores")
print(f"OK {len(df_config)} distribuidores carregados da planilha")

lista_ids = df_config["ID"].tolist()
print(f"   -> IDs: {lista_ids}")
print()

# =============================================================================
# PASSO 2: Consultar dados de sell-out (Unity Catalog ou CSV local)
# =============================================================================
print("=" * 60)
print("PASSO 2: Consultando dados de sell-out...")
print("=" * 60)

if USAR_SPARK:
    ids_sql = ", ".join([f"'{i}'" for i in lista_ids])
    query = f"""
    SELECT
        distribuidor_id AS ID,
        cnpj,
        MAX(data_nota_fiscal) AS ultima_nota_fiscal,
        MAX(data_arquivo)     AS ultimo_arquivo,
        SUM(quantidade_linhas) AS total_linhas
    FROM {CATALOG}.{SCHEMA}.{TABELA}
    WHERE distribuidor_id IN ({ids_sql})
    GROUP BY distribuidor_id, cnpj
    ORDER BY ultimo_arquivo ASC
    """
    df_sellout = spark.sql(query).toPandas()
    print(f"OK Fonte: Unity Catalog ({CATALOG}.{SCHEMA}.{TABELA})")
else:
    # Local: ler do CSV gerado pelo script 01
    df_raw = pd.read_csv(CAMINHO_LOCAL_TABELA, parse_dates=["data_nota_fiscal", "data_arquivo"])
    df_sellout = (
        df_raw[df_raw["distribuidor_id"].isin(lista_ids)]
        .groupby(["distribuidor_id", "cnpj"], as_index=False)
        .agg(
            ultima_nota_fiscal=("data_nota_fiscal", "max"),
            ultimo_arquivo=("data_arquivo", "max"),
            total_linhas=("quantidade_linhas", "sum"),
        )
        .rename(columns={"distribuidor_id": "ID"})
        .sort_values("ultimo_arquivo")
    )
    print(f"OK Fonte: arquivo local ({CAMINHO_LOCAL_TABELA})")

print(f"   -> {len(df_sellout)} distribuidores encontrados")
print()

# Merge com dados da config (para ter e-mails e nomes)
df = df_config.merge(df_sellout, on="ID", how="left")
df["data da ultima nota fiscal"] = pd.to_datetime(df["ultima_nota_fiscal"]).dt.strftime("%d/%m/%Y")
df["Data ultimo arquivo"]        = pd.to_datetime(df["ultimo_arquivo"]).dt.strftime("%d/%m/%Y")
df["Quantidade de linhas"]       = df["total_linhas"].fillna(0).astype(int)

print("Tabela consolidada:")
print("-" * 100)
colunas_exibir = ["ID", "DISTRIBUIDOR", "data da ultima nota fiscal", "Data ultimo arquivo", "Quantidade de linhas"]
print(df[colunas_exibir].to_string(index=False))
print()

# =============================================================================
# PASSO 3: Detectar distribuidores em atraso
# =============================================================================
print("=" * 60)
print("PASSO 3: Detectando distribuidores em atraso...")
print("=" * 60)

data_referencia = pd.Timestamp(date.today())
data_corte      = data_referencia - BDay(SLA_DIAS_UTEIS)

print(f"Data de referencia: {data_referencia.strftime('%d/%m/%Y')} ({data_referencia.strftime('%A')})")
print(f"SLA: {SLA_DIAS_UTEIS} dias uteis -> corte em {data_corte.strftime('%d/%m/%Y')}")
print()

df["ultimo_arquivo_dt"] = pd.to_datetime(df["ultimo_arquivo"])

df_atrasados = df[
    (df["ultimo_arquivo_dt"] < data_corte) &
    (~df["ID"].isin(EXCECOES_D3))
].copy()

df_atrasados["dias_atraso"] = df_atrasados["ultimo_arquivo_dt"].apply(
    lambda x: len(pd.bdate_range(x, data_referencia)) - 1 if pd.notna(x) else None
)

print(f"OK Distribuidores em dia:    {len(df) - len(df_atrasados)}")
print(f"   Distribuidores em atraso: {len(df_atrasados)}")
print()

if len(df_atrasados) > 0:
    print("Distribuidores em atraso:")
    print("-" * 80)
    cols_atraso = ["ID", "DISTRIBUIDOR", "Data ultimo arquivo", "dias_atraso"]
    print(df_atrasados[cols_atraso].to_string(index=False))
    print()

# =============================================================================
# PASSO 4: Gerar payloads de e-mail
# =============================================================================
print("=" * 60)
print("PASSO 4: Gerando payloads de e-mail...")
print("=" * 60)

payloads = []

for _, row in df_atrasados.iterrows():
    email_dtr   = str(row["EMAIL DTR"]).strip()
    email_mars  = str(row["EMAIL MARS"]).strip()
    email_extra = str(row["EMAIL EXTRA"]).strip()

    if email_dtr in ["0", "nan", "", "None"]:
        destinatario = email_mars
        cc = ""
    else:
        destinatario = email_dtr
        cc = email_mars

    if email_extra not in ["0", "nan", "", "None"]:
        cc = f"{cc};{email_extra}" if cc else email_extra

    if MODO == "Teste":
        destinatario_final = EMAIL_TESTE
        cc_final = ""
    else:
        destinatario_final = destinatario
        cc_final = cc

    periodo_inicio = row["ultimo_arquivo_dt"] + pd.Timedelta(days=1)
    periodo_fim    = data_referencia

    corpo = f"""Prezado(a),

Identificamos que os dados de sell-out de {row['DISTRIBUIDOR']} nao foram recebidos desde {row['Data ultimo arquivo']}.

Solicitamos o envio retroativo dos dados referentes ao periodo de {periodo_inicio.strftime('%d/%m/%Y')} a {periodo_fim.strftime('%d/%m/%Y')}.

Caso ja tenha enviado, por favor desconsidere esta mensagem.

Atenciosamente,
Equipe de Inteligencia de Vendas"""

    payload = {
        "to": destinatario_final,
        "cc": cc_final,
        "subject": f"Dados Pendentes - {row['DISTRIBUIDOR']}",
        "body": corpo,
        "importance": "high",
        "_metadata": {
            "distribuidor_id": row["ID"],
            "destinatario_original": destinatario,
            "cc_original": cc,
            "modo": MODO,
            "dias_atraso": int(row["dias_atraso"]) if pd.notna(row["dias_atraso"]) else None
        }
    }
    payloads.append(payload)

with open(CAMINHO_PAYLOADS, "w", encoding="utf-8") as f:
    json.dump(payloads, f, ensure_ascii=False, indent=2)

print(f"OK {len(payloads)} payloads gerados")
print(f"   Salvos em: {CAMINHO_PAYLOADS}")
print(f"   Modo: {MODO}")
if MODO == "Teste":
    print(f"   -> Todos os e-mails redirecionados para: {EMAIL_TESTE}")
print()

if payloads:
    print("Exemplo de payload gerado:")
    print("-" * 60)
    exemplo = {k: v for k, v in payloads[0].items() if k != "_metadata"}
    print(json.dumps(exemplo, ensure_ascii=False, indent=2))
    print()

print("=" * 60)
print("RESUMO DA EXECUCAO")
print("=" * 60)
print(f"""
  Distribuidores monitorados:  {len(df)}
  Distribuidores em dia:       {len(df) - len(df_atrasados)}
  Distribuidores em atraso:    {len(df_atrasados)}
  Excecoes (D+3):              {len(EXCECOES_D3)} {EXCECOES_D3}
  Payloads gerados:            {len(payloads)}
  Modo de envio:               {MODO}
""")
