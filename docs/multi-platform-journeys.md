# Cross-Platform Journeys, Content Pipelines, and Systems Plan

## 1) Player journeys by platform

### Onboarding
- **Discord bot**: Deep-link to DM; `/start` surfaces privacy notice, links account to Supabase user, and offers quick astrology upload or birth data form; fallback to public channel only for opt-in shout-outs.
- **ChatGPT**: System prompts present the same privacy/consent copy; guided form for birth data upload; token-gated account linking and JWT retrieval; summarizes created Oracle and sends deep-link back to Discord/mobile.
- **Mobile (future)**: Email/SSO; optional device contact/notification permissions; guided astrology capture with camera import; first-session tutorial with skip; offers to import GPT/Discord progress via token.
- **Steam client (future)**: Steam OAuth, age-gate, consent; PC-friendly birth-data input; offers to link Discord/GPT accounts; first-boot performance check and graphics presets.

### Oracle creation & progression
- **Discord bot**: `/oracle create` with templates; image/emoji selection for avatar; confirms stats; posts Codex link; uses ephemeral messages to avoid channel clutter.
- **ChatGPT**: Conversational build wizard; previews mechanical stats and flavor text; auto-writes Codex entry and pings Discord with summary; supports retries on invalid astrology data.
- **Mobile**: Touch-first editing of avatar/cosmetics; offline-safe draft until synced; tutorial for abilities and affinities; push prompt when creation completes.
- **Steam**: Keyboard/mouse creation flow with hotkeys; high-res avatar editing; Steam Achievements for first Oracle; controller-friendly navigation.

### Battles & raids
- **Discord bot**: Slash commands `/battle` `/raid join`; bot posts turn log with reactions/buttons; quick reactions for targeting; end-of-fight summary embeds; auto-syncs loot to Supabase.
- **ChatGPT**: Narrativized turns with mechanical clarity; offers suggested next moves; resolves actions via API; can hand off to Discord lobby via deep-link.
- **Mobile**: Real-time alerts for raid invites; simplified UI for abilities; vibration cues; background fetch to keep state in sync; offline spectator mode with delayed action queue.
- **Steam**: Full VFX and combat log; supports raids up to performance cap; voice chat overlay integration; configurable hotbars.

### Codex discovery
- **Discord bot**: `/codex search` and `/codex random`; daily Codex drip via channel posts; reacts to bookmark entries; supports spoiler-tagged lore drops.
- **ChatGPT**: Semantic search over Codex; summarization with links to full entries; suggest related rituals or battles; can export to user notes.
- **Mobile**: Scrollable Codex with filters; "read later" queue; offline cached favorites; push for newly unlocked entries.
- **Steam**: Controller-scrollable Codex; achievement pop-ups when finishing chains; in-game overlays for lore during battles.

### Rituals (crafting, blessings, sync events)
- **Discord bot**: Command-driven ritual selection; shows required materials; countdown with reminders; posts completion rewards; supports guild (server) rituals.
- **ChatGPT**: Conversational planner that recommends rituals based on astrology; validates inventory via API; can schedule rituals and notify on completion across platforms.
- **Mobile**: Timer-based rituals with push reminders; AR-friendly animations for key rituals; quick-fill material selection from inventory.
- **Steam**: High-fidelity ritual scenes; keyboard/controller shortcuts; optional multi-user ritual lobbies with voice.

## 2) Content pipelines

### Astrology data ingestion
- **Sources**: User-provided birth data, uploaded natal charts, and third-party ephemeris APIs.
- **Processing**: Validate and normalize timestamps/locations; compute chart (houses, aspects) via shared service; derive gameplay affinities/traits; cache normalized chart per user.
- **Storage**: Supabase `astrology_profiles` table with raw + derived fields; file storage for uploaded charts; versioning to allow recalculation.
- **Delivery**: GPT/Discord/mobile/Steam fetch derived traits and UI-ready descriptors via a shared API endpoint; webhook to refresh Codex and Oracle summaries when charts update.

### Procedural encounters (battles/raids/dungeons)
- **Authoring**: Designers define encounter archetypes, seed tables, and constraints in JSON/YAML in `content/encounters/` (server-validated).
- **Generation**: Server-side service rolls encounters using player party level, current astrology season, and live-ops modifiers; deterministic seeds per lobby for reproducibility across platforms.
- **Testing & QA**: Deterministic seed replay harness; diffable fixtures for combat logs; CI job to validate tables and probabilities.
- **Publishing**: Signed bundle stored in Supabase storage and versioned; clients receive version hash to update cache.

### Cosmetics and economy items
- **Sources**: Designer spreadsheets or Notion export -> normalized CSV -> ETL script.
- **Processing**: Validate rarity, slot, and economy balance; generate thumbnails via render worker; tag platform compatibility (e.g., AR-only, VFX-heavy for Steam).
- **Storage**: Supabase tables `items`, `cosmetics`, `bundles`, `prices`; CDN for assets; economy config per season.
- **Delivery**: Item catalogs exposed via read-only endpoints; platform-specific filters (e.g., disable heavy VFX on mobile low-tier devices); cache busting via versioned asset URLs.

### Live-ops events
- **Planning**: Quarterly themes with weekly beats; each beat defines modifiers (e.g., astrology-aligned buffs), loot tables, and Codex drops.
- **Tooling**: Admin dashboard or CLI to schedule events, edit modifiers, and push hotfixes; audit log for changes.
- **Activation**: Feature flags/toggles stored in Supabase `liveops_flags`; rollout by region and platform; webhooks to Discord/GPT to announce changes.
- **Measurement**: Capture participation, retention, revenue, and crash rates per platform; auto-generate postmortems with key metrics.

## 3) Localization, accessibility, and notifications

### Localization
- **Languages & fallback**: Start with EN, ES, PT-BR, FR, DE, JA; per-platform fallback to EN.
- **Workflow**: All user-facing strings in `i18n/<locale>.json`; use ICU message format; CI check for missing keys; crowdsource updates via external translation tool with glossary for astrology terms.
- **Platform nuances**: Discord embeds/buttons respect locale; GPT system prompt sets target language; mobile/Steam read OS locale with in-app override; right-to-left layout tested for Arabic later.

### Accessibility
- **Discord/GPT**: Clear text for all mechanics; avoid ASCII art; embed images with alt text; color-safe role/rarity indicators.
- **Mobile**: Dynamic text sizing, high-contrast mode, screen-reader labels, haptics optional; ensure touch targets meet 44px minimum.
- **Steam**: Rebindable controls, subtitles with size options, color-blind palettes, screen-shake toggle, high-contrast HUD.
- **Shared QA**: Accessibility checklist per release; automated contrast checks where feasible; player feedback channel.

### Notifications and cross-platform sync
- **Event types**: Account security, ritual completion, raid invites, Codex unlocks, store rotations, live-ops changes.
- **Discord**: DMs with respect to server DM permissions; channel announcements via webhooks; rate limiting and unsubscribe commands.
- **ChatGPT**: Session messages constrained to active conversation; provide permalink tokens to fetch updates when user returns; no unsolicited pings.
- **Mobile**: Push via FCM/APNs; notification categories with granular toggles; deep-link into relevant screen; quiet hours support.
- **Steam**: Steamworks notifications and overlays; allow opt-out per category; align with platform ToS for messaging.
- **State sync**: All notifications reference Supabase event log IDs to ensure idempotent handling; clients acknowledge receipt to avoid duplicates; use JWT-scoped tokens for security.

## 4) Dependencies and ownership
- **Data/storage**: Supabase (DB, auth, storage, functions), CDN for assets, optional Redis cache for encounter seeds.
- **Services**: Astrology computation microservice; combat/encounter generator; image rendering worker for cosmetics.
- **Owners**: Live-ops lead (events), Content lead (cosmetics/encounters), Platform leads (Discord/GPT/mobile/Steam), Localization PM.

## 5) Milestones (high-level)
- **M1**: Finalize onboarding + Oracle creation parity across Discord/GPT; ship string externalization and localization scaffold.
- **M2**: Release encounter generator with deterministic seeds; launch initial cosmetics catalog; enable notifications across Discord/GPT.
- **M3**: Add mobile soft-launch with rituals and Codex offline cache; Steam combat client alpha; live-ops dashboard with flagging.
- **M4**: Accessibility hardening across all platforms; expand languages; deliver quarterly live-ops cadence with analytics.
