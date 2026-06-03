from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class Situacao(str, Enum):
    ADERENTE = "ADERENTE"
    ATENCAO = "ATENCAO"
    NAO_ADERENTE = "NAO_ADERENTE"
    NAO_INFORMADO = "NAO_INFORMADO"


class AnaliseEntrada(BaseModel):
    medicamento: str = Field(..., min_length=2, description="Nome comercial ou princípio ativo")
    preco_informado: float = Field(..., ge=0, description="Preço informado na guia (R$)")
    tratamento: str = Field("", description="Descrição do tratamento ou diagnóstico clínico")
    cid: str = Field("", description="Código CID-10 (ex: J18.9)")
    procedimento: str = Field("", description="Código SIGTAP (ex: 03.01.01.007-2)")
    quantidade: int = Field(1, ge=1, description="Quantidade prescrita")


class AnaliseTratamento(BaseModel):
    situacao: Situacao
    classe_terapeutica: Optional[str] = None
    motivo: str = ""


class AnaliseCid(BaseModel):
    situacao: Situacao
    cid: Optional[str] = None
    descricao: Optional[str] = None
    motivo: str = ""


class AnaliseProced(BaseModel):
    situacao: Situacao
    procedimento: Optional[str] = None
    descricao: Optional[str] = None
    motivo: str = ""


class AnalisePreco(BaseModel):
    situacao: Situacao
    preco_informado: float
    pf: Optional[float] = None
    pmc: Optional[float] = None
    pmvg: Optional[float] = None
    variacao_pf_pct: Optional[float] = None
    variacao_pmc_pct: Optional[float] = None
    variacao_pmvg_pct: Optional[float] = None
    motivo: str = ""


class AnaliseQuantidade(BaseModel):
    situacao: Situacao
    quantidade_informada: int
    quantidade_esperada: Optional[int] = None
    motivo: str = ""


class AnaliseResultado(BaseModel):
    """Resultado completo da análise de risco."""
    aderente: bool
    pontuacao_aderencia: int = Field(..., ge=0, le=100)
    pontuacao_risco: int = Field(..., ge=0, le=100)
    potencial_glosa: str = Field(..., description="BAIXO | MEDIO | ALTO")
    classificacao_risco: str = Field(..., description="BAIXO | MEDIO | ALTO")
    motivos: list[str]

    analise_tratamento: AnaliseTratamento
    analise_cid: AnaliseCid
    analise_procedimento: AnaliseProced
    analise_cid_procedimento: AnaliseProced
    analise_preco: AnalisePreco
    analise_quantidade: AnaliseQuantidade

    medicamento_encontrado: Optional[str] = None
    numero_registro: Optional[str] = None
    situacao_anvisa: Optional[str] = None
