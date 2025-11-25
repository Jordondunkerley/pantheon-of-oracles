# Mobile & Steam Release + Ops Guide

This document summarizes store requirements, deployment automation, and SRE playbooks for Pantheon of Oracles across Apple, Google Play, and Steam.

## App Store / Play Store / Steam Requirements
- **Privacy & data use**
  - Publish a clear privacy policy URL; enumerate data collection (accounts, telemetry, crash logs) and retention.
  - Complete Apple App Privacy Nutrition Labels and Google Data Safety forms; confirm no unexpected third-party data sharing.
  - Obtain user consent for analytics/crash reporting and honor deletion requests (GDPR/CCPA where applicable).
- **Age ratings**
  - Complete Apple age-rating questionnaire (violence, user-generated content, gambling). Provide content filters/moderation notes.
  - Configure Google Play Content Rating (ICRA/ESRB/PEGI) and target audience/ads disclosures.
  - Steam: set content descriptors and regional ratings where required; verify chat moderation and reporting tools.
- **Payments & commerce**
  - Use StoreKit / Google Play Billing for any digital goods or subscriptions; expose restore purchases and receipts validation.
  - Steam microtransactions via Steam Inventory Service / Microtransaction APIs; confirm regional pricing and tax handling.
  - Provide account deletion/export pathways and terms of service links within the game.
- **Platform SDKs & compliance**
  - Apple: integrate Xcode/StoreKit, Sign in with Apple if using third-party login, Background Modes review notes, push notification entitlement.
  - Google: target latest API level, handle scoped storage, Play Integrity API/Device Check for abuse prevention.
  - Steamworks: initialize `ISteamClient` early, handle overlay, achievements, cloud saves, rich presence, and cross-platform friends if supported.
- **Crash reporting & analytics**
  - Enable Crashlytics/Sentry/Bugsnag with symbol uploads (dSYMs/ProGuard mapping) and PII scrubbing.
  - Instrument gameplay funnels, matchmaking reliability, purchase success, and latency metrics; avoid device identifiers outside platform policies.
  - Document data export/retention schedules and ensure log redaction for user content.

## Deployment Automation
- **TestFlight (iOS)**
  - CI pipeline: build with Xcode/fastlane `gym`, upload via `pilot` with beta app review notes/screenshots.
  - Automatically increment build numbers, sync signing (match/App Store Connect API keys), and attach release notes from CHANGELOG.
  - Create external/internal tester groups and auto-expire builds after release; notify via Slack/Discord webhooks.
- **Google Play internal testing**
  - Use Gradle + fastlane `supply` (or Play Developer API) to upload AABs to the **internal** and **closed** tracks with version codes from CI.
  - Manage service account JSON securely; track rollout percentages and staged rollouts, and promote builds (internal → closed → production) via API.
  - Automate Play Integrity configuration and upload ProGuard/R8 mappings during the same job.
- **Steam branches**
  - Build depots via SteamPipe in CI (Windows/macOS/Linux as needed); upload using `steamcmd` with partner credentials stored in secrets.
  - Maintain branches: `internal` (dev QA), `beta` (wider testers), `public`; gate patch notes and opt-in passwords appropriately.
  - Hook Discord/Slack notifications on successful depot uploads and track build IDs for rollback.

## SRE / Ops Playbooks
- **Monitoring & observability**
  - Emit RED/USE metrics per service: requests rate, errors, latency; CPU/memory saturation; queue lengths; DB/redis health.
  - Centralize logs with structured logging, request IDs, and PII scrubbing; enable distributed tracing (e.g., OpenTelemetry) across backend and gateway.
  - Dashboards: gameplay success funnel, matchmaking latency, purchase throughput/refunds, auth success, third-party API dependency health.
- **Alerts**
  - Page on SLO/SLA breaches (error rate, p95 latency, auth failures, payment success dips, crash spikes per platform).
  - Distinguish paging vs. ticket-only alerts; include runbook links and recent deploy info in alert annotations.
  - Rate-limit noisy alerts; add canary health checks for new releases.
- **Rollback & release controls**
  - Maintain fast rollbacks: App config flags for feature kills, backend canary deploys with automatic rollback on SLO violation, and Steam branch reversion via previous build ID.
  - Keep hotfix branches and signed release artifacts for re-promotion; document database migration reversibility and data backfill steps.
  - Track release owners, approval steps, and pre/post-deploy checklists in CI.
- **Incident response**
  - Triage process: declare severity, assign incident commander and scribe, open comms channel, capture timeline.
  - Runbooks per failure class: auth outage, payment errors, matchmaking instability, gateway timeouts, crash regression.
  - Post-incident: root-cause analysis, action items with owners/dates, update dashboards/tests/alerts to catch recurrence.
