from sqlalchemy import String, Integer, Boolean, DateTime, Numeric, ForeignKey, Index, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import TSVECTOR
from datetime import datetime
from typing import Optional
from app.database import Base


class SigtapGrupo(Base):
    """Grupos SIGTAP (nível 1 da hierarquia de procedimentos SUS)."""

    __tablename__ = "sigtap_grupos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(2), unique=True, nullable=False, index=True)
    descricao: Mapped[Optional[str]] = mapped_column(String(200))
    competencia: Mapped[Optional[str]] = mapped_column(String(6))

    procedimentos: Mapped[list["SigtapProcedimento"]] = relationship(
        "SigtapProcedimento", back_populates="grupo"
    )


class SigtapProcedimento(Base):
    """Tabela de procedimentos SIGTAP (tabela unificada SUS)."""

    __tablename__ = "sigtap_procedimentos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    grupo_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("sigtap_grupos.id"))
    codigo: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    descricao: Mapped[Optional[str]] = mapped_column(String(300))
    complexidade: Mapped[Optional[str]] = mapped_column(String(1))
    sexo: Mapped[Optional[str]] = mapped_column(String(1))
    qt_maxima_execucao: Mapped[Optional[int]] = mapped_column(Integer)
    qt_dias_permanencia: Mapped[Optional[int]] = mapped_column(Integer)
    qt_pontos: Mapped[Optional[int]] = mapped_column(Integer)
    vl_idade_minima: Mapped[Optional[int]] = mapped_column(Integer)
    vl_idade_maxima: Mapped[Optional[int]] = mapped_column(Integer)
    vl_sh: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    vl_sa: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    vl_sp: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    codigo_financiamento: Mapped[Optional[str]] = mapped_column(String(2))
    codigo_rubrica: Mapped[Optional[str]] = mapped_column(String(6))
    qt_tempo_permanencia: Mapped[Optional[int]] = mapped_column(Integer)
    competencia: Mapped[Optional[str]] = mapped_column(String(6))

    search_vector = Column(TSVECTOR)

    grupo: Mapped[Optional[SigtapGrupo]] = relationship("SigtapGrupo", back_populates="procedimentos")
    cids: Mapped[list["SigtapProcedimentoCid"]] = relationship(
        "SigtapProcedimentoCid", back_populates="procedimento"
    )

    __table_args__ = (
        Index("ix_sigtap_procedimentos_search_gin", "search_vector", postgresql_using="gin"),
        Index("ix_sigtap_procedimentos_descricao_trgm", "descricao", postgresql_using="gin",
              postgresql_ops={"descricao": "gin_trgm_ops"}),
    )


class SigtapProcedimentoCid(Base):
    """Relação entre procedimentos SIGTAP e CIDs compatíveis."""

    __tablename__ = "sigtap_procedimento_cid"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    procedimento_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("sigtap_procedimentos.id"))
    cid_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("cid10_subcategorias.id"))
    codigo_procedimento: Mapped[Optional[str]] = mapped_column(String(10), index=True)
    codigo_cid: Mapped[Optional[str]] = mapped_column(String(5), index=True)
    principal: Mapped[Optional[bool]] = mapped_column(Boolean)
    competencia: Mapped[Optional[str]] = mapped_column(String(6))

    procedimento: Mapped[Optional[SigtapProcedimento]] = relationship(
        "SigtapProcedimento", back_populates="cids"
    )
    cid: Mapped[Optional["Cid10Subcategoria"]] = relationship(
        "Cid10Subcategoria", back_populates="procedimentos_cid"
    )
