# Pantheon of Oracles – Architecture & Platform Plan

This plan aligns the game’s full-stack architecture with the patch directives and target platforms (Discord/GPT, mobile, Steam/PC, VR/AR).
It will guide subsequent schema design, feature delivery, and client integrations.

## 1) Architectural principles
- **Authoritative backend** for game state, progression, matchmaking, and economy; clients remain thin.
- **Composable services** so raids/battles/economy/codex can evolve without breaking core loops.
- **Content-driven**: astrology charts, rituals, encounters, and cosmetic packs delivered via pipeline with versioning and flags.
- **Cross-platform identity**: one account across Discord/GPT/mobile/Steam/VR with entitlements synced through Supabase.
- **Observability and safety**: telemetry, anti-cheat, crash reporting, and feature flags baked into every surface.

## 2) Service topology
- **API Gateway (FastAPI)**: single entry for REST/WebSocket. Routes requests to domain services; handles auth, rate limits, flags.
- **Auth & Identity Service**: JWT issuance, OAuth/store logins, platform linking (Discord/GPT/mobile/Steam), session management.
- **Player Profile & Progression Service**: manages profiles, oracle rosters (Host/Friend/Descendant), leveling, crowns/anointment, mythic unlocks, ascension/exalted squads, legions/warbands, faction halls, throne/adventure world access.
- **Matchmaking & Session Service**: queues for battles/raids/rituals/arenas (Leviathan/Behemoth); session lifecycle, team composition rules, MMR; supports synchronous PvP/PvE and async ghost encounters.
- **Combat/Encounter Service**: resolves turn/phase logic for battles, raids, rituals, chamber layouts, warband totems, shapeshifts/pets/forge effects, and environmental modifiers; deterministic simulation with seed-based validation for anti-cheat.
- **Economy & Inventory Service**: coins/tokens, wagering, shop rotations, crafting/forging, cosmetics, codex/oracron unlocks, content pack entitlements, drop tables, and transactional ledgering.
- **Content Pipeline Service**: ingest astrology charts, oracle identity templates, narrative scripts (First Flame/Oracron), chamber backgrounds, cinematic layouts, and event packs; publishes versioned content bundles with feature flags.
- **Codex & Narrative Service**: logs oracle actions, tracks codex entries/oracron, story mode progress, adventure/throne world chapters, and lore unlocks.
- **Telemetry & Safety Service**: analytics events, anti-cheat checks (replay hash validation, rate anomalies), crash/error reporting, moderation hooks, parental controls, and age/region gating.

## 3) Data flows
- **Account linking**: platform login → Auth service exchanges for JWT → links to canonical player ID in Supabase → entitlements fetched via Economy service.
- **Match entry**: player selects roster/loadout → Matchmaking reserves session → Combat service runs simulation (server-auth, optionally authoritative turn validation via WebSocket) → results persisted to Progression and Economy services.
- **Content delivery**: Content pipeline publishes bundle → Gateway serves bundle manifest → clients pull assets/configs; feature flags gate access per platform/region.
- **Codex logging**: in-client actions post to Codex service → entries unlock lore, cosmetics, and progression triggers.

## 4) Client integration surfaces
- **Mobile/Steam/VR clients**: primary protocol is JSON over HTTPS for CRUD and lobby flows; WebSocket for real-time combat, raids, rituals, and live events. SDK wrapper per platform to standardize auth, telemetry, and reconnection.
- **Discord/GPT**: lightweight wrappers that call the same gateway endpoints; uses token-scoped flows to log oracle actions, fetch codex entries, and trigger encounters with rate limits.
- **Offline/async support**: clients can queue async encounters; Combat service validates on submit; ghost data cached for low-bandwidth cases.

## 5) Data & schema direction (high level)
- **Identity**: `players`, `linked_accounts`, `devices`, `sessions`.
- **Oracles & rosters**: `oracles`, `oracle_forms`, `rosters`, `legions`, `warbands`, `totems`, `pets` with loadout slots and synergy tags.
- **Progression**: `levels`, `crowns`, `anointments`, `ascensions`, `exalted_squads`, `story_progress`, `achievements`, `alignment_modifiers`.
- **Match/encounter**: `matches`, `match_participants`, `encounter_turns`, `raid_phases`, `ritual_states`, `seed_hashes` for anti-cheat replay.
- **Economy**: `wallets`, `transactions`, `shop_offers`, `drops`, `crafting_recipes`, `wagers`, `entitlements`, `cosmetics`, `content_packs`.
- **Codex/lore**: `codex_entries`, `oracron_logs`, `lore_unlocks`, `event_journal`.
- **Telemetry/safety**: `telemetry_events`, `anti_cheat_flags`, `crash_reports`.

## 6) Deployment & environments
- **Environments**: dev → staging → production with isolated Supabase projects and Render (or alternative) services; feature flags manage phased rollout.
- **CI/CD**: lint/test → build Docker images → run migrations → deploy gateway/services; mobile builds via CI to TestFlight/Play Store internal tracks; Steam branches for beta/live.
- **Secrets & config**: managed via environment variables; rotated per environment; client-config manifests fetched post-auth.

## 7) Observability & reliability targets
- **SLIs/SLOs**: auth (<300ms p95), match create (<1s p95), combat tick (<150ms p95), error budget tied to rollback policy.
- **Monitoring**: structured logs, metrics (requests, latency, error rates), traces for combat simulations; dashboards per service.
- **Resilience**: circuit breakers on third parties, rate limiting, backpressure on matchmaking queues, idempotent economy writes, replay validation for combat submissions.

## 8) Platform specifics
- **Mobile (iOS/Android)**: store logins (Sign in with Apple/Google), push notifications, background resume; asset bundles optimized for cellular download; controller/touch input mappings.
- **Steam/PC**: Steam auth, achievements, cloud saves; keyboard/mouse + controller input; higher-fidelity VFX.
- **VR/AR**: OpenXR baseline; ARKit/ARCore for mobile AR; room-scale rituals and chamber interactions; performance targets 90fps (VR) with comfort options (vignette, snap turn, seated mode).

## 9) Next steps
1. Produce concrete schema migrations for the tables listed above with Supabase policies per platform.
2. Define gateway route map (REST + WebSocket) with service ownership and request/response contracts.
3. Create platform SDK interface definitions (mobile/Steam/VR) for auth, matchmaking, telemetry, and reconnection flows.
4. Draft CI/CD pipeline configuration covering app store/Steam packaging, migrations, and staged rollouts.
5. Map feature flags to milestone phases (Alpha, Beta, RC, GA) to control content and platform access.
