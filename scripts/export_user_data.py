"""
Export a user's Pantheon data bundle (player account, owned oracles, actions).

Usage:
  SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... \
  python scripts/export_user_data.py --email you@example.com --include-actions --actions-limit 25
  python scripts/export_user_data.py --email you@example.com --include-action-stats --actions-since 2024-10-01

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
    parser.add_argument(
        "--actions-offset",
        type=int,
        default=0,
        help="Number of actions to skip before returning results",
    )
    parser.add_argument(
        "--actions-filter",
        help="Optional action name to filter on (e.g., RITUAL_START)",
    )
    parser.add_argument(
        "--actions-since",
        help="ISO timestamp to limit actions/stats to recent entries",
    )
    parser.add_argument(
        "--actions-until",
        help="ISO timestamp to limit actions/stats to entries created at or before this time",
    )
    parser.add_argument(
        "--include-action-stats",
        action="store_true",
        help="Include aggregated action counts alongside the raw actions list",
    )
    parser.add_argument(
        "--action-stats-limit",
        type=int,
        default=200,
        help="Maximum number of actions to scan when aggregating stats (default 200, max 1000)",
    )
    parser.add_argument(
        "--action-stats-offset",
        type=int,
        default=0,
        help="Number of actions to skip before aggregating counts",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        bundle = get_user_bundle(
            email=args.email,
            include_actions=args.include_actions,
            actions_limit=args.actions_limit,
            actions_offset=args.actions_offset,
            actions_filter=args.actions_filter,
            actions_since=args.actions_since,
            actions_until=args.actions_until,
            include_action_stats=args.include_action_stats,
            action_stats_limit=args.action_stats_limit,
            action_stats_offset=args.action_stats_offset,
        )
    except Exception as exc:  # pragma: no cover - CLI surfacing explicit error
        sys.exit(f"Export failed: {exc}")

    print(json.dumps(bundle, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

