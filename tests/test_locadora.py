import pytest
from app import create_app
from database import init_db, SessionLocal
from models import Funcionario, Cliente, Veiculo, Locacao, Pagamento, Multa


@pytest.fixture
def app():
    test_config = {
        "TESTING": True,
        "DATABASE_URL": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret-key",
    }
    app = create_app(overrides=test_config)
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(client):
    # Realiza login do admin padrão
    res = client.post("/funcionarios/login", json={
        "usuario": "admin",
        "senha": "admin123"
    })
    assert res.status_code == 200
    return client


def test_health_check(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json["status"] == "ok"


def test_auth_login_e_logout(client):
    # Login inválido
    res = client.post("/funcionarios/login", json={"usuario": "admin", "senha": "wrong"})
    assert res.status_code == 400

    # Login válido
    res = client.post("/funcionarios/login", json={"usuario": "admin", "senha": "admin123"})
    assert res.status_code == 200
    assert res.json["usuario"] == "admin"

    # Checa usuário logado
    res = client.get("/funcionarios/me")
    assert res.status_code == 200
    assert res.json["authenticated"] is True
    assert res.json["user"]["usuario"] == "admin"

    # Logout
    res = client.post("/funcionarios/logout")
    assert res.status_code == 200

    # Acesso pós logout
    res = client.get("/funcionarios/me")
    assert res.status_code == 200
    assert res.json["authenticated"] is False
    assert res.json["user"] is None


def test_crud_cliente(auth_client):
    # Criar cliente
    novo_cliente = {
        "cpf": "123.456.789-00",
        "nome": "Maria Silva",
        "telefone": "38999998888",
        "email": "maria@exemplo.com",
        "cnh": "12345678900"
    }
    res = auth_client.post("/clientes/", json=novo_cliente)
    assert res.status_code == 201

    # Listar clientes
    res = auth_client.get("/clientes/")
    assert res.status_code == 200
    cpfs = [c["cpf"] for c in res.json]
    assert "123.456.789-00" in cpfs

    # Buscar cliente por CPF
    res = auth_client.get("/clientes/123.456.789-00")
    assert res.status_code == 200
    assert res.json["nome"] == "Maria Silva"

    # Atualizar cliente
    res = auth_client.put("/clientes/123.456.789-00", json={"nome": "Maria Silva Santos"})
    assert res.status_code == 200

    # Deletar cliente
    res = auth_client.delete("/clientes/123.456.789-00")
    assert res.status_code == 200


def test_veiculo_e_locacao_fluxo_completo(auth_client):
    # 1. Cadastra Cliente
    auth_client.post("/clientes/", json={
        "cpf": "111.222.333-44",
        "nome": "João Souza",
        "telefone": "38988887777",
        "email": "joao@exemplo.com",
        "cnh": "99887766554"
    })

    # 2. Cadastra Veículo
    auth_client.post("/veiculos/", json={
        "placa": "TST1234",
        "marca": "Toyota",
        "modelo": "Yaris",
        "ano": 2023,
        "valor_diaria": 150.00,
        "status": "DISPONIVEL"
    })

    # 3. Cria Locação Ativa
    locacao_payload = {
        "cpf_cliente": "111.222.333-44",
        "placa_veiculo": "TST1234",
        "id_funcionario": 1,
        "data_retirada": "2026-11-20",
        "data_devolucao": "2026-11-23",
        "status": "ATIVA"
    }
    res = auth_client.post("/locacoes/", json=locacao_payload)
    assert res.status_code == 201
    id_locacao = res.json["id_locacao"]
    assert res.json["valor_total"] == 450.00  # 3 diárias * 150.00

    # 4. Verifica se o veículo ficou ALUGADO
    res = auth_client.get("/veiculos/TST1234")
    assert res.status_code == 200
    assert res.json["status"] == "ALUGADO"

    # 5. Adiciona Multa à Locação
    res = auth_client.post("/multas/", json={
        "id_locacao": id_locacao,
        "motivo": "Devolução com combustível abaixo do nível",
        "valor": 80.00,
        "data_multa": "2026-11-23"
    })
    assert res.status_code == 201

    # 6. Adiciona Pagamento
    res = auth_client.post("/pagamentos/", json={
        "id_locacao": id_locacao,
        "valor": 530.00,
        "forma_pagamento": "PIX",
        "data_pagamento": "2026-11-23"
    })
    assert res.status_code == 201

    # 7. Finaliza a Locação (chama Procedure no MySQL / Fallback no SQLite)
    res = auth_client.post(f"/locacoes/{id_locacao}/finalizar")
    assert res.status_code == 200

    # 8. Verifica se a locação foi finalizada e o valor consolidado
    res = auth_client.get(f"/locacoes/{id_locacao}")
    assert res.status_code == 200
    assert res.json["status"] == "FINALIZADA"
    assert res.json["valor_total"] == 530.00  # 450 (diárias) + 80 (multa)

    # 9. Verifica se o veículo voltou a ficar DISPONIVEL
    res = auth_client.get("/veiculos/TST1234")
    assert res.status_code == 200
    assert res.json["status"] == "DISPONIVEL"


def test_dashboard_views(auth_client):
    res = auth_client.get("/dashboard/")
    assert res.status_code == 200
    data = res.json
    assert "counts" in data
    assert "latest" in data
    assert "views" in data
    assert "locacoes_detalhadas" in data["views"]
    assert "veiculos_disponiveis" in data["views"]
    assert "faturamento_frota" in data["views"]
