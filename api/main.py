"""
Pantheon of Oracles – FastAPI service (JWT + Supabase; Render-friendly)

- Env-only secrets (no keys in code)
- Minimal REST: /auth/register, /auth/login, /gpt/update-oracle, /healthz
- Supabase tables expected: users, oracles, oracle_actions
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from pydantic import BaseModel, Field
from supabase import Client

try:
    from .player_oracle_endpoints import router as player_oracle_router
except Exception as exc:  # pragma: no cover - defensive startup guard
    logging.warning("player_oracle_endpoints could not be loaded: %s", exc)
    player_oracle_router = None

# -------- env --------
from .config import get_settings, get_supabase_client
from .supabase_utils import run_supabase
from .security import hash_password, validate_password_strength, verify_password

settings = get_settings()
supabase: Client = get_supabase_client()

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
    password: str = Field(min_length=8)

class LoginRequest(BaseModel):
    email: str
    password: str

class UpdateOracleRequest(BaseModel):
    oracle_id: str          # UUID from `oracles` table
    player_id: str          # e.g., "jordondunkerley"
    action: str             # e.g., "RITUAL_START"
    metadata: Dict[str, Any] = Field(default_factory=dict)

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


def _insert_oracle_action(payload: UpdateOracleRequest) -> Dict[str, Any]:
    """Insert an oracle action into Supabase and return the stored row."""

    response = run_supabase(
        lambda: supabase.table("oracle_actions")
        .insert(
            {
                "oracle_id": payload.oracle_id,
                "player_id": payload.player_id,
                "action": payload.action,
                "metadata": payload.metadata,
            }
        )
        .execute(),
        "insert oracle action",
    )

    rows = response.data or []
    if not rows:
        logging.error("Supabase insert returned no rows")
        raise HTTPException(status_code=500, detail="Failed to record oracle action")

    return rows[0]

# -------- auth --------
@app.post("/auth/register")
def register(req: RegisterRequest):
    try:
        validate_password_strength(req.password)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    hashed = hash_password(req.password)
    res = run_supabase(
        lambda: supabase.table("users").insert({"email": req.email, "password_hash": hashed}).execute(),
        "register user",
    )
    if not res.data:
        raise HTTPException(status_code=400, detail="Registration failed")
    return {"ok": True, "token": create_access_token(sub=req.email)}

@app.post("/auth/login")
def login(req: LoginRequest):
    res = run_supabase(
        lambda: supabase.table("users").select("email,password_hash").eq("email", req.email).single().execute(),
        "login lookup",
    )
    data = res.data or {}
    if not data or not verify_password(req.password, data.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"ok": True, "token": create_access_token(sub=req.email)}

# -------- GPT actions --------
@app.post("/gpt/update-oracle")
def update_oracle(payload: UpdateOracleRequest, authorization: Optional[str] = Header(None)):
    sub = require_auth(authorization)
    logging.info("Authenticated oracle action request from %s", sub)

    record = _insert_oracle_action(payload)

    return {"ok": True, "inserted": record}

@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": settings.app_name}

