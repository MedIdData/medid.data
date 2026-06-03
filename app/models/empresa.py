from sqlalchemy import String, Text, Integer, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from datetime import datetime
from typing import Optional
from app.database import Base


class Plano(Base):
    __tablename__ = "planos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(Text)
    limite_diario: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    limite_mensal: Mapped[int] = mapped_column(Integer, nullable=False, default=2000)
    valor_mensal_centavos: Mapped[int] = mapped_column(Integer, default=0)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    empresas: Mapped[list["Empresa"]] = relationship("Empresa", back_populates="plano")


class Empresa(Base):
    __tablename__ = "empresas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plano_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("planos.id"))
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    cnpj: Mapped[Optional[str]] = mapped_column(String(20), unique=True, index=True)
    email_contato: Mapped[Optional[str]] = mapped_column(String(200))
    ativa: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    plano: Mapped[Optional[Plano]] = relationship("Plano", back_populates="empresas")
    usuarios: Mapped[list["Usuario"]] = relationship("Usuario", back_populates="empresa")
