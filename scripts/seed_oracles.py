"""Seed oracle definitions from GPT patch JSON files into Supabase.

This utility is idempotent (upserts by `code`) and now reuses the shared
Pantheon API configuration so secret handling is centralized. Provide a
patch file via ``--patches`` or the ``PATCHES_PATH`` environment variable.

Environment variables (validated via ``api.config``):
  SUPABASE_URL
  SUPABASE_SERVICE_ROLE_KEY

Usage examples:
  python scripts/seed_oracles.py --patches "./Patches 1-25 – Pantheon of Oracles GPT.JSON"
  PATCHES_PATH="./Patches 26-41 – Pantheon of Oracles GPT.JSON" python scripts/seed_oracles.py
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

from supabase import Client

from api.config import get_supabase_client


def _load_patches(path: Path) -> Iterable[Dict[str, Any]]:
    """Read a patch file into an iterable of patch dictionaries."""

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.exit(f"Patch file not found: {path}")
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive guard
        sys.exit(f"Invalid JSON in {path}: {exc}")

    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    sys.exit(f"Unsupported patch structure in {path} (expected list or object)")


def _iter_oracles(patches: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Collect oracle rows keyed by code/name to avoid duplicate inserts."""

    oracles: Dict[str, Dict[str, Any]] = {}

    for patch in patches:
        for oracle in patch.get("oracles", []) or []:
            code = oracle.get("code") or oracle.get("name")
            if not code:
                continue
            oracles[code] = {
                "code": code,
                "name": oracle.get("name", code.title()),
                "role": oracle.get("role"),
                "rules": oracle.get("rules", {}),
            }

    return oracles


def _upsert_oracles(client: Client, oracles: Dict[str, Dict[str, Any]]) -> int:
    """Persist oracle definitions into Supabase and return the count inserted."""

    count = 0

    for oracle in oracles.values():
        response = client.table("oracles").upsert(oracle, on_conflict="code").execute()
        if response.error:
            sys.exit(f"Failed to upsert oracle '{oracle['code']}': {response.error}")
        count += 1

    return count


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed Pantheon oracles from GPT patch JSON")
    parser.add_argument(
        "--patches",
        type=Path,
        default=None,
        help="Path to a GPT patch JSON file (or set PATCHES_PATH)",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> None:
    args = parse_args(argv or [])

    env_path = os.getenv("PATCHES_PATH")
    patch_path = args.patches or (Path(env_path) if env_path else None)

    if not patch_path:
        sys.exit("Provide a patch file with --patches or set PATCHES_PATH")

    patches = _load_patches(patch_path)
    oracles = _iter_oracles(patches)

    if not oracles:
        sys.exit(f"No oracles found in {patch_path}")

    try:
        client = get_supabase_client()
    except RuntimeError as exc:  # pragma: no cover - environment validation
        sys.exit(str(exc))
    count = _upsert_oracles(client, oracles)

    print(f"Seeded/updated {count} oracles from {patch_path.name}")


if __name__ == "__main__":
    main(sys.argv[1:])
