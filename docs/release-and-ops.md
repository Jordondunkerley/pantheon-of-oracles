# Mobile & Steam Release + Ops Guide

This document summarizes store requirements, deployment automation, and SRE playbooks for Pantheon of Oracles across Apple, Google Play, and Steam. Treat it as a checklist during release prep and incident drills.

## App Store / Play Store / Steam Requirements
- **Privacy & data use**
  - Publish a clear privacy policy URL; enumerate data collection (accounts, telemetry, crash logs) and retention. Map each field to purpose/legal basis in a data inventory.
  - Complete Apple App Privacy Nutrition Labels and Google Data Safety forms; confirm no unexpected third-party data sharing and document any SDK data use (ads/analytics/login).
  - Obtain user consent for analytics/crash reporting and honor deletion requests (GDPR/CCPA where applicable). Provide a “Delete My Account” entry point inside settings that also purges cloud saves where feasible.
  - Maintain DPIA/TRA artifacts for new data flows and renew annually.
- **Age ratings**
  - Complete Apple age-rating questionnaire (violence, user-generated content, gambling). Provide content filters/moderation notes and a user-reporting flow.
  - Configure Google Play Content Rating (ICRA/ESRB/PEGI) and target audience/ads disclosures; verify ad SDKs respect under-18 restrictions when applicable.
  - Steam: set content descriptors and regional ratings where required; verify chat moderation, abuse reporting, and profanity filters.
- **Payments & commerce**
  - Use StoreKit / Google Play Billing for digital goods/subscriptions; expose restore purchases, receipts validation, and subscription management links. Localize price strings and support Family Sharing eligibility review.
  - Steam microtransactions via Steam Inventory Service / Microtransaction APIs; confirm regional pricing, tax/VAT handling, and refund eligibility alignment with Steam policy.
  - Provide account deletion/export pathways and terms of service links within the game; document support SLAs for billing issues.
- **Platform SDKs & compliance**
  - Apple: integrate Xcode/StoreKit, Sign in with Apple if using third-party login, Background Modes review notes, push notification entitlement. Confirm ATS exceptions and reason text in Info.plist.
  - Google: target latest API level, handle scoped storage, Play Integrity API/Device Check for abuse prevention, declare foreground service types, and verify adaptive icon assets.
  - Steamworks: initialize `ISteamClient` early, handle overlay, achievements, cloud saves, rich presence, voice chat, and cross-platform friends if supported. Confirm title is VAC-aware if multiplayer.
- **Crash reporting & analytics**
  - Enable Crashlytics/Sentry/Bugsnag with symbol uploads (dSYMs/ProGuard mapping) and PII scrubbing. Add guardrails to strip chat/user content from breadcrumbs.
  - Instrument gameplay funnels, matchmaking reliability, purchase success, latency metrics, and platform-specific crash rates; avoid device identifiers outside platform policies.
  - Document data export/retention schedules, log redaction for user content, and retention overrides for security investigations.

## Deployment Automation
- **TestFlight (iOS)**
  - CI pipeline: build with Xcode/fastlane `gym`, upload via `pilot` with beta app review notes/screenshots. Example command: `bundle exec fastlane ios beta --env ci`.
  - Automatically increment build numbers, sync signing (match/App Store Connect API keys), and attach release notes from CHANGELOG. Fail the job if screenshots/metadata are missing.
  - Create external/internal tester groups and auto-expire builds after release; notify via Slack/Discord webhooks; tag builds with git commit and feature flags enabled.
- **Google Play internal testing**
  - Use Gradle + fastlane `supply` (or Play Developer API) to upload AABs to the **internal** and **closed** tracks with version codes from CI.
  - Manage service account JSON securely; track rollout percentages and staged rollouts, and promote builds (internal → closed → production) via API. Require human approval before >50% rollout.
  - Automate Play Integrity configuration and upload ProGuard/R8 mappings during the same job. Export the generated `versionCode` and mapping URL to release notes.
- **Steam branches**
  - Build depots via SteamPipe in CI (Windows/macOS/Linux as needed); upload using `steamcmd` with partner credentials stored in secrets.
  - Maintain branches: `internal` (dev QA), `beta` (wider testers), `public`; gate patch notes and opt-in passwords appropriately. Auto-create branch notes from CHANGELOG sections.
  - Hook Discord/Slack notifications on successful depot uploads and track build IDs for rollback. Store `app_build` output artifacts for audit and reversion.

## SRE / Ops Playbooks
- **Monitoring & observability**
  - Emit RED/USE metrics per service: request rate, errors, latency; CPU/memory saturation; queue lengths; DB/redis health. Capture client-side crash rates segmented by platform/branch.
  - Centralize logs with structured logging, request IDs, and PII scrubbing; enable distributed tracing (e.g., OpenTelemetry) across backend and gateway. Sample traces heavier during new releases.
  - Dashboards: gameplay success funnel, matchmaking latency, purchase throughput/refunds, auth success, third-party API dependency health. Include “steam branch vs prod” split and mobile store build numbers in legends.
- **Alerts**
  - Page on SLO/SLA breaches (error rate, p95 latency, auth failures, payment success dips, crash spikes per platform). Add Steam depot upload failures as ticket alerts.
  - Distinguish paging vs. ticket-only alerts; include runbook links and recent deploy info in alert annotations. Add contact rotation for mobile release owners.
  - Rate-limit noisy alerts; add canary health checks for new releases. Include synthetic purchase and login probes.
- **Rollback & release controls**
  - Maintain fast rollbacks: App config flags for feature kills, backend canary deploys with automatic rollback on SLO violation, and Steam branch reversion via previous build ID.
  - Keep hotfix branches and signed release artifacts for re-promotion; document database migration reversibility and data backfill steps. Snapshot feature flag states before rollout.
  - Track release owners, approval steps, and pre/post-deploy checklists in CI. Require dual approval for payments changes.
- **Incident response**
  - Triage process: declare severity, assign incident commander and scribe, open comms channel, capture timeline. Maintain on-call rotation per platform (iOS/Android/Steam/backend).
  - Runbooks per failure class: auth outage, payment errors, matchmaking instability, gateway timeouts, crash regression. Each runbook must list log/trace queries and rollback knobs.
  - Post-incident: root-cause analysis, action items with owners/dates, update dashboards/tests/alerts to catch recurrence. Close the loop with updated release checklists.
