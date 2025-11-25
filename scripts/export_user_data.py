"""
Export a user's Pantheon data bundle (player account, owned oracles, actions).

Usage:
  SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... \
  python scripts/export_user_data.py --email you@example.com --include-actions --actions-limit 25

This script relies on service-role credentials so it can resolve ownership
without an API token. Output is JSON printed to stdout.
"""

import argparse
import json
import sys

from supabase_client import get_user_bundle


def parse_args():
    parser = argparse.ArgumentParser(description="Export a user's Pantheon data bundle")
    parser.add_argument("--email", required=True, help="Email address of the user to export")
    parser.add_argument(
        "--include-actions",
        action="store_true",
        help="Include recent oracle actions scoped to the user's oracle/player IDs",
    )
    parser.add_argument(
        "--actions-limit",
        type=int,
        default=50,
        help="Maximum number of actions to return (default 50, max 500)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        bundle = get_user_bundle(
            email=args.email,
            include_actions=args.include_actions,
            actions_limit=args.actions_limit,
        )
    except Exception as exc:  # pragma: no cover - CLI surfacing explicit error
        sys.exit(f"Export failed: {exc}")

    print(json.dumps(bundle, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

