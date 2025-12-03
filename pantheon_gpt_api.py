"""Minimal GPT webhook that validates a shared secret before recording actions."""

import logging
import os
from secrets import compare_digest
from typing import Dict, Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field


def _require_env(name: str) -> str:
    """Return the environment variable or raise at startup if it is missing."""

    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} must be set for Pantheon GPT webhook access")
    return value


API_SECRET = _require_env("PANTHEON_GPT_SECRET")
APP_NAME = os.getenv("APP_NAME", "Pantheon GPT Webhook")

app = FastAPI(title=APP_NAME)


class OracleUpdate(BaseModel):
    command: str
    oracle_name: str
    action: str
    metadata: Dict[str, object] = Field(default_factory=dict)


def _require_bearer(authorization: Optional[str]) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=403, detail="Unauthorized")

    token = authorization.split(" ", 1)[1]
    if not compare_digest(token, API_SECRET):
        raise HTTPException(status_code=403, detail="Unauthorized")
    return token


@app.post("/gpt/update-oracle")
async def update_oracle(data: OracleUpdate, authorization: Optional[str] = Header(None)):
    _require_bearer(authorization)

    payload = data.model_dump()
    logging.info("Received GPT update: %s", payload)
    return {"status": "success", "message": f"{data.oracle_name} will be {data.action}"}


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "service": APP_NAME}
