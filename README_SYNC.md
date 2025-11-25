# Pantheon of Oracles – Sync Guide

## 1) Rotate secrets (very important)
- Supabase: create a **new Service Role Key**; revoke the old one.
- Render: set env vars (no secrets in code):
  SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, JWT_SECRET, ACCESS_TOKEN_EXPIRE_MINUTES (optional), APP_NAME.

## 2) DB schema
Apply `supabase/migrations/20250903_init.sql` in the Supabase SQL editor (or CLI).
This creates the core auth/oracle tables plus `player_accounts` and
`oracle_profiles`, which preserve the full JSON payloads from the Pantheon
templates so GPT syncing can store every nested field (factions, stats, visual
overlays, etc.).

## 3) Seed from GPT patches
Run twice (once per file) locally or in a job:
```
pip install -r requirements.txt
export SUPABASE_URL=...
export SUPABASE_SERVICE_ROLE_KEY=...
export PATCHES_PATH="./Patches 1-25 – Pantheon of Oracles GPT.JSON"
python scripts/seed_oracles.py
export PATCHES_PATH="./Patches 26-41 – Pantheon of Oracles GPT.JSON"
python scripts/seed_oracles.py
```

## 4) Run locally
```
uvicorn api.main:app --reload
```

## 5) Deploy on Render
- Use `render.yaml` or configure via dashboard.
- Start command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`.

## 6) Smoke tests
```
BASE="https://<your-render-service>"
curl -s -X POST $BASE/auth/register -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"pass123"}'

curl -s -X POST $BASE/auth/login -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"pass123"}'

# Use returned token here:
TOKEN="Bearer <JWT>"
curl -s -X POST $BASE/gpt/update-oracle -H "Authorization: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"oracle_id":"<uuid>","player_id":"jordondunkerley","action":"TEST","metadata":{"ok":true}}'
```

## 7) Legacy code
- Keep old JSON-file endpoints for reference but do not use them as service entry points.
- New entry point is `api/main.py`.
