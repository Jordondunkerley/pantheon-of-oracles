"""Helper for creating Pantheon users via Supabase."""

import uuid

from fastapi import HTTPException
from supabase import Client

from api.config import get_supabase_client
from api.supabase_utils import run_supabase


supabase: Client = get_supabase_client()

def create_user(username: str, first_name: str, last_name: str, password: str):
    """
    Creates a new user in the Supabase 'users' table.
    Automatically assigns a unique user_id (UUIDv4).
    """
    user_id = str(uuid.uuid4())

    data = {
        "id": user_id,
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
        "password": password  # ⛔ Future: hash this before saving
    }

    try:
        response = run_supabase(
            lambda: supabase.table("users").insert(data).execute(),
            "create user helper",
        )
    except HTTPException as exc:
        return {"status": "error", "details": exc.detail}

    if getattr(response, "status_code", None) == 201 or response.data:
        return {"status": "success", "user_id": user_id}

    return {"status": "error", "details": getattr(response, "json", lambda: {})()}
