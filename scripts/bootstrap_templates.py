"""
Bootstrap a demo Pantheon user, player profile, and oracle profile from template JSON files.

Example:
    python scripts/bootstrap_templates.py \
        --email demo@example.com \
        --password changeme \
        --player "Player Account Template.json" \
        --oracle "Oracle Profile Template.JSON"

This script relies on ``supabase_client`` for hashed password handling and JSON
upserts so it mirrors the FastAPI service behavior. The player/oracle payloads
are stored verbatim in the ``profile`` JSONB columns, preserving every nested
field from the Pantheon patches.
"""
from argparse import ArgumentParser
from pathlib import Path
import json
from typing import Any, Dict

from supabase_client import get_or_create_user, upsert_player_account, upsert_oracle_profile


def parse_args() -> Dict[str, Any]:
    parser = ArgumentParser(description="Seed a user with player + oracle templates")
    parser.add_argument("--email", required=True, help="User email to create or reuse")
    parser.add_argument("--password", required=True, help="Password for the user (hashed before insert)")
    parser.add_argument("--player", required=True, help="Path to player template JSON")
    parser.add_argument("--oracle", required=True, help="Path to oracle template JSON")
    return vars(parser.parse_args())


def load_json(path_str: str) -> Dict[str, Any]:
    path = Path(path_str)
    if not path.exists():
        raise SystemExit(f"Template not found: {path_str}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    args = parse_args()

    # Ensure user exists (or create with hashed password)
    user = get_or_create_user(args["email"], args["password"])

    player_payload = load_json(args["player"])
    oracle_payload = load_json(args["oracle"])

    stored_player = upsert_player_account(args["email"], player_payload)
    stored_oracle = upsert_oracle_profile(args["email"], oracle_payload)

    print("✅ Seeded user:", {"id": user.get("id"), "email": user.get("email")})
    print("✅ Player profile:", {"player_id": stored_player.get("player_id"), "username": stored_player.get("username")})
    print("✅ Oracle profile:", {"oracle_id": stored_oracle.get("oracle_id"), "oracle_name": stored_oracle.get("oracle_name")})


if __name__ == "__main__":
    main()
