from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional
from app.database import Base


class ChaveAcesso(Base):
    __tablename__ = "chaves_acesso"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    prefixo: Mapped[str] = mapped_column(String(16), nullable=False)  # exibição: "med_xxxxxxxx..."
    chave_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # SHA-256 do token
    ativa: Mapped[bool] = mapped_column(Boolean, default=True)
    limite_diario_override: Mapped[Optional[int]] = mapped_column(Integer)
    limite_mensal_override: Mapped[Optional[int]] = mapped_column(Integer)
    ultimo_uso_em: Mapped[Optional[datetime]] = mapped_column(DateTime)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    revogada_em: Mapped[Optional[datetime]] = mapped_column(DateTime)

    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="chaves_acesso")
    auditorias: Mapped[list["AuditoriaRequisicao"]] = relationship("AuditoriaRequisicao", back_populates="chave_acesso")
