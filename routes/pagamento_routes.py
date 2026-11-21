from flask import Blueprint, jsonify, request

from auth import admin_required
from services.pagamento_service import criar_pagamento, deletar_pagamento, listar_pagamentos

pagamento_bp = Blueprint("pagamentos", __name__)


@pagamento_bp.route("/", methods=["GET"])
@admin_required
def list_pagamentos():
    id_locacao = request.args.get("id_locacao", type=int)
    return jsonify(listar_pagamentos(id_locacao)), 200


@pagamento_bp.route("/", methods=["POST"])
@admin_required
def create():
    return jsonify(criar_pagamento(request.get_json(silent=True) or {})), 201


@pagamento_bp.route("/<int:id_pagamento>", methods=["DELETE"])
@admin_required
def delete(id_pagamento):
    deletar_pagamento(id_pagamento)
    return jsonify({"message": "Pagamento deletado com sucesso."}), 200
