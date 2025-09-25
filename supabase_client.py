"""Supabase helper utilities for the Pantheon of Oracles backend."""
from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Optional
from uuid import uuid4

from supabase import Client, create_client

logger = logging.getLogger(__name__)


class SupabaseConfigurationError(RuntimeError):
    """Raised when Supabase credentials are not available."""


def _get_env(name: str) -> Optional[str]:
    value = os.getenv(name)
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


def _get_supabase_credentials() -> tuple[str, str]:
    url = _get_env("SUPABASE_URL")
    key = _get_env("SUPABASE_SERVICE_ROLE_KEY") or _get_env("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise SupabaseConfigurationError(
            "Supabase credentials are not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY."
        )
    return url, key


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """Return a cached Supabase client instance."""

    url, key = _get_supabase_credentials()
    logger.debug("Creating Supabase client for %s", url)
    return create_client(url, key)


def create_user(username: str, first_name: str, last_name: str, password: str):
    """Create a new user record inside the Supabase ``users`` table."""

    client = get_supabase_client()
    user_id = str(uuid4())
    data = {
        "id": user_id,
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
        "password": password,
    }
    return client.table("users").insert(data).execute()


def save_astrology_profile(user_id: str, profile_json: dict):
    """Persist an astrology profile for the given ``user_id``."""

    client = get_supabase_client()
    data = {
        "id": str(uuid4()),
        "user_id": user_id,
        "profile_json": profile_json,
    }
    return client.table("astrology_profiles").insert(data).execute()


def save_oracle(user_id: str, oracle_type: str, oracle_data: dict):
    """Persist oracle data for the given ``user_id``."""

    client = get_supabase_client()
    data = {
        "id": str(uuid4()),
        "user_id": user_id,
        "oracle_type": oracle_type,
        "oracle_data": oracle_data,
    }
    return client.table("oracles").insert(data).execute()


def get_user_oracles(user_id: str):
    """Fetch all oracles associated with ``user_id``."""

    client = get_supabase_client()
    return client.table("oracles").select("*").eq("user_id", user_id).execute()


__all__ = [
    "SupabaseConfigurationError",
    "get_supabase_client",
    "create_user",
    "save_astrology_profile",
    "save_oracle",
    "get_user_oracles",
]
