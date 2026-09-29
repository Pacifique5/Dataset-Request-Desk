"""Application settings, loaded from environment variables (and .env locally)."""

from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    database_url: str = "postgresql+psycopg://postgres@localhost:5432/dataset_desk"
    jwt_secret: str = Field(default="change-me", min_length=8)
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    # Secure cookies are only sent over HTTPS. Disable only for plain-HTTP local runs.
    cookie_secure: bool = True
    cors_origins: str = "http://localhost:3000"
    log_level: str = "INFO"

    @model_validator(mode="after")
    def _no_default_secret_in_production(self) -> "Settings":
        if self.app_env == "production" and self.jwt_secret in {"change-me", ""}:
            raise ValueError("JWT_SECRET must be set to a strong random value in production")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
