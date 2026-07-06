"""
01_setup_dados_simulados.py
===========================
Gera os dados simulados necessarios para reproduzir o processo de validacao de Blob.

Executa:
  1. Cria a planilha Excel de configuracao com dados ficticios (config_distribuidores.xlsx)
  2. Cria a tabela simulada de sell-out:
       - Databricks : salva como tabela gerenciada no Unity Catalog via Spark
       - Local/VSCode: salva como arquivo CSV em TMP_DIR (sem dependencia de Spark)

Pre-requisitos:
  - Python 3.8+
  - Pacotes: pandas, openpyxl  (pip install -r requirements.txt)
  - Databricks (opcional): Runtime 13.x+ com Unity Catalog e permissao CREATE TABLE

Uso:
  Execute este script UMA VEZ para preparar o ambiente de simulacao.
  Funciona em Databricks, VSCode, terminal ou qualquer ambiente Python padrao.
"""

import pandas as pd
from datetime import date, timedelta
import random
import os
import tempfile

# =============================================================================
# CONFIGURACOES — altere conforme seu ambiente
# =============================================================================
CATALOG = "catalog_exemplo"          # Altere para seu catalog (apenas Databricks)
SCHEMA  = "sell_out"                 # Altere para seu schema  (apenas Databricks)
TABELA  = "fato_sellout"            # Nome da tabela simulada (apenas Databricks)

TMP_DIR               = tempfile.gettempdir()   # /tmp no Linux/Mac; %TEMP% no Windows
CAMINHO_CONFIG        = os.path.join(TMP_DIR, "config_distribuidores.xlsx")
CAMINHO_LOCAL_TABELA  = os.path.join(TMP_DIR, "fato_sellout.csv")      # fallback local

# ---------------------------------------------------------------------------
# Deteccao de ambiente: tenta obter SparkSession (Databricks/PySpark instalado)
# ---------------------------------------------------------------------------
def _get_spark():
    """Retorna SparkSession se disponivel, senao None."""
    try:
        from pyspark.sql import SparkSession
        return SparkSession.builder.getOrCreate()
    except Exception:
        return None

spark    = _get_spark()
USAR_SPARK = spark is not None
print(f"Ambiente detectado: {'Databricks / PySpark' if USAR_SPARK else 'Local (pandas — sem Spark)'}")
print()

# =============================================================================
# DADOS FICTICIOS DOS DISTRIBUIDORES
# =============================================================================
distribuidores = [
    {"Owner": "Ana Costa",      "ID": "D01", "DISTRIBUIDOR": "DISTRIBUIDORA ALPHA LTDA",  "CNPJ": "12345678000101", "BASE CODE": "alpha_dist",   "SAS KEY": "ref_001", "Completo": "Sim", "EMAIL DTR": "contato@alpha-dist.com.br",     "EMAIL MARS": "analista1@empresa.com", "EMAIL EXTRA": "0"},
    {"Owner": "Carlos Lima",    "ID": "D02", "DISTRIBUIDOR": "COMERCIAL BETA S.A.",        "CNPJ": "23456789000102", "BASE CODE": "beta_com",      "SAS KEY": "ref_002", "Completo": "Sim", "EMAIL DTR": "vendas@beta-com.com.br",        "EMAIL MARS": "analista2@empresa.com", "EMAIL EXTRA": "nan"},
    {"Owner": "Maria Souza",    "ID": "D03", "DISTRIBUIDOR": "GAMMA LOGISTICA LTDA",       "CNPJ": "34567890000103", "BASE CODE": "gamma_log",     "SAS KEY": "ref_003", "Completo": "Sim", "EMAIL DTR": "dados@gamma-log.com.br",        "EMAIL MARS": "analista1@empresa.com", "EMAIL EXTRA": "gestor@gamma-log.com.br"},
    {"Owner": "Pedro Alves",    "ID": "D04", "DISTRIBUIDOR": "DELTA DISTRIBUIDORA LTDA",   "CNPJ": "45678901000104", "BASE CODE": "delta_dist",    "SAS KEY": "ref_004", "Completo": "Sim", "EMAIL DTR": "0",                            "EMAIL MARS": "analista3@empresa.com", "EMAIL EXTRA": "0"},
    {"Owner": "Julia Santos",   "ID": "D05", "DISTRIBUIDOR": "EPSILON ALIMENTOS LTDA",     "CNPJ": "56789012000105", "BASE CODE": "epsilon_alim",  "SAS KEY": "ref_005", "Completo": "Sim", "EMAIL DTR": "fiscal@epsilon-alim.com.br",   "EMAIL MARS": "analista2@empresa.com", "EMAIL EXTRA": "bi@epsilon-alim.com.br"},
    {"Owner": "Roberto Dias",   "ID": "D06", "DISTRIBUIDOR": "ZETA COMERCIO E IMP LTDA",   "CNPJ": "67890123000106", "BASE CODE": "zeta_com",      "SAS KEY": "ref_006", "Completo": "Sim", "EMAIL DTR": "inteligencia@zeta-com.com.br", "EMAIL MARS": "analista1@empresa.com", "EMAIL EXTRA": "0"},
    {"Owner": "Fernanda Reis",  "ID": "D07", "DISTRIBUIDOR": "ETA DISTRIBUIDORA REGIONAL", "CNPJ": "78901234000107", "BASE CODE": "eta_reg",       "SAS KEY": "ref_007", "Completo": "Sim", "EMAIL DTR": "comercial@eta-reg.com.br",      "EMAIL MARS": "analista3@empresa.com", "EMAIL EXTRA": "nan"},
    {"Owner": "Lucas Oliveira", "ID": "D08", "DISTRIBUIDOR": "THETA LOGISTICA NACIONAL",   "CNPJ": "89012345000108", "BASE CODE": "theta_nac",     "SAS KEY": "ref_008", "Completo": "Sim", "EMAIL DTR": "logistica@theta-nac.com.br",   "EMAIL MARS": "analista2@empresa.com", "EMAIL EXTRA": "0"},
    {"Owner": "Camila Ferreira","ID": "D09", "DISTRIBUIDOR": "IOTA COMERCIO E DIST LTDA",  "CNPJ": "90123456000109", "BASE CODE": "iota_dist",     "SAS KEY": "ref_009", "Completo": "Sim", "EMAIL DTR": "vendas@iota-dist.com.br",       "EMAIL MARS": "analista1@empresa.com", "EMAIL EXTRA": "nan"},
    {"Owner": "Ricardo Moura",  "ID": "D10", "DISTRIBUIDOR": "KAPPA DISTRIBUIDORA LTDA",   "CNPJ": "01234567000110", "BASE CODE": "kappa_dist",    "SAS KEY": "ref_010", "Completo": "Sim", "EMAIL DTR": "dados@kappa-dist.com.br",       "EMAIL MARS": "analista3@empresa.com", "EMAIL EXTRA": "gerencia@kappa-dist.com.br"},
    {"Owner": "Ana Costa",      "ID": "D11", "DISTRIBUIDOR": "LAMBDA ALIMENTOS LTDA",      "CNPJ": "11234567000111", "BASE CODE": "lambda_alim",   "SAS KEY": "ref_011", "Completo": "Sim", "EMAIL DTR": "fiscal@lambda-alim.com.br",    "EMAIL MARS": "analista2@empresa.com", "EMAIL EXTRA": "0"},
    {"Owner": "Carlos Lima",    "ID": "D12", "DISTRIBUIDOR": "MU DISTRIBUIDORA REGIONAL",  "CNPJ": "12234567000112", "BASE CODE": "mu_reg",        "SAS KEY": "ref_012", "Completo": "Sim", "EMAIL DTR": "contato@mu-reg.com.br",         "EMAIL MARS": "analista1@empresa.com", "EMAIL EXTRA": "nan"},
    {"Owner": "Maria Souza",    "ID": "D13", "DISTRIBUIDOR": "NU COMERCIO E DISTRIBUICAO", "CNPJ": "13234567000113", "BASE CODE": "nu_com",        "SAS KEY": "ref_013", "Completo": "Sim", "EMAIL DTR": "comercial@nu-com.com.br",       "EMAIL MARS": "analista3@empresa.com", "EMAIL EXTRA": "0"},
    {"Owner": "Pedro Alves",    "ID": "D14", "DISTRIBUIDOR": "XI LOGISTICA LTDA",          "CNPJ": "14234567000114", "BASE CODE": "xi_log",        "SAS KEY": "ref_014", "Completo": "Sim", "EMAIL DTR": "operacoes@xi-log.com.br",       "EMAIL MARS": "analista2@empresa.com", "EMAIL EXTRA": "ti@xi-log.com.br"},
    {"Owner": "Julia Santos",   "ID": "D15", "DISTRIBUIDOR": "OMICRON DISTRIBUIDORA LTDA", "CNPJ": "15234567000115", "BASE CODE": "omicron_dist",  "SAS KEY": "ref_015", "Completo": "Sim", "EMAIL DTR": "vendas@omicron-dist.com.br",    "EMAIL MARS": "analista1@empresa.com", "EMAIL EXTRA": "0"},
]

# =============================================================================
# PASSO 1: Criar planilha de configuracao
# =============================================================================
print("=" * 60)
print("PASSO 1: Criando planilha de configuracao...")
print("=" * 60)

df_config = pd.DataFrame(distribuidores)
df_config.to_excel(CAMINHO_CONFIG, index=False, sheet_name="Distribuidores")
print(f"OK Planilha salva em: {CAMINHO_CONFIG}")
print(f"   -> {len(df_config)} distribuidores cadastrados")
print(f"   -> Colunas: {list(df_config.columns)}")
print()

# =============================================================================
# PASSO 2: Criar tabela simulada de sell-out
# =============================================================================
print("=" * 60)
if USAR_SPARK:
    print("PASSO 2: Criando tabela simulada no Unity Catalog (Spark)...")
else:
    print("PASSO 2: Criando tabela simulada localmente (CSV)...")
print("=" * 60)

hoje = date.today()
random.seed(42)

dados_sellout = []
for dist in distribuidores:
    if random.random() < 0.6:
        dias_atras = random.randint(0, 2)
    else:
        dias_atras = random.randint(4, 15)

    data_arquivo = hoje - timedelta(days=dias_atras)
    data_nf      = data_arquivo - timedelta(days=random.randint(0, 1))
    qtd_linhas   = random.randint(5000, 120000)

    dados_sellout.append({
        "distribuidor_id": dist["ID"],
        "cnpj": dist["CNPJ"],
        "data_nota_fiscal": data_nf,
        "data_arquivo": data_arquivo,
        "quantidade_linhas": qtd_linhas,
        "nome_arquivo": f"{dist['BASE CODE']}_{data_arquivo.strftime('%Y%m%d')}.csv"
    })

df_sellout = pd.DataFrame(dados_sellout)

if USAR_SPARK:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")
    spark_df = spark.createDataFrame(df_sellout)
    spark_df.write.mode("overwrite").saveAsTable(f"{CATALOG}.{SCHEMA}.{TABELA}")
    print(f"OK Tabela criada: {CATALOG}.{SCHEMA}.{TABELA}")
else:
    df_sellout.to_csv(CAMINHO_LOCAL_TABELA, index=False)
    print(f"OK Tabela salva localmente (CSV): {CAMINHO_LOCAL_TABELA}")

print(f"   -> {len(df_sellout)} registros inseridos")
print(f"   -> Distribuidores em dia:      {sum(1 for d in dados_sellout if (hoje - d['data_arquivo']).days <= 2)}")
print(f"   -> Distribuidores em atraso:   {sum(1 for d in dados_sellout if (hoje - d['data_arquivo']).days > 3)}")
print()

print("Amostra dos dados:")
print(df_sellout[["distribuidor_id", "data_nota_fiscal", "data_arquivo", "quantidade_linhas"]].to_string(index=False))
print()
print("=" * 60)
print("OK SETUP COMPLETO!")
print("=" * 60)
print(f"""
Proximos passos:
  1. Execute '02_validacao_e_cobranca.py' para identificar distribuidores em atraso
  2. Execute '03_disparo_emails.py' para simular o envio de e-mails

Artefatos criados:
  - Planilha : {CAMINHO_CONFIG}
  - Tabela   : {CATALOG + "." + SCHEMA + "." + TABELA if USAR_SPARK else CAMINHO_LOCAL_TABELA}
""")
