from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from pydantic import BaseModel
from datetime import datetime
import json, os, random, uuid
import httpx
from dotenv import load_dotenv

from fastapi import FastAPI

pantheon_app = FastAPI(
    title="Pantheon of Oracles API",
    description="Universal Oracle Action Gateway",
    version="1.0.0",
    servers=[
        {"url": "https://pantheon-of-oracles.onrender.com"}
    ]
)


load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

app = FastAPI()

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

# === BATTLE SYSTEM ===
class BattleRequest(BaseModel):
    challenger: str
    opponent: str

@app.post("/start_battle")
def start_battle(req: BattleRequest):
    accounts = load_data(DATA_FILES["accounts"])
    if req.challenger not in accounts or req.opponent not in accounts:
        raise HTTPException(status_code=404, detail="Both users must have accounts")

    winner = random.choice([req.challenger, req.opponent])
    loser = req.opponent if winner == req.challenger else req.challenger

    result = {
        "challenger": req.challenger,
        "opponent": req.opponent,
        "winner": winner,
        "loser": loser,
        "timestamp": str(datetime.now())
    }

    battles = load_data(DATA_FILES["battles"])
    battle_id = f"{req.challenger}_vs_{req.opponent}_{int(datetime.now().timestamp())}"
    battles[battle_id] = result
    save_data(DATA_FILES["battles"], battles)

    return {"message": f"{winner} wins the battle against {loser}!", "battle": result}

# === CREATE ORACLE ===
@app.post("/create_oracle")
async def create_oracle(data: OracleRequest):
    username = await get_user_by_token_supabase(data.session_token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid session token")

    oracle_id = f"{username}_{data.date_of_birth}"
    oracle_data = {
        "oracle_id": oracle_id,
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
        },
        "created_at": str(datetime.now())
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SUPABASE_URL}/rest/v1/oracles",
            headers={
                "apikey": SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=representation"
            },
            json=oracle_data
        )

        if response.status_code != 201:
            raise HTTPException(status_code=400, detail="Oracle creation failed")

        return response.json()[0]

# === GET ORACLE INFO ===
@app.get("/oracle/info")
def get_oracle_info(username: str):
    oracles = load_data(DATA_FILES["oracles"])
    matching = [o for o in oracles.values() if o.get("username") == username]
    if not matching:
        raise HTTPException(status_code=404, detail="No Oracle found for user")
    return matching[0]

# === UPLOAD CHART FILES ===
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

@app.post("/upload_oracle_profile/{username}")
def upload_oracle_profile(username: str, file: UploadFile = File(...)):
    oracles = load_data(DATA_FILES["oracles"])
    try:
        contents = json.load(file.file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")

    oracle_id = f"{username}_uploaded"
    contents["username"] = username
    contents["uploaded"] = str(datetime.now())
    oracles[oracle_id] = contents

    save_data(DATA_FILES["oracles"], oracles)
    return {"message": f"Oracle profile uploaded for {username}"}


class OracleUpdate(BaseModel):
    command: str
    oracle_name: str
    action: str
    metadata: dict

@app.post("/gpt/update-oracle")
async def update_oracle(data: OracleUpdate, request: Request):
    token = request.headers.get("Authorization")
    if token != f"Bearer {os.getenv('PANTHEON_GPT_SECRET')}":
        raise HTTPException(status_code=403, detail="Unauthorized")

    print(f"Received GPT update: {data.dict()}")
    return {"status": "success", "message": f"{data.oracle_name} will be {data.action}"}


# === DUNGEON & RAID SYSTEM ===
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
    raid_party = [u for u, d in accounts.items() if d.get("in_raid")]

    if not raid_party:
        raise HTTPException(status_code=400, detail="No one is currently joined to the raid.")

    boss_defeated = random.choice([True, False])
    mvp = random.choice(raid_party)
    loot_rolls = {user: random.randint(1, 100) for user in raid_party}

    for user in raid_party:
        accounts[user]["in_raid"] = False

    save_data(DATA_FILES["accounts"], accounts)

    return {
        "message": "🔥 The raid has been completed!",
        "boss_defeated": boss_defeated,
        "mvp": mvp,
        "loot_rolls": loot_rolls,
        "party": raid_party
    }

@app.post("/dungeon_enter/{username}")
def dungeon_enter(username: str):
    accounts = load_data(DATA_FILES["accounts"])
    if username not in accounts:
        raise HTTPException(status_code=404, detail="Account not found")

    result = {
        "username": username,
        "result": random.choice(["victory", "defeat"]),
        "loot": random.randint(1, 100),
        "timestamp": str(datetime.now())
    }

    return {"message": f"{username} ventures into the dungeon and meets {result['result']}!", "details": result}



from fastapi import FastAPI, Request, Header, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import pytz

app = FastAPI()

# Metadata structure with full alignment and identity context
class Metadata(BaseModel):
    patch: str
    core_faction: Optional[str]
    planetary_faction: Optional[str]
    guild: Optional[str]
    warband: Optional[str]
    context: str  # e.g., 'battle', 'ritual', 'fusion', 'oricron'
    oracle_tier: str  # Tier 1–10 or 'Ascended'
    oracle_level: int  # 0–100
    ascended_rank: Optional[int]  # 0–300 if applicable
    oracle_form: Optional[str]  # e.g., 'Ascendant Fusion'
    codex_tag: Optional[str]
    timestamp: str  # Client-provided ISO 8601 (EST–Toronto)

# Main payload structure
class OracleCommand(BaseModel):
    command: str = Field(..., example="/report_battle_victory")
    oracle_name: str = Field(..., example="Nyssarion")
    action: str = Field(..., example="Declared victorious in Warband combat under Week 4 alignment.")
    metadata: Metadata

# Secure API key (move to env in production)
API_KEY = "J&h^fvAc*gH!aS#ba@PL#iuW&D11J"

@app.post("/gpt/update-oracle")
async def update_oracle_action(request: Request, oracle_command: OracleCommand, authorization: str = Header(...)):

    if authorization != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Toronto-local timestamp for internal server log
    tz = pytz.timezone("America/Toronto")
    now_est = datetime.now(tz).isoformat()

    print("\n[ORACLE ACTION RECEIVED]")
    print(f"Command:        {oracle_command.command}")
    print(f"Oracle:         {oracle_command.oracle_name}")
    print(f"Action:         {oracle_command.action}")
    print(f"Patch:          {oracle_command.metadata.patch}")
    print(f"Context:        {oracle_command.metadata.context}")
    print(f"Core Faction:   {oracle_command.metadata.core_faction}")
    print(f"Planetary:      {oracle_command.metadata.planetary_faction}")
    print(f"Guild:          {oracle_command.metadata.guild}")
    print(f"Warband:        {oracle_command.metadata.warband}")
    print(f"Tier:           {oracle_command.metadata.oracle_tier}")
    print(f"Level:          {oracle_command.metadata.oracle_level}")
    print(f"Ascended Rank:  {oracle_command.metadata.ascended_rank}")
    print(f"Form:           {oracle_command.metadata.oracle_form}")
    print(f"Codex Tag:      {oracle_command.metadata.codex_tag}")
    print(f"EST Timestamp:  {now_est}")

    # Placeholder: Route to subsystem (e.g., battle logs, prophecy tracker, codex)
    # e.g., if oracle_command.command == "/toggle_fusion": update_fusion_state(...)

    return {
        "status": "success",
        "message": "Oracle action processed and logged",
        "oracle": oracle_command.oracle_name,
        "timestamp": now_est
    }
