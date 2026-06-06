from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional
from app.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empresa_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("empresas.id"))
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    senha_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    perfil: Mapped[str] = mapped_column(String(20), nullable=False, default="USUARIO")  # ADMINISTRADOR | USUARIO
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    limite_diario: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # NULL = ilimitado ou usa plano
    limite_mensal: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # NULL = ilimitado ou usa plano
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    empresa: Mapped[Optional["Empresa"]] = relationship("Empresa", back_populates="usuarios")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship("RefreshToken", back_populates="usuario", cascade="all, delete-orphan")
    chaves_acesso: Mapped[list["ChaveAcesso"]] = relationship("ChaveAcesso", back_populates="usuario", cascade="all, delete-orphan")
    consumo: Mapped[list["ConsumoDiario"]] = relationship("ConsumoDiario", back_populates="usuario", cascade="all, delete-orphan")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    expira_em: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revogado: Mapped[bool] = mapped_column(Boolean, default=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="refresh_tokens")
