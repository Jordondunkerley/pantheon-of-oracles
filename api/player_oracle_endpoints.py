from fastapi import APIRouter, Header, HTTPException
from typing import Optional, Dict, Any
from uuid import uuid4
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
if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")

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

    The incoming payload is stored as a JSON profile so the Pantheon templates
    (factions, stats, tokens, preferences) remain intact. A stable `player_id`
    is generated when missing, enabling repeat upserts from the GPT router.
    """
    user_email = require_auth(authorization)
    user_id = get_user_id_by_email(user_email)
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")

    player_id = payload.get("player_id") or f"player-{uuid4()}"
    username = payload.get("username")
    email = payload.get("email")

    insert_data = {
        "user_id": user_id,
        "player_id": player_id,
        "username": username,
        "email": email,
        "profile": payload,
    }
    res = supabase.table("player_accounts").upsert(insert_data, on_conflict="player_id").execute()
    return {"ok": True, "account": res.data, "player_id": player_id}

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

    All oracle metadata is preserved in the ``profile`` column so rising signs,
    council state, fused creatures, and other nested attributes from the patch
    templates are kept intact.
    """
    user_email = require_auth(authorization)
    user_id = get_user_id_by_email(user_email)
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")

    oracle_id = payload.get("oracle_id") or f"oracle-{uuid4()}"
    oracle_name = payload.get("oracle_name") or payload.get("name")
    archetype = payload.get("archetype")

    insert_data = {
        "user_id": user_id,
        "oracle_id": oracle_id,
        "oracle_name": oracle_name,
        "archetype": archetype,
        "profile": payload,
    }
    res = supabase.table("oracle_profiles").upsert(insert_data, on_conflict="oracle_id").execute()
    return {"ok": True, "oracle": res.data, "oracle_id": oracle_id}

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


@router.get("/gpt/sync")
def sync_player_data(authorization: Optional[str] = Header(None)):
    """
    Return the authenticated user's player account and all oracle profiles.

    This endpoint combines the logic of ``/gpt/player-account`` and ``/gpt/my-oracles``
    into a single call. It verifies the JWT, resolves the user's ID, and then
    retrieves both the player's account and list of oracles from Supabase. This
    allows the Pantheon GPT router to fetch all relevant data in one request,
    enabling continuous syncing across sessions without manual imports.
    """
    user_email = require_auth(authorization)
    user_id = get_user_id_by_email(user_email)
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")
    # Fetch player account (if any)
    acc_res = supabase.table("player_accounts").select("*").eq("user_id", user_id).single().execute()
    # Fetch all oracles owned by the user
    orc_res = supabase.table("oracle_profiles").select("*").eq("user_id", user_id).execute()
    return {
        "ok": True,
        "account": acc_res.data,
        "oracles": orc_res.data,
    }

