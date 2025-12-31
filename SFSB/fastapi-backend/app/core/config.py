from functools import lru_cache
from typing import Optional

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings and configuration.
    Uses environment variables or .env file.
    """

    # Pydantic v2-style configuration
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
    )

    # Application Settings
    APP_NAME: str = "FastAPI Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # API Settings
    API_V1_PREFIX: str = "/api/v1"

    # OpenRouter Configuration
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = "openai/gpt-3.5-turbo"
    OPENROUTER_TIMEOUT: int = 30

    # Database Configuration
    DATABASE_URL: str = "sqlite:///./app.db"

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000


@lru_cache()
def get_settings() -> Settings:
    """
    Create cached settings instance.
    """
    return Settings()
