from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UsuarioPerfil(BaseModel):
    id: int
    nome: str
    email: str
    perfil: str
    ativo: bool

    model_config = {"from_attributes": True}


class ConsumoItem(BaseModel):
    modulo: str
    total: int


class ConsumoResposta(BaseModel):
    plano: str
    limite_diario: int
    limite_mensal: int
    consumo_hoje: int
    consumo_mes: int
    percentual_diario: float
    percentual_mensal: float
    por_modulo_hoje: list[ConsumoItem] = Field(default_factory=list)
    por_modulo_mes: list[ConsumoItem] = Field(default_factory=list)


class ChaveAcessoEntrada(BaseModel):
    nome: str = Field(..., min_length=3, max_length=100, description="Nome descritivo da chave")


class ChaveAcessoResposta(BaseModel):
    id: int
    nome: str
    prefixo: str
    chave_completa: Optional[str] = None  # Só retornado na criação
    ativa: bool
    ultimo_uso_em: Optional[datetime] = None
    criado_em: datetime

    model_config = {"from_attributes": True}


class AtualizarPerfilEntrada(BaseModel):
    nome: str = Field(..., min_length=2, max_length=200)


class AtualizarSenhaEntrada(BaseModel):
    senha_atual: str = Field(..., min_length=6)
    senha_nova: str = Field(..., min_length=6)
