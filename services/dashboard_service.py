from sqlalchemy import func, select

from database import session_scope
from models import (
    Cliente,
    Funcionario,
    Locacao,
    Multa,
    Pagamento,
    Veiculo,
    VwFaturamentoFrota,
    VwLocacaoDetalhada,
    VwVeiculoDisponivel,
)


def _count(db, model) -> int:
    return int(db.scalar(select(func.count()).select_from(model)) or 0)


def _ultimos_clientes(db):
    clientes = db.scalars(select(Cliente).order_by(Cliente.cpf.desc()).limit(3)).all()
    return [cliente.to_dict() for cliente in clientes]


def _ultimos_veiculos(db):
    veiculos = db.scalars(select(Veiculo).order_by(Veiculo.placa.desc()).limit(3)).all()
    return [veiculo.to_dict() for veiculo in veiculos]


def _ultimos_funcionarios(db):
    funcionarios = db.scalars(select(Funcionario).order_by(Funcionario.id_funcionario.desc()).limit(3)).all()
    return [funcionario.to_dict() for funcionario in funcionarios]


def _ultimas_locacoes_view(db):
    # Consulta diretamente a VIEW vw_locacoes_detalhadas
    locacoes = db.scalars(
        select(VwLocacaoDetalhada).order_by(VwLocacaoDetalhada.id_locacao.desc()).limit(5)
    ).all()
    return [locacao.to_dict() for locacao in locacoes]


def _veiculos_disponiveis_view(db):
    # Consulta diretamente a VIEW vw_veiculos_disponiveis
    veiculos = db.scalars(select(VwVeiculoDisponivel).limit(5)).all()
    return [veiculo.to_dict() for veiculo in veiculos]


def _faturamento_frota_view(db):
    # Consulta diretamente a VIEW vw_faturamento_frota
    faturamentos = db.scalars(select(VwFaturamentoFrota)).all()
    return [f.to_dict() for f in faturamentos]


def _ultimos_pagamentos(db):
    pagamentos = db.scalars(select(Pagamento).order_by(Pagamento.id_pagamento.desc()).limit(3)).all()
    return [pagamento.to_dict() for pagamento in pagamentos]


def _ultimas_multas(db):
    multas = db.scalars(select(Multa).order_by(Multa.id_multa.desc()).limit(3)).all()
    return [multa.to_dict() for multa in multas]


def resumo_dashboard():
    with session_scope() as db:
        locacoes_view = _ultimas_locacoes_view(db)
        return {
            "counts": {
                "clientes": _count(db, Cliente),
                "veiculos": _count(db, Veiculo),
                "locacoes": _count(db, Locacao),
                "funcionarios": _count(db, Funcionario),
                "pagamentos": _count(db, Pagamento),
                "multas": _count(db, Multa),
            },
            "latest": {
                "clientes": _ultimos_clientes(db),
                "veiculos": _ultimos_veiculos(db),
                "locacoes": locacoes_view[:3],
                "funcionarios": _ultimos_funcionarios(db),
                "pagamentos": _ultimos_pagamentos(db),
                "multas": _ultimas_multas(db),
            },
            # Dados gerenciais provenientes diretamente das Views SQL
            "views": {
                "locacoes_detalhadas": locacoes_view,
                "veiculos_disponiveis": _veiculos_disponiveis_view(db),
                "faturamento_frota": _faturamento_frota_view(db),
            },
        }
