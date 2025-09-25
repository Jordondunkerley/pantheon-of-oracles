"""Pantheon of Oracles backend configuration helpers."""
from __future__ import annotations

from dataclasses import dataclass
import os
from functools import lru_cache
from typing import Optional


class ConfigurationError(RuntimeError):
    """Raised when critical configuration values are missing."""


@dataclass(slots=True)
class Settings:
    """Runtime configuration values used across the backend."""

    supabase_url: Optional[str]
    supabase_service_role_key: Optional[str]
    pantheon_api_key: Optional[str]
    pantheon_gpt_secret: Optional[str]
    timezone: str = "America/Toronto"

    def require(self, name: str, value: Optional[str]) -> str:
        """Return *value* or raise :class:`ConfigurationError`."""

        if value and value.strip():
            return value
        raise ConfigurationError(f"Missing required configuration value: {name}")


def _get_env(name: str) -> Optional[str]:
    value = os.getenv(name)
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load configuration from environment variables once."""

    return Settings(
        supabase_url=_get_env("SUPABASE_URL"),
        supabase_service_role_key=_get_env("SUPABASE_SERVICE_ROLE_KEY")
        or _get_env("SUPABASE_SERVICE_KEY"),
        pantheon_api_key=_get_env("PANTHEON_API_KEY"),
        pantheon_gpt_secret=_get_env("PANTHEON_GPT_SECRET"),
    )


__all__ = ["ConfigurationError", "Settings", "get_settings"]
