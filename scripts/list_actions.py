"""
List oracle_actions for a given user with ownership-aware filters.

Example:
    python scripts/list_actions.py --email you@example.com --limit 10 --action RITUAL_START

Uses SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY from the environment, relying on
``supabase_client`` to apply the same ownership constraints as the FastAPI
endpoints.
"""
from argparse import ArgumentParser
from typing import Any, Dict

from supabase_client import list_user_actions


def parse_args() -> Dict[str, Any]:
    parser = ArgumentParser(description="List oracle actions for a Pantheon user")
    parser.add_argument("--email", required=True, help="Email of the user whose actions to fetch")
    parser.add_argument("--oracle-id", help="Filter by oracle_id owned by the user")
    parser.add_argument("--player-id", help="Filter by player_id owned by the user")
    parser.add_argument("--action", help="Filter by action type (e.g., RITUAL_START)")
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
        default=50,
        help="Maximum number of rows to return (defaults to 50, max 500)",
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Number of rows to skip before returning results",
    )
    parser.add_argument(
        "--order",
        choices=["asc", "desc"],
        default="desc",
        help="Sort direction for created_at (desc by default)",
    )
    return vars(parser.parse_args())


def main() -> None:
    args = parse_args()
    email = args["email"]
    oracle_id = args.get("oracle_id")
    player_id = args.get("player_id")
    action = args.get("action")
    since = args.get("since")
    until = args.get("until")
    limit = args.get("limit") or 50
    offset = args.get("offset") or 0
    order = args.get("order") or "desc"

    actions_result = list_user_actions(
        email,
        oracle_id=oracle_id,
        player_id=player_id,
        action=action,
        since=since,
        until=until,
        order=order,
        limit=limit,
        offset=offset,
        include_metadata=True,
    )

    actions = actions_result.get("actions", []) if isinstance(actions_result, dict) else actions_result
    meta = actions_result.get("meta") if isinstance(actions_result, dict) else None

    if meta:
        print(
            f"Returned {meta.get('returned', len(actions))} / {meta.get('total_available', 'unknown')} actions "
            f"(limit={meta.get('limit')}, offset={meta.get('offset')}, has_more={meta.get('has_more')})"
        )
    else:
        print(f"Found {len(actions)} actions")

    for row in actions:
        print(row)


if __name__ == "__main__":
    main()
