# Pantheon of Oracles Milestone Breakdown to GA

This plan sequences deliverables from feature-complete alpha through GA, covering mobile (iOS/Android), Steam (PC/VR), and AR/VR layers while honoring patch directives.

## Milestone Ladder

### Milestone A: Feature-Complete Alpha (Discord/GPT-first)
- **Core loop**: Oracle creation, astrology chart ingest, divination responses, and Codex browsing.
- **Combat/rituals**: Implement raids/ritual/battle flows with turn/timer logic, status effects, and oracle progression.
- **Persistence**: Supabase schemas for oracles, parties, encounters, inventory, and Codex unlocks; RLS policies enforced.
- **Ops**: Logging/metrics for Discord/GPT endpoints; basic alerting; seed content pipeline for astrology data and encounters.
- **Testing**: Unit tests for API/game logic; integration tests for Supabase policies; load test baseline for GPT/Discord endpoints.

### Milestone B: Beta – Mobile (iOS/Android) and Steam (PC)
- **Clients**: Mobile app shells with login, Codex, oracle management, raids/ritual participation; Steam desktop parity UI.
- **Networking**: Real-time (WebSocket) session layer for co-op raids/battles; matchmaking queues; reconnection handling.
- **Content ops**: Live-ops tooling to schedule events/encounters; CDN strategy for media; localization scaffolding.
- **Economy**: Soft currency loops, cosmetic unlocks, and progression rewards aligned with patch directives; telemetry for drop rates.
- **Security**: Anti-cheat signals (tamper checks, server authority on combat outcomes); store-linked auth (Apple/Google/Steam) with account linking.
- **Testing**: Device-matrix UI tests; cross-platform integration tests; soak tests for real-time sessions; crash reporting wired.

### Milestone C: Release Candidate – Polish and Compliance
- **UX polish**: Accessibility (screen readers, font scaling, color contrast); refined tutorials and onboarding.
- **Compliance**: Privacy/age ratings, COPPA/GDPR readiness, payments/revenue flows (IAP/Steam wallet) with receipts validation.
- **Operations**: Full observability dashboards; incident playbooks; rollback/feature flags; CDN and edge cache validation.
- **Localization**: Priority locales; translation workflow with QA; dynamic layout testing.
- **Testing**: Full regression suites, performance profiling on device matrix, security/pen tests, store submission checklists.

### Milestone D: GA + AR/VR Rollout
- **VR/AR**: OpenXR-based VR client (SteamVR) and ARCore/ARKit overlays for rituals/raids; spatial UI for Codex.
- **Performance**: Frame pacing/latency budgets, comfort settings (snap turn, vignette), asset LODs; GPU/thermal profiles on mobile/PCVR.
- **Content**: Immersive ritual scenes, spatial interactions for divination, haptics/audio polish; live-ops hooks for VR events.
- **Operations**: Ongoing live-ops calendar, A/B testing for economy and UX; continued anti-cheat/telemetry tuning.

## Cross-Milestone Tranches (parallel work)
- **Backend/gameplay**: Expand rulesets, encounter generators, and oracle abilities; maintain server authority and determinism.
- **Data & safety**: Schema migrations, RLS hardening, audit logs, PII minimization, rate limiting, and abuse detection.
- **Tooling**: Internal admin/live-ops dashboards, content ingestion validators, and synthetic data generators for tests.
- **Build & CI/CD**: Automated builds for mobile (Fastlane/Gradle) and Steam branches; artifact signing; unit/integration checks gating deploys.

## Immediate Next Actions
- Finalize Alpha gameplay specs (raid/ritual turn schemas, oracle ability lists, progression tables).
- Draft Supabase migrations for oracles/encounters/inventory and codify RLS policies.
- Define WebSocket session/message contracts and matchmaking queues for Beta.
- Stand up mobile/Steam client skeletons (auth, Codex, oracle view) and wire to existing API.
- Establish test harnesses: API unit tests, Supabase policy tests, and basic load tests for GPT/Discord endpoints.
