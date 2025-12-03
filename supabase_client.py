"""Supabase helpers for legacy Pantheon utilities.

This module previously embedded a concrete Supabase URL and service key. Those
credentials are now sourced from the environment to avoid shipping secrets in
the repository and to keep behavior aligned with the primary FastAPI service
configuration. The module reuses the shared API settings so any deployment only
needs to export the expected environment variables once.
"""

from uuid import uuid4

from supabase import Client

from api.config import get_supabase_client


# Reuse the shared Supabase client so all Pantheon utilities honor the same
# environment-driven configuration.
supabase: Client = get_supabase_client()


def create_user(username, first_name, last_name, password):
    user_id = str(uuid4())
    data = {
        "id": user_id,
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
        "password": password
    }
    return supabase.table("users").insert(data).execute()


def save_astrology_profile(user_id, profile_json):
    data = {
        "id": str(uuid4()),
        "user_id": user_id,
        "profile_json": profile_json
    }
    return supabase.table("astrology_profiles").insert(data).execute()


def save_oracle(user_id, oracle_type, oracle_data):
    data = {
        "id": str(uuid4()),
        "user_id": user_id,
        "oracle_type": oracle_type,
        "oracle_data": oracle_data
    }
    return supabase.table("oracles").insert(data).execute()


def get_user_oracles(user_id):
    return supabase.table("oracles").select("*").eq("user_id", user_id).execute()
