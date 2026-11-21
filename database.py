from contextlib import contextmanager
from pathlib import Path
from sqlalchemy import create_engine, event, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker
from werkzeug.security import generate_password_hash

from config import Config
from errors import ConflictError

Base = declarative_base()
engine = None
SessionLocal = None

VEICULOS_INICIAIS = [
    {"placa": "ABC1A23", "marca": "Toyota", "modelo": "Corolla", "ano": 2022, "valor_diaria": 180.00, "status": "DISPONIVEL"},
    {"placa": "DEF2B34", "marca": "Honda", "modelo": "Civic", "ano": 2021, "valor_diaria": 175.00, "status": "DISPONIVEL"},
    {"placa": "GHI3C45", "marca": "Chevrolet", "modelo": "Onix", "ano": 2023, "valor_diaria": 120.00, "status": "DISPONIVEL"},
    {"placa": "JKL4D56", "marca": "Hyundai", "modelo": "HB20", "ano": 2022, "valor_diaria": 115.00, "status": "DISPONIVEL"},
    {"placa": "MNO5E67", "marca": "Volkswagen", "modelo": "Polo", "ano": 2023, "valor_diaria": 135.00, "status": "DISPONIVEL"},
    {"placa": "PQR6F78", "marca": "Fiat", "modelo": "Argo", "ano": 2021, "valor_diaria": 100.00, "status": "DISPONIVEL"},
]


def _engine_options(database_url: str) -> dict:
    options = {"future": True}
    if database_url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
    if database_url.startswith("mysql"):
        options["pool_pre_ping"] = True
        options["pool_recycle"] = 280
    return options


def _ensure_mysql_database(database_url: str):
    if not database_url.startswith("mysql") or not Config.MYSQL_AUTO_CREATE_DATABASE:
        return

    from sqlalchemy.engine.url import make_url

    url = make_url(database_url)
    database_name = url.database
    if not database_name:
        return

    server_url = url.set(database=None)
    server_engine = create_engine(server_url, **_engine_options(database_url))
    safe_database_name = database_name.replace("`", "``")

    try:
        with server_engine.begin() as connection:
            connection.execute(text(
                f"CREATE DATABASE IF NOT EXISTS `{safe_database_name}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            ))
    finally:
        server_engine.dispose()


def _parse_sql_statements(content: str) -> list[str]:
    lines = content.splitlines()
    statements = []
    current_stmt = []
    delimiter = ";"

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        if stripped.upper().startswith("DELIMITER"):
            parts = stripped.split()
            if len(parts) >= 2:
                delimiter = parts[1]
            continue

        current_stmt.append(line)
        joined = "\n".join(current_stmt).strip()
        if joined.endswith(delimiter):
            clean_stmt = joined[:-len(delimiter)].strip()
            if clean_stmt:
                statements.append(clean_stmt)
            current_stmt = []

    if current_stmt:
        remaining = "\n".join(current_stmt).strip()
        if remaining:
            statements.append(remaining)

    return statements


def _run_mysql_scripts(engine):
    sql_dir = Path(__file__).resolve().parent / "sql"
    if not sql_dir.exists():
        return

    script_files = [
        "02_indexes.sql",
        "03_views.sql",
        "04_procedures.sql",
        "05_triggers.sql",
    ]

    with engine.connect() as connection:
        for file_name in script_files:
            file_path = sql_dir / file_name
            if not file_path.exists():
                continue
            content = file_path.read_text(encoding="utf-8")
            statements = _parse_sql_statements(content)
            for stmt in statements:
                clean_stmt = stmt.strip()
                if clean_stmt.upper().startswith("USE "):
                    continue
                try:
                    connection.execute(text(clean_stmt))
                    connection.commit()
                except Exception as exc:
                    msg = str(exc).lower()
                    if "duplicate key name" in msg or "already exists" in msg:
                        continue
                    pass


def _run_sqlite_views(engine):
    views_sql = [
        """
        CREATE VIEW IF NOT EXISTS vw_veiculos_disponiveis AS
        SELECT placa, marca, modelo, ano, valor_diaria, status
        FROM veiculos
        WHERE status = 'DISPONIVEL';
        """,
        """
        CREATE VIEW IF NOT EXISTS vw_faturamento_frota AS
        SELECT 
            v.marca,
            v.modelo,
            COUNT(l.id_locacao) AS total_locacoes,
            COALESCE(SUM(l.valor_total), 0.0) AS receita_total
        FROM veiculos v
        LEFT JOIN locacoes l ON v.placa = l.placa_veiculo AND l.status != 'CANCELADA'
        GROUP BY v.marca, v.modelo;
        """,
        """
        CREATE VIEW IF NOT EXISTS vw_locacoes_detalhadas AS
        SELECT 
            l.id_locacao,
            l.status AS status_locacao,
            l.data_retirada,
            l.data_devolucao,
            l.valor_total,
            c.cpf AS cpf_cliente,
            c.nome AS nome_cliente,
            c.telefone AS telefone_cliente,
            v.placa AS placa_veiculo,
            v.marca AS marca_veiculo,
            v.modelo AS modelo_veiculo,
            v.valor_diaria,
            f.id_funcionario,
            f.nome AS nome_funcionario,
            COALESCE(p.total_pago, 0.0) AS total_pago,
            COALESCE(m.total_multas, 0.0) AS total_multas
        FROM locacoes l
        JOIN clientes c ON l.cpf_cliente = c.cpf
        JOIN veiculos v ON l.placa_veiculo = v.placa
        JOIN funcionarios f ON l.id_funcionario = f.id_funcionario
        LEFT JOIN (
            SELECT id_locacao, SUM(valor) AS total_pago 
            FROM pagamentos 
            GROUP BY id_locacao
        ) p ON l.id_locacao = p.id_locacao
        LEFT JOIN (
            SELECT id_locacao, SUM(valor) AS total_multas 
            FROM multas 
            GROUP BY id_locacao
        ) m ON l.id_locacao = m.id_locacao;
        """
    ]
    with engine.connect() as connection:
        for stmt in views_sql:
            try:
                connection.execute(text(stmt))
                connection.commit()
            except Exception:
                pass


def init_db(database_url: str | None = None, reset: bool = False):
    global engine, SessionLocal
    url = database_url or Config.DATABASE_URL
    _ensure_mysql_database(url)
    engine = create_engine(url, **_engine_options(url))

    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, _connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    from models import Funcionario, Veiculo

    if reset:
        Base.metadata.drop_all(bind=engine)

    tables_to_create = [t for name, t in Base.metadata.tables.items() if not name.startswith("vw_")]
    Base.metadata.create_all(bind=engine, tables=tables_to_create)

    # Execução das rotinas avançadas de BD2
    if engine.dialect.name == "mysql":
        _run_mysql_scripts(engine)
    elif engine.dialect.name == "sqlite":
        _run_sqlite_views(engine)

    SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True))
    seed_admin(Funcionario)
    seed_veiculos(Veiculo)


def seed_admin(Funcionario):
    session = SessionLocal()
    try:
        exists = session.query(Funcionario).filter(Funcionario.usuario == Config.ADMIN_USUARIO).first()
        if exists:
            return
        admin = Funcionario(
            nome=Config.ADMIN_NOME,
            cpf=Config.ADMIN_CPF,
            email=Config.ADMIN_EMAIL,
            telefone="",
            cargo="ADMIN",
            usuario=Config.ADMIN_USUARIO,
            senha_hash=generate_password_hash(Config.ADMIN_SENHA),
        )
        session.add(admin)
        session.commit()
    except IntegrityError:
        session.rollback()
    finally:
        session.close()


def seed_veiculos(Veiculo):
    session = SessionLocal()
    try:
        total_veiculos = session.scalar(select(func.count(Veiculo.placa))) or 0
        if total_veiculos > 0:
            return
        for item in VEICULOS_INICIAIS:
            session.add(Veiculo(**item))
        session.commit()
    except IntegrityError:
        session.rollback()
    finally:
        session.close()


@contextmanager
def session_scope():
    if SessionLocal is None:
        init_db()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ConflictError("Registro duplicado ou vinculado a outro cadastro.") from exc
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def remove_session(_exception=None):
    if SessionLocal is not None:
        SessionLocal.remove()
