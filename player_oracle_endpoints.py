from fastapi import APIRouter, Header, HTTPException
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from supabase import create_client
import os

router = APIRouter()

# Environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
JWT_SECRET = os.getenv("JWT_SECRET", "please-change-me")
JWT_ALG = "HS256"

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def require_auth(authorization: Optional[str]) -> str:
    """
    Validate bearer token and return the email (sub) from the JWT.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return sub
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def get_user_id_by_email(email: str) -> Optional[str]:
    """
    Retrieve a user's ID from Supabase based on their email.
    """
    res = supabase.table("users").select("id").eq("email", email).single().execute()
    data = res.data or {}
    return data.get("id") if data else None

@router.post("/gpt/create-player-account")
def create_player_account(payload: Dict[str, Any], authorization: Optional[str] = Header(None)):
    """
    Create or update a player account associated with the authenticated user.
    """
    user_email = require_auth(authorization)
    user_id = get_user_id_by_email(user_email)
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")
    insert_data = {"user_id": user_id, **payload}
    res = supabase.table("player_accounts").upsert(insert_data, on_conflict="user_id").execute()
    return {"ok": True, "account": res.data}

@router.get("/gpt/player-account")
def get_player_account(authorization: Optional[str] = Header(None)):
    """
    Retrieve the player account for the authenticated user.
    """
    user_email = require_auth(authorization)
    user_id = get_user_id_by_email(user_email)
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")
    res = supabase.table("player_accounts").select("*").eq("user_id", user_id).single().execute()
    return {"ok": True, "account": res.data}

@router.post("/gpt/create-oracle")
def create_oracle(payload: Dict[str, Any], authorization: Optional[str] = Header(None)):
    """
    Create or update an oracle profile associated with the authenticated user.
    """
    user_email = require_auth(authorization)
    user_id = get_user_id_by_email(user_email)
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")
    insert_data = {"user_id": user_id, **payload}
    res = supabase.table("oracle_profiles").upsert(insert_data, on_conflict="id").execute()
    return {"ok": True, "oracle": res.data}

@router.get("/gpt/my-oracles")
def get_my_oracles(authorization: Optional[str] = Header(None)):
    """
    Retrieve all oracle profiles belonging to the authenticated user.
    """
    user_email = require_auth(authorization)
    user_id = get_user_id_by_email(user_email)
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")
    res = supabase.table("oracle_profiles").select("*").eq("user_id", user_id).execute()
    return {"ok": True, "oracles": res.data}

from fastapi import Header

@router.post("/player-account")
def plugin_create_player_account(
    payload: Dict[str, Any],
    x_service_token: Optional[str] = Header(None)
):
    """
    Securely create a player account for the GPT plugin.

    This endpoint does not require a user JWT; instead, callers must include
    the service token in the X-Service-Token header.  The payload should
    contain whatever fields you want stored in the player_accounts table.
    The function assigns its own player_id by relying on Supabase’s default
    UUID generation (the `id` column) and never exposes it to the caller.
    """
    # Validate the service token
    expected = os.getenv("SERVICE_TOKEN")
    if not x_service_token or x_service_token != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing service token")

    # Insert the player account. Supabase will auto-generate the primary key (id).
    res = supabase.table("player_accounts").insert(payload).execute()

    # Return a minimal response; we do not send back the generated player_id.
    return {"ok": True}
