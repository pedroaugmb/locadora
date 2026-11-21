from flask import Blueprint, jsonify

from auth import admin_required
from services.dashboard_service import resumo_dashboard

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/", methods=["GET"])
@admin_required
def summary():
    return jsonify(resumo_dashboard()), 200
