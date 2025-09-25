"""FastAPI application for the Pantheon of Oracles backend."""
from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Optional

import pytz
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from config import ConfigurationError, get_settings
from patch_loader import PatchNotFoundError, patch_registry
from supabase_client import SupabaseConfigurationError, get_supabase_client

logger = logging.getLogger("pantheon.main")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())

settings = get_settings()

try:
    supabase = get_supabase_client()
except SupabaseConfigurationError as exc:  # pragma: no cover - configuration issue
    logger.warning("Supabase client unavailable: %s", exc)
    supabase = None

def _resolve_timezone():
    try:
        return pytz.timezone(settings.timezone)
    except Exception:  # pragma: no cover - timezone misconfiguration
        logger.warning("Invalid timezone '%s', falling back to UTC", settings.timezone)
        return pytz.UTC


def _authorise(authorization: Optional[str]) -> None:
    expected = settings.pantheon_api_key
    if not expected:
        raise HTTPException(status_code=503, detail="API key not configured")

    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    if authorization == expected or authorization == f"Bearer {expected}":
        return

    raise HTTPException(status_code=401, detail="Unauthorized")


class Metadata(BaseModel):
    patch: str = Field(..., description="Patch identifier (e.g. 'Patch 26')")
    core_faction: Optional[str] = None
    planetary_faction: Optional[str] = None
    guild: Optional[str] = None
    warband: Optional[str] = None
    context: str
    oracle_tier: str
    oracle_level: int
    ascended_rank: Optional[int] = None
    oracle_form: Optional[str] = None
    codex_tag: Optional[str] = None
    timestamp: Optional[str] = None


class OracleCommand(BaseModel):
    command: str
    oracle_name: str
    action: str
    metadata: Metadata


app = FastAPI(
    title="Pantheon of Oracles API",
    description="Universal Oracle Action Gateway with Auth",
    version="2.0.0",
)


@app.get("/patches")
async def list_patches():
    """Return a summary of all known instructional patches."""

    return {"patches": patch_registry.summaries()}


@app.get("/patches/{patch_identifier}")
async def get_patch(patch_identifier: str):
    """Return the full details for a specific patch."""

    try:
        patch = patch_registry.resolve(patch_identifier)
    except PatchNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown patch '{patch_identifier}'") from exc

    return patch.as_dict()


@app.post("/gpt/update-oracle")
async def update_oracle_action(
    oracle_command: OracleCommand,
    authorization: Optional[str] = Header(None),
):
    _authorise(authorization)

    try:
        patch = patch_registry.resolve(oracle_command.metadata.patch)
    except PatchNotFoundError as exc:
        raise HTTPException(status_code=422, detail=f"Unknown patch '{oracle_command.metadata.patch}'") from exc

    timezone = _resolve_timezone()
    now_est = datetime.now(timezone).isoformat()

    if not oracle_command.metadata.timestamp:
        oracle_command.metadata.timestamp = now_est

    payload = {
        "oracle_name": oracle_command.oracle_name,
        "command": oracle_command.command,
        "action": oracle_command.action,
        "patch": patch.identifier,
        "patch_name": patch.patch_name,
        "core_faction": oracle_command.metadata.core_faction,
        "planetary_faction": oracle_command.metadata.planetary_faction,
        "guild": oracle_command.metadata.guild,
        "warband": oracle_command.metadata.warband,
        "context": oracle_command.metadata.context,
        "tier": oracle_command.metadata.oracle_tier,
        "level": oracle_command.metadata.oracle_level,
        "rank": oracle_command.metadata.ascended_rank,
        "oracle_form": oracle_command.metadata.oracle_form,
        "codex_tag": oracle_command.metadata.codex_tag,
        "timestamp": oracle_command.metadata.timestamp,
    }

    if supabase is None:
        logger.warning("Supabase client not configured; skipping persistence for %s", oracle_command.oracle_name)
        result_payload = {"status": "skipped", "reason": "supabase_not_configured"}
    else:
        try:
            result = supabase.table("oracle_actions").insert(payload).execute()
            result_payload = getattr(result, "data", None)
            if result_payload is None:
                json_method = getattr(result, "json", None)
                if callable(json_method):
                    result_payload = json_method()
            if result_payload is None:
                result_payload = str(result)
            logger.info(
                "[ORACLE ACTION RECEIVED] %s | %s | %s | patch=%s",
                oracle_command.oracle_name,
                oracle_command.command,
                now_est,
                patch.identifier,
            )
        except Exception as exc:  # pragma: no cover - runtime database error
            logger.exception("Failed to persist oracle action: %s", exc)
            raise HTTPException(status_code=500, detail="Failed to record oracle action") from exc

    response_payload = {
        "status": "success",
        "oracle": oracle_command.oracle_name,
        "patch": patch.identifier,
        "patch_name": patch.patch_name,
        "timestamp": now_est,
        "result": result_payload,
    }
    return JSONResponse(response_payload)


@app.exception_handler(ConfigurationError)
async def configuration_error_handler(_: Request, exc: ConfigurationError):  # pragma: no cover - safety net
    return JSONResponse(status_code=500, content={"detail": str(exc)})


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
