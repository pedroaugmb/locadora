from sqlalchemy import select
from werkzeug.security import check_password_hash, generate_password_hash

from database import session_scope
from errors import ForbiddenError, NotFoundError, ValidationError
from models import Funcionario
from services.utils import clean_string, required


def listar_funcionarios():
    with session_scope() as db:
        funcionarios = db.scalars(select(Funcionario).order_by(Funcionario.nome)).all()
        return [funcionario.to_dict() for funcionario in funcionarios]


def buscar_funcionario(id_funcionario: int):
    with session_scope() as db:
        funcionario = db.get(Funcionario, id_funcionario)
        if not funcionario:
            raise NotFoundError("Funcionário não encontrado.")
        return funcionario.to_dict()


def criar_funcionario(dados: dict):
    required(dados, ["nome", "cpf", "email", "usuario"])
    cargo = clean_string(dados.get("cargo")) or "FUNCIONARIO"
    senha = clean_string(dados.get("senha"))
    if cargo.upper() in {"ADMIN", "ADMINISTRADOR", "GERENTE"} and not senha:
        raise ValidationError("Senha é obrigatória para usuário administrador.")

    funcionario = Funcionario(
        nome=clean_string(dados["nome"]),
        cpf=clean_string(dados["cpf"]),
        email=clean_string(dados["email"]),
        telefone=clean_string(dados.get("telefone")),
        cargo=cargo,
        usuario=clean_string(dados["usuario"]),
        senha_hash=generate_password_hash(senha) if senha else None,
    )
    with session_scope() as db:
        db.add(funcionario)
        db.flush()
        return {"id_funcionario": funcionario.id_funcionario, "mensagem": "Funcionário criado com sucesso."}


def atualizar_funcionario(id_funcionario: int, dados: dict):
    with session_scope() as db:
        funcionario = db.get(Funcionario, id_funcionario)
        if not funcionario:
            raise NotFoundError("Funcionário não encontrado.")

        for field in ["nome", "email", "telefone", "cargo", "usuario"]:
            if field in dados:
                setattr(funcionario, field, clean_string(dados.get(field)))

        senha = clean_string(dados.get("senha")) if "senha" in dados else None
        if senha:
            funcionario.senha_hash = generate_password_hash(senha)

        if funcionario.is_admin and not funcionario.senha_hash:
            raise ValidationError("Senha é obrigatória para usuário administrador.")

        db.flush()
        return {"mensagem": "Funcionário atualizado com sucesso."}


def deletar_funcionario(id_funcionario: int, usuario_logado_id: int | None = None):
    if usuario_logado_id and id_funcionario == usuario_logado_id:
        raise ValidationError("O administrador logado não pode excluir a própria conta.")
    with session_scope() as db:
        funcionario = db.get(Funcionario, id_funcionario)
        if not funcionario:
            raise NotFoundError("Funcionário não encontrado.")
        db.delete(funcionario)
        return True


def autenticar_funcionario(usuario: str, senha: str):
    usuario = clean_string(usuario)
    senha = clean_string(senha)
    if not usuario or not senha:
        raise ValidationError("Usuário e senha são obrigatórios.")

    with session_scope() as db:
        funcionario = db.scalar(select(Funcionario).where(Funcionario.usuario == usuario))
        if not funcionario or not funcionario.senha_hash or not check_password_hash(funcionario.senha_hash, senha):
            raise ValidationError("Usuário ou senha inválidos.")
        if not funcionario.is_admin:
            raise ForbiddenError("Acesso restrito a administradores.")
        return funcionario.to_dict() | {"is_admin": True}
