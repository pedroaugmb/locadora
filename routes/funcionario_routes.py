from flask import Blueprint, jsonify, request, session

from auth import admin_required, current_user
from services.funcionario_service import (
    autenticar_funcionario,
    atualizar_funcionario,
    buscar_funcionario,
    criar_funcionario,
    deletar_funcionario,
    listar_funcionarios,
)

funcionario_bp = Blueprint("funcionarios", __name__)


@funcionario_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    user = autenticar_funcionario(data.get("usuario"), data.get("senha"))
    session.clear()
    session["user_id"] = user["id_funcionario"]
    return jsonify(user), 200


@funcionario_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logout realizado com sucesso."}), 200


@funcionario_bp.route("/me", methods=["GET"])
def me():
    user = current_user()
    return jsonify({"authenticated": bool(user), "user": user}), 200


@funcionario_bp.route("/", methods=["GET"])
@admin_required
def list_funcionarios():
    return jsonify(listar_funcionarios()), 200


@funcionario_bp.route("/<int:id_funcionario>", methods=["GET"])
@admin_required
def get_funcionario(id_funcionario):
    return jsonify(buscar_funcionario(id_funcionario)), 200


@funcionario_bp.route("/", methods=["POST"])
@admin_required
def create():
    return jsonify(criar_funcionario(request.get_json(silent=True) or {})), 201


@funcionario_bp.route("/<int:id_funcionario>", methods=["PUT"])
@admin_required
def update(id_funcionario):
    return jsonify(atualizar_funcionario(id_funcionario, request.get_json(silent=True) or {})), 200


@funcionario_bp.route("/<int:id_funcionario>", methods=["DELETE"])
@admin_required
def delete(id_funcionario):
    deletar_funcionario(id_funcionario, session.get("user_id"))
    return jsonify({"message": "Funcionário deletado com sucesso."}), 200
