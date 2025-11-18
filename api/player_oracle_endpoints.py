"""Pantheon of Oracles player + oracle management endpoints.

These routes power the GPT router so that player accounts and oracle profiles
can be created, fetched, and synced directly from ChatGPT conversations. All
requests require a JWT bearer token issued by the `/auth/register` or
`/auth/login` endpoints in ``api.main``.
"""
from fastapi import APIRouter, HTTPException, Header
from typing import Dict, Any, Optional
from jose import jwt, JWTError
from supabase import create_client, Client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALG = "HS256"

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError(
        "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured for player/oracle endpoints"
    )

if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET must be configured for player/oracle endpoints")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

router = APIRouter(prefix="/gpt", tags=["GPT Player/Oracles"])


def verify_token(authorization: Optional[str]) -> str:
    """Validate a JWT bearer token and return the subject (player email)."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    subject = payload.get("sub")
    if not subject:
        raise HTTPException(status_code=401, detail="Token payload missing subject")
    return subject


def get_user_id(email: str) -> str:
    """Return the Supabase user ID for the provided email or raise 404."""
    res = supabase.table("users").select("id").eq("email", email).single().execute()
    data = res.data
    if not data:
        raise HTTPException(status_code=404, detail="User not found")
    return data["id"]


@router.post("/create-player-account")
def create_player_account(payload: Dict[str, Any], authorization: Optional[str] = Header(None)):
    """Create or upsert the authenticated user's player account profile."""
    email = verify_token(authorization)
    user_id = get_user_id(email)
    account_data = {"user_id": user_id, **payload}
    res = supabase.table("player_accounts").upsert(account_data, on_conflict="user_id").execute()
    return {"ok": True, "data": res.data}


@router.get("/player-account")
def get_player_account(authorization: Optional[str] = Header(None)):
    """Fetch the authenticated user's player account."""
    email = verify_token(authorization)
    user_id = get_user_id(email)
    res = supabase.table("player_accounts").select("*").eq("user_id", user_id).single().execute()
    return {"account": res.data}


@router.post("/create-oracle")
def create_oracle_profile(payload: Dict[str, Any], authorization: Optional[str] = Header(None)):
    """Create a new oracle profile owned by the authenticated user."""
    email = verify_token(authorization)
    user_id = get_user_id(email)
    profile_data = {"user_id": user_id, **payload}
    res = supabase.table("oracle_profiles").insert(profile_data).execute()
    return {"ok": True, "data": res.data}


@router.get("/my-oracles")
def get_my_oracles(authorization: Optional[str] = Header(None)):
    """List all oracle profiles for the authenticated user."""
    email = verify_token(authorization)
    user_id = get_user_id(email)
    res = supabase.table("oracle_profiles").select("*").eq("user_id", user_id).execute()
    return {"oracles": res.data}


@router.get("/sync")
def sync_player_data(authorization: Optional[str] = Header(None)):
    """Return the player's account plus all oracle profiles in one response."""
    email = verify_token(authorization)
    user_id = get_user_id(email)
    account_res = (
        supabase.table("player_accounts").select("*").eq("user_id", user_id).single().execute()
    )
    oracle_res = supabase.table("oracle_profiles").select("*").eq("user_id", user_id).execute()
    return {"ok": True, "account": account_res.data, "oracles": oracle_res.data}
