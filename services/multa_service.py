from sqlalchemy import select

from database import session_scope
from errors import NotFoundError, ValidationError
from models import Locacao, Multa
from services.utils import clean_string, parse_date, parse_decimal, required


def listar_multas(id_locacao: int | None = None):
    with session_scope() as db:
        query = select(Multa)
        if id_locacao:
            query = query.where(Multa.id_locacao == id_locacao)
        multas = db.scalars(query.order_by(Multa.data_multa.desc(), Multa.id_multa.desc())).all()
        return [multa.to_dict() for multa in multas]


def criar_multa(dados: dict):
    required(dados, ["id_locacao", "motivo", "valor", "data_multa"])
    with session_scope() as db:
        locacao = db.get(Locacao, int(dados["id_locacao"]))
        if not locacao:
            raise ValidationError("Locação não encontrada.")
        multa = Multa(
            id_locacao=locacao.id_locacao,
            motivo=clean_string(dados["motivo"]),
            valor=parse_decimal(dados["valor"], "valor"),
            data_multa=parse_date(dados["data_multa"], "data_multa"),
        )
        db.add(multa)
        db.flush()
        return {"id_multa": multa.id_multa, "mensagem": "Multa registrada com sucesso."}


def deletar_multa(id_multa: int):
    with session_scope() as db:
        multa = db.get(Multa, id_multa)
        if not multa:
            raise NotFoundError("Multa não encontrada.")
        db.delete(multa)
        return True
