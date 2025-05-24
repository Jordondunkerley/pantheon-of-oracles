from supabase import create_client, Client
import os
from dotenv import load_dotenv
from uuid import uuid4

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


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
