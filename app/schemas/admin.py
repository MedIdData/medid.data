"""
Schemas Pydantic para endpoints de administração.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class EstatisticasResposta(BaseModel):
    """Estatísticas gerais do sistema."""
    total_usuarios: int
    usuarios_ativos: int
    total_chaves: int
    requisicoes_hoje: int


class UsuarioDetalhado(BaseModel):
    """Detalhes completos de um usuário (admin)."""
    id: int
    nome: str
    email: EmailStr
    perfil: str
    ativo: bool
    limite_diario: Optional[int] = None
    limite_mensal: Optional[int] = None
    criado_em: Optional[datetime] = None

    class Config:
        from_attributes = True


class CriarUsuarioEntrada(BaseModel):
    """Dados para criar novo usuário (admin)."""
    nome: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    senha: str = Field(..., min_length=6, max_length=100)
    perfil: str = Field(default="USUARIO", pattern="^(USUARIO|ADMINISTRADOR)$")
    limite_diario: int = Field(default=100, ge=0)
    limite_mensal: int = Field(default=2000, ge=0)


class AtualizarUsuarioEntrada(BaseModel):
    """Dados para atualizar usuário existente (admin)."""
    nome: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    perfil: str = Field(..., pattern="^(USUARIO|ADMINISTRADOR)$")
    ativo: bool
    limite_diario: Optional[int] = Field(None, ge=0)
    limite_mensal: Optional[int] = Field(None, ge=0)


class ResetarSenhaEntrada(BaseModel):
    """Dados para resetar senha de usuário (admin)."""
    senha: str = Field(..., min_length=6, max_length=100, description="Nova senha")
