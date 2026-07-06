-- =============================================================================
-- create_table_simulada.sql
-- =============================================================================
-- Script DDL para criar a tabela simulada de sell-out no Unity Catalog.
-- Use este arquivo como alternativa ao script Python (01_setup_dados_simulados.py)
-- caso prefira criar a tabela manualmente via SQL.
--
-- Pré-requisitos:
--   - Permissão CREATE TABLE no catalog/schema especificado
--   - Altere 'catalog_exemplo.sell_out' para seu catalog.schema
--
-- Uso:
--   Execute cada bloco separadamente ou o script completo em um notebook SQL.
-- =============================================================================

-- 1. Criar schema (se necessário)
CREATE SCHEMA IF NOT EXISTS catalog_exemplo.sell_out;

-- 2. Criar tabela
CREATE OR REPLACE TABLE catalog_exemplo.sell_out.fato_sellout (
    distribuidor_id STRING COMMENT 'Código único do distribuidor (ex: D01, D02)',
    cnpj STRING COMMENT 'CNPJ do distribuidor (14 dígitos, sem formatação)',
    data_nota_fiscal DATE COMMENT 'Data da última nota fiscal recebida',
    data_arquivo DATE COMMENT 'Data em que o arquivo foi depositado no Blob Storage',
    quantidade_linhas INT COMMENT 'Número de linhas no arquivo enviado',
    nome_arquivo STRING COMMENT 'Nome do arquivo CSV enviado pelo distribuidor'
)
COMMENT 'Tabela simulada de sell-out para reprodução do processo de validação de Blob. Dados fictícios.'
TBLPROPERTIES ('quality' = 'silver');

-- 3. Inserir dados simulados
-- Distribuidores em dia (último arquivo recente)
INSERT INTO catalog_exemplo.sell_out.fato_sellout VALUES
('D01', '12345678000101', current_date() - INTERVAL 1 DAY, current_date(), 19839, 'alpha_dist_hoje.csv'),
('D03', '34567890000103', current_date() - INTERVAL 1 DAY, current_date(), 27687, 'gamma_log_hoje.csv'),
('D06', '67890123000106', current_date() - INTERVAL 2 DAYS, current_date() - INTERVAL 1 DAY, 118294, 'zeta_com_ontem.csv'),
('D07', '78901234000107', current_date() - INTERVAL 2 DAYS, current_date() - INTERVAL 1 DAY, 71553, 'eta_reg_ontem.csv'),
('D08', '89012345000108', current_date() - INTERVAL 1 DAY, current_date(), 45230, 'theta_nac_hoje.csv'),
('D09', '90123456000109', current_date() - INTERVAL 1 DAY, current_date(), 33891, 'iota_dist_hoje.csv'),
('D10', '01234567000110', current_date() - INTERVAL 2 DAYS, current_date() - INTERVAL 1 DAY, 67452, 'kappa_dist_ontem.csv'),
('D13', '13234567000113', current_date() - INTERVAL 1 DAY, current_date(), 28910, 'nu_com_hoje.csv'),
('D15', '15234567000115', current_date() - INTERVAL 2 DAYS, current_date() - INTERVAL 1 DAY, 54321, 'omicron_dist_ontem.csv');

-- Distribuidores em atraso (último arquivo com mais de 3 dias úteis)
INSERT INTO catalog_exemplo.sell_out.fato_sellout VALUES
('D02', '23456789000102', current_date() - INTERVAL 5 DAYS, current_date() - INTERVAL 4 DAYS, 47319, 'beta_com_atrasado.csv'),
('D04', '45678901000104', current_date() - INTERVAL 18 DAYS, current_date() - INTERVAL 17 DAYS, 56126, 'delta_dist_muito_atrasado.csv'),
('D05', '56789012000105', current_date() - INTERVAL 7 DAYS, current_date() - INTERVAL 6 DAYS, 29855, 'epsilon_alim_atrasado.csv'),
('D11', '11234567000111', current_date() - INTERVAL 5 DAYS, current_date() - INTERVAL 4 DAYS, 41200, 'lambda_alim_atrasado.csv'),
('D12', '12234567000112', current_date() - INTERVAL 6 DAYS, current_date() - INTERVAL 5 DAYS, 38750, 'mu_reg_atrasado.csv'),
('D14', '14234567000114', current_date() - INTERVAL 10 DAYS, current_date() - INTERVAL 9 DAYS, 22100, 'xi_log_atrasado.csv');

-- 4. Verificar dados inseridos
SELECT
    distribuidor_id AS ID,
    data_nota_fiscal AS ultima_nf,
    data_arquivo AS ultimo_arquivo,
    quantidade_linhas AS linhas,
    CASE
        WHEN data_arquivo >= current_date() - INTERVAL 3 DAYS THEN '✅ Em dia'
        ELSE '⚠️ Atrasado'
    END AS status
FROM catalog_exemplo.sell_out.fato_sellout
ORDER BY data_arquivo ASC;
