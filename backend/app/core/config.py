from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/marketing_db"
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    REDIS_URL: str = "redis://localhost:6379"
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "anthropic/claude-3.5-sonnet"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama3-70b-8192"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "DEBUG"
    ALLOWED_ORIGINS: str = "http://localhost:5173"
    API_KEY: str = "changeme"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: str) -> str:
        return v

    def get_allowed_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
