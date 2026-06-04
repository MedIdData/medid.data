from pydantic import BaseModel, Field, EmailStr


class LoginEntrada(BaseModel):
    email: EmailStr = Field(
        ...,
        description="E-mail cadastrado na plataforma",
        examples=["usuario@empresa.com"]
    )
    senha: str = Field(
        ...,
        min_length=1,
        description="Senha do usuário",
        examples=["senha123"]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "joao@empresa.com",
                    "senha": "minhaSenha123"
                }
            ]
        }
    }


class CadastroEntrada(BaseModel):
    nome: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Nome completo do usuário",
        examples=["João Silva"]
    )
    email: EmailStr = Field(
        ...,
        description="E-mail válido para cadastro",
        examples=["joao@empresa.com"]
    )
    senha: str = Field(
        ...,
        min_length=6,
        max_length=100,
        description="Senha com mínimo de 6 caracteres",
        examples=["senha123"]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "nome": "João Silva",
                    "email": "joao@empresa.com",
                    "senha": "senhaSegura123"
                }
            ]
        }
    }


class TokenSaida(BaseModel):
    access_token: str = Field(
        ...,
        description="Token JWT para autenticação (válido por 30 minutos)",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )
    refresh_token: str = Field(
        ...,
        description="Token para renovar o access_token (válido por 7 dias)",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )
    tipo: str = Field(
        default="bearer",
        description="Tipo de autenticação"
    )
    expira_em: int = Field(
        ...,
        description="Segundos até expiração do access_token",
        examples=[1800]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "tipo": "bearer",
                    "expira_em": 1800
                }
            ]
        }
    }


class RefreshEntrada(BaseModel):
    refresh_token: str = Field(
        ...,
        description="Refresh token obtido no login ou cadastro",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                }
            ]
        }
    }
