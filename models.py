from decimal import Decimal
from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class SerializableMixin:
    def _decimal_to_float(self, value):
        if isinstance(value, Decimal):
            return float(value)
        return value


class Funcionario(Base, SerializableMixin):
    __tablename__ = "funcionarios"

    id_funcionario: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    cpf: Mapped[str] = mapped_column(String(14), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    senha_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telefone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    cargo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    usuario: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    locacoes = relationship("Locacao", back_populates="funcionario")

    @property
    def is_admin(self) -> bool:
        return (self.cargo or "").strip().upper() in {"ADMIN", "ADMINISTRADOR", "GERENTE"}

    def to_dict(self):
        return {
            "id_funcionario": self.id_funcionario,
            "nome": self.nome,
            "cpf": self.cpf,
            "email": self.email,
            "telefone": self.telefone,
            "cargo": self.cargo,
            "usuario": self.usuario,
        }


class Cliente(Base):
    __tablename__ = "clientes"

    cpf: Mapped[str] = mapped_column(String(14), primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    telefone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cnh: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)

    locacoes = relationship("Locacao", back_populates="cliente")

    def to_dict(self):
        return {"cpf": self.cpf, "nome": self.nome, "telefone": self.telefone, "email": self.email, "cnh": self.cnh}


class Veiculo(Base, SerializableMixin):
    __tablename__ = "veiculos"
    __table_args__ = (
        CheckConstraint("status in ('DISPONIVEL', 'ALUGADO', 'MANUTENCAO')", name="ck_veiculo_status"),
    )

    placa: Mapped[str] = mapped_column(String(10), primary_key=True)
    marca: Mapped[str] = mapped_column(String(50), nullable=False)
    modelo: Mapped[str] = mapped_column(String(50), nullable=False)
    ano: Mapped[int] = mapped_column(Integer, nullable=False)
    valor_diaria: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DISPONIVEL")

    locacoes = relationship("Locacao", back_populates="veiculo")

    def to_dict(self):
        return {
            "placa": self.placa,
            "marca": self.marca,
            "modelo": self.modelo,
            "ano": self.ano,
            "valor_diaria": self._decimal_to_float(self.valor_diaria),
            "status": self.status,
        }


class Locacao(Base, SerializableMixin):
    __tablename__ = "locacoes"
    __table_args__ = (
        CheckConstraint("status in ('ATIVA', 'FINALIZADA', 'CANCELADA')", name="ck_locacao_status"),
    )

    id_locacao: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cpf_cliente: Mapped[str] = mapped_column(String(14), ForeignKey("clientes.cpf"), nullable=False)
    placa_veiculo: Mapped[str] = mapped_column(String(10), ForeignKey("veiculos.placa"), nullable=False)
    id_funcionario: Mapped[int] = mapped_column(Integer, ForeignKey("funcionarios.id_funcionario"), nullable=False)
    data_retirada: Mapped[object] = mapped_column(Date, nullable=False)
    data_devolucao: Mapped[object] = mapped_column(Date, nullable=False)
    valor_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ATIVA")

    cliente = relationship("Cliente", back_populates="locacoes")
    veiculo = relationship("Veiculo", back_populates="locacoes")
    funcionario = relationship("Funcionario", back_populates="locacoes")
    pagamentos = relationship("Pagamento", back_populates="locacao", cascade="all, delete-orphan")
    multas = relationship("Multa", back_populates="locacao", cascade="all, delete-orphan")

    def to_list_dict(self):
        return {
            "id_locacao": self.id_locacao,
            "cliente": self.cliente.nome,
            "veiculo": self.veiculo.modelo,
            "placa": self.placa_veiculo,
            "funcionario": self.funcionario.nome,
            "data_retirada": self.data_retirada.isoformat(),
            "data_devolucao": self.data_devolucao.isoformat(),
            "valor_total": self._decimal_to_float(self.valor_total),
            "status": self.status,
        }

    def to_detail_dict(self):
        data = self.to_list_dict()
        data.update({"cpf_cliente": self.cpf_cliente, "id_funcionario": self.id_funcionario})
        return data


class Pagamento(Base, SerializableMixin):
    __tablename__ = "pagamentos"

    id_pagamento: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_locacao: Mapped[int] = mapped_column(Integer, ForeignKey("locacoes.id_locacao"), nullable=False)
    valor: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    forma_pagamento: Mapped[str] = mapped_column(String(30), nullable=False)
    data_pagamento: Mapped[object] = mapped_column(Date, nullable=False)

    locacao = relationship("Locacao", back_populates="pagamentos")

    def to_dict(self):
        return {
            "id_pagamento": self.id_pagamento,
            "id_locacao": self.id_locacao,
            "valor": self._decimal_to_float(self.valor),
            "forma_pagamento": self.forma_pagamento,
            "data_pagamento": self.data_pagamento.isoformat(),
        }


class Multa(Base, SerializableMixin):
    __tablename__ = "multas"

    id_multa: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_locacao: Mapped[int] = mapped_column(Integer, ForeignKey("locacoes.id_locacao"), nullable=False)
    motivo: Mapped[str] = mapped_column(String(255), nullable=False)
    valor: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    data_multa: Mapped[object] = mapped_column(Date, nullable=False)

    locacao = relationship("Locacao", back_populates="multas")

    def to_dict(self):
        return {
            "id_multa": self.id_multa,
            "id_locacao": self.id_locacao,
            "motivo": self.motivo,
            "valor": self._decimal_to_float(self.valor),
            "data_multa": self.data_multa.isoformat(),
        }


# =====================================================================
# Entidades Mapeadas a partir de Views SQL (Somente Leitura)
# =====================================================================

class VwLocacaoDetalhada(Base, SerializableMixin):
    __tablename__ = "vw_locacoes_detalhadas"
    __table_args__ = {"extend_existing": True}

    id_locacao: Mapped[int] = mapped_column(Integer, primary_key=True)
    status_locacao: Mapped[str] = mapped_column(String(20))
    data_retirada: Mapped[object] = mapped_column(Date)
    data_devolucao: Mapped[object] = mapped_column(Date)
    valor_total: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    cpf_cliente: Mapped[str] = mapped_column(String(14))
    nome_cliente: Mapped[str] = mapped_column(String(100))
    telefone_cliente: Mapped[str | None] = mapped_column(String(20), nullable=True)
    placa_veiculo: Mapped[str] = mapped_column(String(10))
    marca_veiculo: Mapped[str] = mapped_column(String(50))
    modelo_veiculo: Mapped[str] = mapped_column(String(50))
    valor_diaria: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    id_funcionario: Mapped[int] = mapped_column(Integer)
    nome_funcionario: Mapped[str] = mapped_column(String(100))
    total_pago: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    total_multas: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    def to_dict(self):
        return {
            "id_locacao": self.id_locacao,
            "status": self.status_locacao,
            "data_retirada": self.data_retirada.isoformat() if self.data_retirada else None,
            "data_devolucao": self.data_devolucao.isoformat() if self.data_devolucao else None,
            "valor_total": self._decimal_to_float(self.valor_total),
            "cpf_cliente": self.cpf_cliente,
            "cliente": self.nome_cliente,
            "telefone_cliente": self.telefone_cliente,
            "placa": self.placa_veiculo,
            "marca": self.marca_veiculo,
            "veiculo": self.modelo_veiculo,
            "valor_diaria": self._decimal_to_float(self.valor_diaria),
            "id_funcionario": self.id_funcionario,
            "funcionario": self.nome_funcionario,
            "total_pago": self._decimal_to_float(self.total_pago),
            "total_multas": self._decimal_to_float(self.total_multas),
        }


class VwVeiculoDisponivel(Base, SerializableMixin):
    __tablename__ = "vw_veiculos_disponiveis"
    __table_args__ = {"extend_existing": True}

    placa: Mapped[str] = mapped_column(String(10), primary_key=True)
    marca: Mapped[str] = mapped_column(String(50))
    modelo: Mapped[str] = mapped_column(String(50))
    ano: Mapped[int] = mapped_column(Integer)
    valor_diaria: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String(20))

    def to_dict(self):
        return {
            "placa": self.placa,
            "marca": self.marca,
            "modelo": self.modelo,
            "ano": self.ano,
            "valor_diaria": self._decimal_to_float(self.valor_diaria),
            "status": self.status,
        }


class VwFaturamentoFrota(Base, SerializableMixin):
    __tablename__ = "vw_faturamento_frota"
    __table_args__ = {"extend_existing": True}

    marca: Mapped[str] = mapped_column(String(50), primary_key=True)
    modelo: Mapped[str] = mapped_column(String(50), primary_key=True)
    total_locacoes: Mapped[int] = mapped_column(Integer)
    receita_total: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    def to_dict(self):
        return {
            "marca": self.marca,
            "modelo": self.modelo,
            "total_locacoes": self.total_locacoes,
            "receita_total": self._decimal_to_float(self.receita_total),
        }
