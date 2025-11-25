
"""
Legacy FastAPI entrypoint kept for compatibility with older deployments.

New development should target ``api/main.py``. This file now relies solely on
environment variables to avoid leaking secrets in source control.
"""

from fastapi import FastAPI, HTTPException, Request, Header
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import pytz, os
from supabase import create_client

# === CONFIG ===
API_KEY = os.getenv("PANTHEON_GPT_SECRET")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not API_KEY or not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Set PANTHEON_GPT_SECRET, SUPABASE_URL, and SUPABASE_SERVICE_KEY/ROLE_KEY")

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
        "tier": oracle_command.metadata.oracle_tier,
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

