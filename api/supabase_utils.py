"""Shared Supabase helpers for Pantheon of Oracles APIs.

These utilities centralize error handling for Supabase operations so routers
can consistently surface HTTP errors and log failures without duplicating
boilerplate around ``.execute()`` calls.
"""

from __future__ import annotations

import logging
from typing import Callable, TypeVar

from fastapi import HTTPException


T = TypeVar("T")


def run_supabase(operation: Callable[[], T], context: str) -> T:
    """Execute a Supabase call, logging and raising on failures.

    Args:
        operation: Callable that performs the Supabase request and returns a
            response object with ``error`` and ``data`` attributes.
        context: Human-readable description for logging.

    Returns:
        The Supabase response object.

    Raises:
        HTTPException: When the request raises an exception or returns an
            error payload.
    """

    try:
        response = operation()
    except Exception as exc:  # pragma: no cover - defensive guard around client
        logging.exception("[%s] Supabase operation raised an exception", context)
        raise HTTPException(status_code=500, detail="Supabase request failed") from exc

    if getattr(response, "error", None):
        logging.error("[%s] Supabase error: %s", context, response.error)
        raise HTTPException(status_code=500, detail="Supabase request failed")

    return response
