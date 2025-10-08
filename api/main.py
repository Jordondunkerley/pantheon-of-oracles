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
    return {"status": "ok", "service": APP_NAME}

# near the top, after other imports
from .player_oracle_endpoints import router as player_oracle_router

# after app instantiation and middleware configuration
app.include_router(player_oracle_router)
