from sqlalchemy import select

from database import session_scope
from errors import NotFoundError, ValidationError
from models import Locacao, Pagamento
from services.utils import parse_date, parse_decimal, required, upper_string

FORMAS_VALIDAS = {"DINHEIRO", "CARTAO_CREDITO", "CARTAO_DEBITO", "PIX", "TRANSFERENCIA"}


def _validar_forma(forma: str) -> str:
    forma = upper_string(forma)
    if forma not in FORMAS_VALIDAS:
        raise ValidationError("Forma de pagamento inválida.")
    return forma


def listar_pagamentos(id_locacao: int | None = None):
    with session_scope() as db:
        query = select(Pagamento)
        if id_locacao:
            query = query.where(Pagamento.id_locacao == id_locacao)
        pagamentos = db.scalars(query.order_by(Pagamento.data_pagamento.desc(), Pagamento.id_pagamento.desc())).all()
        return [pagamento.to_dict() for pagamento in pagamentos]


def criar_pagamento(dados: dict):
    required(dados, ["id_locacao", "valor", "forma_pagamento", "data_pagamento"])
    with session_scope() as db:
        locacao = db.get(Locacao, int(dados["id_locacao"]))
        if not locacao:
            raise ValidationError("Locação não encontrada.")
        pagamento = Pagamento(
            id_locacao=locacao.id_locacao,
            valor=parse_decimal(dados["valor"], "valor"),
            forma_pagamento=_validar_forma(dados["forma_pagamento"]),
            data_pagamento=parse_date(dados["data_pagamento"], "data_pagamento"),
        )
        db.add(pagamento)
        db.flush()
        return {"id_pagamento": pagamento.id_pagamento, "mensagem": "Pagamento registrado com sucesso."}


def deletar_pagamento(id_pagamento: int):
    with session_scope() as db:
        pagamento = db.get(Pagamento, id_pagamento)
        if not pagamento:
            raise NotFoundError("Pagamento não encontrado.")
        db.delete(pagamento)
        return True
