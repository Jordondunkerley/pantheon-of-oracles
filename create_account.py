"""Utility script for creating Pantheon accounts via Supabase."""
from __future__ import annotations

from dotenv import load_dotenv
from typing import Dict
import uuid

from supabase_client import SupabaseConfigurationError, get_supabase_client

load_dotenv()

_supabase_error: str | None = None
try:
    supabase = get_supabase_client()
except SupabaseConfigurationError as exc:  # pragma: no cover - configuration issue
    supabase = None
    _supabase_error = str(exc)


def create_user(username: str, first_name: str, last_name: str, password: str) -> Dict[str, str]:
    """Create a Pantheon account inside Supabase."""

    if supabase is None:
        return {
            "status": "error",
            "details": _supabase_error or "Supabase client is not configured.",
        }

    user_id = str(uuid.uuid4())
    data = {
        "id": user_id,
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
        "password": password,  # TODO: hash before storing in production
    }

    response = supabase.table("users").insert(data).execute()
    status_code = getattr(response, "status_code", None)

    if status_code == 201:
        return {"status": "success", "user_id": user_id}

    return {
        "status": "error",
        "details": getattr(response, "json", lambda: response)(),
    }


__all__ = ["create_user"]
