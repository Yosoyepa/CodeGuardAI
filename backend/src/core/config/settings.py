""" Application configuration settings """
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "CodeGuard AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    DATABASE_URL: str = "sqlite:///./dev.db"

    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB

    class Config:
        env_file = ".env"


settings = Settings()
