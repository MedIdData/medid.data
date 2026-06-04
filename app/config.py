from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://mediddata:mediddata@localhost:5432/mediddata"
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    secret_key: str = "troque-esta-chave-em-producao"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Environment
    environment: str = "development"
    dados_dir: str = "./dados"
    workers: int = 1

    # CORS
    allowed_origins: str = "*"

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # json ou text

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def cors_origins(self) -> List[str]:
        if self.allowed_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(",")]


settings = Settings()
