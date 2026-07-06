-- =============================================================================
-- create_table_simulada.sql
-- =============================================================================
-- Script DDL para criar a tabela simulada de sell-out.
-- Oferece duas variacoes:
--   A) Databricks / Unity Catalog  — usa current_date() e nomenclatura catalog.schema.table
--   B) DuckDB / SQLite (local)     — usa CURRENT_DATE e arquivos locais
--
-- Alternativa recomendada para ambientes locais: usar o script Python
--   01_setup_dados_simulados.py  (gera o Parquet automaticamente sem SQL)
-- =============================================================================


-- ============================================================
-- VARIACAO A: Databricks / Unity Catalog
-- ============================================================
-- Pre-requisito: permissao CREATE TABLE em catalog_exemplo.sell_out
-- Executar em um notebook SQL ou via %sql em um notebook Python.

-- 1. Criar schema (se necessario)
CREATE SCHEMA IF NOT EXISTS catalog_exemplo.sell_out;

-- 2. Criar tabela
CREATE OR REPLACE TABLE catalog_exemplo.sell_out.fato_sellout (
    distribuidor_id  STRING  COMMENT 'Codigo unico do distribuidor (ex: D01, D02)',
    cnpj             STRING  COMMENT 'CNPJ do distribuidor (14 digitos, sem formatacao)',
    data_nota_fiscal DATE    COMMENT 'Data da ultima nota fiscal recebida',
    data_arquivo     DATE    COMMENT 'Data em que o arquivo foi depositado no Blob Storage',
    quantidade_linhas INT    COMMENT 'Numero de linhas no arquivo enviado',
    nome_arquivo     STRING  COMMENT 'Nome do arquivo CSV enviado pelo distribuidor'
)
COMMENT 'Tabela simulada de sell-out para reproducao do processo de validacao de Blob. Dados ficticios.'
TBLPROPERTIES ('quality' = 'silver');

-- 3. Inserir dados — Databricks usa current_date()
INSERT INTO catalog_exemplo.sell_out.fato_sellout VALUES
-- Em dia
('D01', '12345678000101', current_date() - INTERVAL 1 DAY,  current_date(),                  19839, 'alpha_dist_hoje.csv'),
('D03', '34567890000103', current_date() - INTERVAL 1 DAY,  current_date(),                  27687, 'gamma_log_hoje.csv'),
('D06', '67890123000106', current_date() - INTERVAL 2 DAYS, current_date() - INTERVAL 1 DAY, 118294,'zeta_com_ontem.csv'),
('D07', '78901234000107', current_date() - INTERVAL 2 DAYS, current_date() - INTERVAL 1 DAY, 71553, 'eta_reg_ontem.csv'),
('D08', '89012345000108', current_date() - INTERVAL 1 DAY,  current_date(),                  45230, 'theta_nac_hoje.csv'),
('D09', '90123456000109', current_date() - INTERVAL 1 DAY,  current_date(),                  33891, 'iota_dist_hoje.csv'),
('D10', '01234567000110', current_date() - INTERVAL 2 DAYS, current_date() - INTERVAL 1 DAY, 67452, 'kappa_dist_ontem.csv'),
('D13', '13234567000113', current_date() - INTERVAL 1 DAY,  current_date(),                  28910, 'nu_com_hoje.csv'),
('D15', '15234567000115', current_date() - INTERVAL 2 DAYS, current_date() - INTERVAL 1 DAY, 54321, 'omicron_dist_ontem.csv'),
-- Atrasados
('D02', '23456789000102', current_date() - INTERVAL 5 DAYS,  current_date() - INTERVAL 4 DAYS,  47319, 'beta_com_atrasado.csv'),
('D04', '45678901000104', current_date() - INTERVAL 18 DAYS, current_date() - INTERVAL 17 DAYS, 56126, 'delta_dist_muito_atrasado.csv'),
('D05', '56789012000105', current_date() - INTERVAL 7 DAYS,  current_date() - INTERVAL 6 DAYS,  29855, 'epsilon_alim_atrasado.csv'),
('D11', '11234567000111', current_date() - INTERVAL 5 DAYS,  current_date() - INTERVAL 4 DAYS,  41200, 'lambda_alim_atrasado.csv'),
('D12', '12234567000112', current_date() - INTERVAL 6 DAYS,  current_date() - INTERVAL 5 DAYS,  38750, 'mu_reg_atrasado.csv'),
('D14', '14234567000114', current_date() - INTERVAL 10 DAYS, current_date() - INTERVAL 9 DAYS,  22100, 'xi_log_atrasado.csv');

-- 4. Verificar
SELECT
    distribuidor_id AS ID,
    data_nota_fiscal AS ultima_nf,
    data_arquivo     AS ultimo_arquivo,
    quantidade_linhas AS linhas,
    CASE
        WHEN data_arquivo >= current_date() - INTERVAL 3 DAYS THEN 'Em dia'
        ELSE 'Atrasado'
    END AS status
FROM catalog_exemplo.sell_out.fato_sellout
ORDER BY data_arquivo ASC;


-- ============================================================
-- VARIACAO B: DuckDB (local, sem Databricks)
-- ============================================================
-- Instalar: pip install duckdb
-- Executar: duckdb  (ou via Python: import duckdb; con = duckdb.connect())
--
-- Diferencas em relacao ao Databricks:
--   - CURRENT_DATE  (sem parenteses) em vez de current_date()
--   - Sem catalog de tres partes; usa apenas nome de tabela simples
--   - Sem TBLPROPERTIES / COMMENT na tabela
--   - STRING -> VARCHAR

/*
CREATE OR REPLACE TABLE fato_sellout (
    distribuidor_id  VARCHAR,
    cnpj             VARCHAR,
    data_nota_fiscal DATE,
    data_arquivo     DATE,
    quantidade_linhas INTEGER,
    nome_arquivo     VARCHAR
);

INSERT INTO fato_sellout VALUES
-- Em dia
('D01', '12345678000101', CURRENT_DATE - INTERVAL 1 DAY,  CURRENT_DATE,                  19839, 'alpha_dist_hoje.csv'),
('D03', '34567890000103', CURRENT_DATE - INTERVAL 1 DAY,  CURRENT_DATE,                  27687, 'gamma_log_hoje.csv'),
('D06', '67890123000106', CURRENT_DATE - INTERVAL 2 DAYS, CURRENT_DATE - INTERVAL 1 DAY, 118294,'zeta_com_ontem.csv'),
('D08', '89012345000108', CURRENT_DATE - INTERVAL 1 DAY,  CURRENT_DATE,                  45230, 'theta_nac_hoje.csv'),
-- Atrasados
('D02', '23456789000102', CURRENT_DATE - INTERVAL 5 DAYS,  CURRENT_DATE - INTERVAL 4 DAYS,  47319, 'beta_com_atrasado.csv'),
('D04', '45678901000104', CURRENT_DATE - INTERVAL 18 DAYS, CURRENT_DATE - INTERVAL 17 DAYS, 56126, 'delta_dist_muito_atrasado.csv'),
('D05', '56789012000105', CURRENT_DATE - INTERVAL 7 DAYS,  CURRENT_DATE - INTERVAL 6 DAYS,  29855, 'epsilon_alim_atrasado.csv');

SELECT distribuidor_id, data_arquivo,
       CASE WHEN data_arquivo >= CURRENT_DATE - INTERVAL 3 DAYS THEN 'Em dia' ELSE 'Atrasado' END AS status
FROM fato_sellout ORDER BY data_arquivo;
*/
