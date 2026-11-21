import os
from pathlib import Path
from urllib.parse import quote_plus

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

BASE_DIR = Path(__file__).resolve().parent
if load_dotenv:
    load_dotenv(BASE_DIR / ".env")


def _database_url_from_env() -> str:
    direct_url = os.getenv("DATABASE_URL")
    if direct_url:
        return direct_url

    driver = os.getenv("DB_DRIVER", "mysql+pymysql")
    user = quote_plus(os.getenv("DB_USERNAME", "root"))
    password = quote_plus(os.getenv("DB_PASSWORD", ""))
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "3306")
    database = os.getenv("DB_DATABASE", "locadora")
    charset = os.getenv("DB_CHARSET", "utf8mb4")

    if password:
        credentials = f"{user}:{password}"
    else:
        credentials = f"{user}:"

    return f"{driver}://{credentials}@{host}:{port}/{database}?charset={charset}"


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "sim", "yes", "on"}


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "troque-esta-chave-em-producao")
    DATABASE_URL = _database_url_from_env()
    MYSQL_AUTO_CREATE_DATABASE = _as_bool(os.getenv("MYSQL_AUTO_CREATE_DATABASE"), True)
    ADMIN_NOME = os.getenv("ADMIN_NOME", "Administrador")
    ADMIN_CPF = os.getenv("ADMIN_CPF", "000.000.000-00")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@locadora.local")
    ADMIN_USUARIO = os.getenv("ADMIN_USUARIO", "admin")
    ADMIN_SENHA = os.getenv("ADMIN_SENHA", "admin123")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
