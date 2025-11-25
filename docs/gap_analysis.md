# Pantheon of Oracles – Initial Gap Analysis

This document compares the current repository state against the patch directives to highlight missing systems and upcoming work for the full-scale cross-platform release.

## Current implementation snapshot
- **API surface (FastAPI)**: Auth (register/login), oracle action logging, player account CRUD, oracle CRUD, combined sync endpoint. All endpoints are JWT-protected and use Supabase tables (`users`, `player_accounts`, `oracle_profiles`, `oracle_actions`).
- **Deployment guidance**: Render deployment and Supabase secret rotation documented, with seed scripts for importing GPT patch data into Supabase.
- **Patch catalog**: High-level summaries of patches 1–41 available for reference.

## Coverage vs. patch expectations
- **Met or partially present**
  - Core auth and Supabase persistence scaffolding for accounts and oracles.
  - GPT/Discord sync surface via REST endpoints to log oracle actions and fetch player/oracle data.
  - Render deployment and Supabase migration/seed instructions.
- **Absent / needing implementation**
  - Game systems from patches: multiplayer battles/raids/rituals, Warbands/Legions, Host/Friend/Descendant Oracles, Leviathan/Behemoth arenas, faction halls, story mode, adventure/throne worlds, alignment-based scaling, Ascension/Exalted squadrons, crowns/anointment, mythic unlocks, economy (tokens/coins/shop/wagering), crafting/shape-shifting/pet systems, warband totems, cinematic layouts, chamber backgrounds, etc.
  - Gameplay content pipeline: chart ingestion/astrology calculations, oracle identity frameworks, narrative onboarding (First Flame/Oracron), codex/oracron logging, content pack locking, live-ops/event structures.
  - Cross-platform clients: mobile (iOS/Android), Steam/PC, and VR/AR interfaces; store logins and account linking across Discord/GPT/mobile/Steam.
  - Security/compliance: telemetry, anti-cheat, platform policy alignment, privacy/parental controls, payments, crash/analytics SDK integration.
  - CI/CD & testing: automated tests, device/VR test matrices, feature flags, release automation for app stores and Steam.
  - Observability & operations: monitoring, alerting, rollout/rollback playbooks, capacity/load testing.

## Immediate next steps
- Design detailed service architecture covering game logic services, matchmaking, economy, content pipeline, and client SDK layers for Discord/GPT/mobile/Steam/VR.
- Propose database schema expansions for the major patch systems (oracle tiers, battles, raids, warbands, economy, unlocks, progression, cosmetics, telemetry).
- Define milestone roadmap from Alpha → Beta → RC → GA with scope per stage aligned to patch directives.
- Plan cross-platform auth/account-linking and data migration from current Supabase schemas.
