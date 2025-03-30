from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import json, os, random, uuid, requests
from dotenv import load_dotenv

# === ENV ===
load_dotenv(dotenv_path="config.env")

API_BASE = os.getenv("API_BASE")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
API_KEY = os.getenv("API_KEY")

app = FastAPI(
    title="Pantheon of Oracles API",
    version="2.0.0",
    description="Multiplayer server + GPT router unified backend"
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

# === AUTH HEADERS (OPTIONAL) ===
def authorized_headers():
    if API_KEY:
        return {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
    return {"Content-Type": "application/json"}

@app.get("/")
def index():
    return {"message": "Pantheon API + GPT Router is online 🔥"}

# === ACCOUNT + LOGIN ===
@app.post("/create_account")
def create_account(account: Account):
    accounts = load_data(DATA_FILES["accounts"])
    if account.username in accounts:
        raise HTTPException(status_code=400, detail="Username already exists")
    session_token = str(uuid.uuid4())
    accounts[account.username] = {
        "email": account.email,
        "first_name": account.first_name,
        "last_name": account.last_name,
        "password": account.password,
        "created": str(datetime.now()),
        "oracles": [],
        "guild": None,
        "session_token": session_token
    }
    save_data(DATA_FILES["accounts"], accounts)
    return {"message": f"Account created for {account.first_name}", "session_token": session_token}

@app.post("/login")
def login(creds: LoginRequest):
    accounts = load_data(DATA_FILES["accounts"])
    user = accounts.get(creds.username)
    if not user or user["password"] != creds.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"message": f"Welcome back, {creds.username}", "session_token": user["session_token"]}

@app.get("/whoami/{session_token}")
def whoami(session_token: str):
    username, _ = get_user_by_token(session_token)
    if not username:
        raise HTTPException(status_code=404, detail="Session not recognized")
    return {"username": username}

# === ORACLE CREATION ===
@app.post("/create_oracle")
def create_oracle(data: OracleRequest):
    username, accounts = get_user_by_token(data.session_token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid session token")

    oracles = load_data(DATA_FILES["oracles"])
    oracle_id = f"{username}_{data.date_of_birth}"
    if oracle_id in oracles:
        raise HTTPException(status_code=400, detail="Oracle already exists")

    oracle_data = {
        "username": username,
        "oracle_name": "Oracle of the Flame",
        "planetary_ruler": "Unknown",
        "date_of_birth": data.date_of_birth,
        "time_of_birth": data.time_of_birth,
        "location": data.location,
        "rulership_system": data.rulership,
        "chart": data.chart,
        "status": "created",
        "prophecy_arc": {
            "status": "uninitiated",
            "seasonal_seed": None
        }
    }
    oracles[oracle_id] = oracle_data
    accounts[username]["oracles"].append(oracle_id)

    save_data(DATA_FILES["oracles"], oracles)
    save_data(DATA_FILES["accounts"], accounts)

    return {"message": f"Oracle created for {username}", **oracle_data}

# === FILE UPLOAD ===
@app.post("/upload_astrology/{username}")
def upload_astrology(username: str, file: UploadFile = File(...)):
    accounts = load_data(DATA_FILES["accounts"])
    if username not in accounts:
        raise HTTPException(status_code=404, detail="Account not found")

    try:
        contents = json.load(file.file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")

    accounts[username]["astrology_chart"] = contents
    save_data(DATA_FILES["accounts"], accounts)

    return {"message": f"Astrology chart uploaded for {username}"}

# === BATTLE ===
@app.post("/start_battle")
def start_battle(data: BattleInput):
    accounts = load_data(DATA_FILES["accounts"])
    users = list(accounts.keys())
    if len(users) < 2:
        raise HTTPException(status_code=400, detail="Not enough players")
    challenger, opponent = random.sample(users, 2)
    winner = random.choice([challenger, opponent])
    return {"message": f"{winner} wins the battle!"}

# === RAID + DUNGEON ===
@app.post("/raid_join/{username}")
def raid_join(username: str):
    accounts = load_data(DATA_FILES["accounts"])
    if username not in accounts:
        raise HTTPException(status_code=404, detail="Account not found")
    accounts[username]["in_raid"] = True
    save_data(DATA_FILES["accounts"], accounts)
    return {"message": f"{username} has joined the raid party."}

@app.post("/raid_start")
def raid_start():
    accounts = load_data(DATA_FILES["accounts"])
    party = [u for u, d in accounts.items() if d.get("in_raid")]
    if not party:
        raise HTTPException(status_code=400, detail="No players in raid.")
    boss_defeated = random.choice([True, False])
    mvp = random.choice(party)
    rolls = {u: random.randint(1, 100) for u in party}
    for u in party:
        accounts[u]["in_raid"] = False
    save_data(DATA_FILES["accounts"], accounts)
    return {
        "boss_defeated": boss_defeated,
        "mvp": mvp,
        "loot_rolls": rolls,
        "party": party
    }

@app.post("/dungeon_enter/{username}")
def dungeon_enter(username: str):
    result = {
        "username": username,
        "result": random.choice(["victory", "defeat"]),
        "loot": random.randint(10, 100)
    }
    return {"message": f"{username} explored a dungeon.", "details": result}

# === GPT ROUTER COMMANDS ===
@app.post("/oracle/create")
def gpt_oracle_create(data: OracleInput):
    return {"message": f"GPT-Oracle create called for {data.planet}"}

@app.post("/chart/upload")
def gpt_chart_upload(data: ChartInput):
    return {"message": "Chart received", "chart": data.chart}

@app.post("/battle/start")
def gpt_battle(data: BattleInput):
    return start_battle(data)

@app.post("/raid/start")
def gpt_raid(data: RaidInput):
    return raid_start()

@app.post("/directive/do")
def gpt_directive(data: DirectiveInput):
    return {"message": f"Directive executed: {data.directiveId}"}

@app.post("/dungeon/do")
def gpt_dungeon(data: DungeonInput):
    return {"message": f"Dungeon entered on {data.difficulty} difficulty"}

@app.post("/ritual/do")
def gpt_ritual(data: RitualInput):
    return {"message": f"Ritual performed: {data.ritualType}"}

@app.post("/oracle/action")
def gpt_oracle_action(data: OracleActionInput):
    return {"message": f"Oracle {data.oracleId} performed {data.action}"}

@app.post("/codex/entry")
def gpt_codex(data: CodexInput):
    return {"message": f"Codex entry saved: {data.entry}"}
