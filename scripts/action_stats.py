"""Aggregate oracle action counts for a user (service-role).

Usage:
  python scripts/action_stats.py --email user@example.com [--limit 200] [--since 2024-01-01]

Env:
  SUPABASE_URL
  SUPABASE_SERVICE_ROLE_KEY
"""
import argparse

from supabase_client import summarize_user_actions


parser = argparse.ArgumentParser(description="Summarize oracle_actions for a user")
parser.add_argument("--email", required=True, help="User email")
parser.add_argument("--oracle-id", help="Optional oracle_id to filter")
parser.add_argument("--player-id", help="Optional player_id to filter")
parser.add_argument("--action", help="Optional action name filter")
parser.add_argument(
    "--since",
    help="Only include actions created at or after this ISO timestamp",
)
parser.add_argument(
    "--until",
    help="Only include actions created at or before this ISO timestamp",
)
parser.add_argument(
    "--limit",
    type=int,
    default=200,
    help="Max rows to fetch before aggregation (default 200, max 1000)",
)
parser.add_argument(
    "--offset",
    type=int,
    default=0,
    help="Number of rows to skip before aggregating counts",
)


def main():
    args = parser.parse_args()
    limit = min(args.limit if args.limit and args.limit > 0 else 200, 1000)

    stats = summarize_user_actions(
        args.email,
        oracle_id=args.oracle_id,
        player_id=args.player_id,
        action=args.action,
        since=args.since,
        until=args.until,
        limit=limit,
        offset=args.offset,
    )

    print(stats)


if __name__ == "__main__":
    main()
