-- =====================================================================
-- Seminário II - Banco de Dados II: Locadora de Veículos
-- Script: 01_schema.sql
-- Descrição: DDL de criação do banco de dados e das 6 tabelas relacionais.
-- =====================================================================

CREATE DATABASE IF NOT EXISTS `locadora`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `locadora`;

-- 1. Tabela: funcionarios
CREATE TABLE IF NOT EXISTS `funcionarios` (
    `id_funcionario` INT AUTO_INCREMENT PRIMARY KEY,
    `nome` VARCHAR(100) NOT NULL,
    `cpf` VARCHAR(14) NOT NULL UNIQUE,
    `email` VARCHAR(100) NOT NULL UNIQUE,
    `senha_hash` VARCHAR(255) NULL,
    `telefone` VARCHAR(20) NULL,
    `cargo` VARCHAR(50) NULL,
    `usuario` VARCHAR(50) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Tabela: clientes
CREATE TABLE IF NOT EXISTS `clientes` (
    `cpf` VARCHAR(14) PRIMARY KEY,
    `nome` VARCHAR(100) NOT NULL,
    `telefone` VARCHAR(20) NULL,
    `email` VARCHAR(100) NULL,
    `cnh` VARCHAR(20) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Tabela: veiculos
CREATE TABLE IF NOT EXISTS `veiculos` (
    `placa` VARCHAR(10) PRIMARY KEY,
    `marca` VARCHAR(50) NOT NULL,
    `modelo` VARCHAR(50) NOT NULL,
    `ano` INT NOT NULL,
    `valor_diaria` DECIMAL(10, 2) NOT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'DISPONIVEL',
    CONSTRAINT `ck_veiculo_status` CHECK (`status` IN ('DISPONIVEL', 'ALUGADO', 'MANUTENCAO'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Tabela: locacoes
CREATE TABLE IF NOT EXISTS `locacoes` (
    `id_locacao` INT AUTO_INCREMENT PRIMARY KEY,
    `cpf_cliente` VARCHAR(14) NOT NULL,
    `placa_veiculo` VARCHAR(10) NOT NULL,
    `id_funcionario` INT NOT NULL,
    `data_retirada` DATE NOT NULL,
    `data_devolucao` DATE NOT NULL,
    `valor_total` DECIMAL(10, 2) NOT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'ATIVA',
    CONSTRAINT `ck_locacao_status` CHECK (`status` IN ('ATIVA', 'FINALIZADA', 'CANCELADA')),
    CONSTRAINT `fk_locacao_cliente` FOREIGN KEY (`cpf_cliente`) REFERENCES `clientes` (`cpf`) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_locacao_veiculo` FOREIGN KEY (`placa_veiculo`) REFERENCES `veiculos` (`placa`) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_locacao_funcionario` FOREIGN KEY (`id_funcionario`) REFERENCES `funcionarios` (`id_funcionario`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Tabela: pagamentos
CREATE TABLE IF NOT EXISTS `pagamentos` (
    `id_pagamento` INT AUTO_INCREMENT PRIMARY KEY,
    `id_locacao` INT NOT NULL,
    `valor` DECIMAL(10, 2) NOT NULL,
    `forma_pagamento` VARCHAR(30) NOT NULL,
    `data_pagamento` DATE NOT NULL,
    CONSTRAINT `fk_pagamento_locacao` FOREIGN KEY (`id_locacao`) REFERENCES `locacoes` (`id_locacao`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Tabela: multas
CREATE TABLE IF NOT EXISTS `multas` (
    `id_multa` INT AUTO_INCREMENT PRIMARY KEY,
    `id_locacao` INT NOT NULL,
    `motivo` VARCHAR(255) NOT NULL,
    `valor` DECIMAL(10, 2) NOT NULL,
    `data_multa` DATE NOT NULL,
    CONSTRAINT `fk_multa_locacao` FOREIGN KEY (`id_locacao`) REFERENCES `locacoes` (`id_locacao`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
