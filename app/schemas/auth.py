from pydantic import BaseModel, Field


class LoginEntrada(BaseModel):
    email: str = Field(..., description="E-mail cadastrado")
    senha: str = Field(..., min_length=1)


class CadastroEntrada(BaseModel):
    nome: str = Field(..., min_length=2, max_length=200)
    email: str = Field(...)
    senha: str = Field(..., min_length=6, max_length=100)


class TokenSaida(BaseModel):
    access_token: str
    refresh_token: str
    tipo: str = "bearer"
    expira_em: int = Field(..., description="Segundos até expirar o access token")


class RefreshEntrada(BaseModel):
    refresh_token: str
