"""Minimal GPT webhook that validates a shared secret before recording actions."""

import logging
import os
from secrets import compare_digest
from typing import Dict, Optional
from uuid import UUID

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from supabase import Client

from api.config import get_settings, get_supabase_client
from api.supabase_utils import run_supabase


def _require_env(name: str) -> str:
    """Return the environment variable or raise at startup if it is missing."""

    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} must be set for Pantheon GPT webhook access")
    return value


API_SECRET = _require_env("PANTHEON_GPT_SECRET")
APP_NAME = os.getenv("APP_NAME", "Pantheon GPT Webhook")

settings = get_settings()
supabase: Client = get_supabase_client()

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

app = FastAPI(title=APP_NAME)


class OracleUpdate(BaseModel):
    """Incoming webhook payload expected from the GPT agent."""

    oracle_id: UUID
    player_id: str
    action: str
    metadata: Dict[str, object] = Field(default_factory=dict)


def _extract_bearer_token(authorization: Optional[str]) -> str:
    """Validate and return a bearer token or raise an HTTP 403 error."""

    if not authorization:
        raise HTTPException(status_code=403, detail="Unauthorized")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=403, detail="Unauthorized")

    return token


def _require_bearer(authorization: Optional[str]) -> str:
    token = _extract_bearer_token(authorization)

    if not compare_digest(token, API_SECRET):
        raise HTTPException(status_code=403, detail="Unauthorized")
    return token


@app.post("/gpt/update-oracle")
async def update_oracle(data: OracleUpdate, authorization: Optional[str] = Header(None)):
    _require_bearer(authorization)

    payload = data.model_dump()
    logging.info(
        "[%s] Received GPT update for oracle %s", APP_NAME, payload.get("oracle_id")
    )

    record = _insert_oracle_action(data)

    return {
        "status": "success",
        "message": f"Oracle {data.oracle_id} will be {data.action}",
        "record": record,
    }


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "service": APP_NAME}


def _insert_oracle_action(data: OracleUpdate) -> Dict[str, object]:
    """Insert an oracle action into Supabase and return the stored row."""

    response = run_supabase(
        lambda: supabase.table("oracle_actions")
        .insert(
            {
                "oracle_id": str(data.oracle_id),
                "player_id": data.player_id,
                "action": data.action,
                "metadata": data.metadata,
            }
        )
        .execute(),
        "insert oracle action",
    )

    rows = response.data or []
    if not rows:
        logging.error("[%s] Supabase insert returned no rows", APP_NAME)
        raise HTTPException(status_code=500, detail="Failed to record oracle action")

    return rows[0]
