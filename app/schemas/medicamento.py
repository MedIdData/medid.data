from pydantic import BaseModel, Field
from typing import Optional


class MedicamentoItem(BaseModel):
    """Item de resultado de busca de medicamento."""
    id: int
    numero_registro: Optional[str] = None
    medicamento: Optional[str] = Field(None, description="Nome comercial")
    principio_ativo: Optional[str] = None
    fabricante: Optional[str] = None
    apresentacao: Optional[str] = None
    dosagem: Optional[str] = None
    situacao_anvisa: Optional[str] = Field(None, description="Ativo ou Inativo")
    categoria_regulatoria: Optional[str] = None
    classe_terapeutica: Optional[str] = None
    tarja: Optional[str] = None
    pf: Optional[float] = Field(None, description="Preço Fábrica sem impostos (R$)")
    pmc: Optional[float] = Field(None, description="Preço Máximo ao Consumidor 0% ICMS (R$)")
    pmvg: Optional[float] = Field(None, description="Preço Máximo de Venda ao Governo 0% ICMS (R$)")
    indicacoes: Optional[list[str]] = Field(default_factory=list)
    score_relevancia: float = Field(0.0, ge=0.0, le=1.0)

    model_config = {"from_attributes": True}


class MedicamentoBuscaResposta(BaseModel):
    """Resposta paginada da busca de medicamentos."""
    total: int
    pagina: int
    limite: int
    termo: str
    resultados: list[MedicamentoItem]
    sugestao: Optional[str] = Field(None, description="Sugestão ortográfica quando sem resultados")


class MedicamentoDetalhe(BaseModel):
    """Detalhes completos de um medicamento."""
    id: int
    numero_registro: Optional[str] = None
    medicamento: Optional[str] = None
    principio_ativo: Optional[str] = None
    fabricante: Optional[str] = None
    apresentacao: Optional[str] = None
    categoria_regulatoria: Optional[str] = None
    classe_terapeutica: Optional[str] = None
    situacao_anvisa: Optional[str] = None
    tarja: Optional[str] = None
    forma_fisica: Optional[str] = None
    sinonimos: Optional[str] = None
    substancias: Optional[str] = None
    codigo_atc: Optional[str] = None
    indicacoes: Optional[str] = None
    pf: Optional[float] = None
    pmc: Optional[float] = None
    pmvg: Optional[float] = None
    pf_12: Optional[float] = None
    pmc_12: Optional[float] = None
    pmvg_12: Optional[float] = None
    pf_17: Optional[float] = None
    pmc_17: Optional[float] = None
    pmvg_17: Optional[float] = None
    pf_18: Optional[float] = None
    pmc_18: Optional[float] = None
    pmvg_18: Optional[float] = None

    model_config = {"from_attributes": True}
