"""Integration-style tests for the GPT patch router."""

import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parent.parent))

from api import patch_router  # noqa: E402


def test_search_full_returns_enriched_patches(monkeypatch):
    monkeypatch.setattr(
        patch_router,
        "load_all_patches",
        lambda: [
            {"patch_number": 3, "Gamma": {"description": "gamma"}},
            {"patch_number": 1, "Alpha": {"description": "alpha"}},
            {"patch_number": 2, "Beta": {"description": "beta"}},
        ],
    )

    app = FastAPI()
    app.include_router(patch_router.router)
    client = TestClient(app)
    response = client.get("/gpt/patches/search/full", params={"q": "a"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    numbers = [p["patch_number"] for p in payload["patches"]]
    assert numbers == [1, 2, 3]
    assert payload["patches"][0]["patch_name"] == "Alpha"


def test_search_full_filters_by_metadata(monkeypatch):
    monkeypatch.setattr(
        patch_router,
        "load_all_patches",
        lambda: [
            {
                "patch_number": 1,
                "patch_name": "Oracle Chamber Visuals",
                "description": "oracle overlay update",
                "applies_to": ["Oracle Chamber System"],
                "system_tags": ["visual"],
                "status": "Live",
            },
            {
                "patch_number": 2,
                "patch_name": "Backend Patch",
                "description": "backend systems",
                "applies_to": ["Backend"],
                "system_tags": ["api"],
                "status": "Draft",
            },
        ],
    )

    app = FastAPI()
    app.include_router(patch_router.router)
    client = TestClient(app)
    response = client.get(
        "/gpt/patches/search/full",
        params={
            "q": "oracle",
            "applies_to": "chamber",
            "system_tag": "VISUAL",
            "status": "live",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert [p["patch_number"] for p in payload["patches"]] == [1]
