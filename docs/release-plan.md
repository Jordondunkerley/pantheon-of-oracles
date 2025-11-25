# Release Milestones and QA Strategy

## Stage Milestones
- **Alpha – Feature-complete core loop**: Core astrology gameplay loop functional with session persistence, core matchmaking, and baseline telemetry.
- **Beta – Mobile/Steam clients**: Cross-platform clients (iOS/Android/Steam) playable with platform sign-in, controller/touch input, and cross-save.
- **Release Candidate – AR/VR layers**: AR overlays and VR interactions built on top of stable clients; comfort and safety features enabled.
- **General Availability – Polish/compliance**: Quality, scale, and policy readiness for storefront launches and live operations.

## Milestone Deliverables
- **UI/UX**
  - Alpha: Core flows (login, lobby, match, results) with minimal art; accessibility scaffolding (text scaling, color-contrast-safe palette).
  - Beta: Platform-specific layouts, controller/touch affordances, and first-pass tutorials; navigation parity between platforms.
  - RC: AR/VR-specific affordances (gaze/pointer selection, locomotion cues), session recovery prompts, and comfort settings surfaced.
  - GA: Final visual polish, localization-ready layouts, and live-ops surfaces (events, offers, inbox) behind feature flags.

- **Matchmaking Stability**
  - Alpha: Deterministic matchmaking rules, retries/backoff, and telemetry for queue health.
  - Beta: Cross-platform queues, platform-aware latency routing, and shadow traffic to validate load.
  - RC: AR/VR session handling, reconnection for headset sleep/wake, and stress-tested party flows.
  - GA: Autoscaling policies tuned from load tests, SLO dashboards (latency, drop rate), and runbooked mitigations.

- **Monetization Hooks**
  - Alpha: Economy stubs, entitlement tracking, and sandbox SKU schema.
  - Beta: Storefront integrations (Apple/Google/Steam sandbox), price localization, and receipt validation pipeline.
  - RC: AR/VR-safe purchase prompts, VR keyboard/voice input support, and cancellation/timeout handling.
  - GA: Compliance-reviewed purchase flows, live offer config, and rollback/refund playbooks.

- **Accessibility/Localization**
  - Alpha: Text scaling, color contrast checks, basic screen-reader labels for core flows.
  - Beta: Localized strings framework with fallback language, RTL layout checks for mobile, and subtitle/closed-caption options.
  - RC: VR comfort options (snap/teleport, vignette), spatial audio captions, and AR anchoring cues.
  - GA: Full language coverage, post-launch localization pipeline, and accessibility regression gates in CI.

- **Store Compliance**
  - Alpha: Log data classification and consent prompts; initial COPPA/GDPR review.
  - Beta: Platform sign-in, sandbox IAP review notes, and privacy policy links in-app.
  - RC: Platform-specific store checklists for AR/VR (comfort, boundary warnings) and seizure-safety labeling.
  - GA: Final store submissions, age ratings, crash/ANR thresholds met, and privacy/security attestations.

## QA Strategy
- **Test coverage**: Unit tests for gameplay/services; integration tests for matchmaking, persistence, and payment flows; contract tests for platform SDKs; smoke tests on every build.
- **Load and scale**: Synthetic queue/load tests for matchmaking, soak tests for session longevity, chaos tests for dependency loss (auth, payments, telemetry).
- **Device matrix**:
  - Mobile: iOS/Android mid- and high-tier devices, varying network quality (Wi-Fi/LTE), and controller/touch modes.
  - PC/Steam: Min-spec and recommended GPUs/CPUs, windowed/fullscreen, and controller/keyboard/mouse.
  - VR: Quest/SteamVR headsets with comfort presets, guardian/boundary states, and seated/standing modes.
- **VR/AR interaction tests**: Hand tracking vs controllers, gaze/pointer selection latency, locomotion comfort (teleport/snap smoothness), and passthrough occlusion correctness.
- **Release gates**: Per-milestone exit criteria tied to crash-free rate, matchmaking success, purchase success, and accessibility/localization checks.
