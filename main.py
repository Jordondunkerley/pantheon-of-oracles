from fastapi import FastAPI, HTTPException, UploadFile, File, Request, Header
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import json, os, random, uuid, pytz
import httpx
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
API_KEY = "J&h^fvAc*gH!aS#ba@PL#iuW&D11J"

app = FastAPI(
    title="Pantheon of Oracles API",
    description="Universal Oracle Action Gateway",
    version="1.0.0",
    servers=[
        {
            "url": "https://pantheon-of-oracles.onrender.com"
        }
    ]
)

DATA_FILES = {
    "accounts": "accounts.json",
    "oracles": "oracles.json",
    "guilds": "guilds.json",
    "codex": "codex.json",
    "battles": "battles.json"
}

# === FILE UTIL ===
def load_data(file):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f)
    with open(file, "r") as f:
        return json.load(f)

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

# === MODELS ===
class Account(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class OracleRequest(BaseModel):
    session_token: str
    date_of_birth: str
    time_of_birth: str
    location: str
    chart: dict
    rulership: str = "modern"

# === SESSION UTIL ===
async def get_user_by_token_supabase(token: str):
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"{SUPABASE_URL}/rest/v1/accounts",
            headers={
                "apikey": SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"
            },
            params={"session_token": f"eq.{token}"}
        )
        if res.status_code == 200 and res.json():
            return res.json()[0]["username"]
        return None

# === ACCOUNT SYSTEM ===
@app.post("/create_account")
async def create_account(account: Account):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SUPABASE_URL}/rest/v1/accounts",
            headers={
                "apikey": SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=representation"
            },
            json={
                "username": account.username,
                "email": account.email,
                "first_name": account.first_name,
                "last_name": account.last_name,
                "password": account.password,
                "created": str(datetime.now()),
                "session_token": str(uuid.uuid4())
            }
        )

        if response.status_code != 201:
            raise HTTPException(status_code=400, detail="Account creation failed")

        return response.json()[0]

@app.post("/login")
def login(creds: LoginRequest):
    url = f"{SUPABASE_URL}/rest/v1/accounts?username=eq.{creds.username}&select=*"
    res = httpx.get(url, headers={
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"
    })

    if res.status_code != 200 or not res.json():
        raise HTTPException(status_code=404, detail="User not found")

    user = res.json()[0]
    if user["password"] != creds.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"message": f"Welcome back, {creds.username}", "session_token": user["session_token"]}

@app.get("/whoami/{session_token}")
async def whoami(session_token: str):
    username = await get_user_by_token_supabase(session_token)
    if not username:
        raise HTTPException(status_code=404, detail="Session not recognized")
    return {"username": username}

# Remaining parts are unchanged...

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import pytz

app = FastAPI(
    title="Pantheon of Oracles API",
    description="Universal Oracle Action Gateway",
    version="1.0.0",
    servers=[{ "url": "https://pantheon-of-oracles.onrender.com" }]
)

# Define request models
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

API_KEY = "J&h^fvAc*gH!aS#ba@PL#iuW&D11J"

@app.post("/gpt/update-oracle")
async def update_oracle_action(request: Request, oracle_command: OracleCommand, authorization: str = Header(...)):

    if authorization != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    now_est = datetime.now(pytz.timezone("America/Toronto")).isoformat()

    # Insert oracle action into Supabase

    # Insert oracle action into Supabase
    supabase.table("oracle_actions").insert({
        "oracle_name": oracle_command.oracle_name,
        "command": oracle_command.command,
        "context": oracle_command.metadata.context,
        "tier": oracle_command.metadata.oracle_tier,
        "level": oracle_command.metadata.oracle_level,
        "rank": oracle_command.metadata.ascended_rank,
        "timestamp": oracle_command.metadata.timestamp
    }).execute()

    supabase.table("oracle_actions").insert({
        "oracle_name": oracle_command.oracle_name,
        "command": oracle_command.command,
        "context": oracle_command.metadata.context,
        "level": oracle_command.metadata.oracle_level,
        "rank": oracle_command.metadata.ascended_rank,
        "timestamp": oracle_command.metadata.timestamp
    }).execute()


    print(f"\n[ORACLE ACTION RECEIVED] {oracle_command.oracle_name} | {oracle_command.command} | {now_est}")

    return {
        "status": "success",
        "oracle": oracle_command.oracle_name,
        "timestamp": now_est
    }

from supabase import create_client
from supabase_client import supabase

SUPABASE_URL = "https://mammtgndjoydbeeuehiw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1hbW10Z25kam95ZGJlZXVlaGl3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDM0NTM5MzQsImV4cCI6MjA1OTAyOTkzNH0.VPseSq4UpYA3NJfq6wmjVkqfmOpsIFyPM--4lmN8hx4"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))

if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
