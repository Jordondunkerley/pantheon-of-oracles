"""List oracle catalog entries from Supabase.

Usage:
  python scripts/list_oracles.py --limit 5
  python scripts/list_oracles.py --code ORYONOS
  python scripts/list_oracles.py --role "Fire"

Relies on the same SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY env vars used by
other helpers so it can run locally or in jobs.
"""
import argparse
from typing import Optional

from supabase_client import list_oracles


def format_row(code: str, name: str, role: Optional[str]) -> str:
    role_display = role or "-"
    return f"{code:<20} | {name:<30} | {role_display}"


def main() -> None:
    parser = argparse.ArgumentParser(description="List oracle catalog entries from Supabase")
    parser.add_argument("--code", help="Exact oracle code to filter by", default=None)
    parser.add_argument("--role", help="Exact role/archetype to filter by", default=None)
    parser.add_argument("--limit", type=int, default=25, help="Max rows to return (default 25, max 500)")
    args = parser.parse_args()

    rows = list_oracles(code=args.code, role=args.role, limit=args.limit)

    if not rows:
        print("No oracles found; ensure oracles are seeded and filters are correct.")
        return

    print(format_row("CODE", "NAME", "ROLE"))
    print("-" * 70)
    for row in rows:
        print(format_row(row.get("code", ""), row.get("name", ""), row.get("role")))


if __name__ == "__main__":
    main()
