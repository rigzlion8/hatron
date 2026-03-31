"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    """Central configuration for the ERP application.

    All values are loaded from environment variables or .env file.
    """

    # App
    APP_NAME: str = "ERP System"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://erp:erp@localhost:5432/erp"
    DATABASE_URL_SYNC: str = "postgresql://erp:erp@localhost:5432/erp"
    DB_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS (Broadened for dev troubleshooting)
    CORS_ORIGINS: List[str] = ["*"]

    # File uploads
    UPLOAD_DIR: str = "./uploads"

    # M-Pesa (Daraja API)
    MPESA_CONSUMER_KEY: str = ""
    MPESA_CONSUMER_SECRET: str = ""
    MPESA_SHORTCODE: str = "174379"  # Sandbox default
    MPESA_PASSKEY: str = ""
    MPESA_CALLBACK_URL: str = "https://example.com/api/v1/pos/payments/mpesa/callback"
    MPESA_InitiatorName: str = ""
    MPESA_InitiatorPassword: str = ""
    MPESA_PartyA: str = ""
    MPESA_PartyB: str = ""
    MPESA_PhoneNumber: str = ""

    # Paystack
    PAYSTACK_SECRET_KEY: str = ""
    PAYSTACK_PUBLIC_KEY: str = ""

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


settings = Settings()
