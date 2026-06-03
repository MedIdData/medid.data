from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Date, BigInteger, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB, INET
from datetime import datetime, date
from typing import Optional
from app.database import Base


class AuditoriaRequisicao(Base):
    """Registro completo de cada requisição autenticada (web ou API)."""

    __tablename__ = "auditoria_requisicoes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    usuario_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("usuarios.id"))
    chave_acesso_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("chaves_acesso.id"))
    canal: Mapped[str] = mapped_column(String(5), nullable=False)  # WEB | API
    modulo: Mapped[str] = mapped_column(String(20), nullable=False)  # MEDICAMENTOS | ANALISE | CONSUMO | AUTH
    endpoint: Mapped[Optional[str]] = mapped_column(String(200))
    metodo: Mapped[Optional[str]] = mapped_column(String(10))
    parametros_json: Mapped[Optional[dict]] = mapped_column(JSONB)
    resposta_resumo_json: Mapped[Optional[dict]] = mapped_column(JSONB)
    status_http: Mapped[Optional[int]] = mapped_column(Integer)
    tempo_resposta_ms: Mapped[Optional[int]] = mapped_column(Integer)
    ip_origem = mapped_column(INET)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    usuario: Mapped[Optional["Usuario"]] = relationship("Usuario")
    chave_acesso: Mapped[Optional["ChaveAcesso"]] = relationship(
        "ChaveAcesso", back_populates="auditorias"
    )

    __table_args__ = (
        Index("ix_auditoria_usuario_criado", "usuario_id", "criado_em"),
        Index("ix_auditoria_modulo_criado", "modulo", "criado_em"),
    )


class ConsumoDiario(Base):
    """Contador de consumo por usuário, data e módulo (chave composta)."""

    __tablename__ = "consumo_diario"

    usuario_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True
    )
    data_referencia: Mapped[date] = mapped_column(Date, primary_key=True)
    modulo: Mapped[str] = mapped_column(String(20), primary_key=True)
    total_consultas: Mapped[int] = mapped_column(Integer, default=0)

    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="consumo")
