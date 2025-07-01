from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import os

app = FastAPI()

API_SECRET = os.getenv("PANTHEON_GPT_SECRET")
RELEASED_PATCHES = set(os.getenv("RELEASED_PATCHES", "base").split(","))

class OracleUpdate(BaseModel):
    command: str
    oracle_name: str
    action: str
    metadata: dict

@app.post("/gpt/update-oracle")
async def update_oracle(data: OracleUpdate, request: Request):
    token = request.headers.get("Authorization")
    if token != f"Bearer {API_SECRET}":
        raise HTTPException(status_code=403, detail="Unauthorized")

    patch = data.metadata.get("patch")
    if patch not in RELEASED_PATCHES:
        raise HTTPException(status_code=403, detail="Unreleased content")

    print(f"Received GPT update: {data.dict()}")
    return {"status": "success", "message": f"{data.oracle_name} will be {data.action}"}
