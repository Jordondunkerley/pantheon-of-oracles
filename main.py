from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from pydantic import BaseModel
from datetime import datetime
import json, os, random, uuid
from typing import Optional
from router import (
    create_oracle as gpt_create_oracle,
    upload_chart, start_battle as gpt_start_battle,
    start_raid as gpt_start_raid, do_directive, do_dungeon,
    oracle_ritual, oracle_action, codex_entry
)

app = FastAPI(
    title="Pantheon of Oracles API",
    version="1.0.0",
    description="Multiplayer backend API + GPT Router integration"
)

DATA_FILES = {
    "accounts": "accounts.json",
    "oracles": "oracles.json",
    "guilds": "guilds.json",
    "codex": "codex.json",
    "battles": "battles.json",
    "memory": "gpt_user_memory.json"
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

# === INPUT MODELS ===
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

class UploadRequest(BaseModel):
    username: str
    data: dict

class MessageRequest(BaseModel):
    username: str
    message: str
    oracle_id: Optional[str] = None
    context: Optional[dict] = None

class OracleInput(BaseModel):
    planet: str

class ChartInput(BaseModel):
    chart: dict

class BattleInput(BaseModel):
    mode: str = "standard"

class RaidInput(BaseModel):
    raidType: str = "planetary"

class DirectiveInput(BaseModel):
    directiveId: str

class DungeonInput(BaseModel):
    difficulty: str = "normal"

class RitualInput(BaseModel):
    ritualType: str

class OracleActionInput(BaseModel):
    oracleId: str
    action: str

class CodexInput(BaseModel):
    entry: str

# === SESSION UTIL ===
def get_user_by_token(token: str):
    accounts = load_data(DATA_FILES["accounts"])
    for username, data in accounts.items():
        if data.get("session_token") == token:
            return username, accounts
    return None, accounts

@app.get("/")
def index():
    return {"message": "Pantheon of Oracles API is alive 🔥"}

# === ROUTES FOR GPT ROUTER ===
@app.post("/oracle/create")
def oracle_route(data: OracleInput):
    return gpt_create_oracle(data.planet)

@app.post("/chart/upload")
def chart_route(data: ChartInput):
    return upload_chart(data.chart)

@app.post("/battle/start")
def battle_route(data: BattleInput):
    return gpt_start_battle(data.mode)

@app.post("/raid/start")
def raid_route(data: RaidInput):
    return gpt_start_raid(data.raidType)

@app.post("/directive/do")
def directive_route(data: DirectiveInput):
    return do_directive(data.directiveId)

@app.post("/dungeon/do")
def dungeon_route(data: DungeonInput):
    return do_dungeon(data.difficulty)

@app.post("/ritual/do")
def ritual_route(data: RitualInput):
    return oracle_ritual(data.ritualType)

@app.post("/oracle/action")
def oracle_action_route(data: OracleActionInput):
    return oracle_action(data.oracleId, data.action)

@app.post("/codex/entry")
def codex_route(data: CodexInput):
    return codex_entry(data.entry)
