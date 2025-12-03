"""Helper for creating Pantheon users via Supabase."""

import uuid

from supabase import Client

from api.config import get_supabase_client


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

    response = supabase.table("users").insert(data).execute()

    if response.status_code == 201:
        return {"status": "success", "user_id": user_id}
    else:
        return {
            "status": "error",
            "details": response.json()
        }
