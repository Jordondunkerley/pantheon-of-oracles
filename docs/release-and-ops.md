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

### Security, compliance, and legal readiness
- **Security reviews**
  - Maintain threat models for mobile clients, backend services, and Steam integration; refresh when adding new authentication flows or cross-play capabilities.
  - Run SAST/DAST and mobile binary hardening checks (jailbreak/root detection as policy allows, tamper detection, anti-debug toggles). Track findings to closure with ownership.
  - Generate SBOMs for each platform build; scan dependencies for licenses/CVEs and record overrides with legal sign-off.
- **Privacy and data minimization**
  - Re-verify data inventory against telemetry and crash events after new features; ensure payloads minimize user identifiers and strip PII from logs.
  - Validate consent UX language per locale and store platform rules; confirm withdrawal/deletion flows are reachable from in-game settings.
  - Review third-party SDK contracts for data use/sharing; keep an approval register with expiry/renewal dates and audit trails.
- **Legal & policy**
  - Maintain export control statements for encryption, country sanctions blocks, and age-gating for restricted regions. Document if matchmaking or chat is disabled by region.
  - Keep ToS/Privacy Policy diffs reviewed by counsel prior to each store submission; update URLs in store metadata when links change.
  - Document COPPA/child-data exclusions when the audience includes minors; ensure ad SDKs and analytics are configured accordingly.

### Submission artifacts & checklist
- Screenshots and trailers per platform locale (iPhone/iPad sizes, Android phone/tablet, Steam capsules/banners). Include updated age ratings, keywords, and localized descriptions.
- App icons, feature graphics, and store listing disclosures (ads, IAPs, data safety summaries). Verify promotional text matches current feature set.
- Entitlement/config notes for review teams: Sign in with Apple justification, push notification purpose, background modes, health data (if any), and encryption export classifications (USA EAR/ITAR screening questions).
- Accessibility statements and test evidence (VoiceOver/TalkBack, color contrast, controller support). Attach external links for support and privacy policy.
- QA evidence bundle: test matrix by device/OS, network/latency cases, purchase/restoration proofs, save migration, cross-play/cross-progression validation, and crash-free rate from the latest RC build.

### Localization, accessibility, and content operations
- **Localization**
  - Maintain locale coverage targets (e.g., EN, ES, FR, DE, JA, KO, ZH) and translation memory/glossaries for consistency. Require context screenshots for translators and a style guide per market.
  - Run pseudo-localization and string-length overflows in CI; flag hard-coded strings and RTL/LTR layout issues. Capture store listing localization updates alongside in-game text to avoid mismatched claims.
  - Validate legal/age-rating phrasing per locale (e.g., loot box disclosures) and regional holiday/event references. Ensure audio subtitle/captions parity where voice lines exist.
- **Accessibility**
  - Ship per-platform accessibility checklist: font scaling, colorblind palettes, haptic/rumble toggles, text-to-speech support, remappable controls, and caption timing with speaker labels.
  - Add automated contrast checks for UI themes and manual verification for screen reader focus order. Document exceptions with rationale and mitigations.
  - Provide in-game tutorials covering accessibility options; surface them in first-time user experience and settings.
- **Content operations & UGC**
  - Define moderation policy for chat/UGC: profanity filters, image scanning (if applicable), and escalation path for abuse. Log moderation actions with auditor-friendly fields (timestamp, moderator, action, reason).
  - Add parental controls and session limits where required by regional policy; expose reporting/blocking flows on every screen with social features.
  - Run weekly audits of reported content queues and appeal handling SLAs; capture metrics in dashboards and release go/no-go.

### Build provenance, keys, and artifacts
- Sign iOS/Android artifacts with CI-managed identities; rotate App Store Connect keys, Play service accounts, and Steam partner credentials on a schedule and after staff turnover.
- Keep notarization/notary tool outputs, release notes, and build manifests as immutable artifacts linked to git SHAs. Store SBOMs and vulnerability scan reports alongside builds.
- Enforce reproducible builds where possible (locked dependency versions, deterministic asset pipelines); flag differences in binary hashes between local and CI outputs.
- Maintain a secrets inventory (API keys, signing certs, webhook tokens) with owners, rotation cadence, and break-glass retrieval steps.

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

### Release readiness gates (applies to all platforms)
- Pre-flight checks enforced in CI: static analysis (lint/format), unit/UI smoke tests per platform, bundle validation (`altool`/`notarytool` for macOS builds if applicable), and dependency license scanning.
- Manual sign-off steps: product owner approves release notes and screenshots, security reviews OAuth scopes/SDK permissions, and legal reviews privacy/commerce disclosures for changes.
- Go/no-go meeting template: status of blockers, crash/ANR rates from latest build, SLO trendlines, support ticket volume, and rollout plan with staged percentages.
- Release calendar: avoid peak traffic windows; freeze windows documented with approvers. Include back-out window and engineer on-duty for hotfixes.

### Performance, compatibility, and resilience validation
- **Device/OS coverage**
  - Maintain an explicit test matrix per platform: iOS (latest -2 major, low-memory devices), Android (API level latest -3, Play integrity, OEM overlays), Steam (Windows/Linux/macOS GPU/driver spread, Steam Deck if supported).
  - Run real-device smoke tests for cold-start time, login, matchmaking, purchases, and first-session tutorial; record median/p95 metrics by device tier and app version.
  - Track platform-specific ANR/crash regressions; gate releases on crash-free rates and session start success for each store build number/Steam branch.
- **Network and edge-case resilience**
  - Exercise offline/poor-network behaviors (packet loss, latency injection) for login, purchases, and save sync; ensure retries and user-facing messaging are consistent across platforms.
  - Validate timeouts, backoffs, and idempotent purchase receipts; confirm graceful handling of expired tokens and revoked entitlements.
  - Soak-test backend services with long-lived sessions and reconnect storms; capture memory/FD leaks and GC pressure under load.
- **Graphics/performance**
  - Collect FPS/frametime histograms per graphics preset and thermal throttling conditions; ensure defaults auto-tune based on device tiers and Steam Deck profiles.
  - Verify shader pre-warm and asset streaming to avoid frame spikes on first load; test background/foreground transitions for mobile platform policies.
  - Capture GPU/CPU budgets for new features; require variance analysis before enabling on lower-tier devices. Record mitigations (reduced effects, capped crowd sizes).

### Release communications and support operations
- Publish release comms templates (patch notes, downtime announcements) with localized variants; include impacted platforms/branches and expected rollout schedule.
- Align customer support shifts with rollout windows; confirm macros and diagnostics are updated for the new build (log collection steps, device info prompts, refund guidance).
- Define beta/early-access cohort messaging for TestFlight, Play internal testing, and Steam `beta` branches; include clear instructions to switch branches and submit feedback.
- Track open incidents and known issues in a single changelog section; link to mitigations and expected fix versions before promoting to production/public branches.

### Live operations & capacity planning
- **Capacity readiness**
  - Maintain load test profiles per platform and update target concurrency for planned marketing beats; store baselines and deltas in dashboards. Test Steam branch toggles and mobile feature-flag ramps under load.
  - Verify autoscaling policies and rate limits for external dependencies (payments, identity, chat). Stage DB/index migrations with shadow reads and backfill plans before marketing pushes.
  - Keep RPO/RTO targets documented; ensure backups are tested restores, not just snapshots. Track save-data integrity across cross-progression paths.
- **Customer support & trust/safety**
  - Publish support contact paths in-game and on store listings; include billing dispute guidance. Triage macros for frequent issues (purchase fails, account lockout, crash on launch) linked to runbooks.
  - Maintain fraud/abuse detection signals (chargeback spikes, suspicious inventory changes) and pair with rate-limit/flag actions. Share weekly summaries with release owners.
  - Track sentiment and crash/regression feedback from reviews/beta channels; feed into release quality gates and incident retros.
- **Save integrity & migration safety**
  - Catalog save schemas per platform and version; require migration scripts with idempotency and rollback paths for corrupted rows.
  - Validate cross-progression scenarios (mobile ↔ Steam) in CI with fixtures covering divergent schema versions and partial sync failures.
  - Run checksum/manifest validation on cloud saves; block promotion if corruption or deserialization spikes appear in dashboards after a rollout.

### Post-release evaluations and hygiene
- Run 24h/72h/7d post-release reviews capturing crash-free rate trends, purchase funnel health, matchmaking KPIs, and support ticket deltas by platform/branch.
- Maintain a “rollback/forward” decision record per incident with the build ID, flags toggled, and customer impact; close the loop with tests and alerts updated.
- Audit feature flag usage monthly; delete stale flags, document dependencies, and ensure defaults are safe before removing guardrails.
- Refresh dashboards/alerts ownership as teams change; validate synthetic probes for purchase/login still align with current flows.

### Multiplayer, social, and anti-cheat readiness
- **Matchmaking and session stability**
  - Define target match times, fairness constraints, and backfill rules per playlist; test degradations (reduced MMR strictness) for low-population regions.
  - Verify reconnect flows preserve party and voice state across mobile/Steam and handle host migration where applicable.
  - Capture packet loss/latency distributions by region and platform; gate rollouts if spikes correlate to new builds or backend deployments.
- **Social and communications safety**
  - Ensure reporting/blocking works from chat, voice, and friend lists; log moderation events with user IDs, evidence hashes, and responder actions.
  - Provide parental controls for chat/voice; confirm push-to-talk defaults and profanity filters respect age/region policies.
  - Document escalation criteria for harassment/cheating reports and how to preserve evidence while respecting privacy retention rules.
- **Cheat/tamper resilience**
  - Validate anti-cheat integrations (e.g., VAC/EAC/BE) per platform build; confirm debuggers/cheat tools are blocked where policy allows and note any platform review caveats.
  - Monitor suspicious patterns (aim variance outliers, speed hacks, inventory duplication) with alerts tied to ban workflows and customer support scripts.
  - Keep a rollback-and-ban playbook that outlines communication templates, appeal handling, and flag-only vs. actioned enforcement levels.

### Experimentation, release toggles, and rollout control
- Maintain a registry of feature flags and experiments with owners, guardrails, and kill-switch behaviors; require defaults that fail safe when configs are missing.
- Enforce experiment ethics and privacy: anonymize cohorts, cap exposure, and publish stop conditions. Document how user consent is handled for analytics-heavy trials.
- For staged rollouts, record exposure percentages by platform/branch and automate auto-pause on regression thresholds (crash rate, purchase drop, matchmaking failures).
- Add runbooks for rapidly disabling experiments on specific platforms (e.g., Steam only) without redeploying, and verify the behavior during playtests.

### Platform hardware and peripheral readiness
- **Controllers and input**
  - Validate MFi, DualShock/DualSense, Xbox, and Steam Input mappings; ship default layouts and in-game remapping with per-platform glyphs. Confirm haptics, adaptive triggers, and gyro when enabled.
  - Ensure accessibility modes remain usable with controllers (e.g., menu navigation, hold vs. toggle interactions) and that on-screen prompts match connected devices.
- **Device matrices and performance tiers**
  - Maintain tiered device lists (low/medium/high) with FPS/thermal targets and fallback graphics presets; document feature gates for low-memory or older GPUs.
  - Test background/foreground transitions, battery/performance modes, and windowed/fullscreen behavior (Steam Deck/Big Picture) for stability and UI scaling.
- **Network and edge scenarios**
  - Exercise captive portals, IPv6, NAT types, and high-latency/packet-loss profiles. Capture metrics for lobby connectivity, voice quality, and inventory synchronization under these conditions.
  - Validate offline/airplane-mode behaviors (e.g., save queues, entitlement caching) with clear messaging and graceful retry policies per platform.

### Chaos, disaster recovery, and state restoration
- Run periodic chaos drills targeting backend dependencies (DB, cache, payments, identity, chat) with clear rollback and failover steps; record expected vs. actual blast radius.
- Keep disaster recovery runbooks with RPO/RTO per service, secondary region activation steps, DNS/traffic-shift procedures, and data integrity validation after failover.
- Document save-state and entitlement restoration flows after outages; ensure partial writes or duplicated purchases can be reconciled with deterministic scripts and customer support macros.
- Include tabletop exercises for "store outage during release" and "Steam branch promotion failure" with decision trees for pausing rollouts and communicating to players.

### Data governance and observability quality
- Maintain data classification tags across logs, events, and metrics; enforce schema validation in telemetry pipelines and reject PII in disallowed channels.
- Track dashboard/alert ownership with change control: require PR reviews for metric definition edits, alert threshold changes, and new PII-bearing dimensions.
- Audit analytics/crash pipelines quarterly for drop rates, sampling changes, and SDK version drift; publish known caveats alongside dashboards to reduce misreads.
- Align retention and deletion policies across client telemetry, chat logs, and support tickets; verify automation for redaction and data subject requests.

### Store review resilience and rejection handling
- Maintain a “store response kit” with pre-written explanations for permissions (microphone, location, Bluetooth), account deletion, and payment flows.
- Track review submission timestamps, reviewer notes, and quick triage owners; commit to 24h fixes for metadata-only rejections and pre-approved code patches for common blockers.
- Validate entitlement/config toggles that can be adjusted without resubmission (e.g., TestFlight review notes, Steam branch descriptions) and document when a new build is mandatory.

### Operational training and preparedness
- Maintain onboarding guides for release captains, on-call responders, and store submission owners; include tool access, credential retrieval, and mock drills.
- Schedule quarterly joint exercises between release engineering, QA, and customer support to practice rollback/feature-flag kill flows and Steam branch reversions.
- Track runbook coverage and freshness with an inventory (scenario → owner → last review date); fail readiness checks if critical paths lack tested runbooks.

### Audit trails, compliance evidence, and approvals
- **Evidence gathering**
  - Store immutable artifacts for each release: CI logs, build provenance, SBOMs, vulnerability scans, notarization outputs, store listing diffs, and reviewer notes.
  - Keep approvals with timestamps and owners for security, legal, and product sign-offs; include rationale for risk acceptances and temporary exceptions.
  - Archive incident timelines, rollback decisions, and postmortems with links to the exact build IDs and feature flag states at time of impact.
- **Change management**
  - Map releases to tickets/change requests with audit-friendly summaries; ensure on-call is aware of the change window and blast radius.
  - Track data residency controls (regional shards, CDN/geofencing) and encryption export declarations; keep a register of restricted regions and mitigation steps.
  - Run quarterly reviews of access to signing keys, store accounts, and CI secrets; verify least-privilege and session logging are enforced.

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
