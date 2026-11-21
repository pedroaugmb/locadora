from flask import Blueprint, jsonify, request

from auth import admin_required
from services.locacao_service import (
    atualizar_locacao,
    buscar_locacao,
    criar_locacao,
    deletar_locacao,
    finalizar_locacao,
    listar_locacoes,
)

locacao_bp = Blueprint("locacoes", __name__)


@locacao_bp.route("/", methods=["GET"])
@admin_required
def list_locacoes():
    return jsonify(listar_locacoes(request.args.get("status"))), 200


@locacao_bp.route("/<int:id_locacao>", methods=["GET"])
@admin_required
def get_locacao(id_locacao):
    return jsonify(buscar_locacao(id_locacao)), 200


@locacao_bp.route("/", methods=["POST"])
@admin_required
def create():
    return jsonify(criar_locacao(request.get_json(silent=True) or {})), 201


@locacao_bp.route("/<int:id_locacao>", methods=["PUT"])
@admin_required
def update(id_locacao):
    return jsonify(atualizar_locacao(id_locacao, request.get_json(silent=True) or {})), 200


@locacao_bp.route("/<int:id_locacao>/finalizar", methods=["POST"])
@admin_required
def finalize(id_locacao):
    return jsonify(finalizar_locacao(id_locacao)), 200


@locacao_bp.route("/<int:id_locacao>", methods=["DELETE"])
@admin_required
def delete(id_locacao):
    deletar_locacao(id_locacao)
    return jsonify({"message": "Locação deletada com sucesso."}), 200
