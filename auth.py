from functools import wraps
from flask import jsonify, session

from database import session_scope
from errors import ForbiddenError, UnauthorizedError
from models import Funcionario


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    with session_scope() as db:
        user = db.get(Funcionario, int(user_id))
        return user.to_dict() | {"is_admin": user.is_admin} if user else None


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            raise UnauthorizedError("Faça login como administrador para continuar.")
        with session_scope() as db:
            user = db.get(Funcionario, int(user_id))
            if not user:
                session.clear()
                raise UnauthorizedError("Sessão inválida. Faça login novamente.")
            if not user.is_admin:
                raise ForbiddenError("Apenas administradores podem acessar esta operação.")
        return fn(*args, **kwargs)
    return wrapper


def auth_error_response(error):
    return jsonify({"error": error.message}), error.status_code
