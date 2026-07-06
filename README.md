# Automação de Cobrança — Monitoramento de Sell-out por Distribuidor

## Visão Geral

Todo dia, cerca de 52 distribuidores precisam enviar seus dados de sell-out para a equipe de Inteligência de Vendas. Quando o envio atrasa, a equipe gastava **~2 horas diárias** só para descobrir quem estava em atraso, redigir os e-mails de cobrança um a um e garantir que os destinatários certos estavam incluídos.

Esta solução automatiza esse processo do início ao fim. Em menos de 5 minutos, todos os distribuidores são verificados, os atrasados são identificados e os e-mails de cobrança são enviados automaticamente — com o período retroativo correto, para os contatos certos.

**96% de redução no tempo da atividade. Cobertura de 100% dos distribuidores em cada execução.**

---

## O Problema

A equipe depende desses dados diariamente para análises de mercado e acompanhamento de performance. Cada dia sem receber os arquivos de um distribuidor é um dia com informação incompleta.

O processo manual de acompanhamento tinha três problemas crônicos:

* **Cobertura parcial** — com o tempo limitado, nem todos os distribuidores eram verificados todo dia
* **Erros de destinatário** — e-mails iam para contatos desatualizados ou saíam sem os CCs necessários
* **Cálculo manual do período** — o intervalo retroativo de cobrança era calculado na mão, gerando inconsistências

---

## Como Funciona

O processo roda em três etapas automáticas:

**1. Diagnóstico** — Compara as datas de envio de cada distribuidor com o SLA vigente (3 dias úteis) e separa quem está em dia de quem está em atraso.

**2. Composição** — Para cada distribuidor em atraso, monta um e-mail personalizado com o período exato de reenvio e os contatos corretos — distribuidor, responsável interno e cópias adicionais quando aplicável.

**3. Envio** — Dispara todos os e-mails com rastreamento de status e registra um log completo de auditoria ao final.

---

## Impacto

| Indicador | Antes | Depois |
| --- | --- | --- |
| Tempo por execução | ~120 min | ~5 min |
| Cobertura dos distribuidores | Parcial (~70%) | 100% |
| Risco de e-mail para contato errado | Alto | Eliminado |
| Viabilidade de execução diária | Com esforço significativo | Sem esforço |

| Economia de tempo estimada | |
| --- | --- |
| Por semana | ~9,5 horas |
| Por mês | ~42 horas |
| Por ano | ~483 horas (~60 dias de trabalho) |

---

## Recursos

* **Modo teste integrado** — por padrão, todos os e-mails são redirecionados para um endereço de teste, sem risco de envio acidental para produção
* **SLA ajustável** — o prazo de tolerância pode ser alterado sem mexer no código
* **Exceções por distribuidor** — distribuidores com acordos de envio diferenciados podem ser isentados da regra padrão
* **Exclusão pontual** — qualquer distribuidor pode ser pulado em uma execução específica sem alterar o cadastro
* **Rastreabilidade** — cada execução gera um log com destinatários, status de envio e timestamps

---

## Como Reproduzir

Os scripts funcionam em qualquer ambiente Python, sem dependências de infraestrutura.

### Instalação

```bash
pip install -r requirements.txt
```

### Execução

```bash
python 01_setup_dados_simulados.py   # Cria os dados de simulação — rodar apenas uma vez
python 02_validacao_e_cobranca.py    # Identifica atrasos e prepara os e-mails
python 03_disparo_emails.py          # Envia os e-mails (modo simulação por padrão)
```

O modo simulação imprime os e-mails que seriam enviados sem acionar nenhum endpoint. Para envio real, definir a variável de ambiente `WEBHOOK_URL` e alterar `SIMULAR_ENVIO = False` no script 03.

### Parâmetros

| Parâmetro | Arquivo | Descrição |
| --- | --- | --- |
| `SLA_DIAS_UTEIS` | `02_validacao_e_cobranca.py` | Prazo de tolerância em dias úteis (padrão: 3) |
| `MODO` | `02_validacao_e_cobranca.py` | `"Teste"` envia tudo para `EMAIL_TESTE`; `"Producao"` envia para os destinatários reais |
| `EXCECOES_D3` | `02_validacao_e_cobranca.py` | Distribuidores isentos da regra de SLA padrão |
| `SIMULAR_ENVIO` | `03_disparo_emails.py` | `True` simula sem enviar; `False` envia de verdade |
| `WEBHOOK_URL` | variável de ambiente | Endpoint de envio (Power Automate, Logic Apps, etc.) |

---

## Arquivos

```
reproducao/
├── 01_setup_dados_simulados.py   — Gera os dados fictícios para simulação
├── 02_validacao_e_cobranca.py    — Lógica de SLA e composição dos e-mails
├── 03_disparo_emails.py          — Envio e log de auditoria
├── create_table_simulada.sql     — Alternativa em SQL puro
└── requirements.txt              — Dependências Python
```

---

## Segurança

* Nenhum e-mail é enviado sem configuração explícita — o modo simulação é o padrão
* O endpoint de envio é configurado via variável de ambiente, nunca no código
* Os dados de contato dos distribuidores vêm de um arquivo controlado pela equipe
* Nenhuma informação sensível é persistida além do log de auditoria local

---

## Histórico de Versões

| Versão | Data | Descrição |
| --- | --- | --- |
| 1.0 | 2026-07 | Versão inicial |
| 1.1 | 2026-07 | Portabilizado para qualquer ambiente Python |

---

*Os dados usados na simulação são 100% fictícios — nomes, CNPJs, e-mails e identificadores não correspondem a nenhuma entidade real.*
