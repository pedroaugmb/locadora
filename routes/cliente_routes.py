from flask import Blueprint, jsonify, request

from auth import admin_required
from services.cliente_service import atualizar_cliente, buscar_cliente, criar_cliente, deletar_cliente, listar_clientes

cliente_bp = Blueprint("clientes", __name__)


@cliente_bp.route("/", methods=["GET"])
@admin_required
def list_clientes():
    return jsonify(listar_clientes()), 200


@cliente_bp.route("/<string:cpf>", methods=["GET"])
@admin_required
def get_cliente(cpf):
    return jsonify(buscar_cliente(cpf)), 200


@cliente_bp.route("/", methods=["POST"])
@admin_required
def create():
    return jsonify(criar_cliente(request.get_json(silent=True) or {})), 201


@cliente_bp.route("/<string:cpf>", methods=["PUT"])
@admin_required
def update(cpf):
    return jsonify(atualizar_cliente(cpf, request.get_json(silent=True) or {})), 200


@cliente_bp.route("/<string:cpf>", methods=["DELETE"])
@admin_required
def delete(cpf):
    deletar_cliente(cpf)
    return jsonify({"message": "Cliente deletado com sucesso."}), 200
