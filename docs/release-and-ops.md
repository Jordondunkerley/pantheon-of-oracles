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

### Patch delivery, install integrity, and update experience
- **Patch sizing and distribution**
  - Track patch size budgets by platform and device tier; enforce delta/patch compression (e.g., Android App Bundles splits, Steam depot diffs) and validate CDN edge cache hits before rollout.
  - Verify background download/resume behaviors on unstable networks; measure download success rate and time-to-play metrics across geographies. Add in-app messaging for large downloads and low-storage cases.
  - Maintain fallback flows for failed updates (retry with smaller chunks, redirect to Wi‑Fi) and document expected user prompts per platform review requirements.
- **Integrity and compatibility**
  - Validate app/patch signatures (App Store/Play signing, Steam depots) and enforce build ID compatibility between client, DLC, and backend schema versions. Detect mismatched depots/branches and block login gracefully.
  - Run install/uninstall/reinstall cycles across device tiers, including encrypted storage and managed device profiles (MDM/EMM). Confirm cached assets and saves survive OS updates where supported.
- **Update UX and compliance**
  - Ensure update prompts respect platform UX rules (no forced app restarts without warning, support deferred updates where available). Provide localized release notes and highlight privacy/permission changes.
  - For mobile, test in-app updates/redirects from store pages; for Steam, verify auto-updates vs. optional branches and pre-load windows for major releases.

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

### Third-party dependency resilience and vendor readiness
- **Monitoring and contracts**
  - Track status pages and SLAs for payment providers, auth, chat/voice, CDN, and analytics. Configure alert routing to include vendor escalation contacts.
  - Maintain a contract register with usage caps, overage pricing, and regional restrictions; pre-approve failover vendors for critical paths.
- **Failover patterns**
  - Build read-through caching or circuit breakers for dependency outages; define safe degradation modes (e.g., disable cosmetics store, queue purchases) with clear UX copy.
  - Validate retry/backoff per dependency to avoid thundering herds; document how mobile clients surface partial failures vs. blocking errors.
- **Compliance and data residency**
  - Record where third-party data is stored/processed; ensure SDKs respect regional data boundaries and include them in data maps.
  - Run annual vendor security reviews and confirm breach notification timelines align with our incident response SLAs.

### Store review resilience and rejection handling
- Maintain a “store response kit” with pre-written explanations for permissions (microphone, location, Bluetooth), account deletion, and payment flows.
- Track review submission timestamps, reviewer notes, and quick triage owners; commit to 24h fixes for metadata-only rejections and pre-approved code patches for common blockers.
- Validate entitlement/config toggles that can be adjusted without resubmission (e.g., TestFlight review notes, Steam branch descriptions) and document when a new build is mandatory.

### Engineering quality gates and lab management
- **CI quality bars**
  - Enforce unit/integration/E2E coverage thresholds per platform; fail builds on flaky-test detection and require owners to quarantine and fix before promotion.
  - Include static analysis (SwiftLint/Detekt/ESLint), asset size checks, and shader/packfile validation in preflight jobs; publish artifacts to dashboards for trend tracking.
  - Require reproducible build stamps (git SHA, feature flags, device tier) in app settings/about screens for rapid incident correlation.
- **Device labs and playtests**
  - Maintain a rotating device lab matrix (top OEMs, OS N-2, low-memory tiers, Steam Deck) with automated scheduling for nightly runs; record failures with video/screenshot capture.
  - Run structured playtests before submissions with scripted flows (first-time user, restore purchases, cross-progression, offline mode) and attach findings to release tickets.
  - Validate controller/peripheral updates in lab runs after firmware/driver updates; keep a registry of known-good versions for reproducibility.

### Secrets, config, and environment hygiene
- Separate production, staging, and test configs with strict access controls; block production credential use in lower environments via CI policies.
- Use short-lived tokens and hardware-backed key storage where possible (Secure Enclave/Keystore/keychain); rotate store/API credentials on a schedule with audit trails.
- Maintain configuration schemas with defaults and validation in CI; add config drift detection between environments (e.g., feature flags, payment gateways, telemetry endpoints).
- Document break-glass access with approval/expiration, and log all accesses to signing keys, store accounts, and admin consoles.

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

### Capacity planning, scaling, and cost controls
- **Traffic modeling**
  - Maintain per-platform DAU/CCU forecasts with peak factors for events and store featuring; test backend autoscaling thresholds against these peaks with load tests tied to the latest client build.
  - Track Steam branch promotions separately to capture opt-in surges; validate CDN/cache hit rates under patch-day load for mobile and Steam depots.
- **Performance budgets and rate limits**
  - Set API-level rate limits by auth scope/device type; ensure client-side retries and backoff are tuned to avoid stampedes during outages.
  - Define shader/asset budgets per tier (mobile low/medium/high, Steam Deck) and enforce them in CI to prevent creeping load times and patch sizes.
- **Cost governance**
  - Monitor cloud spend by environment and platform; tag resources by release/branch. Add alerts for CDN egress and third-party SDK overages during staged rollouts.
  - Capture per-feature flag and experiment cost impacts (e.g., extra telemetry, matchmaking routes) and include them in go/no-go reviews.

### Customer support readiness and player communications
- **Support playbooks**
  - Provide macros for store-specific billing issues (Apple/Google refunds, Steam wallet) and for account deletion/export requests. Include entitlement reconciliation steps after rollbacks.
  - Keep outage/update banners templated for mobile and Steam; localize status messages and link to known-issues docs. Ensure in-game messaging can be targeted by platform/build.
- **Community and trust/safety**
  - Pre-stage moderation staffing for events/releases; define escalation to legal/PR for abuse spikes. Log enforcement actions with evidence retention aligned to privacy policies.
  - Track social sentiment dashboards (Discord/Steam forums/Reddit) and flag spikes in crash or payment complaints; feed back into incident triage.
- **Feedback loops**
  - Maintain a pipeline for in-game feedback/ratings prompts that respects platform rules; A/B test timing to avoid review-bombing after incidents.
  - Aggregate support tickets by build/branch and root cause to inform post-release reviews and store metadata updates.

### Live event operations and seasonal content
- **Event gating and configs**
  - Store event configs behind server-driven toggles with explicit start/end times and rollback states; verify entitlement grants and drop tables per platform.
  - Validate time zone handling and DST changes for event windows; ensure countdown timers match server time and handle offline/paused states gracefully.
- **Load and matchmaking considerations**
  - Run stress tests for event-specific modes or cosmetics drops; confirm matchmaking rules and rewards cannot be bypassed via older builds or branch hopping.
  - Pre-warm caches/CDN for new assets; monitor patch size regressions and download completion rates by region/device tier.
- **Post-event hygiene**
  - Clean up expired flags/configs, revoke temporary permissions, and archive event telemetry for re-use. Document any post-event migrations or economy adjustments.

### Game systems readiness and balance operations
- **Core loop validation**
  - Verify progression loops (quests, boss gates, crafting, PvP unlocks) are completable without blockers on all platforms and accounts types; script smoke tests in CI for mainline quest paths.
  - Confirm tutorial/FTUE gating is resilient to reconnects, crashes, or device switches; ensure save checkpoints and rewards are idempotent.
- **Economy and monetization integrity**
  - Model currency faucets/sinks and inflation controls; set KPIs (daily/weekly earnings, spend velocity, retention-linked bonuses) and alert on anomalies by platform/branch.
  - Validate price ladders, regional pricing, bundles, and subscription perks against design docs and store policies; include safeguards for accidental over-discounting or stackable perks.
  - Add exploit detection for dupe loops, time-travel (clock changes), and offline accrual abuse. Gate economy-impacting configs behind server flags with rollback.
- **Content cadence and pipelines**
  - Maintain a content release calendar (quests, cosmetics, balance patches) with review/QA checkpoints; track asset dependencies and localization deadlines.
  - Require authoring/playtest guidelines for new content types (boss mechanics, puzzles, PvP maps) with acceptance criteria and failure states captured in runbooks.
- **Balance change execution**
  - Ship balance changes via config flags with staged rollout and experiment support; include automatic reversion if KPI regressions exceed thresholds (win rate deltas, abandon rates, queue times).
  - Publish balance rationale and patch notes templates for transparency; coordinate with CS/Community for expectation management and appeal handling.
  - Keep canonical balance baselines (e.g., target TTK, DPS ranges, heal throughput) in version control; require diffs reviewed by design and analytics before release.

### Player lifecycle, retention, and fairness safeguards
- **Retention systems**
  - Validate daily/weekly challenges, streaks, and battle passes for edge cases (time zones, skips, partial progress); ensure expired rewards are revoked or converted per design.
  - Instrument churn/return funnels and cohort tagging by platform/branch to inform release go/no-go when retention-sensitive changes ship.
- **Match fairness and ranking**
  - Document ranking/MMR systems (decay rules, placement matches, party modifiers) with simulation evidence; alert on skew by region/platform.
  - Ensure cross-play fairness controls (input-based matchmaking, aim assist toggles) are configurable per platform and surfaced in settings.
- **Player-facing trust signals**
  - Maintain transparent policy pages for bans/suspensions, dispute steps, and data export; keep in-game links updated with store metadata.
  - Provide on-device privacy controls for telemetry categories and communication preferences; localize consent text and ensure accessibility compliance.

### Game systems design: combat, classes, world state
- **Combat feel and readability**
  - Lock target animation budgets (windup, recovery, hitstop) and VFX readability standards to keep encounters legible on mobile screens and Steam Deck. Include color-blind-safe damage/healing cues and camera shake budgets.
  - Define invulnerability/armor rules, stagger/poise thresholds, and crowd-control diminishing returns; expose these in debug HUDs for playtesters and capture telemetry on status effect uptime.
  - Validate controller and touch input parity for combos, dodges, and ability wheel usage; record per-input-device failure rates and adjust aim assist curves by platform.
- **Classes, archetypes, and roles**
  - Maintain a roster sheet with class identities (e.g., Vanguard, Mystic, Ranger) that maps to party roles (tank, support, DPS) and outlines unique traversal/utility hooks (zipline anchors, aura beacons). Keep talent trees under a point budget to avoid infinite stacking.
  - Document class ability cooldown formulas, resource generation, and ultimates; track patch history per ability with target DPS/HPS envelopes to keep parity across platforms and controller layouts.
  - Provide onboarding quests per archetype to teach role expectations (aggro control, cleanse timing, burst windows) with success/failure analytics by platform and input method.
- **World state and persistence**
  - Define shard rules (regional shards vs. megaserver) and cross-play visibility limits (platform-only chats, input-based PvP pools). Record decay rules for housing/guild territories to prevent abandoned ownership.
  - Track dynamic world events (sieges, anomalies, rotating vendors) with schedules, spawn conditions, and rollback toggles. Ensure state replication tolerates packet loss and offers reconciliation for mobile reconnects.
  - Maintain lore canon and questline dependencies in a graph to prevent soft-locks; include skip/recap options for returning players and archive cutscene triggers in telemetry.
- **Enemy AI and encounter scripting**
  - Ship AI behavior trees with tunable aggression, leashing, and focus-fire rules; gate high-compute behaviors on mobile low-tier devices while keeping boss mechanics intact. Capture perf metrics for navmesh, pathfinding, and perception loops.
  - Provide encounter design briefs with tells, phase transitions, and safe zones; require fail-safe handling for interrupted scripts (disconnects, host migration, Steam overlay focus loss).
  - Build a spawn budget per arena with concurrency caps to avoid frame drops and network congestion. Include anti-kite and anti-cheese checks (reset timers, tether mechanics) and document overrides used in events.
- **Exploration, traversal, and puzzles**
  - Map traversal verbs (climb, glide, mantle, grappling) to stamina/charge systems with fallbacks for touch vs. controller inputs. Validate collision and ledge detection on device matrices.
  - Catalog puzzle templates (sigils, pressure plates, rhythm, timing) with accessibility variants and hint systems. Include anti-sequence-break safeguards and reset logic after disconnects.
  - Ensure minimap/world map coherence with fog-of-war states, quest pins, and co-op visibility. Add offline-ready breadcrumbing for mobile with cached tiles.
- **Crafting, loot, and progression economy**
  - Balance loot tables with pity timers, duplicate protection, and platform-specific drop-rate disclosures where required. Keep deterministic sources for progression-critical items (boss keys, class unlocks).
  - Define crafting trees with material sinks and time gates; include queue systems that survive app suspends and Steam offline mode. Track recipe unlock sources to avoid deadlocks.
  - Require audit trails for loot seed generation and randomness sources; document anti-abuse protections for re-rolling via clock changes or branch hopping.
- **Social structures and cooperative play**
  - Implement guild/clan frameworks with rank/permission matrices, contribution logs, and inactivity pruning; include moderation hooks for names/emblems.
  - Design co-op roles (healer/support benefits, link mechanics, combo finishers) with clear UI prompts and failure messaging. Verify voice/text callouts have localized quick-chat equivalents.
  - Provide shared bases or hubs with instancing rules, decoration budgets, and cross-platform persistence. Add visitor permissions and social privacy controls.
- **Competitive modes and anti-toxicity**
  - Define PvP modes (duels, arenas, battlegrounds) with MMR bands, map rotations, and seasonal reset rules. Add anti-smurf and anti-boosting checks (party MMR caps, decay, queue restrictions).
  - Calibrate matchmaking inputs for input method, latency, and platform to avoid unfair pairings; log disputes and appeal outcomes to tune enforcement.
  - Publish a seasonal integrity report (ban counts, exploit fixes, leaderboard adjustments) to maintain player trust; archive evidence for contested bans.
- **Live tuning and telemetry**
  - Add per-ability/per-encounter telemetry (hit rate, dodge success, deaths by mechanic) with platform splits to guide tuning. Require patch notes to cite telemetry findings.
  - Stage live-tuning controls for drop rates, boss health, and spawn density with audit logs and rollback toggles; test in sandboxes before exposing to production branches.
  - Set experiment guardrails for game systems (new class mechanics, traversal buffs) with capped exposure and automatic rollback on fairness or stability regressions.

### Narrative, quests, and content authoring
- **Quest structure and branching**
  - Maintain a quest graph with dependencies, failover steps, and soft-lock detection; include recaps/skip logic for returning players or platform switches.
  - Track branching choices with state reconciliation rules for cross-progression; ensure morality/affinity systems do not desync between Steam and mobile saves.
  - Document reward tables and pacing per arc (main, side, faction) with telemetry for completion/drop-off points; add guardrails for time-limited quests during events.
- **Dialogue and cinematics**
  - Provide localization-aware dialogue tools with lip-sync hooks, portrait/emote states, and VO/subtitle parity; validate accessibility (font scaling, timing, speaker labels).
  - Capture conversation interruption rules (combat start, disconnects, overlays) and resume points; ensure skip/fast-forward preserves quest flags correctly.
  - Define cinematic triggers, camera rails, and safe zones for controller/touch input; budget VFX/scripting to maintain FPS on low-tier devices and Steam Deck.

### Companions, mounts, and AI allies
- **Companion behaviors**
  - Ship role-driven behavior packs (tank/support/DPS utility) with leash distances, targeting priorities, and crowd-control avoidance; expose simple commands (stay/attack/focus/heal).
  - Record companion contribution telemetry (damage, interrupts, buffs) and cap automation to avoid trivializing encounters; provide sandbox flags for rapid tuning.
  - Validate pathing and teleport fallback for narrow spaces, elevators, and co-op puzzles; ensure companions respect stealth states and do not break puzzle triggers.
- **Mounts and traversal allies**
  - Define mount movement physics (acceleration, braking, turn radius) and collision with dynamic objects; handle dismount rules for combat zones, interiors, and cinematic triggers.
  - Keep stamina/sprint/boost rules consistent across platforms; verify camera transitions and FOV shifts are comfortable on mobile and docked/desktop modes.
  - Add fail-safes for mount summoning restrictions (water, cramped areas) and recovery when the mount is stuck or the player disconnects.

### Housing, hubs, and social spaces
- **Player housing and bases**
  - Establish instancing rules (personal vs. shared), decoration budgets, and storage limits per platform; include save integrity checks for layout persistence.
  - Provide permission matrices for visitors and guildmates (build, decorate, inspect storage) with audit logs of changes; support rollback of griefing or accidental edits.
  - Validate placement rules for functional objects (crafting stations, respawn points, fast travel) and ensure they remain usable after patches and schema migrations.
- **Shared hubs and vendors**
  - Define hub service availability (crafting, banking, trading, matchmaking terminals) with degradation modes during outages; expose offline-ready kiosks for mobile where possible.
  - Manage shard/instance population caps, AFK handling, and anti-spam measures for vendors/market boards; localize signage and NPC barks.
  - Track foot-traffic telemetry and adjust spawn density/VFX budgets in hubs to prevent FPS drops on low-tier devices.

### UI/UX, camera, and control systems
- **HUD and readability**
  - Maintain HUD layering rules (critical alerts, combat text, quest pins) with safe zones per device aspect ratio; allow scaling presets and colorblind-friendly palettes.
  - Validate input device detection and glyph swaps (touch, keyboard/mouse, controller); expose remapping and aim-assist tuning with per-platform defaults.
  - Require pause/resume resilience across overlays (Steam, notifications) and backgrounding on mobile; persist mid-combat states safely where policy allows.
- **Camera and presentation**
  - Set camera constraints (collision, pitch/yaw limits, FOV ranges) per mode (combat, traversal, cinematics); provide motion blur, camera shake, and lens flare toggles with sensible defaults.
  - Ensure lock-on/target cycling is legible on mobile and controller; prevent camera occlusion in tight spaces with automatic offsets and transparency masks.
  - Include photo mode and replay features behind performance guards; scrub PII and chat UI from captures by default.

### Audio, music, and haptics
- **Mixing and accessibility**
  - Ship dynamic mix rules (ducking for VO, sidechaining UI) with platform-aware output levels; include sliders for VO/SFX/Music/Ambience and presets for accessibility needs.
  - Validate subtitle timing, speaker labeling, and localization line breaks; ensure VO/cinematic desync alerts are part of CI checks.
  - Add audio device hot-swap handling (Bluetooth, USB) and default fallbacks; respect system mute/vibrate policies on mobile and controller rumble toggles on Steam Deck.
- **Haptics and feedback**
  - Map haptic events to combat states (parry, crits, low health) and traversal beats (landings, grapples) with adjustable intensity; disable when accessibility requires.
  - Support platform-specific features (DualSense adaptive triggers/gyro) with degradation paths on unsupported devices; document gameplay advantage boundaries for fairness.
  - Capture telemetry on haptic opt-outs and device failures to tune defaults; include QA routines for firmware/driver updates.

### Worldbuilding, biomes, and level operations
- **Environment topology and traversal**
  - Maintain biome performance budgets (foliage density, weather VFX, physics props) and validate pathing for companions, mounts, and AI across mobile and Steam Deck tiers.
  - Document traversal aids (grapples, climbing, gliding) with stamina/fall-damage rules; ensure camera and control schemes remain readable in vertical spaces and tight interiors.
  - Capture collision/navmesh diffs per patch to prevent soft locks; add automated probes for jump gaps, ladders, elevators, and destructible bridges.
- **Lighting, weather, and readability**
  - Set lighting profiles per platform tier; verify exposure, HDR toggle behavior, and night-vision/flashlight fallbacks. Require color-contrast checks during day/night cycles.
  - Budget dynamic weather effects (rain, snow, sandstorms) with LOD swaps and particle count caps; ensure soundscape/haptics degrade gracefully on low tiers.
  - Validate mission-critical signage, quest markers, and puzzle glyphs remain legible during weather or VFX-heavy encounters; add photo mode exclusions to prevent puzzle bypass.
- **Secrets, collectibles, and respawns**
  - Track collectible spawn tables, rarity, and reset rules; ensure save integrity for partial pickups and cross-progression reconciliation.
  - Add anti-exploit checks for farm loops (respawn timers, instancing abuse) and relocate collectibles when collision/navmesh updates occur.
  - Publish level-change runbooks covering portal/fast-travel safety, loading bounds, and fallback spawns when a scene fails to stream.

### Bosses, encounters, and combat pacing
- **Encounter design and telegraphs**
  - Standardize telegraph readability across input types with clear VFX/audio/haptic cues; provide configurable colorblind palettes and text callouts for lethal mechanics.
  - Validate enrage/timer rules, add fail-safes for spawn blockers, and ensure phase transitions survive disconnects or platform suspend/resume.
  - Maintain boss arena budgets (projectiles, AI counts, particle systems) with per-tier caps; profile worst-case phases on low-end devices and Steam Deck.
- **Co-op roles and revives**
  - Define revive rules (charges, timers, proximity) and ensure UI communicates status across platforms; test edge cases like disconnect mid-revive or platform overlay interruptions.
  - Provide encounter-specific co-op roles or buffs with stack limits to prevent trivialization; log contribution metrics to tune support/healer effectiveness.
  - Add scaling rules for party size and MMR; ensure solo/duo/trio modes receive tuned health/damage and loot tables without enabling power-leveling exploits.
- **Loot, rewards, and pity systems**
  - Document loot tables per encounter difficulty; include bad-luck protection/pity timers where applicable and expose drop-rate transparency per regional policy.
  - Gate chase items behind anti-duplication checks, currency caps, and bind rules; include rollback-safe grant scripts for contested drops or server crashes.
  - Add telemetry for acquisition funnels (attempts-to-drop, abandon after wipe) and wire alerts for regressions after tuning changes.

### Crafting, gathering, and trade economy
- **Crafting pipelines**
  - Define recipes, success modifiers, and quality tiers; ensure deterministic inputs are logged for rollback and economy audits. Validate crafting queues survive disconnects and platform suspends.
  - Enforce material sources and sinks (deconstruction, repair costs) with server-side checks to prevent dupes and time-travel exploits.
  - Add tutorial coverage for crafting/unlocking stations; verify accessibility of UI for touch and controller, including drag/drop alternatives.
- **Gathering and world resources**
  - Track node spawn rules, depletion timers, and competition caps; prevent griefing via spawn blocking or physics abuse. Ensure respawn pacing respects economy targets.
  - Include anti-bot signals (path regularity, session length, input variance) and experiment with rate limits/soft locks for suspicious farming patterns.
  - Validate cross-progression resource counts and reconcile conflicts with authoritative server snapshots; add support runbooks for missing-resource tickets.
- **Trading and player economy**
  - Establish trading channels (direct trade, market boards, auction houses) with fee structures, min/max price bounds, and anti-RMT instrumentation.
  - Require receipt logs and dispute-friendly audit trails for trades; implement cooldowns and account age restrictions to reduce fraud.
  - Monitor velocity and price indices for rare items; trigger circuit breakers or listing freezes on suspected dupe or price-manipulation events.

### Guilds, alliances, and social governance
- **Formation and roles**
  - Define guild creation costs, membership caps, and role permissions (invite/kick, bank withdraw, event scheduling). Include audit logs for sensitive actions and rollback playbooks.
  - Support cross-platform invites and chat with moderation hooks; ensure ban/mute actions propagate consistently across Steam and mobile clients.
  - Validate guild progression (levels, perks, research trees) with clear sinks and throttles to avoid runaway buffs; record perk changes with timestamps for rollback.
- **Shared resources and events**
  - Document guild bank rules (stack limits, binding, withdrawal limits) and escrow mechanics for large trades. Add anti-grief controls like approval queues or vote-based disbursals.
  - Provide scheduling tools for raids/events with time-zone support and reminders; ensure calendar changes respect permissions and survive clock skew.
  - Add attendance/participation telemetry and rewards with anti-exploit checks (AFK detection, minimum contribution); expose appeals for false positives.
- **Governance and safety**
  - Include code-of-conduct acknowledgments and reporting flows inside guild UI; log enforcement actions with evidence hashes respecting privacy policies.
  - Offer succession/ownership transfer rules for inactive leaders; define dissolution safeguards for shared assets and housing plots.
  - Maintain disaster recovery steps for corrupted guild data, including backup frequency, targeted restores, and reconciliation of shared resources.

### Endgame, seasons, and progression resets
- **Season structure and rewards**
  - Publish season length, reset cadence, and reward ladders (battle pass, ranked tiers) with clear free/premium tracks. Validate reward delivery across platforms and edge cases (expired season, partial progression).
  - Require claim windows, grace periods, and restoration scripts for missed rewards due to outages; log claims with build/branch metadata for audits.
  - Add transparency for XP multipliers, catch-up mechanics, and caps; ensure they cannot be stacked with exploits or offline play.
- **Resets and migrations**
  - Define what resets (rank, rating decay) vs. persists (cosmetics, unlocked content); communicate pre-season migration steps and schema changes.
  - Run pre-season stress tests for ranked placement surges and matchmaking calibration; backfill or simulate ratings to avoid unfair placements.
  - Provide rollback plans for season launch failures (reopen prior season, pause rewards) and keep a clear support script for contested placements.
- **Live balance and competitive integrity**
  - Set season-long telemetry KPIs (win-rate ranges per archetype, queue times, economy inflation) and auto-flag regressions for design review.
  - Require fairness reviews for new mechanics added mid-season; gate them behind flags with opt-in betas and platform-specific toggles if needed.
  - Publish end-of-season summaries with enforcement stats (bans, reversions, prize adjustments) and archive them for dispute handling.

### Dungeons, raids, and instancing safety
- **Instance lifecycle and scaling**
  - Define instance creation triggers (queue match, dungeon finder, manual entry) with caps per platform tier and fallback to shard/realm overflow when limits are reached.
  - Capture join/rejoin rules for disconnects and cross-platform parties; ensure Steam/mobile clients can resync state, loot locks, and checkpoints without duplication.
  - Maintain performance budgets for instanced content (mob counts, VFX density, network actor replication) and enforce auto-thinning on low-tier devices to preserve FPS.
- **Boss keys, locks, and progression**
  - Map key/lock requirements to quests, reputation, or guild ownership; ensure anti-skip checks (party member requirements, puzzle completions) before boss rooms.
  - Track lock state in authoritative services with rollback scripts for contested completions; record timestamps/build IDs for dispute resolution.
  - Validate loot locks, personal loot, and shared drops with pity timers; document anti-reset rules for checkpoint abuse and AFK hitchhiking.
- **Procedural and modular content**
  - Specify tile sets, modifier pools (affixes/mutators), and objective variants; attach telemetry to modifier impact (clear time, death rate) and platform splits.
  - Require deterministic seeds for reproducibility in QA and rollback; store seeds with build/branch metadata and player party composition.
  - Include accessibility variants for puzzle-heavy seeds (hint frequency, timing windows) and ensure controller/touch parity for interactables.

### Character builds, cosmetics, and inventory integrity
- **Loadouts and respecs**
  - Ship loadout slots with saved bindings per input type; ensure cross-platform sync and fallbacks when a device lacks mapped inputs (e.g., missing hotkeys on mobile).
  - Define respec rules (costs, cooldowns, free respec tokens) and log state diffs for rollback; prevent exploit loops via disconnect/resume or branch hopping.
  - Add QA coverage for talent/gear swaps during combat, matchmaking queues, and cutscenes; verify server authority on stat aggregation to avoid desyncs.
- **Cosmetic economy and entitlements**
  - Maintain a cosmetics catalog with rarity, sources (store, battle pass, achievements), and region locks; include proof-of-ownership audits tied to platform receipts.
  - Enforce binding rules (account-bound vs. tradeable), dye/skin compatibility, and preview safety (no seizure triggers, content ratings). Document refund/chargeback impacts on cosmetic revocation.
  - Validate cross-platform rendering of cosmetics (LOD, material variants) and ensure fallback appearances on low-tier devices to avoid pay-to-win perception.
- **Inventory, storage, and loss prevention**
  - Implement authoritative inventory transactions with idempotent request IDs; include checksums/manifests for stash migrations and cross-progression sync.
  - Define overflow rules, mail systems, and reclaim windows for expired items; add CS macros and scripts for restoring deleted or lost inventory with audit trails.
  - Run stress tests on stash sorting, search, and filters for low-memory devices; gate bulk actions with confirmation prompts and rate limits to prevent accidental loss.

### Social overlays, communications, and session safety
- **Voice, text, and quick-chat**
  - Validate VOIP region routing, bitrate caps, and fallback to push-to-talk where privacy laws require; include profanity filters and mute/block at user and party levels.
  - Keep quick-chat wheels/keybinds localized with iconography; ensure accessibility by offering text equivalents and haptic cues where VO is disabled.
  - Capture telemetry on packet loss, dropouts, and moderation events per platform; auto-retry or downgrade codecs on constrained networks without impacting gameplay latency.
- **Presence, invites, and cross-play controls**
  - Maintain rich presence states (activity, party size, platform, input type) with privacy toggles; ensure Steam/mobile presence stays in sync across reconnects.
  - Provide invitation flows via friends, guilds, and codes/links; add safeguards against spam (rate limits, mutual consent) and age-gating where required.
  - Expose cross-play toggles and platform/input filters in settings; test matchmaking/instancing behavior when toggles are changed mid-session or during reconnects.
- **Session stability and recovery**
  - Record session tokens/checkpoints frequently; on crash/restart, restore party membership, dungeon checkpoint, and outstanding rewards without duplication.
  - Add safety nets for platform overlays and mobile backgrounding (pause timers, AI take-over, safe logout zones) with clear UI indicators.
  - Keep reconnection budgets and cooldowns configurable; alert on abnormal reconnect loops that indicate server or client regressions.

### AI behavior, factions, and spawn ecology
- **Enemy archetypes and behaviors**
  - Define archetype playbooks (bruiser, ranged, support, controller, summoner) with readable tells and counterplay per input type; ensure no single archetype hard-counters touch users due to aim demands.
  - Maintain AI decision budgets for low-tier mobile and Steam Deck; cap perception checks, pathfinding frequency, and ability evaluations. Add deterministic seeds for replay/debug builds.
  - Document boss/miniboss AI override rules (enrage, soft enrage, retreat) and safe-fail states when scripts desync; include telemetry for stuck/idle AI.
- **Factions and territory control**
  - Map faction hostility, alliances, and territory ownership with escalation thresholds; ensure patrols respect stealth states, disguises, and reputation tiers.
  - Track world-state changes (captured forts, cleared camps) with persistence/expiry and cross-progression reconciliation; add rollback scripts for contested states.
  - Validate civilian/ally AI behavior during events (evacuation routes, reaction to combat) with accessibility-friendly telegraphs for crowd panic or stampede hazards.
- **Spawn, leashing, and population control**
  - Set spawn tables per biome/time/weather with anti-overlap rules to avoid overwhelming mobile clients; include LOD and despawn thresholds for performance.
  - Define leash distances, reset timers, and anti-kite protections; ensure boss leashes respect instancing boundaries and teleports that do not strand players.
  - Monitor density and respawn telemetry to prevent farm loops and empty zones; add dynamic scaling that throttles or boosts spawns based on concurrency and device tier.

### Exploration, puzzles, and world events
- **Puzzle integrity and accessibility**
  - Catalog puzzle types (logic, timing, spatial) with hint cadence, cooldowns, and cooperative rules; ensure controller/touch equivalents exist for precision inputs.
  - Add anti-cheat/anti-skip checks for puzzle triggers (server-validated inputs, timer windows) and record partial progress for reconnect safety.
  - Provide accessibility variants (colorblind-safe glyphs, audio captions for sound cues, slower timing modes) without breaking reward parity.
- **Exploration loops and collectibles**
  - Track exploration milestones (landmarks discovered, vista triggers, codex scans) with per-platform telemetry; prevent duplicate rewards via checksum manifests.
  - Gate traversal aids (grapple points, glides, portals) behind progression while keeping first-time user paths clear; include fallbacks for offline/low-perf modes.
  - Add dynamic hints for missed objectives that respect player preference toggles and do not spoil puzzle solutions; localize clue language carefully.
- **Dynamic events and roaming encounters**
  - Define event templates (caravans, world bosses, invasion waves) with spawn windows, broadcast radius, and safe shutdown when branch toggles change.
  - Ensure rewards scale with participation and contribution metrics; guard against cross-platform exploitation (tag-and-run, AFK participation) with minimum engagement checks.
  - Provide event UIs with countdowns, phases, and failure states; test cancellation/rollback behaviors when branches revert or hotfixes apply mid-event.

### Achievements, collections, and codex fidelity
- **Achievement design and validation**
  - Maintain platform achievement/entitlement parity (Game Center, Play Games, Steam Achievements) with server validation to prevent spoofing; include offline queues with replay limits.
  - Define retroactive unlock rules after bugs or rollbacks; provide CS scripts for manual grants with audit trails and platform receipt checks.
  - Track achievement rarity and failure points; set alerts for sudden unlock spikes or drops that signal regressions or exploit attempts.
- **Collections, lore, and codex**
  - Structure codex entries with sources, spoiler flags, and localization rules; ensure text/audio/imagery comply with age ratings and seizure guidelines.
  - Validate collection progress (pets, mounts, titles, cards) against server authority; include duplicate protection, reclaim flows, and cross-progression merges.
  - Provide UI search/filter/bookmark tools with accessibility shortcuts; capture telemetry for discoverability pain points and update FTUE tips accordingly.
- **Leaderboards and competitive integrity**
  - Offer cross-platform leaderboards with anti-cheat validation, rate limits, and shadow bans for suspicious entries; include “last verified build” metadata.
  - Define seasonal/weekly reset rules and prize delivery with rollback-ready grant logs; support region/playlist segmentation to protect low-population queues.
  - Add privacy options (opt-out, anonymized names) and parental controls; ensure appeals and dispute processes are documented for rank adjustments.

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

### World interaction, physics, and hazard safety
- **Physics and collision budgets**
  - Set physics step budgets per device tier and platform; cap rigidbody counts, solver iterations, and cloth/hair simulations with graceful degradation on low-end devices.
  - Validate collision layers/masks for combat, traversal, and puzzle interactables; ensure controller/touch aim assist respects collision priority and does not soft-lock players in geometry.
  - Add regression tests for navmesh baking, dynamic obstacles, and destructible props; capture telemetry for stuck locations and auto-heal problematic areas via live config.
- **Environmental hazards and status effects**
  - Catalog hazard types (fire, poison, cold, fall, environmental puzzles) with stacking rules, cleanse counters, and accessibility-friendly tells (colorblind-safe, audio cues, haptics).
  - Enforce damage caps and safe fallbacks for sudden spikes (physics explosions, chain reactions) to avoid one-shots on mobile/Steam Deck; add rollback scripts for accidental deaths during outages.
  - Validate crowd control durations, diminishing returns, and immunity windows across PvE/PvP; log outlier chains for design review and exploit detection.
- **Traversal assists and recovery**
  - Provide unstuck/self-recover tools with cooldowns; support safe respawn anchors per biome/instance and record use for telemetry heatmaps.
  - Guard grapple/glide/teleport endpoints against out-of-bounds exploits and visual seams; ensure fallback paths exist for accessibility/low-performance modes.
  - Test water/swim/underwater rules (breath timers, buoyancy) with clear UI and accessibility variants; document edge cases for ladders, ledges, and mount dismounts near hazards.

### Mini-games, side activities, and hubs
- **Mini-game design and fairness**
  - Standardize input rules (timing windows, aim assist allowances) across controller/touch/mouse; provide latency compensation where networked mini-games exist.
  - Prevent resource inflation by capping rewards, daily limits, and tying mini-game currencies to sinks; include anti-bot signals and server validation for score submissions.
  - Ship tutorial overlays and practice modes; log completion and failure reasons to tune difficulty without breaking retention or accessibility needs.
- **Social hubs and events**
  - Define hub population caps, instancing rules, and AFK handling to protect FPS and chat/voice stability; validate emote/gesture spam limits and camera culling behaviors.
  - Curate hub vendors and services (crafting, mail, matchmaking kiosks) with outage-safe fallbacks and queue systems; ensure regional legal notices and payment flows render correctly in hubs.
  - Instrument live events hosted in hubs (concerts, announcements) with broadcast reliability metrics, abuse/mute controls, and graceful exits when branches roll back.
- **Collection rooms and showrooms**
  - Provide safe display spaces for cosmetics, mounts, and trophies with privacy toggles; include permission layers for visitors and screenshot/capture guidance.
  - Validate lighting/performance presets for showrooms on mobile and Steam Deck; cap spawnable NPCs/pets to prevent frame drops.
  - Record showroom layout changes for rollback and dispute resolution; ensure entitlements sync when cross-progression merges occur.

### Competitive modes, tournaments, and integrity
- **Playlist and ruleset governance**
  - Document playlists (ranked, unranked, limited-time) with map/mode rotations, party size limits, and input matchmaking pools (cross-play, input-based, platform-only).
  - Publish rulesets for scoring, tie-breakers, overtime, and surrender; include accessibility variants (longer timers, reduced APM) without granting competitive advantage.
  - Maintain dispute and appeal processes for contested matches, DC handling, and suspected cheating; link CS scripts and evidence preservation rules.
- **Tournaments and brackets**
  - Support bracket formats (single/double elimination, Swiss) with server-authoritative match reporting and redundancy for score submissions; protect against spoofed results and timing exploits.
  - Provide admin tools for reschedules, pauses, and rulings; log all interventions with build/branch metadata and participant IDs for audit trails.
  - Integrate spectator modes with privacy controls, delay options (anti-stream-snipe), and performance caps; validate capture/stream overlays on mobile/Steam.
- **Competitive rewards and anti-exploit**
  - Define prize eligibility, account age/minimum matches, and ban checks before grants; store grant manifests with rollback scripts for disputes or rule violations.
  - Monitor suspicious patterns (win-trading, boosting, disconnect dodging) with alerts and automated temporary locks; pair with manual investigations before escalations.
  - Add integrity probes to CI/playtests (input spoofing, macro detection, latency abuse) and simulate adversarial conditions to validate safeguards before live tournaments.

### Cross-platform identity, linking, and cloud progression
- **Account linking and trust**
  - Provide clear in-game flows for linking store accounts (Apple/Google/Steam) to a unified game ID; include unlink/relink with cooldowns and proof-of-ownership checks.
  - Enforce session hygiene (MFA prompts, device fingerprinting where policy allows) and notify users of new device sign-ins; expose session revocation from settings.
  - Maintain rate limits and anomaly detection for link attempts to prevent account takeovers; include CS macros for contested ownership with audit trails.
- **Entitlements and receipts**
  - Normalize receipts across stores into a canonical entitlement ledger; reconcile periodic receipt checks with store APIs and block gameplay advantages on invalid tokens.
  - Support entitlement replay after outages with idempotent grant scripts; log grants/redactions with platform, build, and branch metadata for dispute resolution.
  - Validate platform-specific perks (Game Center/Play Games/Steam achievements, DLC) across cross-progression merges; provide player-facing summaries of retained vs. lost entitlements.
- **Cloud saves and conflict resolution**
  - Implement authoritative cloud save slots with versioning, checksums, and platform metadata; provide manual conflict resolution UX with previews and rollbacks.
  - Test offline queues and resumable uploads/downloads across suspend/resume and branch swaps; ensure saves can be restored after partial writes or corruption.
  - Define data minimization and retention for saves (encryption at rest, least-privilege access) and document support flows for GDPR/CCPA deletion requests.

### Vehicles, naval/air systems, and traversal networks
- **Vehicle physics and safety**
  - Set per-vehicle physics budgets (wheels/hover/flight) with capped speeds, collision layers, and damage rules; profile on low-tier devices for stability.
  - Add safe entry/exit rules (combat locks, steep terrain) and recovery fallbacks when vehicles flip, sink, or clip; include telemetry for stuck events and automatic unstuck triggers.
  - Validate passenger slots, firing arcs, and seat permissions in co-op; ensure cross-platform input prompts/glyphs map correctly for vehicles.
- **Transportation networks**
  - Define fast travel, portals, ferries, and rail systems with load boundaries and fallback spawns; simulate network outages and branch rollbacks to avoid stranded players.
  - Maintain schedule/state replication for shared transports (airships, trains) with anti-grief rules (AFK kick, friendly-fire suppression) and accessibility seating/telemetry.
  - Provide map overlays and waypoint rules for land/sea/air routes with localized signage and colorblind-safe icons; log travel costs and uptime for ops dashboards.
- **Vehicle combat and customization**
  - Balance vehicle combat with DPS/firing arcs, heat/energy systems, and counterplay; avoid pay-to-win by constraining upgrade deltas and publishing tuning baselines.
  - Validate cosmetic customization (decals, dyes, contrails) with platform-safe content filters and LOD fallbacks; ensure previews do not leak unreleased items.
  - Include repair/refuel/resupply economies with sinks and cooldowns; attach rollback scripts for bugged vehicle losses or duped upgrades.

### Modifiers, mutators, and dynamic rulesets
- **Seasonal and rotating modifiers**
  - Curate modifier pools (elemental twists, double-jump weeks, loot boosts) with opt-in playlists and exposure caps; validate accessibility variants to avoid blocking players with disabilities.
  - Track KPI impacts (TTK, completion times, crash rates) per modifier and platform; auto-disable modifiers that exceed regression thresholds.
  - Require deterministic seeds and reproducible test cases for modifier bugs; document rollback steps and communication templates for early shutdowns.
- **Encounter and world mutators**
  - Apply mutators to dungeons/world events with server-side gating and per-tier performance budgets; ensure telegraphs remain readable when mechanics change.
  - Add anti-exploit checks for synergy stacking (modifiers that trivialize bosses or economy sinks) and guard against unintended XP/loot inflations.
  - Provide sandbox toggles for QA and live-ops to rehearse upcoming modifiers; include safety rails to revert to baseline ruleset within minutes.
- **Player-visible ruleset clarity**
  - Surface active modifiers in HUD/tooltips/loading screens with localization and accessibility cues; archive prior modifier states for dispute handling.
  - Document how modifiers interact with achievements, leaderboards, and seasonal progression; prevent unintended unlocks during experimental rotations.
  - Include monitoring for modifier-related crash/latency deltas and annotate dashboards/alerts with the current ruleset to reduce MTTR.

### Player expression, UGC, and sharing
- **Creation tools and safety**
  - Provide in-game editors (housing layouts, emblems, photo/replay cameras) with performance budgets, undo/redo history, and sandbox validation to prevent invalid placements or memory spikes.
  - Enforce content filters for text, images, and shapes; integrate pre-submission scans for offensive or IP-violating content and route escalations to moderation with audit logs.
  - Include publish/retract flows with visibility settings (private/friends/public), age-appropriate defaults, and player reporting that links to offender/asset IDs.
- **Discovery and curation**
  - Build browse/search with tag taxonomies, locale filters, and accessibility cues (subtitle availability, colorblind-friendly palettes); add rate limits and bot-detection for likes/downloads.
  - Feature slots and rotating spotlights should be manually curatable with rollback controls; document how featured assets affect matchmaking or instance performance.
  - Support cross-platform sharing policies (Steam Workshop/UGC TOS) with clear ownership/licensing prompts and removal SLAs for DMCA/privacy requests.
- **Collaboration and attribution**
  - Allow co-authoring with permission hierarchies (edit/view/publish) and change history; protect against grief edits with owner-only revert and publish gates.
  - Track dependencies (prefabs, custom audio, decals) and warn before deleting shared assets; ensure downloads are deterministic and versioned for replays.
  - Provide in-game and store-facing attribution (creator names, co-authors, music licensing) and anonymized options for minors where required by policy.

### Live narrative arcs and seasonal structure
- **Story cadence and state management**
  - Plan season/episode cadences with clear entry points, catch-up quests, and recap UI; ensure branching states reconcile across platforms and cloud saves without deadlocks.
  - Provide narrative fail-safes (auto-complete after N failed attempts, accessibility variants) and off-ramps to avoid blocking combat/economy progression.
  - Version dialogue, cinematics, and VO with locale bundles; validate lip-sync and subtitle timing on low-end devices and streaming conditions.
- **Seasonal artifacts and migrations**
  - Define which currencies, cosmetics, achievements, and quest flags persist between seasons versus reset; document migration scripts and player-facing summaries.
  - Archive prior-season states for support disputes and replay theater; attach rollback playbooks if migrations corrupt quest progression or entitlements.
  - Validate battle pass or seasonal track integrations with daily/weekly challenges, ensuring anti-FOMO guardrails and parental controls are respected across stores.
- **Event delivery and pacing**
  - Schedule limited-time world changes (weather shifts, faction invasions) with testable toggles and staged rollouts; include telemetry to measure server/latency impacts.
  - Gate narrative beats behind reliability checks (crash thresholds, matchmaking health) and allow pause/skip of live beats during incidents without soft-locking players.
  - Coordinate marketing/comms with in-game banners, patch notes, and community updates; ensure localization completeness and imagery approvals for each platform.

### Hardcore modes, ladders, and challenge variants
- **Mode rules and fairness**
  - Define hardcore/permadeath rulesets with clear loss conditions, safe zones, and grace periods for disconnects; log cause-of-death details for dispute resolution.
  - Enforce anti-cheat and anti-exploit checks tuned for ladder modes; isolate character inventories/progression to prevent cross-contamination with standard modes.
  - Provide reconnection/rollback policies for server crashes or verified platform outages; avoid punitive losses due to client updates or store-side maintenance.
- **Ranking, seasons, and rewards**
  - Build ladders with transparent scoring formulas, decay rules, and anti-boosting checks (party MMR gaps, repeated opponent detection); expose audit-friendly snapshots.
  - Rotate ladder seasons with predictable calendars, provisional placements, and demotion protection; ensure rewards are claimable across platforms with entitlement proofs.
  - Include moderation hooks to remove illegitimate entries and re-issue rewards; publish post-season integrity reports to reinforce player trust.
- **Spectating and broadcasting**
  - Offer spectate/replay modes with streamer-safe privacy (chat filters, hide player IDs) and performance caps; validate camera paths and HUD readability on mobile/Steam Deck.
  - Provide data APIs or overlays with rate limits and attribution; coordinate with anti-cheat to mask sensitive telemetry that could aid exploits.
  - Support tournament ops with admin tools for pauses, remakes, seed locking, and prize validation; scriptable tools should log authority actions for later review.

### World bosses, invasions, and shard health
- **Spawn governance and fairness**
  - Define predictable spawn windows and shard balancing rules for world bosses/invasions; avoid overcrowding by instancing overflow shards and offering staggered regional timings.
  - Enforce contribution tracking that rewards participation (damage/healing/objective time) instead of last-hit mechanics; publish loot rules so rewards feel fair across platforms.
  - Add grief protection (spawn camping shields, AFK removal, revive zones) and accessibility variants (lower visual noise modes, clearer telegraphs) for crowded encounters.
- **Operations and fail-safes**
  - Simulate shard recovery/restarts to ensure boss state rolls forward or cleanly resets without duping loot; include GM/CS scripts for refunding keys/tickets when events cancel.
  - Track capacity/latency dashboards during events with automated throttles for new entrants; trigger branch-specific hotfixes or temporary debuffs when server stability regresses.
  - Archive event state snapshots for incident review and rollback; annotate alerts with event names/modifiers to reduce MTTR during live disruptions.
- **Reward pipelines**
  - Version world boss loot tables and cosmetic drops; attach tuning knobs for drop protection/bad-luck protection and test on non-public branches before global release.
  - Gate chase rewards behind account binding or time-limited claims to prevent cross-shard trading exploits; log high-rarity drops with player, shard, and platform metadata.
  - Align community-facing calendars, in-game banners, and store descriptions so players understand availability, eligibility, and platform-specific participation rules.

### Itemization integrity, loot tables, and inflation control
- **Loot governance**
  - Centralize loot tables with deterministic seeds and audit history; require code reviews for changes that affect drop rates, pity timers, or duplicate-protection rules.
  - Segment loot pools by activity tier and platform capability (controller vs. touch complexity, Steam Deck performance) to avoid inaccessible mechanics driving drop disparity.
  - Validate boss/add-on synergies that could turbocharge loot (e.g., mutators that double chests); add caps and dashboards for average loot per hour across playlists.
- **Economy resilience**
  - Model currency sinks vs. faucets with budgets per season; alert when inflation thresholds (pricing drift, trade volume spikes) exceed targets, and gate high-value crafts behind time/effort limits.
  - Enforce server-side item creation and trade limits; detect dupes via checksum/versioning, and provide one-click rollback scripts scoped by item IDs and player segments.
  - Keep bind-on-pickup/bind-on-equip rules consistent across platforms; surface clear UI warnings for irreversible binds, reforges, and salvage actions.
- **Tuning and QA**
  - Maintain comparative DPS/TTK baselines per archetype and platform input; require A/B sandboxes for major stat or affix changes with telemetry on completion time, deaths, and crash deltas.
  - Capture golden test cases (build templates, encounter seeds) for performance-sensitive loot changes and verify they hold on low-end devices and Steam Deck.
  - Coordinate loot and economy patch notes with community/support macros; include compensation plans for rollbacks or fixes that materially change player progression.

### Co-op, party systems, and mentorship
- **Party lifecycle and reliability**
  - Standardize party creation/join/invite flows across platforms with presence-awareness; support rejoin after disconnects and branch swaps without losing matchmaking position.
  - Add ready checks, vote-to-kick safeguards, and AFK detection tuned per platform; keep UI prompts controller- and touch-friendly with accessibility labels.
  - Provide shared waypoints, ping systems, and loot-visibility rules; ensure cross-play voice/text is opt-in with moderation and recording disclosures where legally required.
- **Mentorship and new-player protection**
  - Implement mentor/apprentice programs with level gates, anti-boosting checks, and reward throttles; require opt-in consent and an exit path to avoid coercion.
  - Offer tutorial overlays and simplified mechanics for first-time party members; allow mentors to share instanced quests without breaking progression or granting unintended rewards.
  - Track mentorship abuse metrics (power-leveling hotspots, carry-for-hire spam) and provide CS tooling to suspend or reset mentor perks when exploited.
- **Cross-session continuity**
  - Persist party state across sessions/time zones with clear ownership of leader settings (difficulty, privacy, voice); store last-known objectives for smooth resume.
  - Record party composition and role data in telemetry to debug matchmaking fairness and encounter balance; include platform identifiers to isolate device-specific issues.
  - Provide visibility into feature flag differences per party member (new modifier pilots, economy experiments) and gracefully fall back to the lowest-common ruleset when compatibility fails.

### Faction reputation, crime, and justice systems
- **Reputation integrity**
  - Keep a single source of truth for faction reputation across platforms with server-authoritative updates; snapshot reputation deltas for rollback and CS adjustments.
  - Rate-limit reputation gains/losses per activity to prevent farming or grief spikes; validate multi-character exploits and shared-account scenarios.
  - Provide clear UI telemetry for reputation changes (why/how much) with accessibility cues; ensure localization supports faction-specific terms and honorifics.
- **Crime, bounty, and law enforcement**
  - Define crime categories (theft, assault, trespass) with intent checks and accidental-friendly buffers; separate PvE, PvP, and social hub rulesets.
  - Implement bounty and guard responses with predictable escalation ladders; ensure guards are performance-budgeted and respect collision/navmesh on low-end devices.
  - Offer appeal/forgiveness flows (CS pardons, mentor overrides, restitution payments) with audit trails; protect new players from permanent lockouts.
- **Justice events and edge cases**
  - Simulate mass-participation justice events (public trials, jailbreaks) with shard-aware scaling and rejoin protections; log offender/victim metadata for dispute resolution.
  - Add anti-grief controls for duels and arena crimes (consent prompts, cooldowns, safe spectators); gate PvP punishment rules by playlist and platform.
  - Expose sandbox flags for testing crime/justice modifiers on non-public branches before enabling globally.

### Survival, crafting upkeep, and environmental hazards
- **Hunger, thirst, and temperature systems**
  - Tune depletion curves with platform-aware UI prompts and haptics; prevent rapid oscillation that forces micromanagement on controllers or touch.
  - Provide safe zones and consumable fallbacks for accessibility; allow CS/GM restoration for accidental death cascades caused by latency or desync.
  - Log survival tick deltas and damage sources for audit and balancing; integrate with analytics to detect bottlenecks or grief loops.
- **Environmental hazards and sheltering**
  - Standardize hazard tags (poison, burn, freeze, radiation) with mitigation rules; confirm VFX readability under low-light and colorblind filters.
  - Require shelter/building placement validation to prevent exploits (safe spots in boss rooms, out-of-bounds immunity); support rollback of invalid structures.
  - Script weather and disaster events (sandstorms, blizzards) with staged intensity and recovery timers; keep device performance budgets for particle-heavy effects.
- **Upkeep and maintenance**
  - Attach durability/maintenance to crafted structures with server-driven decay; provide alerts, grace periods, and batch repair tools to reduce churn.
  - Validate co-op ownership and permissions for shared bases; include eviction and transfer flows with logs to resolve disputes.
  - Enforce resource sinks and upkeep costs to stabilize economies; alert when repair/material consumption diverges from targets.

### Meta-progression, challenges, and seasonal battle passes
- **Account-level progression**
  - Define meta tracks (season XP, prestige, renown) with deterministic rewards and platform-consistent pacing; prevent double-dipping via cross-save exploits.
  - Ensure unlocks are entitlement-bound with receipt validation; add regrant scripts for failed claims and audit reports for CS adjustments.
  - Offer catch-up mechanics and weekly caps to reduce grind spikes; publish schedules and expiry dates clearly in all locales.
- **Challenges and achievements**
  - Curate rotating challenge lists with difficulty tiers and accessibility variants; test completion triggers against edge cases (disconnects, crashes, offline mode).
  - Record proof points (activity IDs, loadout, modifiers) for achievements to investigate abuse; throttle progress when anomalies spike.
  - Support feature flags for experimental challenge rules; validate that leaderboards and achievements handle new modifiers without corrupting historic scores.
- **Battle passes and reward delivery**
  - Build battle pass progression with server-side XP/mission grants; allow mission rerolls and anti-frustration mechanics for blocked objectives.
  - Provide transparent UI for free vs. premium tracks, refund policies, and region-specific legal text; ensure restores handle delayed purchases and platform downtimes.
  - Pre-stage cosmetic rewards in non-public branches and run lighting/performance checks on low-end devices; attach rollback plans and compensation macros for mis-awarded tiers.

### Modding, tools, and creator pipelines
- **Sandboxing and security**
  - Require signed mods/add-ons with checksum validation, sandboxed execution, and strict API surface limits; block file system/network access by default and log sensitive syscalls.
  - Provide safe data schemas for mod persistence with forward-compatible migrations; enforce quota and rate limits to prevent server load spikes.
  - Ship crash/compatibility scanners that flag unstable mods before matchmaking; add safe mode boot to disable offending mods and preserve player saves.
- **Versioning and distribution**
  - Standardize semantic versioning for game and mod APIs; expose compatibility matrices in UI and block mismatched clients from joining authoritative sessions.
  - Run CI signing/publishing for mods and internal tools with review gates, malware scanning, and provenance stamps; mirror artifacts per region for latency and compliance.
  - Offer rollback channels and deprecation warnings when APIs change; keep telemetry on mod uptake, crashes, and abusive patterns to inform removals.
- **Creator tools and content QA**
  - Provide WYSIWYG editors with performance budgets, navmesh previews, and accessibility checks (color contrast, caption completeness) baked into export validation.
  - Add automated linting for scripts, dialogue tokens, localization keys, and animation events; surface human-in-the-loop approvals for risky content (violence, IP, UGC).
  - Include submission checklists for lighting bake quality, spawn safety, and encounter balance; support branch-based collaboration with merge conflict resolution for scene graphs.

### Competitive seasons, PvP rulesets, and fairness operations
- **Ranked ladders and MMR**
  - Define transparent rank tiers, decay rules, and placement calibration with protections against smurfing and boosting; rate-limit duo/party MMR deltas to reduce exploitation.
  - Capture per-match proofs (inputs, pings, loadouts, modifiers) for dispute resolution; store match hashes for integrity audits and tournament reviews.
  - Provide cross-platform latency normalization and server selection policies; surface pre-match warnings for high ping/packet loss with graceful rematch options.
- **Playlist governance and rotations**
  - Curate rotating playlists with clear rule summaries, map pools, and banned/featured items; validate each rotation for load distribution and crash regressions.
  - Implement feature flags for experimental PvP modifiers with shard-aware rollout and instant rollback; test spectator modes, replays, and broadcast overlays for stability.
  - Enforce anti-grief controls (friendly-fire toggles, spawn protection, AFK/kick logic) tuned per mode; track abuse reports with fast CS/GM escalation paths.
- **Anti-cheat and enforcement**
  - Combine client attestation, server-side validation, heuristic detection, and periodic challenges; keep fallback “trusted” builds for platform review while protecting live integrity.
  - Maintain ban/penalty ladders with region-aware policies, appeal workflows, and communication templates; snapshot inventories and ratings pre-action for accurate rollbacks.
  - Run chaos/soak tests against anti-cheat updates in canary regions before global deploy; monitor false positive rates and auto-pause rollouts if error budgets are exceeded.

### Live narrative arcs, expansions, and content drops
- **Episodic delivery and gating**
  - Plan narrative beats with pre-patch data staging and unlock tokens; support offline-safe gating to avoid corruption during downloads or outages.
  - Add catch-up recaps, codex entries, and quest state reconciliation for returning players; localize branching dialogue with lip-sync and font fallback validation per platform.
  - Track completion funnels and abandonment reasons to tune difficulty spikes; wire telemetry to content flags so failed steps can be hotfixed without full client updates.
- **Expansion rollout and migration**
  - Use phased unlocks (prologue, region access, endgame features) with shard-aware load shedding; rehearse migration scripts in staging with representative save corpora.
  - Validate cross-expansion entitlements (mounts, cosmetics, boosts) with regrant tools; keep downgrade and rollback plans for corrupted progression or missing assets.
  - Preflight cinematic/audio packages for device storage and streaming constraints; include fallback media for low bandwidth and accessibility (captions, descriptive audio).
- **Content lifecycle and sunsetting**
  - Define sunsetting policies for outdated quests, loot, or seasonal mechanics with compensation plans; archive states for dispute resolution and legacy achievements.
  - Add deprecation warnings and time-limited conversions for currencies or items; keep migration scripts idempotent and auditable.
  - Maintain lore/canon integrity checks when rotating content out; ensure UI, maps, and NPCs handle removed nodes gracefully without soft-locks.

### Relics, artifacts, and ancient site operations
- **Discovery and gating**
  - Define relic tiers, shard collection rules, and puzzle locks with telemetry on solve paths; prevent sequence breaks by enforcing prerequisite flags server-side.
  - Add environmental hazard checks (traps, collapsing floors) with accessibility variants and mobile-friendly prompts; include safe extraction/evacuation flows on disconnects.
  - Record seed/version metadata for procedurally placed relic rooms to reproduce bugs and rollback unsafe layouts across Steam/mobile branches.
- **Curation, upgrades, and lore**
  - Maintain an artifact catalog with provenance, lore unlocks, and upgrade paths; require rollback-friendly stat deltas and visual variants per tier.
  - Enforce upgrade materials sinks and cooldowns to avoid runaway power creep; include CS macros for restoring lost progress after crashes or fraud investigations.
  - Localize lore entries with spoiler-aware gating and audio/text parity; ensure codex updates sync across platforms and survive partial downloads.
- **Exploits, trading, and fairness**
  - Add anti-duplication checks for relic shards and bind-on-acquire rules for high-tier artifacts; log acquisition context (party, instance seed, modifiers) for dispute resolution.
  - Gate trading/auction eligibility by account age and completion of integrity checks; include escrow and refund windows for contested trades.
  - Monitor completion times, death rates, and drop distributions for relic sites; auto-pause rotations if anomalies suggest exploits or tuning regressions.

### Naval, airship, and caravan systems
- **Vehicle construction and ownership**
  - Define blueprint rarity, crafting inputs, and crew role requirements for ships/airships; validate ownership/auth permissions for shared vehicles across platforms.
  - Track durability, fuel/energy, and maintenance intervals; add repair docks/stations with queueing and offline/steam branch-friendly persistence.
  - Include recovery flows for sunken/crashed vehicles with item preservation rules and insurance-like restitution scripts for CS.
- **Navigation, combat, and hazards**
  - Map traversal lanes, wind/currents/thermals, and fast-travel anchors; provide autopilot with safe-stop behavior for disconnects or high-latency mobile sessions.
  - Budget cannons/weapon systems, boarding mechanics, and crew stations to meet performance caps; validate camera/UI readability for deck and cockpit views.
  - Script storms, reefs, and piracy events with shard-aware scaling; ensure collision/navmesh updates do not strand players and that fail-safes teleport to safe harbors when needed.
- **Logistics, trade, and multiplayer flows**
  - Support caravan/convoy missions with escort rules, loot weight limits, and anti-bot route randomization; log risk/reward balance for tuning.
  - Provide guild/party permissions for cargo loading/unloading with audit trails; add anti-theft locks and grace windows for accidental drops.
  - Integrate matchmaking for naval/airship PvP and co-op voyages with cross-platform latency disclosures; include surrender/retreat mechanics to avoid grief loops.

### Professions, crafting mastery, and economy specialization
- **Profession leveling and perks**
  - Define profession XP curves, specialization branches, and mastery perks with caps to prevent runaway stacking; expose respec tokens with audit logs.
  - Add daily/weekly work orders and contracts to stabilize resource inflows; ensure quests respect device-specific interaction limits (touch drag-drop alternatives).
  - Provide telemetry for resource scarcity, completion rates, and gold-per-hour to tune faucets/sinks by platform and branch.
- **Crafting mini-games and quality control**
  - Standardize crafting mini-games (timing/precision/pattern) with accessibility modes and alternative auto-craft paths that respect balance; log input sources for anti-bot checks.
  - Require QA validations for quality tiers and affix pools before release; include rollback scripts for misrolled items and compensation plans for affected players.
  - Add provenance tags to crafted goods (crafter ID, station, build ID) to support fraud investigations and leaderboard/market filters.
- **Market influence and regionalization**
  - Implement regional price bands and tax/fee modifiers to control inflation; monitor cross-region arbitrage and adjust trade restrictions as needed.
  - Provide platform-aware notification and delivery systems for completed orders/sales; ensure offline/mobile clients receive reliable updates without duping.
  - Publish economic health dashboards (supply/demand, price indices, crafting success rates) with alert thresholds that gate release go/no-go when drifting.
