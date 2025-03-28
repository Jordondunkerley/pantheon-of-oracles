from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from datetime import datetime
import json, os

app = FastAPI()

DATA_FILES = {
    "accounts": "accounts.json",
    "oracles": "oracles.json",
    "guilds": "guilds.json",
    "codex": "codex.json"
}

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
    username: str
    date_of_birth: str
    time_of_birth: str
    location: str
    chart: dict
    rulership: str = "modern"

class GuildJoinRequest(BaseModel):
    username: str
    guild_name: str

# === UTILITY ===
def assign_ruler(dob, system="modern"):
    m, d = int(dob[5:7]), int(dob[8:10])
    if (m == 3 and d >= 21) or (m == 4 and d <= 19): return "Mars"
    elif (m == 4 and d >= 20) or (m == 5 and d <= 20): return "Venus"
    elif (m == 5 and d >= 21) or (m == 6 and d <= 20): return "Mercury"
    elif (m == 6 and d >= 21) or (m == 7 and d <= 22): return "Moon"
    elif (m == 7 and d >= 23) or (m == 8 and d <= 22): return "Sun"
    elif (m == 8 and d >= 23) or (m == 9 and d <= 22): return "Mercury"
    elif (m == 9 and d >= 23) or (m == 10 and d <= 22): return "Venus"
    elif (m == 10 and d >= 23) or (m == 11 and d <= 21): return "Pluto" if system == "modern" else "Mars"
    elif (m == 11 and d >= 22) or (m == 12 and d <= 21): return "Jupiter"
    elif (m == 12 and d >= 22) or (m == 1 and d <= 19): return "Saturn"
    elif (m == 1 and d >= 20) or (m == 2 and d <= 18): return "Uranus" if system == "modern" else "Saturn"
    elif (m == 2 and d >= 19) or (m == 3 and d <= 20): return "Neptune" if system == "modern" else "Jupiter"
    return "Unknown"

# === ROUTES ===
@app.get("/")
def root():
    return {"message": "Pantheon of Oracles API is alive 🔥"}

@app.post("/create_account")
def create_account(account: Account):
    accounts = load_data(DATA_FILES["accounts"])
    if account.username in accounts:
        raise HTTPException(status_code=400, detail="Username already exists")
    accounts[account.username] = {
        "email": account.email,
        "first_name": account.first_name,
        "last_name": account.last_name,
        "password": account.password,
        "created": str(datetime.now()),
        "oracles": [],
        "guild": None
    }
    save_data(DATA_FILES["accounts"], accounts)
    return {"message": f"Account created for {account.first_name} {account.last_name}"}

@app.post("/login")
def login(creds: LoginRequest):
    accounts = load_data(DATA_FILES["accounts"])
    if creds.username not in accounts:
        raise HTTPException(status_code=404, detail="Account not found")
    if accounts[creds.username]["password"] != creds.password:
        raise HTTPException(status_code=401, detail="Incorrect password")
    return {"message": f"Welcome back, {creds.username}"}

@app.post("/create_oracle")
def create_oracle(data: OracleRequest):
    oracles = load_data(DATA_FILES["oracles"])
    accounts = load_data(DATA_FILES["accounts"])

    if data.username not in accounts:
        raise HTTPException(status_code=404, detail="Account not found")

    oracle_id = f"{data.username}_{data.date_of_birth}"
    if oracle_id in oracles:
        raise HTTPException(status_code=400, detail="Oracle already exists")

    oracle_data = {
        "username": data.username,
        "oracle_name": "Oracle of the Flame",
        "planetary_ruler": assign_ruler(data.date_of_birth, data.rulership),
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
    accounts[data.username]["oracles"].append(oracle_id)

    save_data(DATA_FILES["oracles"], oracles)
    save_data(DATA_FILES["accounts"], accounts)

    return {"message": f"Oracle created for {data.username}", **oracle_data}

@app.post("/initiate_player_prophecy/{username}")
def initiate_prophecy(username: str):
    oracles = load_data(DATA_FILES["oracles"])
    updated = []
    for key, oracle in oracles.items():
        if oracle["username"] == username:
            oracle["prophecy_arc"]["status"] = "active"
            oracle["prophecy_arc"]["seasonal_seed"] = "Cycle of the Ember Gate"
            updated.append(oracle)
    if not updated:
        raise HTTPException(status_code=404, detail="No Oracles found to update")
    save_data(DATA_FILES["oracles"], oracles)
    return {"message": f"Prophecy initiated for {username}", "oracles": updated}

@app.post("/join_guild")
def join_guild(req: GuildJoinRequest):
    accounts = load_data(DATA_FILES["accounts"])
    guilds = load_data(DATA_FILES["guilds"])

    if req.username not in accounts:
        raise HTTPException(status_code=404, detail="Account not found")

    if req.guild_name not in guilds:
        guilds[req.guild_name] = {"members": []}

    if req.username not in guilds[req.guild_name]["members"]:
        guilds[req.guild_name]["members"].append(req.username)
        accounts[req.username]["guild"] = req.guild_name

    save_data(DATA_FILES["guilds"], guilds)
    save_data(DATA_FILES["accounts"], accounts)
    return {"message": f"{req.username} joined guild {req.guild_name}"}
