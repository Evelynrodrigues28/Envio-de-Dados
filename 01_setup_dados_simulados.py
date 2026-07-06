"""
01_setup_dados_simulados.py
===========================
Gera os dados simulados necessários para reproduzir o processo de validação de Blob.

Executa:
  1. Cria a planilha Excel de configuração com dados fictícios (config_distribuidores.xlsx)
  2. Cria a tabela simulada de sell-out no Unity Catalog

Pré-requisitos:
  - Cluster Databricks com Runtime 13.x+
  - Pacotes: openpyxl, pandas
  - Permissão de escrita no catalog/schema definido abaixo

Uso:
  Execute este script UMA VEZ para preparar o ambiente de simulação.
"""

import pandas as pd
from datetime import date, timedelta
import random
import os

# =============================================================================
# CONFIGURAÇÕES — altere conforme seu ambiente
# =============================================================================
CATALOG = "catalog_exemplo"          # Altere para seu catalog
SCHEMA = "sell_out"                  # Altere para seu schema
TABELA = "fato_sellout"             # Nome da tabela simulada
CAMINHO_CONFIG = "/tmp/config_distribuidores.xlsx"  # Onde salvar o Excel

# =============================================================================
# DADOS FICTÍCIOS DOS DISTRIBUIDORES
# =============================================================================
distribuidores = [
    {"Owner": "Ana Costa", "ID": "D01", "DISTRIBUIDOR": "DISTRIBUIDORA ALPHA LTDA", "CNPJ": "12345678000101", "BASE CODE": "alpha_dist", "SAS KEY": "ref_001", "Completo": "Sim", "EMAIL DTR": "contato@alpha-dist.com.br", "EMAIL MARS": "analista1@empresa.com", "EMAIL EXTRA": "0"},
    {"Owner": "Carlos Lima", "ID": "D02", "DISTRIBUIDOR": "COMERCIAL BETA S.A.", "CNPJ": "23456789000102", "BASE CODE": "beta_com", "SAS KEY": "ref_002", "Completo": "Sim", "EMAIL DTR": "vendas@beta-com.com.br", "EMAIL MARS": "analista2@empresa.com", "EMAIL EXTRA": "nan"},
    {"Owner": "Maria Souza", "ID": "D03", "DISTRIBUIDOR": "GAMMA LOGISTICA LTDA", "CNPJ": "34567890000103", "BASE CODE": "gamma_log", "SAS KEY": "ref_003", "Completo": "Sim", "EMAIL DTR": "dados@gamma-log.com.br", "EMAIL MARS": "analista1@empresa.com", "EMAIL EXTRA": "gestor@gamma-log.com.br"},
    {"Owner": "Pedro Alves", "ID": "D04", "DISTRIBUIDOR": "DELTA DISTRIBUIDORA LTDA", "CNPJ": "45678901000104", "BASE CODE": "delta_dist", "SAS KEY": "ref_004", "Completo": "Sim", "EMAIL DTR": "0", "EMAIL MARS": "analista3@empresa.com", "EMAIL EXTRA": "0"},
    {"Owner": "Julia Santos", "ID": "D05", "DISTRIBUIDOR": "EPSILON ALIMENTOS LTDA", "CNPJ": "56789012000105", "BASE CODE": "epsilon_alim", "SAS KEY": "ref_005", "Completo": "Sim", "EMAIL DTR": "fiscal@epsilon-alim.com.br", "EMAIL MARS": "analista2@empresa.com", "EMAIL EXTRA": "bi@epsilon-alim.com.br"},
    {"Owner": "Roberto Dias", "ID": "D06", "DISTRIBUIDOR": "ZETA COMERCIO E IMP LTDA", "CNPJ": "67890123000106", "BASE CODE": "zeta_com", "SAS KEY": "ref_006", "Completo": "Sim", "EMAIL DTR": "inteligencia@zeta-com.com.br", "EMAIL MARS": "analista1@empresa.com", "EMAIL EXTRA": "0"},
    {"Owner": "Fernanda Reis", "ID": "D07", "DISTRIBUIDOR": "ETA DISTRIBUIDORA REGIONAL", "CNPJ": "78901234000107", "BASE CODE": "eta_reg", "SAS KEY": "ref_007", "Completo": "Sim", "EMAIL DTR": "comercial@eta-reg.com.br", "EMAIL MARS": "analista3@empresa.com", "EMAIL EXTRA": "nan"},
    {"Owner": "Lucas Oliveira", "ID": "D08", "DISTRIBUIDOR": "THETA LOGISTICA NACIONAL", "CNPJ": "89012345000108", "BASE CODE": "theta_nac", "SAS KEY": "ref_008", "Completo": "Sim", "EMAIL DTR": "logistica@theta-nac.com.br", "EMAIL MARS": "analista2@empresa.com", "EMAIL EXTRA": "0"},
    {"Owner": "Camila Ferreira", "ID": "D09", "DISTRIBUIDOR": "IOTA COMERCIO E DIST LTDA", "CNPJ": "90123456000109", "BASE CODE": "iota_dist", "SAS KEY": "ref_009", "Completo": "Sim", "EMAIL DTR": "vendas@iota-dist.com.br", "EMAIL MARS": "analista1@empresa.com", "EMAIL EXTRA": "nan"},
    {"Owner": "Ricardo Moura", "ID": "D10", "DISTRIBUIDOR": "KAPPA DISTRIBUIDORA LTDA", "CNPJ": "01234567000110", "BASE CODE": "kappa_dist", "SAS KEY": "ref_010", "Completo": "Sim", "EMAIL DTR": "dados@kappa-dist.com.br", "EMAIL MARS": "analista3@empresa.com", "EMAIL EXTRA": "gerencia@kappa-dist.com.br"},
    {"Owner": "Ana Costa", "ID": "D11", "DISTRIBUIDOR": "LAMBDA ALIMENTOS LTDA", "CNPJ": "11234567000111", "BASE CODE": "lambda_alim", "SAS KEY": "ref_011", "Completo": "Sim", "EMAIL DTR": "fiscal@lambda-alim.com.br", "EMAIL MARS": "analista2@empresa.com", "EMAIL EXTRA": "0"},
    {"Owner": "Carlos Lima", "ID": "D12", "DISTRIBUIDOR": "MU DISTRIBUIDORA REGIONAL", "CNPJ": "12234567000112", "BASE CODE": "mu_reg", "SAS KEY": "ref_012", "Completo": "Sim", "EMAIL DTR": "contato@mu-reg.com.br", "EMAIL MARS": "analista1@empresa.com", "EMAIL EXTRA": "nan"},
    {"Owner": "Maria Souza", "ID": "D13", "DISTRIBUIDOR": "NU COMERCIO E DISTRIBUICAO", "CNPJ": "13234567000113", "BASE CODE": "nu_com", "SAS KEY": "ref_013", "Completo": "Sim", "EMAIL DTR": "comercial@nu-com.com.br", "EMAIL MARS": "analista3@empresa.com", "EMAIL EXTRA": "0"},
    {"Owner": "Pedro Alves", "ID": "D14", "DISTRIBUIDOR": "XI LOGISTICA LTDA", "CNPJ": "14234567000114", "BASE CODE": "xi_log", "SAS KEY": "ref_014", "Completo": "Sim", "EMAIL DTR": "operacoes@xi-log.com.br", "EMAIL MARS": "analista2@empresa.com", "EMAIL EXTRA": "ti@xi-log.com.br"},
    {"Owner": "Julia Santos", "ID": "D15", "DISTRIBUIDOR": "OMICRON DISTRIBUIDORA LTDA", "CNPJ": "15234567000115", "BASE CODE": "omicron_dist", "SAS KEY": "ref_015", "Completo": "Sim", "EMAIL DTR": "vendas@omicron-dist.com.br", "EMAIL MARS": "analista1@empresa.com", "EMAIL EXTRA": "0"},
]

# =============================================================================
# PASSO 1: Criar planilha de configuração
# =============================================================================
print("=" * 60)
print("PASSO 1: Criando planilha de configuração...")
print("=" * 60)

df_config = pd.DataFrame(distribuidores)
df_config.to_excel(CAMINHO_CONFIG, index=False, sheet_name="Distribuidores")
print(f"✅ Planilha salva em: {CAMINHO_CONFIG}")
print(f"   → {len(df_config)} distribuidores cadastrados")
print(f"   → Colunas: {list(df_config.columns)}")
print()

# =============================================================================
# PASSO 2: Criar tabela simulada de sell-out no Unity Catalog
# =============================================================================
print("=" * 60)
print("PASSO 2: Criando tabela simulada no Unity Catalog...")
print("=" * 60)

# Gerar dados de sell-out simulados
# Alguns distribuidores estão em dia, outros em atraso
hoje = date.today()
random.seed(42)  # Reprodutibilidade

dados_sellout = []
for dist in distribuidores:
    # Simular: 60% em dia (último arquivo = ontem ou hoje), 40% atrasados
    if random.random() < 0.6:
        # Em dia: último arquivo entre hoje e 2 dias atrás
        dias_atras = random.randint(0, 2)
    else:
        # Atrasado: último arquivo entre 4 e 15 dias atrás
        dias_atras = random.randint(4, 15)

    data_arquivo = hoje - timedelta(days=dias_atras)
    # Nota fiscal geralmente 1 dia antes do arquivo
    data_nf = data_arquivo - timedelta(days=random.randint(0, 1))
    qtd_linhas = random.randint(5000, 120000)

    dados_sellout.append({
        "distribuidor_id": dist["ID"],
        "cnpj": dist["CNPJ"],
        "data_nota_fiscal": data_nf,
        "data_arquivo": data_arquivo,
        "quantidade_linhas": qtd_linhas,
        "nome_arquivo": f"{dist['BASE CODE']}_{data_arquivo.strftime('%Y%m%d')}.csv"
    })

df_sellout = pd.DataFrame(dados_sellout)

# Criar tabela via Spark
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

# Criar schema se necessário
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")

# Criar tabela a partir do DataFrame
spark_df = spark.createDataFrame(df_sellout)
spark_df.write.mode("overwrite").saveAsTable(f"{CATALOG}.{SCHEMA}.{TABELA}")

print(f"✅ Tabela criada: {CATALOG}.{SCHEMA}.{TABELA}")
print(f"   → {len(df_sellout)} registros inseridos")
print(f"   → Distribuidores em dia: {sum(1 for d in dados_sellout if (hoje - d['data_arquivo']).days <= 2)}")
print(f"   → Distribuidores atrasados: {sum(1 for d in dados_sellout if (hoje - d['data_arquivo']).days > 3)}")
print()

# Mostrar amostra
print("Amostra dos dados:")
spark.sql(f"SELECT * FROM {CATALOG}.{SCHEMA}.{TABELA} ORDER BY data_arquivo").show(truncate=False)

print()
print("=" * 60)
print("✅ SETUP COMPLETO!")
print("=" * 60)
print(f"""
Próximos passos:
  1. Execute '02_validacao_e_cobranca.py' para identificar distribuidores em atraso
  2. Execute '03_disparo_emails.py' para simular o envio de e-mails

Artefatos criados:
  - Planilha: {CAMINHO_CONFIG}
  - Tabela:   {CATALOG}.{SCHEMA}.{TABELA}
""")
