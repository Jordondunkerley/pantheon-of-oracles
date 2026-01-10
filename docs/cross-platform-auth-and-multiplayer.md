# Cross-Platform Auth, Data Security, and Multiplayer Governance

## Auth Flow Alignment
- **JWT-first core**: Issue short-lived access tokens (15m) signed with JWS (RS256) and rotate refresh tokens (30d) stored in httpOnly/secure cookies for web and Authorization headers for GPT/Discord bots. Include `sub` (user UUID), `scope`, `platform` (discord|gpt|mobile|steam|browser), and `session_id` claims to align audit trails.
- **OAuth/store logins**: Use the same Supabase auth user for Discord, Steam, Apple/Google mobile stores, and browser. Map providers via the `linked_identities` table (see migration) and require email verification for stores that provide emails; otherwise, require device attestation plus an onboarding email link.
- **GPT auth**: GPT clients call the Router with Bearer tokens. For long-running chats, use the refresh token flow via a lightweight `/auth/refresh` endpoint and rotate `session_id` on each refresh to invalidate stolen tokens quickly.
- **Discord auth**: Use OAuth2 Code + PKCE, exchange for a Supabase session, and push the `discord_user_id` into `linked_identities`. Store Discord guild/context in `session_metadata` to scope bot actions.
- **Steam/mobile auth**: Validate Steam tickets / App Store/Play integrity attestation server-side, then upsert `provider_user_id` into `linked_identities`. Require a one-time email/passwordless link to guarantee recovery and cross-device linking.
- **Store login parity**: Apply the same JWT scopes (`play`, `economy`, `admin`) across GPT/Discord/mobile. Enforce scope checks in API handlers and Supabase policies to avoid platform-specific bypasses.

## Account Linking Contracts
- Single canonical `user_id` (Supabase auth). Each external identity maps to `linked_identities` rows; enforce uniqueness on `(provider, provider_user_id)`.
- **Linking UX**: Present short-lived, single-use link codes (6–8 chars) that resolve to a `linking_token` row with an expiry. Steam/mobile clients present the code; GPT/Discord accounts approve via DM/inline prompt. The backend exchanges it for upserting the identity row and returns a refreshed JWT pair.
- **Unlinking and recovery**: Require a verified email or two factors (one existing linked identity + email OTP) before unlinking. Soft-delete identities and keep an audit log entry for reversals.

## Secure Astrology Data Handling
- **Storage**: Persist charts and readings in `astrology_charts.encrypted_payload` (pgcrypto PGP_SYM_ENCRYPT) with a per-environment symmetric key; store derived traits/cached projections separately in `astrology_charts.derived_profile` for queryable fields.
- **Access controls**: RLS checks ensure only `auth.uid()` or an approved party member (via `party_membership`) can read/write their chart. Admins (scope contains `admin`) can read for moderation only.
- **Transit and caching**: Require TLS everywhere; avoid client-side caching of decrypted charts on shared devices. Server-side, cache only derived, non-sensitive projections.
- **Backups**: Use encrypted backups; rotate keys quarterly and re-encrypt `encrypted_payload` with a background job to reduce blast radius.

## Database Migration & Policy Plan (Supabase)
See `supabase/migrations/20250915_auth_multiplayer.sql` for the concrete DDL and RLS policies. Key tables:
- `profiles`: canonical user profile keyed by Supabase auth `uuid` with display data and culture/region hints for matchmaking.
- `linked_identities`: provider + provider_user_id mapping to `user_id` with uniqueness and timestamps for audit.
- `astrology_charts`: encrypted payload + derived projection fields, versioning, and checksum for tamper detection.
- `parties` & `party_members`: lightweight group play containers with roles for co-op rituals/raids.
- `match_sessions`: cross-platform PvE/PvP sessions with status, platform, and seed metadata for anti-cheat.
- `wallets`, `currency_transactions`, `inventory_items`: economy primitives with double-entry style `currency_transactions` and optimistic balance checks.

Policies enforce owner-only reads/writes, allow party readers for shared play, and gate economy writes on valid sessions plus balance guards.

## Telemetry, Anti-Cheat, and Safety Layer
- **Event pipeline**: Emit signed telemetry envelopes (`session_id`, `platform`, `build_hash`, `ip_hash`, `device_fingerprint`, `anticheat_flag`) to a queue (e.g., Redpanda/SQS) with batch workers persisting to `analytics.events` (separate warehouse) and `match_sessions` aggregates.
- **Integrity signals**: Compare client-reported timestamps vs. server receive time, detect clock skew, impossible action rates, and mismatched deterministic seeds. Flag and store in `match_sessions.integrity_state`.
- **Client hardening**: Use platform-native attestation (Steam VAC checks, Apple/Play Integrity), obfuscate assets, and require signed action payloads for competitive modes. GPT/Discord commands use server authority only (no client simulation).
- **Safety**: Add content filters on player-generated text, rate limits per `session_id`/IP, and abuse review hooks for moderators. Keep an audit log (e.g., `currency_transactions` + `linked_identities` history) for dispute resolution.
- **Operational response**: Auto-quarantine suspicious sessions (limited rewards, no trading), notify player, and allow appeal. Provide admin override endpoints gated by `admin` scope + RLS policy allowing `auth.role() = 'service_role'`.
