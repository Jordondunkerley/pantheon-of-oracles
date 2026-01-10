"""Service-role helper to bulk insert oracle_actions with ownership checks.

Usage:
    python scripts/log_actions_bulk.py --email you@example.com --actions-file actions.json

The actions file should be a JSON list with objects containing ``oracle_id``,
``player_id``, ``action``, optional ``client_action_id`` (for idempotency), and
 optional ``metadata`` fields. The script reuses the service-role ownership
 protections defined in ``supabase_client`` to prevent cross-user inserts and
 will report how many entries were deduplicated vs inserted.
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from supabase_client import record_oracle_actions_bulk


def load_actions(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Actions file must contain a JSON list")
    return data


def main():
    parser = argparse.ArgumentParser(description="Bulk insert oracle_actions for a user")
    parser.add_argument("--email", required=True, help="User email to scope ownership checks")
    parser.add_argument(
        "--actions-file",
        required=True,
        type=Path,
        help="Path to JSON file containing a list of action payloads",
    )

    args = parser.parse_args()
    actions = load_actions(args.actions_file)
    result = record_oracle_actions_bulk(args.email, actions)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
