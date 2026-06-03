from sqlalchemy import String, Text, Numeric, Boolean, DateTime, Integer, Index, Column
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import TSVECTOR
from datetime import datetime
from typing import Optional
from app.database import Base


class MedicamentoAnvisa(Base):
    """Registro unificado das duas fontes ANVISA (medicamentos + consulta)."""

    __tablename__ = "medicamentos_anvisa"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    numero_registro: Mapped[Optional[str]] = mapped_column(String(50), unique=True, index=True)
    tipo_produto: Mapped[Optional[str]] = mapped_column(String(50))
    nome_produto: Mapped[Optional[str]] = mapped_column(String(500), index=True)
    data_finalizacao_processo: Mapped[Optional[str]] = mapped_column(String(30))
    categoria_regulatoria: Mapped[Optional[str]] = mapped_column(String(100))
    data_vencimento_registro: Mapped[Optional[str]] = mapped_column(String(30))
    numero_processo: Mapped[Optional[str]] = mapped_column(String(100))
    classe_terapeutica: Mapped[Optional[str]] = mapped_column(String(300))
    empresa_detentora: Mapped[Optional[str]] = mapped_column(String(500))
    situacao_registro: Mapped[Optional[str]] = mapped_column(String(30), index=True)  # Ativo | Inativo
    principio_ativo: Mapped[Optional[str]] = mapped_column(Text)
    # Campos vindos de anvisa_consulta_medicamentos.csv
    indicacoes: Mapped[Optional[str]] = mapped_column(Text)
    sinonimos: Mapped[Optional[str]] = mapped_column(Text)
    codigo_atc: Mapped[Optional[str]] = mapped_column(String(30))
    tarja: Mapped[Optional[str]] = mapped_column(String(50))
    forma_fisica: Mapped[Optional[str]] = mapped_column(String(20))
    situacao_apresentacao: Mapped[Optional[str]] = mapped_column(String(50))
    substancias: Mapped[Optional[str]] = mapped_column(Text)
    importado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Coluna de busca full-text (atualizada pelo script de importação)
    search_vector = Column(TSVECTOR)

    __table_args__ = (
        Index("ix_medicamentos_anvisa_search_gin", "search_vector", postgresql_using="gin"),
        Index("ix_medicamentos_anvisa_nome_trgm", "nome_produto", postgresql_using="gin",
              postgresql_ops={"nome_produto": "gin_trgm_ops"}),
        Index("ix_medicamentos_anvisa_principio_trgm", "principio_ativo", postgresql_using="gin",
              postgresql_ops={"principio_ativo": "gin_trgm_ops"}),
    )


class MedicamentoCmed(Base):
    """Preços CMED: PF (Preço Fábrica), PMC e PMVG por alíquota de ICMS."""

    __tablename__ = "medicamentos_cmed"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo_ggrem: Mapped[Optional[str]] = mapped_column(String(20), unique=True, index=True)
    substancia: Mapped[Optional[str]] = mapped_column(Text)
    cnpj: Mapped[Optional[str]] = mapped_column(String(20))
    laboratorio: Mapped[Optional[str]] = mapped_column(String(300))
    registro: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    ean1: Mapped[Optional[str]] = mapped_column(String(20))
    ean2: Mapped[Optional[str]] = mapped_column(String(20))
    ean3: Mapped[Optional[str]] = mapped_column(String(20))
    produto: Mapped[Optional[str]] = mapped_column(String(500))
    apresentacao: Mapped[Optional[str]] = mapped_column(Text)
    classe_terapeutica: Mapped[Optional[str]] = mapped_column(String(300))
    tipo_produto: Mapped[Optional[str]] = mapped_column(String(100))
    regime_preco: Mapped[Optional[str]] = mapped_column(String(50))
    # Preços fábrica
    pf_sem_impostos: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    pf_0: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    pf_12: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    pf_17: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    pf_17_5: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    pf_18: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    pf_20: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    # Preços máximos ao consumidor
    pmc_sem_impostos: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    pmc_0: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    pmc_12: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    pmc_17: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    pmc_17_5: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    pmc_18: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    pmc_20: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    # Preços máximos de venda ao governo (preenchidos pelo importar_cmed PMVG)
    pmvg_sem_impostos: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    pmvg_0: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    pmvg_12: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    pmvg_17: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    pmvg_17_5: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    pmvg_18: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    pmvg_20: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    # Flags regulatórias
    restricao_hospitalar: Mapped[Optional[bool]] = mapped_column(Boolean)
    cap: Mapped[Optional[bool]] = mapped_column(Boolean)
    confaz_87: Mapped[Optional[bool]] = mapped_column(Boolean)
    icms_0: Mapped[Optional[bool]] = mapped_column(Boolean)
    analise_recursal: Mapped[Optional[str]] = mapped_column(String(5))
    comercializacao_2024: Mapped[Optional[str]] = mapped_column(String(5))
    tarja: Mapped[Optional[str]] = mapped_column(String(50))
    destinacao_comercial: Mapped[Optional[str]] = mapped_column(String(100))
    importado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Dcb(Base):
    """Denominações Comuns Brasileiras (DCB) — lista oficial ANVISA."""

    __tablename__ = "dcb"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    numero_dcb: Mapped[Optional[int]] = mapped_column(Integer, unique=True, index=True)
    denominacao: Mapped[Optional[str]] = mapped_column(String(300), index=True)
    numero_cas: Mapped[Optional[str]] = mapped_column(String(50))
    classificacao: Mapped[Optional[str]] = mapped_column(String(10))  # IFA, INF, HOM, BIO, EXA, PM, RAD
    historico: Mapped[Optional[str]] = mapped_column(Text)
    importado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_dcb_denominacao_trgm", "denominacao", postgresql_using="gin",
              postgresql_ops={"denominacao": "gin_trgm_ops"}),
    )
