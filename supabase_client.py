"""
Supabase helper utilities aligned with the new Pantheon schema.

This module keeps secrets in the environment (matching ``api/main.py``) and
provides convenience helpers for scripts/notebooks to create users and upsert
player/oracle profiles without re-implementing the FastAPI validation logic.
"""
from supabase import create_client, Client
from passlib.context import CryptContext
from uuid import uuid4
import os
from typing import Dict, Any, Optional

from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in your environment")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _get_user_record(email: str) -> Optional[Dict[str, Any]]:
    """Return the full user row for the given email, if it exists."""
    res = supabase.table("users").select("id,email,password_hash").eq("email", email).single().execute()
    return res.data if res.data else None


def _get_user_id_by_email(email: str) -> Optional[str]:
    data = _get_user_record(email) or {}
    return data.get("id") if data else None


def create_user(email: str, password: str) -> Dict[str, Any]:
    """Create a user in the "users" table using the hashed password schema."""
    hashed = pwd_context.hash(password)
    res = supabase.table("users").insert({"email": email, "password_hash": hashed}).execute()
    if not res.data:
        raise ValueError("User creation failed; check Supabase logs for details")
    return res.data[0]


def get_or_create_user(email: str, password: str) -> Dict[str, Any]:
    """Return an existing user record or create a new one with the provided password."""
    existing = _get_user_record(email)
    if existing:
        return existing
    return create_user(email, password)


def upsert_player_account(user_email: str, profile: Dict[str, Any]) -> Dict[str, Any]:
    """Upsert a full player profile payload for the given user email."""
    user_id = _get_user_id_by_email(user_email)
    if not user_id:
        raise ValueError("User not found for provided email")

    player_id = profile.get("player_id") or str(uuid4())
    insert_data = {
        "user_id": user_id,
        "player_id": player_id,
        "username": profile.get("username"),
        "email": profile.get("email"),
        "profile": profile,
    }
    res = supabase.table("player_accounts").upsert(insert_data, on_conflict="player_id").execute()
    return res.data[0] if res.data else insert_data


def upsert_oracle_profile(user_email: str, profile: Dict[str, Any]) -> Dict[str, Any]:
    """Upsert an oracle profile payload for the given user email."""
    user_id = _get_user_id_by_email(user_email)
    if not user_id:
        raise ValueError("User not found for provided email")

    oracle_id = profile.get("oracle_id") or str(uuid4())
    insert_data = {
        "user_id": user_id,
        "oracle_id": oracle_id,
        "oracle_name": profile.get("oracle_name") or profile.get("name"),
        "archetype": profile.get("archetype"),
        "profile": profile,
    }
    res = supabase.table("oracle_profiles").upsert(insert_data, on_conflict="oracle_id").execute()

    # Keep the base oracles catalog in sync so oracle_actions inserts do not violate FKs
    supabase.table("oracles").upsert(
        {
            "id": oracle_id,
            "code": insert_data.get("oracle_name") or oracle_id,
            "name": insert_data.get("oracle_name") or oracle_id,
            "role": insert_data.get("archetype"),
        },
        on_conflict="code",
    ).execute()
    return res.data[0] if res.data else insert_data


def record_oracle_action(oracle_id: str, player_id: str, action: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Insert an action row tied to an oracle_id/player_id pair."""
    res = supabase.table("oracle_actions").insert({
        "oracle_id": oracle_id,
        "player_id": player_id,
        "action": action,
        "metadata": metadata or {},
    }).execute()
    if not res.data:
        raise ValueError("Failed to record oracle action")
    return res.data[0]
