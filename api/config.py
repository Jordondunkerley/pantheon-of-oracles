"""Centralized configuration and client factories for the Pantheon API.

This module validates required environment variables exactly once and exposes
shared helpers for JWT settings and the Supabase client. Importing the module
avoids duplicating secret handling across routers.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from supabase import Client, create_client


@dataclass(frozen=True)
class Settings:
    app_name: str
    supabase_url: str
    supabase_service_role_key: str
    jwt_secret: str
    jwt_alg: str = "HS256"
    access_token_expire_minutes: int = 120


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} must be set for the Pantheon API")
    return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and validate configuration from environment variables."""

    app_name = os.getenv("APP_NAME", "Pantheon of Oracles API")
    supabase_url = _require_env("SUPABASE_URL")
    supabase_service_role_key = _require_env("SUPABASE_SERVICE_ROLE_KEY")
    jwt_secret = _require_env("JWT_SECRET")
    access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))

    return Settings(
        app_name=app_name,
        supabase_url=supabase_url,
        supabase_service_role_key=supabase_service_role_key,
        jwt_secret=jwt_secret,
        access_token_expire_minutes=access_token_expire_minutes,
    )


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_role_key)

