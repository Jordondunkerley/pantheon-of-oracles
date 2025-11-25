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


def list_oracles(code: Optional[str] = None, role: Optional[str] = None, limit: int = 100) -> list[Dict[str, Any]]:
    """Fetch seeded oracle catalog entries, optionally filtered by code or role."""

    capped_limit = min(limit if limit and limit > 0 else 100, 500)

    query = supabase.table("oracles").select("id,code,name,role,rules").order("code")

    if code:
        query = query.eq("code", code)
    if role:
        query = query.eq("role", role)

    query = query.limit(capped_limit)
    res = query.execute()
    return res.data or []


def get_user_bundle(
    email: str,
    include_actions: bool = False,
    actions_limit: int = 50,
) -> Dict[str, Any]:
    """Return player account, owned oracles, and optional recent actions for a user."""

    user_id = _get_user_id_by_email(email)
    if not user_id:
        raise ValueError("User not found for provided email")

    player_res = supabase.table("player_accounts").select("*").eq("user_id", user_id).single().execute()
    oracles_res = supabase.table("oracle_profiles").select("*").eq("user_id", user_id).execute()

    actions = []
    if include_actions:
        capped_limit = actions_limit if actions_limit and actions_limit > 0 else 50
        capped_limit = min(capped_limit, 500)

        oracle_ids = [row["oracle_id"] for row in (oracles_res.data or []) if row.get("oracle_id")]
        player_ids = []
        if player_res.data:
            pid = player_res.data.get("player_id")
            if pid:
                player_ids.append(pid)

        if oracle_ids:
            query = (
                supabase.table("oracle_actions")
                .select("*")
                .in_("oracle_id", oracle_ids)
                .order("created_at", desc=True)
                .limit(capped_limit)
            )

            if player_ids:
                query = query.in_("player_id", player_ids)

            actions_res = query.execute()
            actions = actions_res.data or []

    return {
        "account": player_res.data,
        "oracles": oracles_res.data or [],
        "actions": actions,
    }


def delete_user_bundle(
    email: str,
    *,
    delete_actions: bool = True,
    delete_user: bool = False,
) -> Dict[str, Any]:
    """Delete a user's account, oracles, and optionally actions + user row.

    This helper is intended for service-role scripts to reset demo data. It removes
    player/oracle profiles for the given email. When ``delete_actions`` is True, it
    also purges oracle_actions linked to the user's oracle_ids (and player_id when
    present). Set ``delete_user`` to remove the user record after dependent rows
    are cleared.
    """

    user_record = _get_user_record(email)
    if not user_record:
        raise ValueError("User not found for provided email")

    user_id = user_record.get("id")

    player_res = supabase.table("player_accounts").select("*").eq("user_id", user_id).single().execute()
    oracles_res = supabase.table("oracle_profiles").select("oracle_id").eq("user_id", user_id).execute()

    player_row = player_res.data or {}
    oracle_ids = [row.get("oracle_id") for row in (oracles_res.data or []) if row.get("oracle_id")]

    deleted_actions = 0
    if delete_actions:
        query = supabase.table("oracle_actions").delete()

        if oracle_ids:
            query = query.in_("oracle_id", oracle_ids)
        if player_row.get("player_id"):
            query = query.eq("player_id", player_row["player_id"])

        # Only execute when we have at least one constraint to avoid wiping all rows
        if oracle_ids or player_row.get("player_id"):
            actions_res = query.execute()
            deleted_actions = len(actions_res.data or []) if hasattr(actions_res, "data") else 0

    profiles_res = supabase.table("oracle_profiles").delete().eq("user_id", user_id).execute()
    players_res = supabase.table("player_accounts").delete().eq("user_id", user_id).execute()

    user_deleted = False
    if delete_user:
        supabase.table("users").delete().eq("id", user_id).execute()
        user_deleted = True

    return {
        "deleted_actions": deleted_actions,
        "deleted_oracle_profiles": len(profiles_res.data or []) if hasattr(profiles_res, "data") else 0,
        "deleted_player_accounts": len(players_res.data or []) if hasattr(players_res, "data") else 0,
        "user_deleted": user_deleted,
    }
