"""
03_disparo_emails.py
====================
Dispara os e-mails de cobranca gerados pelo script 02.

Comportamento:
  - SIMULACAO (padrao): Apenas imprime os e-mails que seriam enviados, sem chamar nenhum endpoint.
  - PRODUCAO: Envia os payloads via POST para o endpoint configurado (Power Automate / webhook).

Pre-requisitos:
  - Executar '02_validacao_e_cobranca.py' antes (gera payloads_cobranca.json)
  - Python 3.8+
  - Pacotes: requests  (apenas para envio real; pip install -r requirements.txt)

Uso:
  Funciona em Databricks, VSCode, terminal ou qualquer ambiente Python padrao.
  Por padrao, roda em modo SIMULACAO. Para enviar de verdade, altere SIMULAR_ENVIO = False.
"""

import json
import sys
import time
import os
import tempfile
from datetime import datetime

# =============================================================================
# CONFIGURACOES
# =============================================================================
TMP_DIR          = tempfile.gettempdir()
CAMINHO_PAYLOADS = os.path.join(TMP_DIR, "payloads_cobranca.json")
LOG_PATH         = os.path.join(TMP_DIR, "log_envio_cobranca.json")

# SIMULACAO: True = apenas imprime, nao envia nada
#            False = envia para o endpoint real
SIMULAR_ENVIO = True

# URL do endpoint (Power Automate, Logic Apps, ou qualquer webhook)
# Em producao real no Databricks, buscar de Secrets:
#   url = dbutils.secrets.get(scope="meu-scope", key="power-automate-url")
# Em outros ambientes, usar variavel de ambiente:
#   url = os.environ.get("WEBHOOK_URL", "")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://webhook-exemplo.com/trigger")

# =============================================================================
# PASSO 1: Carregar payloads
# =============================================================================
print("=" * 60)
print("DISPARO DE E-MAILS DE COBRANCA")
print(f"Modo: {'SIMULACAO' if SIMULAR_ENVIO else 'PRODUCAO'}")
print(f"Data/hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
print("=" * 60)
print()

with open(CAMINHO_PAYLOADS, "r", encoding="utf-8") as f:
    payloads = json.load(f)

if not payloads:
    print("Nenhum payload para enviar. Todos os distribuidores estao em dia!")
    print("   Finalizando sem acao.")
    sys.exit(0)

print(f"{len(payloads)} e-mails para enviar")
print()

# =============================================================================
# PASSO 2: Enviar (ou simular envio)
# =============================================================================
enviados = 0
erros    = []
log_envio = []

print("Progresso:")
print("-" * 60)

for i, payload in enumerate(payloads, 1):
    dist_id = payload.get("_metadata", {}).get("distribuidor_id", "???")
    subject = payload["subject"]
    to      = payload["to"]
    cc      = payload.get("cc", "")

    progresso = int((i / len(payloads)) * 30)
    barra     = "#" * progresso + "." * (30 - progresso)
    print(f"\r[{barra}] {i}/{len(payloads)}", end="", flush=True)

    if SIMULAR_ENVIO:
        time.sleep(0.05)
        status   = "simulado"
        enviados += 1
    else:
        try:
            import requests
            payload_envio = {k: v for k, v in payload.items() if k != "_metadata"}
            response = requests.post(WEBHOOK_URL, json=payload_envio, timeout=30)
            response.raise_for_status()
            status   = "enviado"
            enviados += 1
        except Exception as e:
            status = f"erro: {str(e)}"
            erros.append({"distribuidor_id": dist_id, "subject": subject, "erro": str(e)})

    log_envio.append({
        "distribuidor_id": dist_id,
        "to": to,
        "cc": cc,
        "subject": subject,
        "status": status,
        "timestamp": datetime.now().isoformat()
    })

print()
print()

# =============================================================================
# PASSO 3: Relatorio de envio
# =============================================================================
print("=" * 60)
print("RELATORIO DE ENVIO")
print("=" * 60)
print()

for item in log_envio:
    icone = "OK" if "erro" not in item["status"] else "ERRO"
    print(f"  [{icone}] {item['distribuidor_id']} - {item['subject']}")
    print(f"       Para: {item['to']}")
    if item["cc"]:
        print(f"       CC:   {item['cc']}")
    print(f"       Status: {item['status']}")
    print()

print("-" * 60)
print(f"  Total:    {len(payloads)}")
print(f"  Enviados: {enviados}")
print(f"  Erros:    {len(erros)}")
print()

if erros:
    print("Detalhes dos erros:")
    for e in erros:
        print(f"   - {e['distribuidor_id']}: {e['erro']}")
    print()

# =============================================================================
# PASSO 4: Salvar log de auditoria
# =============================================================================
log_completo = {
    "data_execucao": datetime.now().isoformat(),
    "modo": "SIMULACAO" if SIMULAR_ENVIO else "PRODUCAO",
    "total_payloads": len(payloads),
    "enviados": enviados,
    "erros": len(erros),
    "detalhes": log_envio
}

with open(LOG_PATH, "w", encoding="utf-8") as f:
    json.dump(log_completo, f, ensure_ascii=False, indent=2)

print(f"Log de auditoria salvo em: {LOG_PATH}")
print()

print("=" * 60)
if SIMULAR_ENVIO:
    print("SIMULACAO CONCLUIDA COM SUCESSO")
    print()
    print("   Nenhum e-mail foi realmente enviado.")
    print("   Para enviar de verdade:")
    print("     1. Configure a variavel de ambiente WEBHOOK_URL com a URL real")
    print("        (ou dbutils.secrets no Databricks)")
    print("     2. Altere SIMULAR_ENVIO = False")
    print("     3. Execute novamente")
else:
    print(f"ENVIO CONCLUIDO: {enviados}/{len(payloads)} e-mails enviados")
    if erros:
        print(f"ATENCAO: {len(erros)} erros encontrados. Verifique o log.")
print("=" * 60)
