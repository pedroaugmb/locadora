from decimal import Decimal
from sqlalchemy import select, text

from database import session_scope
from errors import NotFoundError, ValidationError
from models import Cliente, Funcionario, Locacao, Veiculo
from services.utils import parse_date, upper_string

STATUS_VALIDOS = {"ATIVA", "FINALIZADA", "CANCELADA"}


def _validar_status(status: str | None) -> str:
    status = upper_string(status) or "ATIVA"
    if status not in STATUS_VALIDOS:
        raise ValidationError("Status inválido. Use ATIVA, FINALIZADA ou CANCELADA.")
    return status


def _calcular_total(veiculo: Veiculo, data_retirada, data_devolucao) -> Decimal:
    if data_devolucao <= data_retirada:
        raise ValidationError("A data de devolução deve ser posterior à data de retirada.")
    dias = max((data_devolucao - data_retirada).days, 1)
    return Decimal(veiculo.valor_diaria) * Decimal(dias)


def listar_locacoes(status_filtro: str | None = None):
    with session_scope() as db:
        query = select(Locacao)
        if status_filtro:
            query = query.where(Locacao.status == _validar_status(status_filtro))
        locacoes = db.scalars(query.order_by(Locacao.id_locacao.desc())).unique().all()
        return [locacao.to_list_dict() for locacao in locacoes]


def buscar_locacao(id_locacao: int):
    with session_scope() as db:
        locacao = db.get(Locacao, id_locacao)
        if not locacao:
            raise NotFoundError("Locação não encontrada.")
        return locacao.to_detail_dict()


def criar_locacao(dados: dict):
    for campo in ["cpf_cliente", "placa_veiculo", "id_funcionario", "data_retirada", "data_devolucao"]:
        if not dados.get(campo):
            raise ValidationError(f"Campo obrigatório ausente: {campo}.")

    data_retirada = parse_date(dados["data_retirada"], "data_retirada")
    data_devolucao = parse_date(dados["data_devolucao"], "data_devolucao")
    placa = upper_string(dados["placa_veiculo"])
    status = _validar_status(dados.get("status"))

    with session_scope() as db:
        cliente = db.get(Cliente, dados["cpf_cliente"])
        if not cliente:
            raise ValidationError("Cliente não encontrado.")
        veiculo = db.get(Veiculo, placa)
        if not veiculo:
            raise ValidationError("Veículo não encontrado.")
        funcionario = db.get(Funcionario, int(dados["id_funcionario"]))
        if not funcionario:
            raise ValidationError("Funcionário não encontrado.")
        if status == "ATIVA" and veiculo.status != "DISPONIVEL":
            raise ValidationError(f"Veículo não está disponível. Status atual: {veiculo.status}.")

        valor_total = _calcular_total(veiculo, data_retirada, data_devolucao)
        locacao = Locacao(
            cpf_cliente=cliente.cpf,
            placa_veiculo=veiculo.placa,
            id_funcionario=funcionario.id_funcionario,
            data_retirada=data_retirada,
            data_devolucao=data_devolucao,
            valor_total=valor_total,
            status=status,
        )
        db.add(locacao)

        # Em MySQL, a Trigger trg_locacao_after_insert altera o status do veículo para ALUGADO.
        # Mantemos fallback para SQLite em ambiente de teste automatizado:
        if db.bind and db.bind.dialect.name == "sqlite" and status == "ATIVA":
            veiculo.status = "ALUGADO"

        db.flush()
        return {
            "id_locacao": locacao.id_locacao,
            "valor_total": float(locacao.valor_total),
            "dias": (data_devolucao - data_retirada).days,
            "mensagem": "Locação criada com sucesso.",
        }


def finalizar_locacao(id_locacao: int):
    with session_scope() as db:
        locacao = db.get(Locacao, id_locacao)
        if not locacao:
            raise NotFoundError("Locação não encontrada.")
        if locacao.status == "FINALIZADA":
            raise ValidationError("Esta locação já foi finalizada.")

        # Em MySQL aciona a Stored Procedure sp_finalizar_locacao
        if db.bind and db.bind.dialect.name == "mysql":
            db.execute(text("CALL sp_finalizar_locacao(:id)"), {"id": id_locacao})
        else:
            # Fallback para SQLite em testes
            total_multas = sum(Decimal(str(m.valor)) for m in locacao.multas)
            dias = max((locacao.data_devolucao - locacao.data_retirada).days, 1)
            locacao.valor_total = (Decimal(locacao.veiculo.valor_diaria) * Decimal(dias)) + total_multas
            locacao.status = "FINALIZADA"
            locacao.veiculo.status = "DISPONIVEL"

        return {"mensagem": "Locação finalizada com sucesso."}


def atualizar_locacao(id_locacao: int, dados: dict):
    with session_scope() as db:
        locacao = db.get(Locacao, id_locacao)
        if not locacao:
            raise NotFoundError("Locação não encontrada.")

        novo_status = _validar_status(dados.get("status")) if "status" in dados else locacao.status
        data_retirada = parse_date(dados["data_retirada"], "data_retirada") if "data_retirada" in dados else locacao.data_retirada
        data_devolucao = parse_date(dados["data_devolucao"], "data_devolucao") if "data_devolucao" in dados else locacao.data_devolucao

        if novo_status == "FINALIZADA" and locacao.status != "FINALIZADA":
            locacao.data_retirada = data_retirada
            locacao.data_devolucao = data_devolucao
            db.flush()
            if db.bind and db.bind.dialect.name == "mysql":
                db.execute(text("CALL sp_finalizar_locacao(:id)"), {"id": id_locacao})
            else:
                total_multas = sum(Decimal(str(m.valor)) for m in locacao.multas)
                dias = max((data_devolucao - data_retirada).days, 1)
                locacao.valor_total = (Decimal(locacao.veiculo.valor_diaria) * Decimal(dias)) + total_multas
                locacao.status = "FINALIZADA"
                locacao.veiculo.status = "DISPONIVEL"
            return {"mensagem": "Locação finalizada com sucesso."}

        locacao.valor_total = _calcular_total(locacao.veiculo, data_retirada, data_devolucao)
        locacao.data_retirada = data_retirada
        locacao.data_devolucao = data_devolucao

        if locacao.status != novo_status:
            if novo_status == "ATIVA" and locacao.veiculo.status != "DISPONIVEL":
                raise ValidationError(f"Veículo não está disponível. Status atual: {locacao.veiculo.status}.")
            locacao.status = novo_status
            # No SQLite, sincroniza manualmente; no MySQL a Trigger trg_locacao_after_update faz isso
            if db.bind and db.bind.dialect.name == "sqlite":
                if novo_status == "ATIVA":
                    locacao.veiculo.status = "ALUGADO"
                elif novo_status in {"FINALIZADA", "CANCELADA"}:
                    locacao.veiculo.status = "DISPONIVEL"

        return {"mensagem": "Locação atualizada com sucesso."}


def deletar_locacao(id_locacao: int):
    with session_scope() as db:
        locacao = db.get(Locacao, id_locacao)
        if not locacao:
            raise NotFoundError("Locação não encontrada.")
        # No SQLite, libera manualmente; no MySQL a Trigger trg_locacao_after_delete cuida disso
        if db.bind and db.bind.dialect.name == "sqlite" and locacao.status == "ATIVA":
            locacao.veiculo.status = "DISPONIVEL"
        db.delete(locacao)
        return True
