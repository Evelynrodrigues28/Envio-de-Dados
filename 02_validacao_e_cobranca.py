"""
02_validacao_e_cobranca.py
==========================
Executa a validação dos dados de sell-out e identifica distribuidores em atraso.
Gera os payloads de e-mail de cobrança prontos para envio.

Pré-requisitos:
  - Executar '01_setup_dados_simulados.py' antes (cria planilha e tabela)
  - Cluster Databricks com Runtime 13.x+
  - Pacotes: openpyxl, pandas

Uso:
  Execute após o setup. Gera o arquivo de payloads em /tmp/payloads_cobranca.json
"""

import pandas as pd
from pandas.tseries.offsets import BDay
from datetime import date
import json
from pyspark.sql import SparkSession

# =============================================================================
# CONFIGURAÇÕES — devem ser as mesmas do script 01
# =============================================================================
CATALOG = "catalog_exemplo"
SCHEMA = "sell_out"
TABELA = "fato_sellout"
CAMINHO_CONFIG = "/tmp/config_distribuidores.xlsx"
CAMINHO_PAYLOADS = "/tmp/payloads_cobranca.json"

# SLA em dias úteis
SLA_DIAS_UTEIS = 3

# IDs com exceção (distribuidores que consistentemente enviam em D+3)
# Estes não são considerados "em atraso" mesmo se ultrapassarem o SLA padrão
EXCECOES_D3 = ["D07", "D08"]

# Modo de execução: "Teste" ou "Producao"
MODO = "Teste"
EMAIL_TESTE = "analista.teste@empresa.com"

# =============================================================================
# PASSO 1: Carregar planilha de configuração
# =============================================================================
print("=" * 60)
print("PASSO 1: Carregando planilha de configuração...")
print("=" * 60)

df_config = pd.read_excel(CAMINHO_CONFIG, sheet_name="Distribuidores")
print(f"✅ {len(df_config)} distribuidores carregados da planilha")

# Extrair lista de IDs
lista_ids = df_config["ID"].tolist()
print(f"   → IDs: {lista_ids}")
print()

# =============================================================================
# PASSO 2: Consultar Unity Catalog (última NF e último arquivo por distribuidor)
# =============================================================================
print("=" * 60)
print("PASSO 2: Consultando tabela de sell-out no Unity Catalog...")
print("=" * 60)

spark = SparkSession.builder.getOrCreate()

# Consulta principal: buscar status de cada distribuidor
ids_sql = ", ".join([f"'{id}'" for id in lista_ids])
query = f"""
SELECT
    distribuidor_id AS ID,
    cnpj,
    MAX(data_nota_fiscal) AS ultima_nota_fiscal,
    MAX(data_arquivo) AS ultimo_arquivo,
    SUM(quantidade_linhas) AS total_linhas
FROM {CATALOG}.{SCHEMA}.{TABELA}
WHERE distribuidor_id IN ({ids_sql})
GROUP BY distribuidor_id, cnpj
ORDER BY ultimo_arquivo ASC
"""

df_sellout = spark.sql(query).toPandas()
print(f"✅ Processados {len(df_sellout)} distribuidores via Unity Catalog")

# Merge com dados da config (para ter e-mails e nomes)
df = df_config.merge(df_sellout, on="ID", how="left")

# Formatar datas para exibição
df["data da ultima nota fiscal"] = pd.to_datetime(df["ultima_nota_fiscal"]).dt.strftime("%d/%m/%Y")
df["Data ultimo arquivo"] = pd.to_datetime(df["ultimo_arquivo"]).dt.strftime("%d/%m/%Y")
df["Quantidade de linhas"] = df["total_linhas"].fillna(0).astype(int)

# Exibir tabela consolidada
print()
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

# Data de referência
data_referencia = pd.Timestamp(date.today())
data_corte = data_referencia - BDay(SLA_DIAS_UTEIS)

print(f"📅 Data de referência: {data_referencia.strftime('%d/%m/%Y')} ({data_referencia.strftime('%A')})")
print(f"📏 SLA: {SLA_DIAS_UTEIS} dias úteis → corte em {data_corte.strftime('%d/%m/%Y')}")
print()

# Converter coluna de data para datetime
df["ultimo_arquivo_dt"] = pd.to_datetime(df["ultimo_arquivo"])

# Filtrar atrasados (excluindo exceções D+3)
df_atrasados = df[
    (df["ultimo_arquivo_dt"] < data_corte) &
    (~df["ID"].isin(EXCECOES_D3))
].copy()

# Calcular dias de atraso em dias úteis
df_atrasados["dias_atraso"] = df_atrasados["ultimo_arquivo_dt"].apply(
    lambda x: len(pd.bdate_range(x, data_referencia)) - 1 if pd.notna(x) else None
)

print(f"✅ Distribuidores em dia: {len(df) - len(df_atrasados)}")
print(f"⚠️  Distribuidores em atraso: {len(df_atrasados)}")
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
    # Determinar destinatário
    email_dtr = str(row["EMAIL DTR"]).strip()
    email_mars = str(row["EMAIL MARS"]).strip()
    email_extra = str(row["EMAIL EXTRA"]).strip()

    # Fallback: se distribuidor não tem e-mail, envia para o analista interno
    if email_dtr in ["0", "nan", "", "None"]:
        destinatario = email_mars
        cc = ""
    else:
        destinatario = email_dtr
        cc = email_mars

    # Adicionar CC extra se existir
    if email_extra not in ["0", "nan", "", "None"]:
        cc = f"{cc};{email_extra}" if cc else email_extra

    # Modo teste: redirecionar tudo para e-mail de teste
    if MODO == "Teste":
        destinatario_final = EMAIL_TESTE
        cc_final = ""
    else:
        destinatario_final = destinatario
        cc_final = cc

    # Período retroativo
    periodo_inicio = row["ultimo_arquivo_dt"] + pd.Timedelta(days=1)
    periodo_fim = data_referencia

    # Corpo do e-mail
    corpo = f"""Prezado(a),

Identificamos que os dados de sell-out de {row['DISTRIBUIDOR']} não foram recebidos desde {row['Data ultimo arquivo']}.

Solicitamos o envio retroativo dos dados referentes ao período de {periodo_inicio.strftime('%d/%m/%Y')} a {periodo_fim.strftime('%d/%m/%Y')}.

Caso já tenha enviado, por favor desconsidere esta mensagem.

Atenciosamente,
Equipe de Inteligência de Vendas"""

    payload = {
        "to": destinatario_final,
        "cc": cc_final,
        "subject": f"Dados Pendentes – {row['DISTRIBUIDOR']}",
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

# Salvar payloads para auditoria e para uso no script 03
with open(CAMINHO_PAYLOADS, "w", encoding="utf-8") as f:
    json.dump(payloads, f, ensure_ascii=False, indent=2)

print(f"✅ {len(payloads)} payloads gerados")
print(f"📁 Salvos em: {CAMINHO_PAYLOADS}")
print(f"📧 Modo: {MODO}")
if MODO == "Teste":
    print(f"   → Todos os e-mails redirecionados para: {EMAIL_TESTE}")
print()

# Exibir exemplo de payload
if payloads:
    print("Exemplo de payload gerado:")
    print("-" * 60)
    exemplo = {k: v for k, v in payloads[0].items() if k != "_metadata"}
    print(json.dumps(exemplo, ensure_ascii=False, indent=2))
    print()

# =============================================================================
# RESUMO
# =============================================================================
print("=" * 60)
print("RESUMO DA EXECUÇÃO")
print("=" * 60)
print(f"""
  Distribuidores monitorados:  {len(df)}
  Distribuidores em dia:       {len(df) - len(df_atrasados)}
  Distribuidores em atraso:    {len(df_atrasados)}
  Exceções (D+3):              {len(EXCECOES_D3)} ({', '.join(EXCECOES_D3)})
  Payloads gerados:            {len(payloads)}
  Modo de execução:            {MODO}
  Arquivo de payloads:         {CAMINHO_PAYLOADS}

Próximo passo:
  Execute '03_disparo_emails.py' para enviar os e-mails (ou simular o envio).
""")
