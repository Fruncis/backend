"""
Application settings — loaded from a YAML config file.

The path to the YAML file is read from the CONFIG_PATH environment variable
(defaults to "config.yaml" in the project root).
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, computed_field, model_validator


# ── Nested setting models ────────────────────────────────────────────────


class ServerSettings(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False


class DatabaseSettings(BaseModel):
    host: str = "localhost"
    port: int = 5432
    name: str = "cv_processor"
    user: str = "postgres"
    password: str = "postgres"

    @model_validator(mode="after")
    def _override_host_from_env(self) -> DatabaseSettings:
        """Allow ``DATABASE_HOST`` env var to override the YAML value.

        This is the key to making Docker work seamlessly: ``docker-compose``
        sets ``DATABASE_HOST=db`` so the backend connects to the Compose
        service name, while local development (no env var) keeps using
        whatever ``config.yaml`` specifies (typically ``localhost``).
        """
        env_host = os.getenv("DATABASE_HOST")
        if env_host:
            self.host = env_host
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def url(self) -> str:
        """Return a valid SQLAlchemy connection string."""
        return (
            f"postgresql+psycopg2://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}"
        )


class AISettings(BaseModel):
    model_name: str = "gemini-3.1-pro-preview"
    api_key_env: str = "GEMINI_API_KEY"
    prompts_file_path: str = "prompts/cv_parsing.txt"

    @property
    def api_key(self) -> str | None:
        """Resolve the actual API key from the environment."""
        return os.getenv(self.api_key_env)


# ── Root settings model ─────────────────────────────────────────────────


class Settings(BaseModel):
    server: ServerSettings = ServerSettings()
    database: DatabaseSettings = DatabaseSettings()
    ai: AISettings = AISettings()


# ── Loader ───────────────────────────────────────────────────────────────


def _load_yaml(path: str | Path) -> dict:
    """Read and parse a YAML config file."""
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Build and cache the application Settings.

    Reads the YAML file whose path is in the CONFIG_PATH env var
    (default: "config.yaml").
    """
    config_path = os.getenv("CONFIG_PATH", "config.yaml")
    raw = _load_yaml(config_path)
    return Settings(**raw)
