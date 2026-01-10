from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from supabase import create_client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL") or "https://mammtgndjoydbeeuehiw.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1hbW10Z25kam95ZGJlZXVlaGl3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDM0NTM5MzQsImV4cCI6MjA1OTAyOTkzNH0.VPseSq4UpYA3NJfq6wmjVkqfmOpsIFyPM--4lmN8hx4"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

router = APIRouter()

class UserCredentials(BaseModel):
    email: str
    password: str
    first_name: str | None = None
    last_name: str | None = None

@router.post("/")
async def login_or_create_user(credentials: UserCredentials):
    try:
        # Try to sign in first
        login_res = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
        return {"status": "logged_in", "session": login_res}
    except Exception:
        # If sign in fails, try to create the account
        try:
            signup_res = supabase.auth.sign_up({
                "email": credentials.email,
                "password": credentials.password
            })
            return {"status": "created", "user": signup_res}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

# export router with clear name
login_router = router
