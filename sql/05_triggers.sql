-- =====================================================================
-- Seminário II - Banco de Dados II: Locadora de Veículos
-- Script: 05_triggers.sql
-- Descrição: Triggers para automatização de integridade e sincronismo
--            do status dos veículos a partir de eventos em locações.
-- =====================================================================

USE `locadora`;

DROP TRIGGER IF EXISTS `trg_locacao_after_insert`;
DROP TRIGGER IF EXISTS `trg_locacao_after_update`;
DROP TRIGGER IF EXISTS `trg_locacao_after_delete`;

DELIMITER //

-- 1. Trigger ao inserir locação: marca veículo como ALUGADO
CREATE TRIGGER `trg_locacao_after_insert`
AFTER INSERT ON `locacoes`
FOR EACH ROW
BEGIN
    IF NEW.status = 'ATIVA' THEN
        UPDATE `veiculos`
        SET `status` = 'ALUGADO'
        WHERE `placa` = NEW.placa_veiculo;
    END IF;
END //

-- 2. Trigger ao atualizar locação: sincroniza status do veículo nas transições
CREATE TRIGGER `trg_locacao_after_update`
AFTER UPDATE ON `locacoes`
FOR EACH ROW
BEGIN
    -- Caso a placa do veículo tenha sido alterada
    IF OLD.placa_veiculo <> NEW.placa_veiculo THEN
        IF OLD.status = 'ATIVA' THEN
            UPDATE `veiculos`
            SET `status` = 'DISPONIVEL'
            WHERE `placa` = OLD.placa_veiculo;
        END IF;

        IF NEW.status = 'ATIVA' THEN
            UPDATE `veiculos`
            SET `status` = 'ALUGADO'
            WHERE `placa` = NEW.placa_veiculo;
        END IF;
    ELSE
        -- Mesma placa: verifica transições de status da locação
        IF OLD.status = 'ATIVA' AND NEW.status IN ('FINALIZADA', 'CANCELADA') THEN
            UPDATE `veiculos`
            SET `status` = 'DISPONIVEL'
            WHERE `placa` = NEW.placa_veiculo;
        ELSEIF OLD.status <> 'ATIVA' AND NEW.status = 'ATIVA' THEN
            UPDATE `veiculos`
            SET `status` = 'ALUGADO'
            WHERE `placa` = NEW.placa_veiculo;
        END IF;
    END IF;
END //

-- 3. Trigger ao deletar locação: libera o veículo se a locação estava ATIVA
CREATE TRIGGER `trg_locacao_after_delete`
AFTER DELETE ON `locacoes`
FOR EACH ROW
BEGIN
    IF OLD.status = 'ATIVA' THEN
        UPDATE `veiculos`
        SET `status` = 'DISPONIVEL'
        WHERE `placa` = OLD.placa_veiculo;
    END IF;
END //

DELIMITER ;
