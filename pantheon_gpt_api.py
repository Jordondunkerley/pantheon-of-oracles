"""Minimal GPT webhook that validates a shared secret before recording actions."""

import os

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel


def _require_env(name: str) -> str:
    """Return the environment variable or raise at startup if it is missing."""

    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} must be set for Pantheon GPT webhook access")
    return value

app = FastAPI()

API_SECRET = _require_env("PANTHEON_GPT_SECRET")

class OracleUpdate(BaseModel):
    command: str
    oracle_name: str
    action: str
    metadata: dict

@app.post("/gpt/update-oracle")
async def update_oracle(data: OracleUpdate, request: Request):
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(status_code=403, detail="Unauthorized")

    if token.split(" ", 1)[1] != API_SECRET:
        raise HTTPException(status_code=403, detail="Unauthorized")

    print(f"Received GPT update: {data.dict()}")
    return {"status": "success", "message": f"{data.oracle_name} will be {data.action}"}
