"""
Service-role helper to delete a user's Pantheon data for clean re-seeding.

Example:
    python scripts/purge_user_data.py --email you@example.com --delete-user

Requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in the environment. When
--delete-user is omitted, only player/oracle data (and their oracle_actions)
are removed so the auth row can be reused.
"""
from argparse import ArgumentParser
from typing import Any, Dict

from supabase_client import delete_user_bundle


def parse_args() -> Dict[str, Any]:
    parser = ArgumentParser(description="Delete a user's Pantheon data from Supabase")
    parser.add_argument("--email", required=True, help="Email of the user to purge")
    parser.add_argument(
        "--keep-actions",
        action="store_true",
        help="Do not delete oracle_actions (default is to delete them)",
    )
    parser.add_argument(
        "--delete-user",
        action="store_true",
        help="Delete the auth user row after removing dependent records",
    )
    return vars(parser.parse_args())


def main() -> None:
    args = parse_args()
    email = args["email"]
    keep_actions = args["keep_actions"]
    delete_user = args["delete_user"]

    result = delete_user_bundle(
        email,
        delete_actions=not keep_actions,
        delete_user=delete_user,
    )

    print("✅ Purge complete:", result)


if __name__ == "__main__":
    main()
