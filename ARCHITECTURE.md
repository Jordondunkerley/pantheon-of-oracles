# Target Architecture: Discord + GPT + Mobile (iOS/Android) + Steam (PC/VR)

## High-Level Overview
- **Clients**: Discord bot, mobile apps (iOS/Android), Steam (PC/VR). All connect to a shared backend over REST + WebSocket (for real-time features).
- **Backend**: Stateless API layer (FastAPI/Node), game logic services, matchmaking, content pipeline services, economy, analytics/telemetry. Uses Supabase (Postgres + Auth + Storage) and Render for compute/queues.
- **Data & Messaging**: Postgres (Supabase), Redis (Render) for caching/rate limits/matchmaking queues, object storage (Supabase) for assets, optional CDN for static assets. Event bus via Redis streams or lightweight queue (Render private service). Feature flags stored in Postgres and cached in Redis.

## Service Boundaries
### API Gateway / Edge
- Terminates TLS, routes to REST/WebSocket services, handles auth (Supabase JWT), rate limiting (Redis), request logging.
- Exposes: `/api/*` REST, `/ws` WebSocket, Discord interaction endpoint.

### Session & Identity
- Supabase Auth for user accounts and token issuance.
- Discord users mapped via OAuth/interaction payloads; Steam OpenID mapped to shared account; device identifiers for guests.

### Game Logic Service
- Stateless microservice; authoritative rules and progression validation.
- Handles per-session state, inventory/economy calls, GPT-driven narrative hooks (calls GPT orchestrator), and writes to Postgres.
- Provides REST for CRUD/state, WebSocket for live session updates.

### Matchmaking Service
- Uses Redis sorted sets/lists for lobbies/queues; Postgres for persistent party/match records.
- Computes skill/role constraints; emits match assignments to game logic service.
- WebSocket notifications for queue position and match found events.

### GPT Orchestrator
- Dedicated service to call OpenAI (or Azure OpenAI) with guardrails (system prompts, safety filters, rate limits).
- Caches reusable prompts/snippets; streams tokens to clients via server-sent events or WebSocket.
- Enforces content policy and logs prompts/completions to telemetry pipeline.

### Content Pipeline Service
- Receives creator submissions (quests, dialog, items) via admin UI or CLI.
- Validates schema, runs GPT-assisted linting, produces JSON/Protobuf bundles stored in Supabase Storage and versioned.
- Publishes new content versions to CDN; notifies clients via feature-flag rollout or in-app news feed.

### Economy Service
- Central wallet/balance, purchase validation, price configuration, and reward granting.
- Integrates with platform payments: Discord SKUs, App Store/Play Store receipts, Steam microtransactions/DLC.
- Signed server-side receipts; fraud checks; double-entry ledger in Postgres; uses idempotency keys.

### Analytics / Telemetry Pipeline
- Client and server emit events to ingestion endpoint (REST/Batch) -> queued in Redis streams -> workers forward to data warehouse (Supabase/Postgres or BigQuery/Redshift).
- Real-time dashboards for health metrics; user-level telemetry stored with privacy controls.
- A/B testing and feature flags evaluation (Postgres tables + Redis cache) consumed by clients on startup.

## Client Integration Surfaces
### Discord Bot
- Interaction endpoint (slash commands, buttons) via REST; event-driven; uses WebSocket for outgoing game updates to interested sessions.
- Uses bot token + Supabase service key to act as privileged client for certain admin flows.

### Mobile (iOS/Android)
- SDK layer wrapping REST + WebSocket with automatic reconnect and feature-flag fetch on launch.
- Uses platform push notifications for match found/session events; background fetch for content updates.
- In-app purchases validated via Economy Service; receipts sent server-side.

### Steam (PC/VR)
- Native client SDK integrating REST + WebSocket; uses Steamworks for auth + commerce.
- Supports rich presence and lobby join via Steamworks; VR build reads same SDK surfaces.

### Cross-Platform Considerations
- Shared protocol schemas (OpenAPI + JSON schemas; optional Protobuf for WebSocket payloads).
- Deterministic server-side decisions; clients mostly thin to prevent cheating.
- Time sync via server timestamps; replay protection via signed requests and nonce.

## Build & Deploy Strategy
### CI/CD
- GitHub Actions (or Render native) pipeline: lint, type-check, test; build Docker images for backend services; push to registry.
- Infra as code via `render.yaml` (services, cron jobs, background workers) and Supabase migrations (`supabase/migrations`).
- Versioned content bundles built in pipeline and published to Supabase Storage/CDN.

### Backend Deploy (Render + Supabase)
- Render Web Service for API gateway/game logic; Render Background Worker for matchmaking and telemetry ingestion; Redis instance for cache/queues.
- Supabase for Postgres/Auth/Storage; run `supabase db push` migrations via CI before deploy.
- Feature flags configured via Postgres table; rollout controlled through admin UI and cached in Redis.

### Mobile Store Pipelines
- iOS: Fastlane workflow for build/test, code signing, TestFlight; production App Store submit on tagged releases.
- Android: Gradle + Play Console integration for internal/alpha/beta tracks; uses feature flags to dark-launch.
- Mobile SDK published to package managers (Swift Package Manager/CocoaPods; Maven/Gradle) from CI.

### Steam Builds (PC/VR)
- SteamPipe build scripts in CI for Windows/Linux; VR build variant shares codebase with platform-specific assets.
- Uses Steam branches for beta/preview; integrates feature flags to gate new systems.

### Release & Feature Management
- Trunk-based development with short-lived branches; release tags trigger production deploys and store submissions.
- Feature flags wrap major surfaces (new matchmaking modes, GPT prompt variants, economy items).
- Observability baked into rollout: metrics + traces + structured logs; automatic rollback via Render if health checks fail.

## Security & Compliance
- Secrets via Render environment + Supabase secrets; no secrets in repo.
- Request signing for economy endpoints; platform receipt validation server-side only.
- PII minimization and GDPR/CCPA controls; data retention policies enforced via scheduled jobs.
