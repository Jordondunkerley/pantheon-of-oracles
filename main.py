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
    description="Universal Oracle Actions and Data Service",
    version="1.0.0",
)

# === DATA HANDLING UTILITIES ===

def ensure_file(file: str):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f)
    with open(file, "r") as f:
        return json.load(f)

def save_data(file: str, data: dict):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

# === MODELS ===

class Account(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: Optional[str] = None
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(pytz.timezone("America/Toronto")).isoformat())

class OracleCommand(BaseModel):
    oracle_name: str
    command: str
    metadata: dict

# === ROUTES ===

@app.get("/status")
async def status():
    return {"status": "OK", "timestamp": datetime.now(pytz.timezone("America/Toronto")).isoformat()}

@app.post("/accounts")
async def create_account(account: Account, authorization: str = Header(...)):
    if authorization != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    data = ensure_file("accounts.json")
    if account.username in data:
        raise HTTPException(status_code=400, detail="Account already exists")
    data[account.username] = account.dict()
    save_data("accounts.json", data)
    return {"message": "Account created", "account": account}

@app.post("/oracles/action")
async def update_oracle_action(request: Request, oracle_command: OracleCommand, authorization: str = Header(...)):
    if authorization != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    now_est = datetime.now(pytz.timezone("America/Toronto")).isoformat()
    supabase.table("oracle_actions").insert({
        "oracle_name": oracle_command.oracle_name,
        "command": oracle_command.command,
        "context": oracle_command.metadata.get("context"),
        "tier": oracle_command.metadata.get("oracle_tier"),
        "level": oracle_command.metadata.get("oracle_level"),
        "timestamp": now_est
    }).execute()
    return {"message": "Oracle action recorded", "timestamp": now_est}

# === SUPABASE CLIENT ===

from supabase import create_client
from supabase_client import supabase

SUPABASE_URL = "https://mammtgndjoydbeeuehiw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ...cCI6MjA1OTAyOTkzNH0.VPseSq4UpYA3NJfq6wmjVkqfmOpsIFyPM--4lmN8hx4"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
