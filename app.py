from flask import Flask, jsonify, redirect, send_from_directory

from config import Config
from database import init_db, remove_session
from errors import AppError
from routes.cliente_routes import cliente_bp
from routes.dashboard_routes import dashboard_bp
from routes.funcionario_routes import funcionario_bp
from routes.locacao_routes import locacao_bp
from routes.multa_routes import multa_bp
from routes.pagamento_routes import pagamento_bp
from routes.veiculo_routes import veiculo_bp


def create_app(config: type[Config] = Config, overrides: dict | None = None) -> Flask:
    app = Flask(__name__, static_folder="frontend", static_url_path="/app")
    app.config.from_object(config)
    if overrides:
        app.config.update(overrides)

    init_db(app.config["DATABASE_URL"], reset=app.config.get("RESET_DATABASE", False))

    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(funcionario_bp, url_prefix="/funcionarios")
    app.register_blueprint(cliente_bp, url_prefix="/clientes")
    app.register_blueprint(veiculo_bp, url_prefix="/veiculos")
    app.register_blueprint(locacao_bp, url_prefix="/locacoes")
    app.register_blueprint(pagamento_bp, url_prefix="/pagamentos")
    app.register_blueprint(multa_bp, url_prefix="/multas")

    @app.route("/", methods=["GET"])
    def root():
        return redirect("/app/")

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "app": "Locadora de Veículos"}), 200

    @app.route("/app/", methods=["GET"])
    @app.route("/app", methods=["GET"])
    def frontend():
        return send_from_directory(app.static_folder, "index.html")

    @app.errorhandler(AppError)
    def handle_app_error(error: AppError):
        return jsonify({"error": error.message}), error.status_code

    @app.errorhandler(404)
    def handle_not_found(_error):
        return jsonify({"error": "Rota não encontrada."}), 404

    @app.errorhandler(500)
    def handle_internal_error(_error):
        return jsonify({"error": "Erro interno no servidor."}), 500

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        remove_session(exception)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=True)
