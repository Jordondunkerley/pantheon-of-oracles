"""
CLI helper to create a Pantheon user with hashed password storage.

Usage:
    python create_account.py --email you@example.com --password hunter2

The script uses the shared Supabase environment variables (`SUPABASE_URL`,
`SUPABASE_SERVICE_ROLE_KEY`) and leverages ``supabase_client`` so credentials
match the FastAPI service defaults. It is idempotent when ``--allow-existing``
is provided, returning the existing record instead of failing.
"""
from argparse import ArgumentParser
from typing import Any, Dict

from supabase_client import get_or_create_user, create_user, _get_user_record


def parse_args() -> Dict[str, Any]:
    parser = ArgumentParser(description="Create a Pantheon account in Supabase")
    parser.add_argument("--email", required=True, help="User email to create")
    parser.add_argument("--password", required=True, help="Plaintext password to hash")
    parser.add_argument(
        "--allow-existing", action="store_true", help="Return the existing user instead of failing"
    )
    return vars(parser.parse_args())


def main() -> None:
    args = parse_args()
    email = args["email"]
    password = args["password"]
    allow_existing = args["allow_existing"]

    if allow_existing:
        user = get_or_create_user(email, password)
    else:
        existing = _get_user_record(email)
        if existing:
            raise SystemExit(f"User already exists for {email}; rerun with --allow-existing")
        user = create_user(email, password)

    print("✅ User ready:", {"id": user.get("id"), "email": user.get("email")})


if __name__ == "__main__":
    main()
