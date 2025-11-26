"""
Supabase helper utilities aligned with the new Pantheon schema.

This module keeps secrets in the environment (matching ``api/main.py``) and
provides convenience helpers for scripts/notebooks to create users and upsert
player/oracle profiles without re-implementing the FastAPI validation logic.
"""
from supabase import create_client, Client
from passlib.context import CryptContext
from uuid import uuid4
from datetime import datetime
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


def _cap_limit(value: Optional[int], *, default: int, max_limit: int) -> int:
    """Clamp result sizes for Supabase queries."""

    if value is None or value <= 0:
        return default
    return min(value, max_limit)


def _normalize_offset(value: Optional[int], *, default: int = 0) -> int:
    """Ensure offsets are non-negative to avoid Supabase errors."""

    if value is None or value < 0:
        return default
    return value


def _parse_iso_timestamp(value: Optional[str]) -> Optional[str]:
    """Normalize ISO-8601 timestamps and raise on invalid input."""

    if not value:
        return None

    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError("Invalid ISO timestamp format") from exc

    return parsed.isoformat()


def _normalize_sort_direction(value: Optional[str], *, default: str = "desc") -> str:
    """Return ``asc`` or ``desc`` for ordering."""

    if not value:
        return default

    lowered = value.lower()
    if lowered not in {"asc", "desc"}:
        raise ValueError("Invalid sort direction; use 'asc' or 'desc'")

    return lowered


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


def record_oracle_actions_bulk(email: str, actions: list[Dict[str, Any]], *, max_batch: int = 100) -> Dict[str, Any]:
    """Insert a batch of oracle actions for a user after ownership checks."""

    if not actions:
        raise ValueError("At least one action payload is required")
    if len(actions) > max_batch:
        raise ValueError(f"Batch too large; maximum {max_batch} actions supported")

    user_id = _get_user_id_by_email(email)
    if not user_id:
        raise ValueError("User not found for provided email")

    oracles_res = supabase.table("oracle_profiles").select("oracle_id").eq("user_id", user_id).execute()
    players_res = supabase.table("player_accounts").select("player_id").eq("user_id", user_id).single().execute()

    owned_oracles = {row["oracle_id"] for row in (oracles_res.data or []) if row.get("oracle_id")}
    owned_players = {players_res.data.get("player_id")} if players_res.data and players_res.data.get("player_id") else set()

    rows = []
    touched_oracles: set[str] = set()
    for idx, action in enumerate(actions):
        oracle_id = action.get("oracle_id")
        player_id = action.get("player_id")
        action_name = action.get("action")

        if not oracle_id or oracle_id not in owned_oracles:
            raise ValueError(f"Oracle not found for this user at index {idx}")
        if not player_id or player_id not in owned_players:
            raise ValueError(f"Player account not found for this user at index {idx}")
        if not action_name:
            raise ValueError(f"Action name is required at index {idx}")

        touched_oracles.add(oracle_id)
        rows.append(
            {
                "oracle_id": oracle_id,
                "player_id": player_id,
                "action": action_name,
                "metadata": action.get("metadata") or {},
            }
        )

    for oid in touched_oracles:
        supabase.table("oracles").upsert(
            {"id": oid, "code": oid, "name": oid},
            on_conflict="code",
        ).execute()

    res = supabase.table("oracle_actions").insert(rows).execute()
    if not res.data:
        raise ValueError("Failed to record oracle actions")

    return {"inserted": len(res.data), "actions": res.data, "meta": {"requested": len(actions)}}


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
    include_action_stats: bool = False,
    actions_limit: int = 50,
    actions_offset: int = 0,
    actions_order: str = "desc",
    actions_filter: Optional[str] = None,
    actions_since: Optional[str] = None,
    actions_until: Optional[str] = None,
    action_stats_limit: int = 200,
    action_stats_offset: int = 0,
    action_stats_order: str = "desc",
) -> Dict[str, Any]:
    """Return player account, owned oracles, and optional recent actions for a user."""

    user_id = _get_user_id_by_email(email)
    if not user_id:
        raise ValueError("User not found for provided email")

    player_res = supabase.table("player_accounts").select("*").eq("user_id", user_id).single().execute()
    oracles_res = supabase.table("oracle_profiles").select("*").eq("user_id", user_id).execute()

    actions = []
    actions_meta: Optional[Dict[str, Any]] = None
    action_stats = None
    action_stats_meta: Optional[Dict[str, Any]] = None
    normalized_since = _parse_iso_timestamp(actions_since)
    normalized_until = _parse_iso_timestamp(actions_until)
    if include_actions:
        actions_result = list_user_actions(
            email,
            limit=_cap_limit(actions_limit, default=50, max_limit=500),
            offset=_normalize_offset(actions_offset),
            order=actions_order,
            action=actions_filter,
            since=normalized_since,
            until=normalized_until,
            include_metadata=True,
        )
        actions = actions_result.get("actions", []) if isinstance(actions_result, dict) else actions_result
        actions_meta = actions_result.get("meta") if isinstance(actions_result, dict) else None
    if include_action_stats:
        capped_stats_limit = _cap_limit(action_stats_limit, default=200, max_limit=1000)
        stats_result = summarize_user_actions(
            email,
            action=actions_filter,
            since=normalized_since,
            until=normalized_until,
            order=action_stats_order,
            limit=capped_stats_limit,
            offset=_normalize_offset(action_stats_offset),
        )
        action_stats = stats_result.get("action_counts") if isinstance(stats_result, dict) else None
        action_stats_meta = stats_result.get("meta") if isinstance(stats_result, dict) else None

    return {
        "account": player_res.data,
        "oracles": oracles_res.data or [],
        "actions": actions,
        "actions_meta": actions_meta,
        "action_stats": action_stats,
        "action_stats_meta": action_stats_meta,
    }


def list_user_actions(
    email: str,
    *,
    oracle_id: Optional[str] = None,
    player_id: Optional[str] = None,
    action: Optional[str] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    order: str = "desc",
    limit: int = 50,
    offset: int = 0,
    include_metadata: bool = False,
) -> Any:
    """Return recent oracle_actions constrained to the user's owned IDs.

    This helper mirrors the ownership rules used by the FastAPI endpoints. When no
    explicit filters are supplied, results are limited to the caller's oracle_ids
    (and, if present, the player's stored player_id). Limits are capped to 500 to
    avoid heavy queries. When ``include_metadata`` is True, pagination metadata is
    returned alongside the rows so CLI callers can plan follow-up pages.
    """

    user_id = _get_user_id_by_email(email)
    if not user_id:
        raise ValueError("User not found for provided email")

    oracles_res = supabase.table("oracle_profiles").select("oracle_id").eq("user_id", user_id).execute()
    players_res = supabase.table("player_accounts").select("player_id").eq("user_id", user_id).single().execute()

    owned_oracles = {row["oracle_id"] for row in (oracles_res.data or []) if row.get("oracle_id")}
    owned_players = {players_res.data.get("player_id")} if players_res.data and players_res.data.get("player_id") else set()

    capped_limit = _cap_limit(limit, default=50, max_limit=500)
    normalized_offset = _normalize_offset(offset)
    normalized_since = _parse_iso_timestamp(since)
    normalized_until = _parse_iso_timestamp(until)
    normalized_order = _normalize_sort_direction(order)

    if oracle_id and oracle_id not in owned_oracles:
        raise ValueError("Oracle not found for this user")
    if player_id and player_id not in owned_players:
        raise ValueError("Player account not found for this user")

    select_kwargs = {"count": "exact"} if include_metadata else {}
    query = supabase.table("oracle_actions").select("*", **select_kwargs).order(
        "created_at", desc=normalized_order == "desc"
    )

    if oracle_id:
        query = query.eq("oracle_id", oracle_id)
    else:
        if not owned_oracles:
            if include_metadata:
                return {
                    "actions": [],
                    "meta": {
                        "total_available": 0,
                        "returned": 0,
                        "limit": capped_limit,
                        "offset": normalized_offset,
                        "oracle_ids": [],
                        "player_ids": list(owned_players),
                        "since": normalized_since,
                        "until": normalized_until,
                        "action": action,
                        "order": normalized_order,
                        "has_more": False,
                    },
                }
            return []
        query = query.in_("oracle_id", list(owned_oracles))

    if player_id:
        query = query.eq("player_id", player_id)

    if action:
        query = query.eq("action", action)

    if normalized_since:
        query = query.gte("created_at", normalized_since)

    if normalized_until:
        query = query.lte("created_at", normalized_until)

    query = query.range(normalized_offset, normalized_offset + capped_limit - 1)
    res = query.execute()
    actions = res.data or []

    if not include_metadata:
        return actions

    total_available = getattr(res, "count", None)
    has_more = False
    if total_available is not None:
        has_more = normalized_offset + len(actions) < total_available
    else:
        has_more = len(actions) >= capped_limit

    return {
        "actions": actions,
        "meta": {
            "total_available": total_available,
            "returned": len(actions),
            "limit": capped_limit,
            "offset": normalized_offset,
            "oracle_id": oracle_id,
            "player_id": player_id,
            "since": normalized_since,
            "until": normalized_until,
            "action": action,
            "order": normalized_order,
            "oracle_ids": sorted(list(owned_oracles)) if not oracle_id else [oracle_id],
            "player_ids": sorted(list(owned_players)) if not player_id else [player_id],
            "has_more": has_more,
        },
    }


def summarize_user_actions(
    email: str,
    *,
    oracle_id: Optional[str] = None,
    player_id: Optional[str] = None,
    action: Optional[str] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    order: str = "desc",
    limit: int = 200,
    offset: int = 0,
) -> Dict[str, Any]:
    """Aggregate action counts for a user's owned oracle/player IDs.

    The helper reuses ``list_user_actions`` for ownership checks and filtering, then
    computes a simple count per action type. ``limit`` caps the number of rows to
    fetch before aggregation to avoid heavy queries. The response now includes a
    ``meta`` block mirroring the actions listing so clients can paginate through
    aggregation windows while keeping filters aligned.
    """

    capped_limit = _cap_limit(limit, default=200, max_limit=1000)
    normalized_offset = _normalize_offset(offset)
    normalized_since = _parse_iso_timestamp(since)
    normalized_until = _parse_iso_timestamp(until)
    normalized_order = _normalize_sort_direction(order)

    rows_result = list_user_actions(
        email,
        oracle_id=oracle_id,
        player_id=player_id,
        action=action,
        since=normalized_since,
        until=normalized_until,
        order=normalized_order,
        limit=capped_limit,
        offset=normalized_offset,
        include_metadata=True,
    )

    rows = rows_result.get("actions", []) if isinstance(rows_result, dict) else rows_result
    meta = rows_result.get("meta", {}) if isinstance(rows_result, dict) else {}

    counts: Dict[str, int] = {}
    for row in rows:
        key = row.get("action") or "UNKNOWN"
        counts[key] = counts.get(key, 0) + 1

    return {
        "action_counts": sorted(
            [{"action": k, "count": v} for k, v in counts.items()],
            key=lambda x: x["action"],
        ),
        "meta": {
            "rows_aggregated": len(rows),
            "returned": meta.get("returned", len(rows)),
            "limit": meta.get("limit", capped_limit),
            "offset": meta.get("offset", normalized_offset),
            "since": meta.get("since", normalized_since),
            "until": meta.get("until", normalized_until),
            "oracle_ids": meta.get("oracle_ids"),
            "player_ids": meta.get("player_ids"),
            "action": action,
            "order": meta.get("order", normalized_order),
            "total_available": meta.get("total_available"),
            "has_more": meta.get("has_more", False),
        },
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
