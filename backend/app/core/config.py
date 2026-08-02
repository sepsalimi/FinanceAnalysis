"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    app_secret_key: str = "dev-secret-change-me"
    api_cors_origins: str = "http://localhost:3000"
    access_token_expire_minutes: int = 60 * 24 * 7

    database_url: str = "postgresql+psycopg://finance:finance@localhost:5432/finance_dev"
    test_database_url: str = "postgresql+psycopg://finance:finance@localhost:5432/finance_test"
    redis_url: str = "redis://localhost:6379/0"

    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "finance-uploads"
    s3_region: str = "us-east-1"
    s3_use_ssl: bool = False
    storage_filesystem_fallback: bool = True
    storage_local_path: str = "./.data/uploads"

    llm_provider: str = "stub"
    llm_model: str = "stub-v1"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    llm_base_url: str = ""

    max_upload_bytes: int = 25 * 1024 * 1024
    cookie_name: str = "finance_access_token"
    cookie_secure: bool = False
    cookie_samesite: str = "lax"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.api_cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
