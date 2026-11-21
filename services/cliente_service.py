from sqlalchemy import select

from database import session_scope
from errors import NotFoundError
from models import Cliente
from services.utils import clean_string, required


def listar_clientes():
    with session_scope() as db:
        clientes = db.scalars(select(Cliente).order_by(Cliente.nome)).all()
        return [cliente.to_dict() for cliente in clientes]


def buscar_cliente(cpf: str):
    with session_scope() as db:
        cliente = db.get(Cliente, cpf)
        if not cliente:
            raise NotFoundError("Cliente não encontrado.")
        return cliente.to_dict()


def criar_cliente(dados: dict):
    required(dados, ["cpf", "nome", "cnh"])
    cliente = Cliente(
        cpf=clean_string(dados["cpf"]),
        nome=clean_string(dados["nome"]),
        telefone=clean_string(dados.get("telefone")),
        email=clean_string(dados.get("email")),
        cnh=clean_string(dados["cnh"]),
    )
    with session_scope() as db:
        db.add(cliente)
        db.flush()
        return {"cpf": cliente.cpf, "mensagem": "Cliente criado com sucesso."}


def atualizar_cliente(cpf: str, dados: dict):
    with session_scope() as db:
        cliente = db.get(Cliente, cpf)
        if not cliente:
            raise NotFoundError("Cliente não encontrado.")
        for field in ["nome", "telefone", "email", "cnh"]:
            if field in dados:
                setattr(cliente, field, clean_string(dados.get(field)))
        return {"mensagem": "Cliente atualizado com sucesso."}


def deletar_cliente(cpf: str):
    with session_scope() as db:
        cliente = db.get(Cliente, cpf)
        if not cliente:
            raise NotFoundError("Cliente não encontrado.")
        db.delete(cliente)
        return True
