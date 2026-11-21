from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from errors import ValidationError


def required(data: dict, fields: list[str]):
    for field in fields:
        value = data.get(field)
        if value is None or str(value).strip() == "":
            raise ValidationError(f"Campo obrigatório ausente: {field}.")


def parse_date(value, field: str) -> date:
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValidationError(f"Campo {field} deve estar no formato YYYY-MM-DD.") from exc


def parse_decimal(value, field: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise ValidationError(f"Campo {field} deve ser um número válido.") from exc
    if number < 0:
        raise ValidationError(f"Campo {field} não pode ser negativo.")
    return number.quantize(Decimal("0.01"))


def clean_string(value):
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def upper_string(value):
    cleaned = clean_string(value)
    return cleaned.upper() if cleaned else cleaned
