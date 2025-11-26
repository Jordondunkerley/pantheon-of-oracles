from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from uuid import uuid4
from jose import jwt, JWTError
from supabase import create_client
from datetime import datetime
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


def _cap_limit(value: Optional[int], *, default: int = 50, max_limit: int = 500) -> int:
    """Return a sane limit value bounded by ``max_limit``.

    Negative or zero values fall back to ``default`` to avoid unexpected empty
    responses or heavy Supabase scans.
    """

    if value is None or value <= 0:
        return default
    return min(value, max_limit)


def _parse_iso_timestamp(value: Optional[str]) -> Optional[str]:
    """Validate and normalize ISO-8601 timestamps.

    Returns a string suitable for Supabase queries or raises ``HTTPException``
    when the input cannot be parsed. Accepts ``Z`` suffixes by translating them
    to ``+00:00`` for ``datetime.fromisoformat`` compatibility.
    """

    if not value:
        return None

    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ISO timestamp format")

    return parsed.isoformat()


class PlayerAccountPayload(BaseModel):
    player_id: Optional[str] = Field(None, description="Stable player UUID/string")
    username: Optional[str] = None
    email: Optional[str] = None
    profile: Dict[str, Any] = Field(default_factory=dict)


class OracleProfilePayload(BaseModel):
    oracle_id: Optional[str] = Field(None, description="Stable oracle UUID/string")
    oracle_name: Optional[str] = None
    name: Optional[str] = None
    archetype: Optional[str] = None
    profile: Dict[str, Any] = Field(default_factory=dict)


class OracleActionPayload(BaseModel):
    oracle_id: str
    player_id: str
    action: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

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
def create_player_account(payload: PlayerAccountPayload, authorization: Optional[str] = Header(None)):
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

    player_id = payload.player_id or str(uuid4())
    username = payload.username
    email = payload.email or user_email

    profile_data = payload.profile or payload.dict(exclude={"profile"}, exclude_none=True)

    insert_data = {
        "user_id": user_id,
        "player_id": player_id,
        "username": username,
        "email": email,
        "profile": profile_data,
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
def create_oracle(payload: OracleProfilePayload, authorization: Optional[str] = Header(None)):
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

    oracle_id = payload.oracle_id or str(uuid4())
    oracle_name = payload.oracle_name or payload.name
    archetype = payload.archetype

    profile_data = payload.profile or payload.dict(exclude={"profile"}, exclude_none=True)

    insert_data = {
        "user_id": user_id,
        "oracle_id": oracle_id,
        "oracle_name": oracle_name,
        "archetype": archetype,
        "profile": profile_data,
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
    action: Optional[str] = None,
    since: Optional[str] = None,
):
    """
    Fetch recent oracle_actions scoped to owned oracle/player IDs.

    This helper mirrors the ownership protections in ``/gpt/oracle-actions``
    by constraining the Supabase query to the caller's oracle_ids. Player
    filtering is optional but constrained to known player_ids when present.
    ``limit`` is capped at 500, and ``action`` can filter by action name.
    """

    capped_limit = _cap_limit(limit, default=50, max_limit=500)
    normalized_since = _parse_iso_timestamp(since)

    if not oracle_ids:
        return []

    query = supabase.table("oracle_actions").select("*").order("created_at", desc=True)
    query = query.in_("oracle_id", list(oracle_ids))

    if player_ids:
        query = query.in_("player_id", list(player_ids))

    if action:
        query = query.eq("action", action)

    if normalized_since:
        query = query.gte("created_at", normalized_since)

    query = query.limit(capped_limit)

    res = query.execute()
    return res.data or []


def _summarize_actions_for_owned(
    oracle_ids: set,
    player_ids: set,
    limit: int,
    action: Optional[str] = None,
    since: Optional[str] = None,
    *,
    include_ok_flag: bool = False,
):
    """Aggregate counts for owned actions with optional filters.

    Reuses ``_list_actions_for_owned`` to enforce ownership scoping and limits, then
    counts the number of rows per action name. ``include_ok_flag`` mirrors the API
    response structure when reused in route handlers.
    """

    actions = _list_actions_for_owned(
        oracle_ids,
        player_ids,
        limit,
        action,
        since,
    )

    counts: Dict[str, int] = {}
    for row in actions:
        key = row.get("action") or "UNKNOWN"
        counts[key] = counts.get(key, 0) + 1

    response = {
        "total": len(actions),
        "limit": limit,
        "since": since,
        "action_counts": sorted(
            [{"action": k, "count": v} for k, v in counts.items()],
            key=lambda x: x["action"],
        ),
    }

    if include_ok_flag:
        response = {"ok": True, **response}

    return response


@router.get("/gpt/sync")
def sync_player_data(
    include_actions: bool = False,
    include_action_stats: bool = False,
    actions_limit: int = 50,
    actions_filter: Optional[str] = None,
    actions_since: Optional[str] = None,
    action_stats_limit: int = 200,
    authorization: Optional[str] = Header(None),
):
    """
    Return the authenticated user's player account and all oracle profiles.

    This endpoint combines the logic of ``/gpt/player-account`` and ``/gpt/my-oracles``
    into a single call. It verifies the JWT, resolves the user's ID, and then
    retrieves both the player's account and list of oracles from Supabase. When
    ``include_actions`` is true, recent oracle_actions are also returned, capped
    to 500 rows and optionally filtered by ``actions_filter`` (action name) or
    ``actions_since`` (ISO timestamp). This allows the Pantheon GPT router to
    fetch all relevant data in one request, enabling continuous syncing across
    sessions without manual imports.
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
    action_stats = None
    normalized_since = _parse_iso_timestamp(actions_since)
    if include_actions:
        owned_ids = _get_owned_ids(user_id)
        actions = _list_actions_for_owned(
            owned_ids["oracle_ids"],
            owned_ids["player_ids"],
            _cap_limit(actions_limit, default=50, max_limit=500),
            actions_filter,
            normalized_since,
        )
    if include_action_stats:
        owned_ids = _get_owned_ids(user_id)
        capped_stats_limit = _cap_limit(action_stats_limit, default=200, max_limit=1000)
        action_stats = _summarize_actions_for_owned(
            owned_ids["oracle_ids"],
            owned_ids["player_ids"],
            capped_stats_limit,
            actions_filter,
            normalized_since,
        )
    return {
        "ok": True,
        "account": acc_res.data,
        "oracles": orc_res.data,
        "actions": actions,
        "action_stats": action_stats,
    }


@router.post("/gpt/oracle-action")
def log_oracle_action(payload: OracleActionPayload, authorization: Optional[str] = Header(None)):
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

    oracle_id = payload.oracle_id
    player_id = payload.player_id
    action = payload.action
    metadata = payload.metadata or {}

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
    action: Optional[str] = None,
    since: Optional[str] = None,
    limit: int = 50,
    authorization: Optional[str] = Header(None),
):
    """
    List recent oracle actions for the authenticated user.

    Ownership is enforced by intersecting the requested ``oracle_id``/``player_id``
    with the caller's stored profiles. When no filters are provided, only actions
    tied to the user's own oracle IDs are returned. ``limit`` defaults to 50 and
    is capped at 500. ``action`` can be supplied to filter by action name, and
    ``since`` can restrict results to recent entries via ``created_at``.
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

    capped_limit = _cap_limit(limit, default=50, max_limit=500)
    normalized_since = _parse_iso_timestamp(since)

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

    if action:
        query = query.eq("action", action)

    if normalized_since:
        query = query.gte("created_at", normalized_since)

    query = query.limit(capped_limit)

    res = query.execute()
    return {"ok": True, "actions": res.data or []}


@router.get("/gpt/oracle-action-stats")
def oracle_action_stats(
    oracle_id: Optional[str] = None,
    player_id: Optional[str] = None,
    action: Optional[str] = None,
    since: Optional[str] = None,
    limit: int = 200,
    authorization: Optional[str] = Header(None),
):
    """
    Aggregate action counts for the authenticated user's oracle/player IDs.

    Returns a simple count per action type drawn from ``oracle_actions`` after
    enforcing ownership of the supplied IDs. ``since`` can restrict results to
    recent activity (based on ``created_at`` timestamps), and ``limit`` caps the
    number of rows fetched before aggregation (default 200, max 1000).
    """

    user_email = require_auth(authorization)
    user_id = get_user_id_by_email(user_email)
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")

    owned_ids = _get_owned_ids(user_id)

    if oracle_id and oracle_id not in owned_ids["oracle_ids"]:
        raise HTTPException(status_code=404, detail="Oracle not found for this user")
    if player_id and player_id not in owned_ids["player_ids"]:
        raise HTTPException(status_code=404, detail="Player account not found for this user")

    capped_limit = _cap_limit(limit, default=200, max_limit=1000)
    normalized_since = _parse_iso_timestamp(since)

    return _summarize_actions_for_owned(
        owned_ids["oracle_ids"] if not oracle_id else {oracle_id},
        owned_ids["player_ids"] if not player_id else {player_id},
        capped_limit,
        action,
        normalized_since,
        include_ok_flag=True,
    )


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

