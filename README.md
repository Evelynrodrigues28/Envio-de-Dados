# Envio de Dados Blob — Monitoramento de Distribuidores

## Resumo Executivo

Este notebook automatiza o **monitoramento diário do envio de dados de sell-out por distribuidores** via Azure Blob Storage. Ele identifica distribuidores em atraso (SLA de 3 dias úteis), gera e-mails personalizados de cobrança e os envia automaticamente via Power Automate.

O processo substitui uma rotina 100% manual que demandava **~2 horas/dia** de um analista, reduzindo para ~5 minutos/dia com supervisão mínima.

---

## Problema

A equipe de Inteligência de Vendas monitora aproximadamente 52 distribuidores que devem enviar diariamente seus dados de sell-out (notas fiscais) via Blob Storage. Quando um distribuidor não envia os dados dentro do SLA esperado, é necessário:

1. Verificar quais distribuidores estão em atraso
2. Identificar a data da última nota fiscal vs. data do último arquivo recebido
3. Compor e-mails individuais de cobrança com o período retroativo correto
4. Enviar para os contatos adequados (distribuidor + stakeholders internos)

**Dor principal:** O processo manual é repetitivo, sujeito a erros (destinatário errado, CC faltando) e consome tempo significativo do analista diariamente.

---

## Arquitetura da Solução

```
┌─────────────────────┐     ┌──────────────────────┐     ┌───────────────────────┐
│  Planilha Config    │────▶│  Unity Catalog       │────▶│  Detecção de Atraso   │
│  (Cadastro de      │     │  (Consulta Tabela    │     │  (Lógica de Dias      │
│   Distribuidores)  │     │   Fato Sell-out)     │     │   Úteis - BDay)       │
└─────────────────────┘     └──────────────────────┘     └───────────┬───────────┘
                                                                     │
                                                                     ▼
┌─────────────────────┐     ┌──────────────────────┐     ┌───────────────────────┐
│  Power Automate     │◀────│  Payload JSON        │◀────│  Geração de E-mails   │
│  (Envio SMTP)      │     │  (Estruturado)       │     │  (Templates HTML)     │
└─────────────────────┘     └──────────────────────┘     └───────────────────────┘
```

### Etapas do Pipeline

| Etapa | Descrição | Tecnologia |
| --- | --- | --- |
| 1. Carregar Config | Lê cadastro de distribuidores (IDs, contatos, CNPJs) | Pandas + openpyxl |
| 2. Consultar Dados | Busca última NF, último arquivo e contagem de linhas no data lake | Spark SQL / Unity Catalog |
| 3. Detectar Atrasos | Aplica lógica de dias úteis (SLA D-3) com exceções configuráveis | Pandas + BDay offsets |
| 4. Gerar E-mails | Monta e-mails HTML personalizados com destinatários e CC corretos | Python string templating |
| 5. Disparar | Envia e-mails via Power Automate com barra de progresso | JavaScript + REST API |

---

## Funcionalidades Principais

* **Execução parametrizada** — suporta modo Teste/Produção via widgets do notebook, evitando envios acidentais
* **Exclusão seletiva** — IDs de distribuidores podem ser excluídos via dropdown multiselect
* **Lógica de SLA inteligente** — cálculo por dias úteis (exclui fins de semana) com regra de exceção para distribuidores que consistentemente enviam em D+3
* **Roteamento automático de contatos** — envia para o contato do distribuidor ou fallback interno, com CC apropriado
* **Progresso em tempo real** — barra de progresso durante o disparo com relatório de erros
* **Trilha de auditoria** — payload JSON salvo no workspace para rastreabilidade

---

## Análise de Tempo Economizado

### Antes da Automação (Processo Manual)

| Tarefa | Tempo por Execução | Frequência |
| --- | --- | --- |
| Abrir fonte de dados e verificar status de cada distribuidor | ~30 min | Diário |
| Cruzar data da última NF vs. data do último upload | ~20 min | Diário |
| Compor e-mails individuais (média 15-20 distribuidores/dia) | ~40 min | Diário |
| Verificar destinatários e contatos em CC | ~15 min | Diário |
| Enviar e-mails um a um | ~15 min | Diário |
| **Total esforço manual** | **~2 horas/dia (120 min)** | **Diário** |

### Após Automação (Este Notebook)

| Tarefa | Tempo por Execução | Frequência |
| --- | --- | --- |
| Executar notebook (todas as células) | ~2 min | Diário |
| Revisar resultados e confirmar envio | ~3 min | Diário |
| **Total esforço automatizado** | **~5 min/dia** | **Diário** |

### Resumo de Impacto

| Métrica | Valor |
| --- | --- |
| Tempo economizado por execução | **~115 minutos** |
| Economia semanal (5 dias úteis) | **~9,5 horas** |
| Economia mensal (22 dias úteis) | **~42 horas** |
| Economia anual (252 dias úteis) | **~483 horas (~60 dias de trabalho)** |
| Redução de erros (destinatário errado, CC faltando) | **~95%** |
| Cobertura (distribuidores verificados por execução) | **100% (vs. verificações parciais no manual)** |
| Redução percentual do tempo da atividade | **96%** |

---

## Simulação — Exemplo de Execução

### Etapa 1: Dados Carregados (Amostra Anonimizada)

Após carregar a planilha de configuração e consultar o Unity Catalog, o notebook gera a seguinte tabela consolidada:

```
┌──────┬──────────────────────────────┬────────────────┬──────────────┬──────────────┬──────────┐
│  ID  │  Distribuidor                │  CNPJ          │  Última NF   │  Último Arq. │  Linhas  │
├──────┼──────────────────────────────┼────────────────┼──────────────┼──────────────┼──────────┤
│ D01  │  DISTRIBUIDORA ALPHA LTDA    │  **.***.***/**  │  02/07/2026  │  03/07/2026  │  19.839  │
│ D02  │  COMERCIAL BETA S.A.         │  **.***.***/**  │  30/06/2026  │  01/07/2026  │  47.319  │
│ D03  │  GAMMA LOGÍSTICA LTDA        │  **.***.***/**  │  02/07/2026  │  03/07/2026  │  27.687  │
│ D04  │  DELTA DISTRIBUIDORA LTDA    │  **.***.***/**  │  16/06/2026  │  17/06/2026  │  56.126  │
│ D05  │  EPSILON ALIMENTOS LTDA      │  **.***.***/**  │  27/06/2026  │  30/06/2026  │  29.855  │
│ D06  │  ZETA COMÉRCIO E IMP. LTDA   │  **.***.***/**  │  01/07/2026  │  02/07/2026  │ 118.294  │
│ D07  │  ETA DISTRIBUIDORA LTDA      │  **.***.***/**  │  02/07/2026  │  04/07/2026  │  71.553  │
│ ...  │  (total: ~50 distribuidores) │  ...           │  ...         │  ...         │  ...     │
└──────┴──────────────────────────────┴────────────────┴──────────────┴──────────────┴──────────┘
```

### Etapa 2: Detecção de Atrasos

O notebook aplica a regra de SLA (3 dias úteis a partir da data atual) e identifica distribuidores em atraso:

```
📅 Data de referência: 04/07/2026 (sexta-feira)
📏 SLA: 3 dias úteis → corte em 01/07/2026 (terça-feira)

✅ Distribuidores em dia: 32
⚠️  Distribuidores em atraso: 19

Distribuidores em atraso:
┌──────┬──────────────────────────────┬──────────────┬────────────────────┐
│  ID  │  Distribuidor                │  Última NF   │  Dias de Atraso    │
├──────┼──────────────────────────────┼──────────────┼────────────────────┤
│ D02  │  COMERCIAL BETA S.A.         │  30/06/2026  │  2 dias úteis      │
│ D04  │  DELTA DISTRIBUIDORA LTDA    │  16/06/2026  │  14 dias úteis     │
│ D05  │  EPSILON ALIMENTOS LTDA      │  27/06/2026  │  5 dias úteis      │
│ D06  │  ZETA COMÉRCIO E IMP. LTDA   │  01/07/2026  │  1 dia útil        │
│ ...  │  (total: 19 distribuidores)  │  ...         │  ...               │
└──────┴──────────────────────────────┴──────────────┴────────────────────┘
```

### Etapa 3: Geração de E-mail (Exemplo de Payload)

Para cada distribuidor em atraso, é gerado um payload JSON estruturado:

```json
{
  "to": "contato@distribuidora-exemplo.com.br",
  "cc": "analista.interno@empresa.com",
  "subject": "Dados Pendentes – COMERCIAL BETA S.A.",
  "body": "<html>...</html>",
  "importance": "high"
}
```

**Exemplo de corpo do e-mail (texto simplificado):**

```
Prezado(a),

Identificamos que os dados de sell-out da COMERCIAL BETA S.A.
não foram recebidos desde 30/06/2026.

Solicitamos o envio retroativo dos dados referentes ao período
de 01/07/2026 a 04/07/2026.

Caso já tenha enviado, por favor desconsidere esta mensagem.

Atenciosamente,
Equipe de Inteligência de Vendas
```

### Etapa 4: Disparo com Progresso

```
📧 Enviando e-mails via Power Automate...
[████████████████████░░░░░░░░] 15/19 enviados
  ✅ D02 - COMERCIAL BETA S.A. → enviado
  ✅ D04 - DELTA DISTRIBUIDORA LTDA → enviado
  ✅ D05 - EPSILON ALIMENTOS LTDA → enviado
  ...
  ✅ 19/19 e-mails enviados com sucesso
```

---

## Como Reproduzir

Os scripts da pasta `reproducao/` funcionam em **qualquer ambiente Python** —
Databricks, VSCode, terminal local, CI/CD — sem necessidade de infraestrutura.

### Instalacao (ambiente local)

```bash
pip install -r reproducao/requirements.txt
```

Dependencias: `pandas`, `openpyxl`, `pyarrow`, `requests`.
PySpark **nao e necessario** para execucao local.

### Quickstart

```bash
# 1. Preparar ambiente (cria planilha Excel + tabela simulada)
python reproducao/01_setup_dados_simulados.py

# 2. Validar dados e gerar e-mails de cobranca
python reproducao/02_validacao_e_cobranca.py

# 3. Simular o disparo de e-mails (simulacao por padrao)
python reproducao/03_disparo_emails.py
```

### Compatibilidade de ambientes

| Ambiente | Suporte | Observacao |
| --- | --- | --- |
| Databricks Runtime 13.x+ | Completo | Salva tabela no Unity Catalog via Spark |
| VSCode / terminal local (Linux, Mac) | Completo | Salva tabela como Parquet local em /tmp |
| VSCode / terminal local (Windows) | Completo | Salva em %TEMP% (deteccao automatica) |
| GitHub Actions / CI-CD | Completo | Mesma execucao local sem Spark |
| Google Colab | Completo | Mesma execucao local sem Spark |

A deteccao de ambiente e automatica: o script tenta importar PySpark e, se nao encontrar,
usa pandas + Parquet local. Nenhuma alteracao de codigo e necessaria.

### Estrutura dos Arquivos

```
reproducao/
+-- 01_setup_dados_simulados.py    # Gera planilha + tabela simulada
+-- 02_validacao_e_cobranca.py     # Valida dados e gera payloads
+-- 03_disparo_emails.py           # Dispara e-mails (simulacao ou producao)
+-- create_table_simulada.sql      # DDL alternativo (Databricks e DuckDB)
+-- requirements.txt               # Dependencias Python
```

### Descricao de Cada Arquivo

| Arquivo | O que faz | Output |
| --- | --- | --- |
| `01_setup_dados_simulados.py` | Gera 15 distribuidores ficticios em Excel, cria tabela simulada (Unity Catalog ou Parquet local) | `config_distribuidores.xlsx` + tabela |
| `02_validacao_e_cobranca.py` | Le config + consulta tabela, aplica regra de SLA (3 dias uteis), gera payloads de e-mail | `payloads_cobranca.json` |
| `03_disparo_emails.py` | Le os payloads e envia (ou simula envio), com barra de progresso e log de auditoria | `log_envio_cobranca.json` |
| `create_table_simulada.sql` | Alternativa SQL — variacao Databricks (current_date()) e DuckDB (CURRENT_DATE) | Tabela no UC ou DuckDB |
| `requirements.txt` | Lista de dependencias Python para instalacao local | — |

### Configuracoes para Adaptar

Cada script possui um bloco `CONFIGURACOES` no topo. Para adaptar ao seu ambiente:

| Variavel | Arquivo | O que alterar |
| --- | --- | --- |
| `CATALOG` | 01, 02 | Nome do catalog no Unity Catalog (ignorado em execucao local) |
| `SCHEMA` | 01, 02 | Nome do schema (ignorado em execucao local) |
| `SLA_DIAS_UTEIS` | 02 | Quantidade de dias uteis de tolerancia |
| `EXCECOES_D3` | 02 | IDs de distribuidores com SLA diferenciado |
| `MODO` | 02 | "Teste" (redireciona e-mails) ou "Producao" |
| `SIMULAR_ENVIO` | 03 | `True` (nao envia nada) ou `False` (envia de verdade) |
| `WEBHOOK_URL` | 03 | URL do Power Automate — via variavel de ambiente `WEBHOOK_URL` ou `dbutils.secrets` |

### Pre-requisitos

* Python 3.8+
* Pacotes: `pip install -r reproducao/requirements.txt`
* Databricks (opcional): Runtime 13.x+ com Unity Catalog e permissao CREATE TABLE
* Para envio real: endpoint HTTP configurado (Power Automate, Logic Apps, etc.)


## Fontes de Dados

| Fonte | Tipo | Descrição |
| --- | --- | --- |
| Cadastro de Distribuidores | Excel (.xlsx) | Contém IDs, nomes, CNPJs e e-mails de contato |
| Tabela Fato Sell-out | Unity Catalog (Camada Silver) | Dados de notas fiscais com datas e metadados |
| Endpoint Power Automate | Secret (Key Vault) | URL HTTP trigger para disparo de e-mails |

---

## Parâmetros de Execução

| Parâmetro | Tipo | Finalidade |
| --- | --- | --- |
| `mode` | Dropdown (Teste/Produção) | Controla se e-mails vão para endereço de teste ou destinatários reais |
| `test_email` | Texto | Endereço destino no modo teste |
| `exclude_ids` | Multiselect | IDs de distribuidores a pular na execução atual |

---

## Segurança e Privacidade

* URLs sensíveis armazenadas em Databricks Secrets (nunca hardcoded)
* Modo teste impede envios acidentais para produção
* Notebook executado em compute single-user com ACLs apropriadas
* Dados de CNPJ e contatos vêm de arquivo de configuração controlado
* Nenhum dado pessoal é persistido em logs ou outputs do notebook
* Scripts de reprodução usam dados 100% fictícios

---

## Histórico de Versões

| Versão | Data | Descrição |
| --- | --- | --- |
| 1.0 | 2026-07 | Versão inicial — validação + envio automatizado via notebook |

---

*Documento gerado para fins de documentação no repositório GitHub. Todos os dados foram anonimizados — nomes de empresas, CNPJs, e-mails e identificadores são fictícios. Os scripts da pasta `reproducao/` podem ser executados em qualquer ambiente Databricks sem dependências de dados reais.*
