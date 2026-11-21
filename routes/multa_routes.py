from flask import Blueprint, jsonify, request

from auth import admin_required
from services.multa_service import criar_multa, deletar_multa, listar_multas

multa_bp = Blueprint("multas", __name__)


@multa_bp.route("/", methods=["GET"])
@admin_required
def list_multas():
    id_locacao = request.args.get("id_locacao", type=int)
    return jsonify(listar_multas(id_locacao)), 200


@multa_bp.route("/", methods=["POST"])
@admin_required
def create():
    return jsonify(criar_multa(request.get_json(silent=True) or {})), 201


@multa_bp.route("/<int:id_multa>", methods=["DELETE"])
@admin_required
def delete(id_multa):
    deletar_multa(id_multa)
    return jsonify({"message": "Multa deletada com sucesso."}), 200
