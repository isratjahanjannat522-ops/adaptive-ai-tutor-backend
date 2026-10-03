from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    SECRET_KEY: str = "dev-secret-key-change-in-production-please-use-long-random-string"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_MINUTES: int = 60
    REFRESH_TOKEN_DAYS: int = 7

    # This will now read from .env file
    DATABASE_URL: str

    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "openrouter/free"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # ========== EMAIL SETTINGS (Gmail) ==========
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = ""
    MAIL_FROM_NAME: str = "Adaptive AI Tutor"
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_PORT: int = 587

    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://127.0.0.1:8000"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()