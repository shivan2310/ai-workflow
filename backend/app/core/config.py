from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_NAME: str = "AutoPilot AI"
    API_PREFIX: str = "/api"

    # Database
    DATABASE_URL: str = "sqlite:///./test.db"

    # Supabase Auth
    SUPABASE_URL: str = "https://placeholder.supabase.co"
    SUPABASE_JWKS_URL: Optional[str] = None
    SUPABASE_JWT_ISSUER: Optional[str] = None
    SUPABASE_JWT_AUDIENCE: str = "authenticated"
    SUPABASE_JWT_SECRET: Optional[str] = None

    # Cloud LLM: GPT-OSS 120B
    LLM_PROVIDER: str = "cloud"
    LLM_API_BASE_URL: str = "https://api.cloud-provider.com/v1"
    LLM_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-oss-120b"
    LLM_TIMEOUT_SECONDS: int = 60
    MAX_PLANNER_RETRIES: int = 2

    # Frontend Integration
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def jwks_url(self) -> str:
        if self.SUPABASE_JWKS_URL:
            return self.SUPABASE_JWKS_URL
        return f"{self.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"

    @property
    def jwt_issuer(self) -> str:
        if self.SUPABASE_JWT_ISSUER:
            return self.SUPABASE_JWT_ISSUER
        return f"{self.SUPABASE_URL.rstrip('/')}/auth/v1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
