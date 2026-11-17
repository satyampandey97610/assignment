"""Application settings and configuration loaded from environment variables."""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings for Care Concierge service."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/care"
    TEST_DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/care_test"

    LLM_PROVIDER: str = "openai"
    LLM_MODEL: str = "gpt-4o-mini"
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None

    # LLM execution mode: 'live', 'record', or 'replay'
    LLM_MODE: Literal["live", "record", "replay"] = "replay"

    EMBED_MODEL: str = "intfloat/multilingual-e5-small"
    SIM_THRESHOLD: float = 0.80

    SAFETY_TIMEOUT_S: float = 4.0
    LLM_TIMEOUT_S: float = 20.0
    DB_STATEMENT_TIMEOUT_MS: int = 5000
    TOOL_CALL_CAP: int = 4
    SAFETY_REGEX_UNION: bool = True

    LOG_LEVEL: str = "INFO"


settings = Settings()
