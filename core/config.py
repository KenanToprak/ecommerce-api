import logging
import secrets
from typing import List

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    PROJECT_NAME: str = "E-Commerce API"
    PROJECT_VERSION: str = "1.0.0"

    # Safe local default; configure PostgreSQL in .env for production
    DATABASE_URL: str = "sqlite:///./ecommerce.db"

    # JWT Settings (must be set via .env / environment in production)
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS Settings
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def ensure_secret_key(self) -> "Settings":
        if not self.SECRET_KEY or not self.SECRET_KEY.strip():
            logger.warning(
                "SECRET_KEY is not set in environment or .env; generating an ephemeral key for this process."
            )
            self.SECRET_KEY = secrets.token_urlsafe(32)
        return self


settings = Settings()
