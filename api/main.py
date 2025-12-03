"""
Pantheon of Oracles – FastAPI service (JWT + Supabase; Render-friendly)

- Env-only secrets (no keys in code)
- Minimal REST: /auth/register, /auth/login, /gpt/update-oracle, /healthz
- Supabase tables expected: users, oracles, oracle_actions
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from supabase import Client

try:
    from .player_oracle_endpoints import router as player_oracle_router
except Exception as exc:  # pragma: no cover - defensive startup guard
    logging.warning("player_oracle_endpoints could not be loaded: %s", exc)
    player_oracle_router = None

# -------- env --------
from .config import get_settings, get_supabase_client

settings = get_settings()
supabase: Client = get_supabase_client()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -------- app --------
app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

if player_oracle_router:
    app.include_router(player_oracle_router)

# -------- models --------
class RegisterRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class UpdateOracleRequest(BaseModel):
    oracle_id: str          # UUID from `oracles` table
    player_id: str          # e.g., "jordondunkerley"
    action: str             # e.g., "RITUAL_START"
    metadata: Optional[Dict[str, Any]] = None

# -------- utils --------
def create_access_token(sub: str) -> str:
    payload = {
        "sub": sub,
        "exp": datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)

def require_auth(authorization: Optional[str]) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Token payload missing subject")
    return sub

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
    _ = require_auth(authorization)
    ins = supabase.table("oracle_actions").insert({
        "oracle_id": payload.oracle_id,
        "player_id": payload.player_id,
        "action": payload.action,
        "metadata": payload.metadata
    }).execute()
    return {"ok": True, "inserted": ins.data}

@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": settings.app_name}

