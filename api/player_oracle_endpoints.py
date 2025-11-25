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


def _get_player_by_player_id(player_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    res = (
        supabase.table("player_accounts")
        .select("*")
        .eq("player_id", player_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    return res.data


def _get_oracle_profile(oracle_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    res = (
        supabase.table("oracle_profiles")
        .select("*")
        .eq("oracle_id", oracle_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    return res.data


def _get_owned_ids(user_id: str) -> Dict[str, set]:
    """Return the oracle_ids and player_ids belonging to a user for ownership checks."""

    oracles_res = (
        supabase.table("oracle_profiles")
        .select("oracle_id")
        .eq("user_id", user_id)
        .execute()
    )
    players_res = (
        supabase.table("player_accounts")
        .select("player_id")
        .eq("user_id", user_id)
        .execute()
    )

    return {
        "oracle_ids": {row["oracle_id"] for row in (oracles_res.data or []) if row.get("oracle_id")},
        "player_ids": {row["player_id"] for row in (players_res.data or []) if row.get("player_id")},
    }


def _ensure_oracle_row(oracle_id: str, oracle_name: Optional[str], archetype: Optional[str]) -> None:
    """
    Guarantee there is an ``oracles`` row that matches the externally visible oracle_id.

    ``oracle_actions.oracle_id`` has a foreign key reference to ``oracles.id``. To keep
    inserts consistent, we upsert into ``oracles`` with the user-facing oracle_id so
    action logging always succeeds.
    """
    supabase.table("oracles").upsert(
        {
            "id": oracle_id,
            "code": oracle_name or oracle_id,
            "name": oracle_name or oracle_id,
            "role": archetype,
        },
        on_conflict="code",
    ).execute()

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

    player_id = payload.get("player_id") or str(uuid4())
    username = payload.get("username")
    email = payload.get("email") or user_email

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

    oracle_id = payload.get("oracle_id") or str(uuid4())
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

    # Ensure the oracle is also registered in the base "oracles" table so action logging works
    _ensure_oracle_row(oracle_id, oracle_name, archetype)

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


def _list_actions_for_owned(
    oracle_ids: set,
    player_ids: set,
    limit: int,
):
    """
    Fetch recent oracle_actions scoped to owned oracle/player IDs.

    This helper mirrors the ownership protections in ``/gpt/oracle-actions``
    by constraining the Supabase query to the caller's oracle_ids. Player
    filtering is optional but constrained to known player_ids when present.
    """

    capped_limit = limit if limit and limit > 0 else 50
    capped_limit = min(capped_limit, 500)

    if not oracle_ids:
        return []

    query = supabase.table("oracle_actions").select("*").order("created_at", desc=True)
    query = query.in_("oracle_id", list(oracle_ids))

    if player_ids:
        query = query.in_("player_id", list(player_ids))

    query = query.limit(capped_limit)

    res = query.execute()
    return res.data or []


@router.get("/gpt/sync")
def sync_player_data(
    include_actions: bool = False,
    actions_limit: int = 50,
    authorization: Optional[str] = Header(None),
):
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

    actions = []
    if include_actions:
        owned_ids = _get_owned_ids(user_id)
        actions = _list_actions_for_owned(owned_ids["oracle_ids"], owned_ids["player_ids"], actions_limit)
    return {
        "ok": True,
        "account": acc_res.data,
        "oracles": orc_res.data,
        "actions": actions,
    }


@router.post("/gpt/oracle-action")
def log_oracle_action(payload: Dict[str, Any], authorization: Optional[str] = Header(None)):
    """
    Record an oracle action after verifying ownership of the supplied player/oracle IDs.

    The incoming payload should include ``oracle_id``, ``player_id``, ``action``, and
    optional ``metadata``. We confirm that both IDs belong to the authenticated user
    before inserting into ``oracle_actions``.
    """
    user_email = require_auth(authorization)
    user_id = get_user_id_by_email(user_email)
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")

    oracle_id = payload.get("oracle_id")
    player_id = payload.get("player_id")
    action = payload.get("action")
    metadata = payload.get("metadata") or {}

    if not oracle_id or not player_id or not action:
        raise HTTPException(status_code=400, detail="oracle_id, player_id, and action are required")

    if not _get_oracle_profile(oracle_id, user_id):
        raise HTTPException(status_code=404, detail="Oracle not found for this user")
    if not _get_player_by_player_id(player_id, user_id):
        raise HTTPException(status_code=404, detail="Player account not found for this user")

    # Ensure oracle exists in `oracles` for FK constraint safety
    _ensure_oracle_row(oracle_id, None, None)

    res = (
        supabase.table("oracle_actions")
        .insert({"oracle_id": oracle_id, "player_id": player_id, "action": action, "metadata": metadata})
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=400, detail="Failed to record action")

    return {"ok": True, "action": res.data[0]}


@router.get("/gpt/oracle-actions")
def list_oracle_actions(
    oracle_id: Optional[str] = None,
    player_id: Optional[str] = None,
    limit: int = 50,
    authorization: Optional[str] = Header(None),
):
    """
    List recent oracle actions for the authenticated user.

    Ownership is enforced by intersecting the requested ``oracle_id``/``player_id``
    with the caller's stored profiles. When no filters are provided, only actions
    tied to the user's own oracle IDs are returned. ``limit`` defaults to 50.
    """

    user_email = require_auth(authorization)
    user_id = get_user_id_by_email(user_email)
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")

    owned_ids = _get_owned_ids(user_id)

    # Validate supplied filters belong to the caller
    if oracle_id and oracle_id not in owned_ids["oracle_ids"]:
        raise HTTPException(status_code=404, detail="Oracle not found for this user")
    if player_id and player_id not in owned_ids["player_ids"]:
        raise HTTPException(status_code=404, detail="Player account not found for this user")

    query = supabase.table("oracle_actions").select("*").order("created_at", desc=True)

    if oracle_id:
        query = query.eq("oracle_id", oracle_id)
    else:
        # Constrain to caller-owned oracle_ids to avoid leaking other users' actions
        if not owned_ids["oracle_ids"]:
            return {"ok": True, "actions": []}
        query = query.in_("oracle_id", list(owned_ids["oracle_ids"]))

    if player_id:
        query = query.eq("player_id", player_id)

    if limit and limit > 0:
        query = query.limit(limit)

    res = query.execute()
    return {"ok": True, "actions": res.data or []}


@router.get("/gpt/oracle-catalog")
def list_oracle_catalog(
    code: Optional[str] = None,
    role: Optional[str] = None,
    limit: int = 100,
    authorization: Optional[str] = Header(None),
):
    """
    Return seeded oracle catalog entries for authenticated callers.

    This surfaces the compact rules and metadata stored in the ``oracles``
    table (seeded from the GPT patches). Callers can optionally filter by
    oracle ``code`` or ``role`` and cap the result size with ``limit``
    (defaults to 100, max 500).
    """

    user_email = require_auth(authorization)
    user_id = get_user_id_by_email(user_email)
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")

    capped_limit = min(limit if limit and limit > 0 else 100, 500)

    query = supabase.table("oracles").select("id,code,name,role,rules").order("code")

    if code:
        query = query.eq("code", code)
    if role:
        query = query.eq("role", role)

    query = query.limit(capped_limit)

    res = query.execute()
    return {"ok": True, "oracles": res.data or []}

