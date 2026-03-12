import os
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BASE_DIR: Path = Path(__file__).resolve().parent.parent

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_PRICE_ID: str = ""
    STRIPE_PRICE_SINGLE: str = ""
    STRIPE_PRICE_MONTHLY: str = ""
    STRIPE_PRICE_YEARLY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # Resend
    RESEND_API_KEY: str = ""

    # App
    BASE_URL: str = "http://localhost:5000"
    URL_PREFIX: str = ""
    FLASK_SECRET_KEY: str = "dev-secret-change-me"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres123@localhost:5432/playbooks_development"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres123@localhost:5432/playbooks_development"

    # JWT
    JWT_SECRET_KEY: str = "dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""

    # Sentry
    SENTRY_DSN: str = ""

    # Google Analytics
    GA_MEASUREMENT_ID: str = ""

    # Admin
    ADMIN_UNLOCK_CODE: str = "elijahsentme"

    # Referrals
    REFERRAL_MIN_PAYOUT_CENTS: int = 1000  # $10 minimum
    REFERRAL_TAX_THRESHOLD_CENTS: int = 50000  # $500 warning threshold

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def DATA_DIR(self) -> Path:
        if os.environ.get("RENDER"):
            return Path("/opt/render/project/src/data")
        return self.BASE_DIR / "data"

    @property
    def PDF_PATH(self) -> Path:
        return self.BASE_DIR / "assets" / "conductors_playbook.pdf"

    model_config = {"env_file": ".env"}


settings = Settings()
