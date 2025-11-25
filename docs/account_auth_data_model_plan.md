# Pantheon of Oracles – Account, Auth, and Data Model Plan

This plan expands account/auth flows and core schemas to support cross-platform identity, progression, and safety across Discord/GPT, mobile (iOS/Android), Steam/PC, and VR/AR. It reflects patch stacking (Patch 1 as an accumulation of early systems) and later patch overrides.

## 1) Goals and principles
- **Single canonical identity** per player with platform links (Discord/GPT/mobile/Steam) and device/session tracking.
- **Role- and flag-driven access**: feature flags and roles control access to rituals, raids, arenas (Leviathan/Behemoth), story/adventure/throne worlds, and content packs.
- **Secure-by-default**: short-lived tokens, hashed secrets, least-privilege RLS, auditable economy writes, anti-cheat hooks.
- **Migration-first**: evolve current Supabase tables (`users`, `player_accounts`, `oracle_profiles`, `oracle_actions`) into the expanded model without losing data.

## 2) Core schemas (Supabase/Postgres)
- **Identity & linkage**
  - `players`: canonical player record; fields for display name, region, privacy settings, parental controls, ban state.
  - `linked_accounts`: `player_id`, `provider` (discord, gpt, apple, google, steam), `provider_user_id`, `token_meta`, `last_linked_at`.
  - `devices`: device identifiers + platform/os/version, push token, fraud flags.
  - `sessions`: JWT/session metadata, issued_at/exp, device_id, platform, feature flag snapshot, last_seen.
- **Oracles & rosters**
  - `oracles`: canonical oracle identity (Host/Friend/Descendant), alignment tags, crowns/anointment, mythic unlocks, ascension tier, cosmetics.
  - `oracle_forms`: alternate forms (shapeshifts, pets, mounts, forged aspects) with loadout slots.
  - `rosters`: per-player squad builds (including Exalted Squads, legions/warbands) with totem slots and synergy tags.
- **Progression & story**
  - `levels`, `alignment_modifiers`, `story_progress` (First Flame, Oracron, adventure/throne world chapters), `achievements`, `lore_unlocks`.
- **Match/encounter**
  - `matches` (type: battle/raid/ritual/arena), `match_participants`, `raid_phases`, `encounter_turns`, `seed_hashes` (anti-cheat), `ghost_snapshots` for async encounters.
- **Economy & entitlements**
  - `wallets` (coins/tokens), `transactions` (idempotent ledger), `wagers`, `shop_offers`, `drops`, `crafting_recipes`, `content_packs`, `entitlements`, `cosmetics`, `codex_unlocks`.
- **Telemetry & safety**
  - `telemetry_events`, `anti_cheat_flags`, `crash_reports`, `moderation_actions` (reports, suspensions), `audit_logs` for admin/GM actions.

## 3) Auth and platform flows
- **Discord/GPT**: token-scoped login → Gateway exchanges bot token/OAuth code for JWT tied to `linked_accounts.provider='discord'|'gpt'`; limited scopes, rate limits, and feature flags restricting heavy actions (e.g., PvP queues).
- **Mobile (iOS/Android)**: Sign in with Apple/Google → Auth service verifies store token → links/creates player → issues JWT + refresh; supports guest creation with mandatory upgrade before multiplayer/economy.
- **Steam/PC**: Steam OpenID/Encrypted App Ticket → verify via Steam WebAPI → link account and issue JWT; enforce anti-cheat flags on mismatches.
- **VR/AR**: piggybacks on mobile/Steam auth; device binding required for safety; optional 2FA for purchases.
- **Account linking & merge**: existing Supabase `users` rows map to `players`; new `linked_accounts` rows created during first login per provider; conflict resolution asks for verification (email/OTP) before merging.

## 4) RLS, permissions, and roles
- **RLS defaults**: per-table policies keyed on `auth.uid()` mapped to `players.id` via `sessions`; write scopes restricted to owning player; admin/GM roles separated via JWT claims and `roles` array.
- **Feature flags**: stored per environment; snapshot embedded in `sessions` and refreshed on resume; gates for closed alpha/beta, patch-specific content (e.g., Leviathan arena), AR/VR experiments.
- **Rate limits**: per provider and IP/device; stricter for Discord/GPT to avoid abuse; matchmaking/economy writes behind idempotency keys.

## 5) Anti-cheat, safety, privacy
- **Replay validation**: combat submissions include `seed_hashes` and turn logs; server recomputes for integrity.
- **Device integrity**: track device fingerprint, OS attestation where available; flag rooted/jailbroken devices; require online validation for ranked queues.
- **Economy protection**: all `transactions` signed with deterministic hash; withdrawals/wagers double-entry ledger; admin actions logged in `audit_logs`.
- **Safety/compliance**: COPPA/age gating via `players.region` + declared age; parental controls enforced on chat/multiplayer/purchases; data retention windows for telemetry; privacy toggles for profile visibility and matchmaking.

## 6) Migration from current schema
- Create `players` table and migrate `users.id` → `players.id`; add derived fields (display name, region, privacy defaults).
- Add `linked_accounts` rows for existing Discord/GPT users using stored identifiers; mark records as verified where applicable.
- Split `player_accounts` into `wallets` (currency) and `story_progress` (chapters/achievements); keep backward-compatible views during transition.
- Move oracle data from `oracle_profiles` into `oracles` and `oracle_forms`; attach alignment/crown/anointment fields per patch directives.
- Repoint endpoints in `pantheon_gpt_api.py` and `player_oracle_endpoints.py` to new tables once migrations are in place; keep read-only fallbacks for legacy tables until clients update.

## 7) Operational hooks
- **Session lifecycle**: refresh tokens with rotation; revoke on device risk or moderation; store last_seen for reconnect logic.
- **Logging/observability**: structured audit trail for auth events, link attempts, failed validations; PII minimized in logs.
- **Backups & recovery**: nightly backups with PITR; tabletop drills for account-merge regressions and ledger corruption.

## 8) Immediate implementation steps
1. Draft SQL migrations for `players`, `linked_accounts`, `devices`, `sessions`, `rosters`, `wallets`, `transactions`, `matches`, `telemetry_events`, `anti_cheat_flags`, `content_packs`, `entitlements`.
2. Add RLS policies and JWT claim mapping for player → session → row ownership; seed admin roles.
3. Implement auth flows per provider in the gateway (FastAPI) with device binding and feature flag snapshotting.
4. Update API handlers to read/write new tables with idempotency keys for economy/matchmaking endpoints.
5. Add telemetry/anti-cheat hooks to combat submission and economy writes; emit `audit_logs` on admin actions.
6. Provide migration scripts to backfill from existing Supabase data and validate linkage integrity.
