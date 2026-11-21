-- =====================================================================
-- Seminário II - Banco de Dados II: Locadora de Veículos
-- Script: 03_views.sql
-- Descrição: Criação de visões (VIEWS) para simplificar consultas
--            gerenciais e evitar múltiplos JOINs repetitivos no backend.
-- =====================================================================

USE `locadora`;

-- 1. Visão de Locações Detalhadas com dados consolidados de cliente, veículo, funcionário, pagamentos e multas
CREATE OR REPLACE VIEW `vw_locacoes_detalhadas` AS
SELECT 
    l.id_locacao,
    l.status AS status_locacao,
    l.data_retirada,
    l.data_devolucao,
    l.valor_total,
    c.cpf AS cpf_cliente,
    c.nome AS nome_cliente,
    c.telefone AS telefone_cliente,
    v.placa AS placa_veiculo,
    v.marca AS marca_veiculo,
    v.modelo AS modelo_veiculo,
    v.valor_diaria,
    f.id_funcionario,
    f.nome AS nome_funcionario,
    COALESCE(p.total_pago, 0.00) AS total_pago,
    COALESCE(m.total_multas, 0.00) AS total_multas
FROM locacoes l
JOIN clientes c ON l.cpf_cliente = c.cpf
JOIN veiculos v ON l.placa_veiculo = v.placa
JOIN funcionarios f ON l.id_funcionario = f.id_funcionario
LEFT JOIN (
    SELECT id_locacao, SUM(valor) AS total_pago 
    FROM pagamentos 
    GROUP BY id_locacao
) p ON l.id_locacao = p.id_locacao
LEFT JOIN (
    SELECT id_locacao, SUM(valor) AS total_multas 
    FROM multas 
    GROUP BY id_locacao
) m ON l.id_locacao = m.id_locacao;

-- 2. Visão de Veículos Disponíveis para novas locações
CREATE OR REPLACE VIEW `vw_veiculos_disponiveis` AS
SELECT 
    placa,
    marca,
    modelo,
    ano,
    valor_diaria,
    status
FROM veiculos
WHERE status = 'DISPONIVEL';

-- 3. Visão Gerencial de Faturamento e Demanda por Modelo/Marca da Frota
CREATE OR REPLACE VIEW `vw_faturamento_frota` AS
SELECT 
    v.marca,
    v.modelo,
    COUNT(l.id_locacao) AS total_locacoes,
    COALESCE(SUM(l.valor_total), 0.00) AS receita_total
FROM veiculos v
LEFT JOIN locacoes l ON v.placa = l.placa_veiculo AND l.status != 'CANCELADA'
GROUP BY v.marca, v.modelo;
