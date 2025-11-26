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

### Seed a demo player + oracle
Use the shared templates to create a user with full JSON payloads stored in
`player_accounts` and `oracle_profiles`:
```
python create_account.py --email you@example.com --password pass123 --allow-existing
python scripts/bootstrap_templates.py \
  --email you@example.com \
  --password pass123 \
  --player "Player Account Template.json" \
  --oracle "Oracle Profile Template.JSON"
```
Both scripts respect `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` so they align
with the FastAPI defaults. Oracle IDs are now plain UUID strings to keep action
logging compatible with the `oracle_actions` foreign key.

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

# Record an action while verifying that the oracle/player belong to the caller
curl -s -X POST $BASE/gpt/oracle-action -H "Authorization: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"oracle_id":"<uuid>","player_id":"<player_uuid>","action":"RITUAL_START"}'

# List recent actions scoped to your oracle/player IDs (optional filters)
curl -s "$BASE/gpt/oracle-actions?limit=10" -H "Authorization: $TOKEN"
# Skip the first 25 results (pagination style)
curl -s "$BASE/gpt/oracle-actions?limit=10&offset=25" -H "Authorization: $TOKEN"
# Filter to a specific action type (e.g., only ritual starts)
curl -s "$BASE/gpt/oracle-actions?action=RITUAL_START&limit=5" -H "Authorization: $TOKEN"
# Only pull actions created after a timestamp
curl -s "$BASE/gpt/oracle-actions?since=2024-10-01T00:00:00Z&limit=25" -H "Authorization: $TOKEN"
# Slice a window using inclusive bounds
curl -s "$BASE/gpt/oracle-actions?since=2024-10-01T00:00:00Z&until=2024-11-01T00:00:00Z&limit=25" -H "Authorization: $TOKEN"

# Aggregate counts per action type for your owned IDs (now with meta)
curl -s "$BASE/gpt/oracle-action-stats?since=2024-10-01T00:00:00Z" -H "Authorization: $TOKEN"
# Offset aggregation to paginate through larger windows; meta echoes limits/filters
curl -s "$BASE/gpt/oracle-action-stats?since=2024-10-01T00:00:00Z&offset=100&limit=200" -H "Authorization: $TOKEN"
# Aggregate within a bounded window
curl -s "$BASE/gpt/oracle-action-stats?since=2024-10-01T00:00:00Z&until=2024-11-01T00:00:00Z" -H "Authorization: $TOKEN"

# Reset your own bundle (player + oracles + optional actions)
curl -s -X POST $BASE/gpt/delete-bundle -H "Authorization: $TOKEN" \
  -H "Content-Type: application/json" -d '{"delete_actions":true}'

# Fetch seeded oracle catalog entries (requires at least one account for auth)
curl -s "$BASE/gpt/oracle-catalog?limit=5" -H "Authorization: $TOKEN"

# Pull a combined bundle (account, oracles, recent actions)
curl -s "$BASE/gpt/sync?include_actions=true&actions_limit=25" -H "Authorization: $TOKEN"
# Sync only a specific action type when fetching history
curl -s "$BASE/gpt/sync?include_actions=true&actions_filter=RITUAL_START&actions_limit=10" -H "Authorization: $TOKEN"
# Sync only actions created after a timestamp
curl -s "$BASE/gpt/sync?include_actions=true&actions_since=2024-10-01T00:00:00Z&actions_limit=25" -H "Authorization: $TOKEN"
# Sync within a bounded window (actions_since + actions_until)
 curl -s "$BASE/gpt/sync?include_actions=true&actions_since=2024-10-01T00:00:00Z&actions_until=2024-11-01T00:00:00Z&actions_limit=25" -H "Authorization: $TOKEN"
 # Sync starting from a higher offset for pagination
 curl -s "$BASE/gpt/sync?include_actions=true&actions_offset=50&actions_limit=25" -H "Authorization: $TOKEN"
 # Sync and include aggregated action counts (uses the same filters/limits)
 curl -s "$BASE/gpt/sync?include_action_stats=true&actions_since=2024-10-01T00:00:00Z&actions_until=2024-11-01T00:00:00Z&action_stats_limit=500" -H "Authorization: $TOKEN"
 # Paginate action stats while keeping filters aligned
 curl -s "$BASE/gpt/sync?include_action_stats=true&actions_offset=100&action_stats_offset=100&actions_limit=25" -H "Authorization: $TOKEN"
```

**Timestamps & limits**
- All `since`/`until` parameters require ISO-8601 strings (e.g., `2024-10-01T00:00:00Z`). Invalid timestamps now return `400` so problems surface quickly.
- Limits are capped automatically (actions: max 500, action stats: max 1000) to keep Supabase queries efficient.

**Pagination metadata**
- `/gpt/oracle-actions` returns a `meta` block with the applied limit/offset, filters, and `has_more` + `total_available` (when Supabase provides it) so clients can walk paginated windows safely.
- `/gpt/oracle-action-stats` echoes a `meta` block (limit, offset, filters, rows_aggregated, and `has_more`) to mirror the history endpoint and align aggregation windows with paginated fetches.
- `/gpt/sync` mirrors both `actions_meta` and `action_stats_meta` alongside the combined bundle, and `scripts/list_actions.py` echoes the metadata to help plan subsequent CLI calls.

 Or run locally against Supabase using the helper script after seeding:

```
python scripts/list_oracles.py --limit 5

# Export a user's bundle using service-role credentials
python scripts/export_user_data.py --email you@example.com --include-actions --actions-limit 25
# Export with an action offset for pagination and matching stats window
python scripts/export_user_data.py --email you@example.com --include-actions --actions-offset 25 --include-action-stats --action-stats-offset 25
# Export with filtered history and aggregated action stats
python scripts/export_user_data.py --email you@example.com --include-action-stats --actions-since 2024-10-01 --actions-until 2024-11-01 --actions-filter RITUAL_START

# Reset a user for fresh imports (service-role)
python scripts/purge_user_data.py --email you@example.com --delete-user

# Inspect a user's oracle_actions with optional filters (service-role)
python scripts/list_actions.py --email you@example.com --action RITUAL_START --since 2024-10-01 --until 2024-11-01 --limit 10

# Summarize a user's action counts (service-role)
python scripts/action_stats.py --email you@example.com --since 2024-10-01 --until 2024-11-01
# Summarize with an offset to paginate aggregation
python scripts/action_stats.py --email you@example.com --since 2024-10-01 --until 2024-11-01 --offset 100
```

## 7) Legacy code
- Keep old JSON-file endpoints for reference but do not use them as service entry points.
- New entry point is `api/main.py`.
