# config.py
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):

    # ── ServiceNow ────────────────────────────────────────────
    sn_instance: str
    sn_user: str
    sn_password: str

    # ── Cohere (LLM + embeddings) ─────────────────────────────
    cohere_api_key: str
    cohere_model: str

    # ── PostgreSQL ────────────────────────────────────────────
    postgres_host: str
    postgres_port: int = 5432
    postgres_db: str
    postgres_user: str
    postgres_password: str

    # ── FastAPI ───────────────────────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_env: str = "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def postgres_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def sn_base_url(self) -> str:
        return f"{self.sn_instance}/api/now/table"

    @property
    def is_production(self) -> bool:
        return self.api_env == "production"

    @property
    def is_development(self) -> bool:
        return self.api_env == "development"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()