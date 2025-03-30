from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from pydantic import BaseModel
from datetime import datetime
import json, os, random

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
class BattleRequest(BaseModel):
    challenger: str
    opponent: str

# === BATTLE SYSTEM ===
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

# === JSON FILE UPLOAD ===
@app.post("/upload_astrology/{username}")
def upload_astrology(username: str, file: UploadFile = File(...)):
    accounts = load_data(DATA_FILES["accounts"])
    if username not in accounts:
        raise HTTPException(status_code=404, detail="Account not found")

    contents = json.load(file.file)
    accounts[username]["astrology"] = contents
    save_data(DATA_FILES["accounts"], accounts)

    return {"message": f"Astrology chart uploaded for {username}"}

@app.post("/upload_oracle/{username}")
def upload_oracle(username: str, file: UploadFile = File(...)):
    oracles = load_data(DATA_FILES["oracles"])
    oracle_id = f"{username}_custom"
    contents = json.load(file.file)
    contents["username"] = username
    contents["uploaded"] = str(datetime.now())

    oracles[oracle_id] = contents
    save_data(DATA_FILES["oracles"], oracles)

    return {"message": f"Oracle profile uploaded for {username}"}

# === DUNGEON & RAID PLACEHOLDER ===
@app.post("/raid_join/{username}")
def raid_join(username: str):
    return {"message": f"{username} has joined the raid party. (Placeholder)"}

@app.post("/dungeon_enter/{username}")
def dungeon_enter(username: str):
    return {"message": f"{username} enters the dungeon of shifting fate. (Placeholder)"}
