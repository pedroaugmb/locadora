from sqlalchemy import select

from database import session_scope
from errors import NotFoundError, ValidationError
from models import Veiculo
from services.utils import clean_string, parse_decimal, required, upper_string

STATUS_VALIDOS = {"DISPONIVEL", "ALUGADO", "MANUTENCAO"}


def _validar_status(status: str | None) -> str:
    status = upper_string(status) or "DISPONIVEL"
    if status not in STATUS_VALIDOS:
        raise ValidationError("Status inválido. Use DISPONIVEL, ALUGADO ou MANUTENCAO.")
    return status


def listar_veiculos(status_filtro: str | None = None):
    with session_scope() as db:
        query = select(Veiculo)
        if status_filtro:
            query = query.where(Veiculo.status == _validar_status(status_filtro))
        veiculos = db.scalars(query.order_by(Veiculo.marca, Veiculo.modelo)).all()
        return [veiculo.to_dict() for veiculo in veiculos]


def buscar_veiculo(placa: str):
    with session_scope() as db:
        veiculo = db.get(Veiculo, upper_string(placa))
        if not veiculo:
            raise NotFoundError("Veículo não encontrado.")
        return veiculo.to_dict()


def criar_veiculo(dados: dict):
    required(dados, ["placa", "marca", "modelo", "ano", "valor_diaria"])
    veiculo = Veiculo(
        placa=upper_string(dados["placa"]),
        marca=clean_string(dados["marca"]),
        modelo=clean_string(dados["modelo"]),
        ano=int(dados["ano"]),
        valor_diaria=parse_decimal(dados["valor_diaria"], "valor_diaria"),
        status=_validar_status(dados.get("status")),
    )
    with session_scope() as db:
        db.add(veiculo)
        db.flush()
        return {"placa": veiculo.placa, "mensagem": "Veículo criado com sucesso."}


def atualizar_veiculo(placa: str, dados: dict):
    with session_scope() as db:
        veiculo = db.get(Veiculo, upper_string(placa))
        if not veiculo:
            raise NotFoundError("Veículo não encontrado.")
        for field in ["marca", "modelo"]:
            if field in dados:
                setattr(veiculo, field, clean_string(dados.get(field)))
        if "ano" in dados:
            veiculo.ano = int(dados["ano"])
        if "valor_diaria" in dados:
            veiculo.valor_diaria = parse_decimal(dados["valor_diaria"], "valor_diaria")
        if "status" in dados:
            veiculo.status = _validar_status(dados.get("status"))
        return {"mensagem": "Veículo atualizado com sucesso."}


def deletar_veiculo(placa: str):
    with session_scope() as db:
        veiculo = db.get(Veiculo, upper_string(placa))
        if not veiculo:
            raise NotFoundError("Veículo não encontrado.")
        db.delete(veiculo)
        return True
