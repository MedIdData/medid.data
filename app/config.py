from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    database_url: str = "postgresql://mediddata:mediddata@localhost:5432/mediddata"
    redis_url: str = "redis://localhost:6379/0"

    secret_key: str = "troque-esta-chave-em-producao"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    environment: str = "development"
    dados_dir: str = "./dados"
    workers: int = 1

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


settings = Settings()
