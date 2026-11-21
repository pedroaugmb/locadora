-- =====================================================================
-- Seminário II - Banco de Dados II: Locadora de Veículos
-- Script: 04_procedures.sql
-- Descrição: Stored Procedures para encapsular regras transacionais
--            complexas diretamente no banco de dados.
-- =====================================================================

USE `locadora`;

DROP PROCEDURE IF EXISTS `sp_finalizar_locacao`;

DELIMITER //

CREATE PROCEDURE `sp_finalizar_locacao`(
    IN `p_id_locacao` INT
)
BEGIN
    DECLARE v_valor_diaria DECIMAL(10, 2);
    DECLARE v_dias INT;
    DECLARE v_total_diarias DECIMAL(10, 2);
    DECLARE v_total_multas DECIMAL(10, 2) DEFAULT 0.00;
    DECLARE v_valor_final DECIMAL(10, 2);
    DECLARE v_status_atual VARCHAR(20);
    DECLARE v_data_retirada DATE;
    DECLARE v_data_devolucao DATE;

    -- 1. Obter dados da locação e da diária do veículo
    SELECT l.status, l.data_retirada, l.data_devolucao, v.valor_diaria
    INTO v_status_atual, v_data_retirada, v_data_devolucao, v_valor_diaria
    FROM locacoes l
    JOIN veiculos v ON l.placa_veiculo = v.placa
    WHERE l.id_locacao = p_id_locacao;

    -- 2. Validações de existência e integridade de status
    IF v_status_atual IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Locação não encontrada.';
    END IF;

    IF v_status_atual = 'FINALIZADA' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Esta locação já foi finalizada.';
    END IF;

    -- 3. Cálculo de diárias (mínimo de 1 diária)
    SET v_dias = DATEDIFF(v_data_devolucao, v_data_retirada);
    IF v_dias <= 0 THEN
        SET v_dias = 1;
    END IF;

    SET v_total_diarias = v_dias * v_valor_diaria;

    -- 4. Somatório de multas vinculadas à locação
    SELECT COALESCE(SUM(valor), 0.00)
    INTO v_total_multas
    FROM multas
    WHERE id_locacao = p_id_locacao;

    -- 5. Consolidação do valor final (diárias + multas)
    SET v_valor_final = v_total_diarias + v_total_multas;

    -- 6. Atualização do registro da locação
    -- Nota: A trigger trg_locacao_after_update liberará o veículo automaticamente
    UPDATE locacoes
    SET status = 'FINALIZADA',
        valor_total = v_valor_final
    WHERE id_locacao = p_id_locacao;

END //

DELIMITER ;
