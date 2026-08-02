"""Validated local configuration."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from supportops.errors import ConfigurationError


class Settings(BaseSettings):
    """Application settings with safe, offline defaults."""

    model_config = SettingsConfigDict(
        env_prefix="SUPPORTOPS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Literal["local", "test"] = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    llm_enabled: bool = False
    db_path: Path = Path("data/supportops.db")
    db_busy_timeout_ms: int = Field(default=5000, ge=100, le=30000)
    export_root: Path = Path("exports")
    triage_policy_path: Path | None = None

    @field_validator("llm_enabled")
    @classmethod
    def reject_enabled_llm(cls, value: bool) -> bool:
        if value:
            raise ValueError("LLM must remain disabled")
        return value


def load_settings() -> Settings:
    """Load settings or raise an actionable error without rejected values."""

    try:
        return Settings()
    except ValidationError as exc:
        fields = sorted(
            {
                str(error["loc"][0])
                for error in exc.errors(include_url=False, include_input=False)
                if error["loc"]
            }
        )
        field_text = ", ".join(fields) if fields else "unknown"
        raise ConfigurationError(
            "Invalid SupportOps configuration. Correct environment field(s): "
            f"{field_text}. See .env.example."
        ) from None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return one validated settings instance for the current process."""

    return load_settings()
