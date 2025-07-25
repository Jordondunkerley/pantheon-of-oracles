
from fastapi import FastAPI, HTTPException, Request, Header
rom pydantic import BaseModel
from typing import Optional

from datetime import datetime
import pytz, os
from supabase import create_client

# === CONFIG ===
API_KEY = "J&h^fvAc*gH!aS#ba@PL#iuW&D11J"
SUPABASE_URL = os.getenv("SUPABASE_URL") or "https://mammtgndjoydbeeuehiw.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1hbW10Z25kam95ZGJlZXVlaGl3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDM0NTM5MzQsImV4cCI6MjA1OTAyOTkzNH0.VPseSq4UpYA3NJfq6wmjVkqfmOpsIFyPM--4lmN8hx4"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# === FASTAPI APP ===
app = FastAPI(
    title="Pantheon of Oracles API",
    description="Universal Oracle Action Gateway with Auth",
    version="1.1.0",
    servers=[{
        "url": "https://pantheon-of-oracles.onrender.com"
    }]
)

# === ORACLE SCHEMAS ===
class Metadata(BaseModel):
    patch: str
    core_faction: Optional[str]
    planetary_faction: Optional[str]
    guild: Optional[str]
    warband: Optional[str]
    context: str
    oracle_tier: str
    oracle_level: int
    ascended_rank: Optional[int]
    oracle_form: Optional[str]
    codex_tag: Optional[str]
    timestamp: str

class OracleCommand(BaseModel):
    command: str
    oracle_name: str
    action: str
    metadata: Metadata

# === ORACLE ROUTE ===
@app.post("/gpt/update-oracle")
async def update_oracle_action(request: Request, oracle_command: OracleCommand, authorization: str = Header(...)):
    if authorization != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    now_est = datetime.now(pytz.timezone("America/Toronto")).isoformat()

    payload = {
        "oracle_name": oracle_command.oracle_name,
        "command": oracle_command.command,
        "action": oracle_command.action,
        "patch": oracle_command.metadata.patch,
        "core_faction": oracle_command.metadata.core_faction,
        "planetary_faction": oracle_command.metadata.planetary_faction,
        "guild": oracle_command.metadata.guild,
       "warband": oracle_command.metadata.warband,

        "context": oracle_command.metadata.context,
       "level": oracle_command.metadata.oracle_level,
        "rank": oracle_command.metadata.ascended_rank,
        "oracle_form": oracle_command.metadata.oracle_form,
        "codex_tag": oracle_command.metadata.codex_tag,
        "timestamp": oracle_command.metadata.timestamp
    }

    result = supabase.table("oracle_actions").insert(payload).execute()
    print(f"\n[ORACLE ACTION RECEIVED] {oracle_command.oracle_name} | {oracle_command.command} | {now_est}")
    print(f"[SUPABASE INSERT RESULT] {result}")

    return {
        "status": "success",
        "oracle": oracle_command.oracle_name,
        "timestamp": now_est
    }

# === AUTH ROUTES ===
@app.post("/auth/signup")
async def signup(request: Request):
    data = await request.json()
    email = data.get("email")
    password = data.get("password")

    try:
        result = supabase.auth.sign_up({"email": email, "password": password})
        print(f"🧙 Signup triggered for: {email}")
        return {"status": "success", "email": email, "result": result}
    except Exception as e:
        print(f"⚠️ Signup failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/login")
async def login(request: Request):
    data = await request.json()
    email = data.get("email")
    password = data.get("password")

    try:
        result = supabase.auth.sign_in_with_password({"email": email, "password": password})
        print(f"🔐 Login success for: {email}")
        return {"status": "success", "session": result}
    except Exception as e:
        print(f"❌ Login failed: {str(e)}")
        raise HTTPException(status_code=401, detail=str(e))

# === ENTRYPOINT FOR RENDER ===
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)


import json

# Load account and oracle data for token endpoints
BASE_DIR = os.path.dirname(__file__)
_accounts_path = os.path.join(BASE_DIR, "accounts.json")
_oracles_path = os.path.join(BASE_DIR, "oracles.json")
try:
    with open(_accounts_path, "r") as f:
        _accounts_data = json.load(f)
except Exception:
    _accounts_data = {}
try:
    with open(_oracles_path, "r") as f:
        _oracles_data = json.load(f)
except Exception:
    _oracles_data = {}

# Simple token store
_issued_tokens: set[str] = set()

def _generate_token() -> str:
    import uuid
    token = uuid.uuid4().hex
    _issued_tokens.add(token)
    return token

class AuthCredentials(BaseModel):
    username: str
    password: str

@app.post("/token")
async def issue_token(credentials: AuthCredentials):
    if credentials.username not in _accounts_data:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    expected_pw = os.getenv("API_PASSWORD")
    if not expected_pw or credentials.password != expected_pw:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = _generate_token()
    return {"access_token": token, "token_type": "bearer"}

@app.get("/oracles")
async def list_oracles(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    token = authorization.split(" ", 1)[1]
    if token not in _issued_tokens:
        raise HTTPException(status_code=401, detail="Invalid token")
    return _oracles_data
