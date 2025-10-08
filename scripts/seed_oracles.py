"""
Seed Oracles from GPT patches JSON into Supabase.
Idempotent: upserts by 'code'.
Env:
  SUPABASE_URL
  SUPABASE_SERVICE_ROLE_KEY
  PATCHES_PATH  (path to a patches JSON file)
"""
import os, json, sys
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
PATCHES_PATH = os.environ.get("PATCHES_PATH")

if not (SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY and PATCHES_PATH):
    sys.exit("Set SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY and PATCHES_PATH")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

with open(PATCHES_PATH, "r", encoding="utf-8") as f:
    patches = json.load(f)

acc = {}
# Expected structure: a list/dict containing patches, each with an "oracles" array
# Adapt mapping here if your JSON uses different keys.
def maybe_iter(x):
    if isinstance(x, list): return x
    if isinstance(x, dict): return [x]
    return []

for patch in maybe_iter(patches):
    for o in maybe_iter(patch.get("oracles", [])):
        code = o.get("code") or o.get("name")
        if not code: continue
        acc[code] = {
            "code": code,
            "name": o.get("name", code.title()),
            "role": o.get("role"),
            "rules": o.get("rules", {})
        }

count = 0
for row in acc.values():
    supabase.table("oracles").upsert(row, on_conflict="code").execute()
    count += 1

print(f"Seeded/updated {count} oracles from {os.path.basename(PATCHES_PATH)}")
