"""
Pantheon of Oracles – FastAPI service (JWT + Supabase; Render-friendly)

- Env-only secrets (no keys in code)
- Minimal REST: /auth/register, /auth/login, /gpt/update-oracle, /healthz
- Supabase tables expected: users, oracles, oracle_actions
"""
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from supabase import create_client, Client
import os

from .player_oracle_endpoints import router as player_oracle_router

# -------- env --------
APP_NAME = os.getenv("APP_NAME", "Pantheon of Oracles API")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
JWT_SECRET = os.getenv("JWT_SECRET", "please-change-me")
JWT_ALG = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -------- app --------
app = FastAPI(title=APP_NAME)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

app.include_router(player_oracle_router)

# -------- models --------
class RegisterRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class UpdateOracleRequest(BaseModel):
    """Request model for updating oracle actions.

    The plugin may omit ``oracle_id`` and ``player_id`` at the top level. When
    absent, these values can be provided inside the ``metadata`` dictionary.
    Both fields are optional here and will be resolved in the endpoint
    logic.  ``oracle_name`` can also be provided to look up an oracle
    identifier automatically.
    """
    oracle_id: Optional[str] = None  # UUID from ``oracles`` table
    player_id: Optional[str] = None  # Player account UUID
    action: str  # e.g., "RITUAL_START"
    oracle_name: Optional[str] = None  # Human‑readable oracle name
    metadata: Optional[Dict[str, Any]] = None


# -------- utils --------
def create_access_token(sub: str) -> str:
    payload = {"sub": sub, "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def require_auth(authorization: Optional[str]) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        return payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# -------- auth --------
@app.post("/auth/register")
def register(req: RegisterRequest):
    hashed = pwd_context.hash(req.password)
    res = supabase.table("users").insert({"email": req.email, "password_hash": hashed}).execute()
    if not res.data:
        raise HTTPException(status_code=400, detail="Registration failed")
    return {"ok": True, "token": create_access_token(sub=req.email)}

@app.post("/auth/login")
def login(req: LoginRequest):
    res = supabase.table("users").select("email,password_hash").eq("email", req.email).single().execute()
    data = res.data or {}
    if not data or not pwd_context.verify(req.password, data.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"ok": True, "token": create_access_token(sub=req.email)}

# -------- GPT actions --------
@app.post("/gpt/update-oracle")
def update_oracle(payload: UpdateOracleRequest, authorization: Optional[str] = Header(None)):
    """Insert an oracle action into the log.

    This endpoint accepts both our internal and plugin-style payloads. It resolves
    the ``player_id`` and ``oracle_id`` automatically when they are omitted:

    * ``player_id`` is looked up from the authenticated user's player account.
    * ``oracle_id`` can come from the top‑level field, the ``metadata``
      dictionary, or be resolved via ``oracle_name`` in conjunction with the user.

    A 400 error is raised if an oracle identifier cannot be determined.
    """
    # Validate the token and get user email
    user_email = require_auth(authorization)
    # Get the user's internal id
    user_id = get_user_id_by_email(user_email)
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")
    # Resolve player_id: prefer payload.player_id then metadata.player_id then lookup
    player_id = payload.player_id
    if not player_id and payload.metadata and isinstance(payload.metadata, dict):
        player_id = payload.metadata.get("player_id")
    if not player_id:
        # fetch player account id from table
        player_res = supabase.table("player_accounts").select("id").eq("user_id", user_id).single().execute()
        if player_res.data:
            player_id = player_res.data.get("id")
    # Resolve oracle_id: prefer payload.oracle_id then metadata.oracle_id then lookup by oracle_name
    oracle_id = payload.oracle_id
    if not oracle_id and payload.metadata and isinstance(payload.metadata, dict):
        oracle_id = payload.metadata.get("oracle_id")
    if not oracle_id and payload.oracle_name:
        # look up by oracle_name for this user
        or_res = supabase.table("oracle_profiles").select("id").eq("user_id", user_id).eq("oracle_name", payload.oracle_name).single().execute()
        if or_res.data:
            oracle_id = or_res.data.get("id")
    if not oracle_id:
        raise HTTPException(status_code=400, detail="Missing oracle identifier (oracle_id or oracle_name)")
    if not player_id:
        raise HTTPException(status_code=400, detail="Missing player identifier")
    # Insert the action
    ins = supabase.table("oracle_actions").insert({
        "oracle_id": oracle_id,
        "player_id": player_id,
        "action": payload.action,
        "metadata": payload.metadata
    }).execute()
    return {"ok": True, "inserted": ins.data}


@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": APP_NAME}

