from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict
import os
import jwt
from datetime import datetime, timedelta

API_SECRET = os.getenv("PANTHEON_GPT_SECRET", "change-me")
ALGORITHM = "HS256"

app = FastAPI(
    title="Pantheon API to GPT Router",
    description="Minimal routing layer for GPT commands",
)

class AuthRequest(BaseModel):
    email: str
    password: str

class ChartUpload(BaseModel):
    chart: Dict[str, str]

class OracleCommand(BaseModel):
    oracle_name: str
    action: str
    metadata: Dict[str, str] = {}

class GameAction(BaseModel):
    actor: str
    target: Optional[str] = None
    metadata: Dict[str, str] = {}


def verify_token(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=403, detail="Invalid authorization header")
    token = authorization.split("Bearer ", 1)[1]
    try:
        payload = jwt.decode(token, API_SECRET, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=403, detail="Invalid token")
    return payload

@app.post("/register")
def register(data: AuthRequest):
    """Register a new user. Placeholder implementation."""
    return {"status": "registered", "email": data.email}

@app.post("/login")
def login(data: AuthRequest):
    payload = {"sub": data.email, "exp": datetime.utcnow() + timedelta(hours=1)}
    token = jwt.encode(payload, API_SECRET, algorithm=ALGORITHM)
    return {"access_token": token}

@app.post("/chart")
def upload_chart(data: ChartUpload, _: dict = Depends(verify_token)):
    """Upload or update a natal chart."""
    return {"status": "chart stored"}

@app.post("/oracle")
def create_oracle(cmd: OracleCommand, _: dict = Depends(verify_token)):
    """Create or modify an oracle."""
    return {"status": "oracle updated", "oracle": cmd.oracle_name}

@app.post("/battle")
def battle(action: GameAction, _: dict = Depends(verify_token)):
    return {"result": "battle started", "actor": action.actor}

@app.post("/raids")
def raids(action: GameAction, _: dict = Depends(verify_token)):
    return {"result": "raid started", "actor": action.actor}

@app.post("/ritual")
def ritual(action: GameAction, _: dict = Depends(verify_token)):
    return {"result": "ritual performed", "actor": action.actor}

@app.post("/codex")
def codex_entry(data: Dict[str, str], _: dict = Depends(verify_token)):
    return {"status": "codex updated"}
