from pydantic import BaseModel, Field, field_validator
from typing import Optional
from enum import Enum
import re


class Situacao(str, Enum):
    ADERENTE = "ADERENTE"
    ATENCAO = "ATENCAO"
    NAO_ADERENTE = "NAO_ADERENTE"
    NAO_INFORMADO = "NAO_INFORMADO"


class AnaliseEntrada(BaseModel):
    medicamento: str = Field(..., min_length=2, max_length=300, description="Nome comercial ou princípio ativo")
    preco_informado: float = Field(..., ge=0, le=999999.99, description="Preço informado na guia (R$)")
    tratamento: str = Field("", max_length=500, description="Descrição do tratamento ou diagnóstico clínico")
    cid: str = Field("", max_length=10, description="Código CID-10 (ex: J18.9)")
    procedimento: str = Field("", max_length=20, description="Código SIGTAP (ex: 03.01.01.007-2)")
    quantidade: int = Field(1, ge=1, le=9999, description="Quantidade prescrita")

    @field_validator('medicamento')
    @classmethod
    def validar_medicamento(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('Medicamento não pode ser vazio')
        if len(v) < 2:
            raise ValueError('Medicamento deve ter pelo menos 2 caracteres')
        # Deve conter pelo menos uma letra
        if not any(c.isalpha() for c in v):
            raise ValueError('Medicamento deve conter texto, não apenas números')
        return v

    @field_validator('preco_informado')
    @classmethod
    def validar_preco(cls, v: float) -> float:
        if v < 0:
            raise ValueError('Preço não pode ser negativo')
        if v > 999999.99:
            raise ValueError('Preço muito alto (máximo R$ 999.999,99)')
        # Valida que tem no máximo 2 casas decimais
        if round(v, 2) != v:
            raise ValueError('Preço deve ter no máximo 2 casas decimais')
        return round(v, 2)

    @field_validator('quantidade')
    @classmethod
    def validar_quantidade(cls, v: int) -> int:
        if v < 1:
            raise ValueError('Quantidade deve ser pelo menos 1')
        if v > 9999:
            raise ValueError('Quantidade muito alta (máximo 9999)')
        return v

    @field_validator('cid')
    @classmethod
    def validar_cid(cls, v: str) -> str:
        v = v.strip().upper()
        if v and not re.match(r'^[A-Z]\d{2}(\.\d{1,2})?$', v):
            raise ValueError('CID-10 inválido (formato: A00 ou A00.0)')
        return v

    @field_validator('procedimento')
    @classmethod
    def validar_procedimento(cls, v: str) -> str:
        v = v.strip()
        if v and not re.match(r'^\d{2}\.\d{2}\.\d{2}\.\d{3}-\d$', v):
            raise ValueError('Código SIGTAP inválido (formato: 00.00.00.000-0)')
        return v

    @field_validator('tratamento')
    @classmethod
    def validar_tratamento(cls, v: str) -> str:
        v = v.strip()
        if len(v) > 500:
            raise ValueError('Descrição do tratamento muito longa (máximo 500 caracteres)')
        return v


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
