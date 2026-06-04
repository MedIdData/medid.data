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
