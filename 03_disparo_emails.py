"""
03_disparo_emails.py
====================
Dispara os e-mails de cobrança gerados pelo script 02.

Comportamento:
  - SIMULAÇÃO (padrão): Apenas imprime os e-mails que seriam enviados, sem chamar nenhum endpoint.
  - PRODUÇÃO: Envia os payloads via POST para o endpoint configurado (Power Automate / webhook).

Pré-requisitos:
  - Executar '02_validacao_e_cobranca.py' antes (gera /tmp/payloads_cobranca.json)

Uso:
  Execute após a validação. Por padrão, roda em modo SIMULAÇÃO.
  Para enviar de verdade, altere SIMULAR_ENVIO = False e configure a URL do webhook.
"""

import json
import time
from datetime import datetime

# =============================================================================
# CONFIGURAÇÕES
# =============================================================================
CAMINHO_PAYLOADS = "/tmp/payloads_cobranca.json"

# SIMULAÇÃO: True = apenas imprime, não envia nada
#            False = envia para o endpoint real
SIMULAR_ENVIO = True

# URL do endpoint (Power Automate, Logic Apps, ou qualquer webhook)
# Em produção real, buscar de Databricks Secrets:
#   url = dbutils.secrets.get(scope="meu-scope", key="power-automate-url")
WEBHOOK_URL = "https://webhook-exemplo.com/trigger"  # placeholder

# =============================================================================
# PASSO 1: Carregar payloads
# =============================================================================
print("=" * 60)
print("DISPARO DE E-MAILS DE COBRANÇA")
print(f"Modo: {'SIMULAÇÃO' if SIMULAR_ENVIO else 'PRODUÇÃO'}")
print(f"Data/hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
print("=" * 60)
print()

with open(CAMINHO_PAYLOADS, "r", encoding="utf-8") as f:
    payloads = json.load(f)

if not payloads:
    print("ℹ️  Nenhum payload para enviar. Todos os distribuidores estão em dia!")
    print("   Finalizando sem ação.")
    exit(0)

print(f"📧 {len(payloads)} e-mails para enviar")
print()

# =============================================================================
# PASSO 2: Enviar (ou simular envio)
# =============================================================================
enviados = 0
erros = []
log_envio = []

print("Progresso:")
print("-" * 60)

for i, payload in enumerate(payloads, 1):
    dist_id = payload.get("_metadata", {}).get("distribuidor_id", "???")
    subject = payload["subject"]
    to = payload["to"]
    cc = payload.get("cc", "")

    # Barra de progresso simples
    progresso = int((i / len(payloads)) * 30)
    barra = "█" * progresso + "░" * (30 - progresso)
    print(f"\r[{barra}] {i}/{len(payloads)}", end="", flush=True)

    if SIMULAR_ENVIO:
        # Apenas simula — não faz nenhuma chamada HTTP
        time.sleep(0.1)  # Simula latência
        status = "simulado"
        enviados += 1
    else:
        # Envio real via HTTP POST
        try:
            import requests
            # Remover metadata antes de enviar
            payload_envio = {k: v for k, v in payload.items() if k != "_metadata"}
            response = requests.post(WEBHOOK_URL, json=payload_envio, timeout=30)
            response.raise_for_status()
            status = "enviado"
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

print()  # Nova linha após barra de progresso
print()

# =============================================================================
# PASSO 3: Relatório de envio
# =============================================================================
print("=" * 60)
print("RELATÓRIO DE ENVIO")
print("=" * 60)
print()

# Detalhes de cada envio
for item in log_envio:
    icone = "✅" if "erro" not in item["status"] else "❌"
    print(f"  {icone} {item['distribuidor_id']} - {item['subject']}")
    print(f"     Para: {item['to']}")
    if item["cc"]:
        print(f"     CC:   {item['cc']}")
    print(f"     Status: {item['status']}")
    print()

# Resumo
print("-" * 60)
print(f"  Total:    {len(payloads)}")
print(f"  Enviados: {enviados}")
print(f"  Erros:    {len(erros)}")
print()

if erros:
    print("⚠️  Detalhes dos erros:")
    for e in erros:
        print(f"   - {e['distribuidor_id']}: {e['erro']}")
    print()

# =============================================================================
# PASSO 4: Salvar log de auditoria
# =============================================================================
log_path = "/tmp/log_envio_cobranca.json"
log_completo = {
    "data_execucao": datetime.now().isoformat(),
    "modo": "SIMULACAO" if SIMULAR_ENVIO else "PRODUCAO",
    "total_payloads": len(payloads),
    "enviados": enviados,
    "erros": len(erros),
    "detalhes": log_envio
}

with open(log_path, "w", encoding="utf-8") as f:
    json.dump(log_completo, f, ensure_ascii=False, indent=2)

print(f"📁 Log de auditoria salvo em: {log_path}")
print()

# =============================================================================
# RESUMO FINAL
# =============================================================================
print("=" * 60)
if SIMULAR_ENVIO:
    print("✅ SIMULAÇÃO CONCLUÍDA COM SUCESSO")
    print()
    print("   Nenhum e-mail foi realmente enviado.")
    print("   Para enviar de verdade:")
    print("     1. Configure WEBHOOK_URL com a URL real do Power Automate")
    print("     2. Altere SIMULAR_ENVIO = False")
    print("     3. Execute novamente")
else:
    print(f"✅ ENVIO CONCLUÍDO: {enviados}/{len(payloads)} e-mails enviados")
    if erros:
        print(f"⚠️  {len(erros)} erros encontrados. Verifique o log.")
print("=" * 60)
