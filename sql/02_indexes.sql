-- =====================================================================
-- Seminário II - Banco de Dados II: Locadora de Veículos
-- Script: 02_indexes.sql
-- Descrição: Criação de índices para otimização de consultas críticas,
--            filtros frequentes e junções entre tabelas.
-- =====================================================================

USE `locadora`;

-- 1. Otimização de filtro por status de veículos (ex.: busca de veículos disponíveis)
CREATE INDEX `idx_veiculos_status`
ON `veiculos` (`status`);

-- 2. Otimização de consultas de locações ativas e ordenação/filtro por período
CREATE INDEX `idx_locacoes_status_data`
ON `locacoes` (`status`, `data_retirada`);

-- 3. Otimização de buscas e junções por cliente nas locações
CREATE INDEX `idx_locacoes_cliente`
ON `locacoes` (`cpf_cliente`);

-- 4. Otimização de histórico de locações por veículo
CREATE INDEX `idx_locacoes_veiculo`
ON `locacoes` (`placa_veiculo`);

-- 5. Otimização de buscas textuais por nome de clientes
CREATE INDEX `idx_clientes_nome`
ON `clientes` (`nome`);

-- 6. Otimização de agregações e junções de pagamentos por locação
CREATE INDEX `idx_pagamentos_locacao`
ON `pagamentos` (`id_locacao`);

-- 7. Otimização de somatório de multas por locação
CREATE INDEX `idx_multas_locacao`
ON `multas` (`id_locacao`);
