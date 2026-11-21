from flask import Blueprint, jsonify, request

from auth import admin_required
from services.veiculo_service import atualizar_veiculo, buscar_veiculo, criar_veiculo, deletar_veiculo, listar_veiculos

veiculo_bp = Blueprint("veiculos", __name__)


@veiculo_bp.route("/", methods=["GET"])
@admin_required
def list_veiculos():
    return jsonify(listar_veiculos(request.args.get("status"))), 200


@veiculo_bp.route("/<string:placa>", methods=["GET"])
@admin_required
def get_veiculo(placa):
    return jsonify(buscar_veiculo(placa)), 200


@veiculo_bp.route("/", methods=["POST"])
@admin_required
def create():
    return jsonify(criar_veiculo(request.get_json(silent=True) or {})), 201


@veiculo_bp.route("/<string:placa>", methods=["PUT"])
@admin_required
def update(placa):
    return jsonify(atualizar_veiculo(placa, request.get_json(silent=True) or {})), 200


@veiculo_bp.route("/<string:placa>", methods=["DELETE"])
@admin_required
def delete(placa):
    deletar_veiculo(placa)
    return jsonify({"message": "Veículo deletado com sucesso."}), 200
