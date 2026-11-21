-- =====================================================================
-- Seminário II - Banco de Dados II: Locadora de Veículos
-- Arquivo: docs/benchmark_explain.sql
-- Descrição: Roteiro experimental de benchmark utilizando EXPLAIN e
--            EXPLAIN ANALYZE (MySQL 8) para demonstrar os ganhos de
--            desempenho obtidos com os índices criados em 02_indexes.sql.
-- =====================================================================

USE `locadora`;

-- =====================================================================
-- 1. CENÁRIO 1: Busca de Veículos por Status ('DISPONIVEL')
-- Coluna avaliada: veiculos.status
-- Índice correspondente: idx_veiculos_status
-- =====================================================================

-- [A] ANTES DO ÍNDICE:
-- Caso o índice já exista no schema, removemos temporariamente para demonstrar o plano sem indexação:
DROP INDEX IF EXISTS `idx_veiculos_status` ON `veiculos`;

-- Execução do EXPLAIN sem o índice:
EXPLAIN SELECT * FROM `veiculos` WHERE `status` = 'DISPONIVEL';

-- EXPLAIN ANALYZE (MySQL 8.0+) para medição de custo e tempo real:
EXPLAIN ANALYZE SELECT * FROM `veiculos` WHERE `status` = 'DISPONIVEL';
-- Observação esperada:
--   - type: ALL (Full Table Scan)
--   - rows: Varre 100% das linhas da tabela
--   - Filter: (veiculos.`status` = 'DISPONIVEL')

-- [B] CRIAÇÃO DO ÍNDICE:
CREATE INDEX `idx_veiculos_status` ON `veiculos` (`status`);

-- [C] DEPOIS DO ÍNDICE:
EXPLAIN SELECT * FROM `veiculos` WHERE `status` = 'DISPONIVEL';

EXPLAIN ANALYZE SELECT * FROM `veiculos` WHERE `status` = 'DISPONIVEL';
-- Observação esperada:
--   - type: ref
--   - key: idx_veiculos_status
--   - rows: Apenas os registros compatíveis no nó folha da B-Tree
--   - Ganho: Evita leitura sequencial do disco


-- =====================================================================
-- 2. CENÁRIO 2: Locações Ativas por Período de Retirada
-- Colunas avaliadas: locacoes.status, locacoes.data_retirada
-- Índice correspondente: idx_locacoes_status_data (Índice Composto)
-- =====================================================================

-- [A] ANTES DO ÍNDICE:
DROP INDEX IF EXISTS `idx_locacoes_status_data` ON `locacoes`;

EXPLAIN SELECT `id_locacao`, `placa_veiculo`, `data_retirada`, `valor_total`
FROM `locacoes`
WHERE `status` = 'ATIVA' AND `data_retirada` >= '2026-01-01'
ORDER BY `data_retirada` DESC;

EXPLAIN ANALYZE SELECT `id_locacao`, `placa_veiculo`, `data_retirada`, `valor_total`
FROM `locacoes`
WHERE `status` = 'ATIVA' AND `data_retirada` >= '2026-01-01'
ORDER BY `data_retirada` DESC;
-- Observação esperada:
--   - type: ALL
--   - Extra: Using where; Using filesort (requer ordenação em memória/disco)

-- [B] CRIAÇÃO DO ÍNDICE COMPOSTO:
CREATE INDEX `idx_locacoes_status_data` ON `locacoes` (`status`, `data_retirada`);

-- [C] DEPOIS DO ÍNDICE COMPOSTO:
EXPLAIN SELECT `id_locacao`, `placa_veiculo`, `data_retirada`, `valor_total`
FROM `locacoes`
WHERE `status` = 'ATIVA' AND `data_retirada` >= '2026-01-01'
ORDER BY `data_retirada` DESC;

EXPLAIN ANALYZE SELECT `id_locacao`, `placa_veiculo`, `data_retirada`, `valor_total`
FROM `locacoes`
WHERE `status` = 'ATIVA' AND `data_retirada` >= '2026-01-01'
ORDER BY `data_retirada` DESC;
-- Observação esperada:
--   - type: range
--   - key: idx_locacoes_status_data
--   - Extra: Using index condition (Backward index scan / elimina o filesort pois a B-Tree já está ordenada)


-- =====================================================================
-- 3. CENÁRIO 3: Pesquisa Textual de Clientes por Prefixo de Nome
-- Coluna avaliada: clientes.nome
-- Índice correspondente: idx_clientes_nome
-- =====================================================================

-- [A] ANTES DO ÍNDICE:
DROP INDEX IF EXISTS `idx_clientes_nome` ON `clientes`;

EXPLAIN SELECT `cpf`, `nome`, `telefone`, `cnh`
FROM `clientes`
WHERE `nome` LIKE 'Maria%';

EXPLAIN ANALYZE SELECT `cpf`, `nome`, `telefone`, `cnh`
FROM `clientes`
WHERE `nome` LIKE 'Maria%';
-- Observação esperada:
--   - type: ALL

-- [B] CRIAÇÃO DO ÍNDICE:
CREATE INDEX `idx_clientes_nome` ON `clientes` (`nome`);

-- [C] DEPOIS DO ÍNDICE:
EXPLAIN SELECT `cpf`, `nome`, `telefone`, `cnh`
FROM `clientes`
WHERE `nome` LIKE 'Maria%';

EXPLAIN ANALYZE SELECT `cpf`, `nome`, `telefone`, `cnh`
FROM `clientes`
WHERE `nome` LIKE 'Maria%';
-- Observação esperada:
--   - type: range
--   - key: idx_clientes_nome
--   - Nota: Consultas com prefixo fixo (LIKE 'Termo%') aproveitam o índice B-Tree,
--     ao contrário de sufixo puro (%Termo), que exigiria Full Table Scan ou Fulltext.


-- =====================================================================
-- 4. CENÁRIO 4: Junção e Agregação de Pagamentos por Contrato
-- Colunas avaliadas: pagamentos.id_locacao (Chave Estrangeira)
-- Índice correspondente: idx_pagamentos_locacao
-- =====================================================================

-- [A] ANTES DO ÍNDICE:
DROP INDEX IF EXISTS `idx_pagamentos_locacao` ON `pagamentos`;

EXPLAIN SELECT 
    l.id_locacao,
    l.status,
    l.valor_total,
    COALESCE(SUM(p.valor), 0) AS total_pago
FROM `locacoes` l
LEFT JOIN `pagamentos` p ON l.id_locacao = p.id_locacao
GROUP BY l.id_locacao, l.status, l.valor_total;

-- [B] CRIAÇÃO DO ÍNDICE NA CHAVE ESTRANGEIRA:
CREATE INDEX `idx_pagamentos_locacao` ON `pagamentos` (`id_locacao`);

-- [C] DEPOIS DO ÍNDICE:
EXPLAIN SELECT 
    l.id_locacao,
    l.status,
    l.valor_total,
    COALESCE(SUM(p.valor), 0) AS total_pago
FROM `locacoes` l
LEFT JOIN `pagamentos` p ON l.id_locacao = p.id_locacao
GROUP BY l.id_locacao, l.status, l.valor_total;
-- Observação esperada:
--   - Na tabela p (pagamentos), type passa para 'ref' usando idx_pagamentos_locacao.
--   - O custo relativo de agregação (join cost) cai proporcionalmente ao volume de pagamentos.
