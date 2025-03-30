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
