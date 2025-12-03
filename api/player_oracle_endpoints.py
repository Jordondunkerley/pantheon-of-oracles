"""FastAPI router for creating and retrieving player accounts and oracles.

This module is the Pantheon GPT entry point for managing player account
profiles and oracle records. All endpoints require a JWT bearer token obtained
through ``/auth/register`` or ``/auth/login``.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException
from jose import JWTError, jwt
from supabase import Client

from .config import get_settings, get_supabase_client
from .security import normalize_email
from .supabase_utils import run_supabase


settings = get_settings()
supabase: Client = get_supabase_client()
router = APIRouter(prefix="/gpt", tags=["GPT Player/Oracles"])


def verify_token(authorization: Optional[str]) -> str:
    """Validate a bearer token and return the email (``sub`` claim)."""

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Token payload missing subject")
    try:
        return normalize_email(sub)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))


def get_user_id(email: str) -> str:
    """Return the Supabase ``users.id`` for the given email or raise 404."""

    res = run_supabase(
        lambda: supabase.table("users").select("id").eq("email", email).single().execute(),
        "lookup user id",
    )
    data = res.data
    if not data:
        raise HTTPException(status_code=404, detail="User not found")
    return data["id"]


@router.post("/create-player-account")
def create_player_account(payload: Dict[str, Any], authorization: Optional[str] = Header(None)):
    """Create or update a player account for the authenticated user."""

    email = verify_token(authorization)
    user_id = get_user_id(email)
    account_data = {"user_id": user_id, **payload}
    res = run_supabase(
        lambda: supabase.table("player_accounts").upsert(account_data, on_conflict="user_id").execute(),
        "upsert player account",
    )
    return {"ok": True, "data": res.data}


@router.get("/player-account")
def get_player_account(authorization: Optional[str] = Header(None)):
    """Retrieve the authenticated user's player account profile."""

    email = verify_token(authorization)
    user_id = get_user_id(email)
    res = run_supabase(
        lambda: supabase.table("player_accounts").select("*").eq("user_id", user_id).single().execute(),
        "fetch player account",
    )
    return {"account": res.data}


@router.post("/create-oracle")
def create_oracle_profile(payload: Dict[str, Any], authorization: Optional[str] = Header(None)):
    """Create or update an oracle profile owned by the authenticated user."""

    email = verify_token(authorization)
    user_id = get_user_id(email)
    profile_data = {"user_id": user_id, **payload}
    res = run_supabase(
        lambda: supabase.table("oracle_profiles").insert(profile_data).execute(),
        "insert oracle profile",
    )
    return {"ok": True, "data": res.data}


@router.get("/my-oracles")
def get_my_oracles(authorization: Optional[str] = Header(None)):
    """Return all oracle profiles belonging to the authenticated user."""

    email = verify_token(authorization)
    user_id = get_user_id(email)
    res = run_supabase(
        lambda: supabase.table("oracle_profiles").select("*").eq("user_id", user_id).execute(),
        "fetch oracle profiles",
    )
    return {"ok": True, "oracles": res.data}


@router.get("/sync")
def sync_player_data(authorization: Optional[str] = Header(None)):
    """Return both the player's account record and all owned oracles."""

    email = verify_token(authorization)
    user_id = get_user_id(email)
    account = run_supabase(
        lambda: supabase.table("player_accounts").select("*").eq("user_id", user_id).single().execute(),
        "sync player account",
    )
    oracles = run_supabase(
        lambda: supabase.table("oracle_profiles").select("*").eq("user_id", user_id).execute(),
        "sync oracle profiles",
    )
    return {
        "ok": True,
        "account": account.data,
        "oracles": oracles.data,
    }

