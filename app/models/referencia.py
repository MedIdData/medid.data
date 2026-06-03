from sqlalchemy import String, Text, Boolean, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional
from app.database import Base


class Cid10Categoria(Base):
    """CID-10: categorias de nível superior (ex: A00 — Cólera)."""

    __tablename__ = "cid10_categorias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(5), unique=True, nullable=False, index=True)
    classif: Mapped[Optional[str]] = mapped_column(String(10))
    descricao: Mapped[Optional[str]] = mapped_column(String(300))
    descricao_abrev: Mapped[Optional[str]] = mapped_column(String(200))
    refer: Mapped[Optional[str]] = mapped_column(String(100))
    excluidos: Mapped[Optional[str]] = mapped_column(Text)

    subcategorias: Mapped[list["Cid10Subcategoria"]] = relationship(
        "Cid10Subcategoria", back_populates="categoria"
    )


class Cid10Subcategoria(Base):
    """CID-10: subcategorias com código de 4 caracteres (ex: A000)."""

    __tablename__ = "cid10_subcategorias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    categoria_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("cid10_categorias.id"))
    codigo: Mapped[str] = mapped_column(String(5), unique=True, nullable=False, index=True)
    classif: Mapped[Optional[str]] = mapped_column(String(10))
    restricao_sexo: Mapped[Optional[str]] = mapped_column(String(5))
    causa_obito: Mapped[Optional[bool]] = mapped_column(Boolean)
    descricao: Mapped[Optional[str]] = mapped_column(String(300))
    descricao_abrev: Mapped[Optional[str]] = mapped_column(String(200))
    refer: Mapped[Optional[str]] = mapped_column(String(100))
    excluidos: Mapped[Optional[str]] = mapped_column(Text)

    categoria: Mapped[Optional[Cid10Categoria]] = relationship(
        "Cid10Categoria", back_populates="subcategorias"
    )
    procedimentos_cid: Mapped[list["SigtapProcedimentoCid"]] = relationship(
        "SigtapProcedimentoCid", back_populates="cid"
    )

    __table_args__ = (
        Index("ix_cid10_subcategorias_descricao_trgm", "descricao", postgresql_using="gin",
              postgresql_ops={"descricao": "gin_trgm_ops"}),
    )
