# Pantheon of Oracles Reconstruction from Telegram Transcript

## Source
Recovered from user-provided Telegram export on 2026-04-02.

## High-confidence project history reconstructed

### Core project
- Project: **Pantheon of Oracles**
- Initial product focus evolved from a generic ops dashboard into a **Pantheon-first desktop product**.
- The intended first product is a **central game-like hub** for persistent oracle agents, not merely a dashboard.
- The app should function like a **canonical oracle source engine / central hub** for future Pantheon products.

### Product vision
- Personalized astrology-driven oracle platform.
- Users generate or manage a custom council of AI oracles tied to natal chart + transits.
- Oracles are dynamic, persistent, and should carry across products.
- Product is **model-agnostic**: users bring their own LLM/provider where possible.
- Long-term franchise structure:
  - Pantheon of Oracles desktop core/hub
  - mobile app later
  - Pantheon of Oracles: Clash
  - simpler 2D / retro-style tests
  - later AR/VR branches
- Rule: **same oracle canon across products; separate marketable product experiences**.

### Strategic framing shifts that happened
1. Started as Clawdbot Console / ops dashboard.
2. Shifted into Pantheon-first desktop prototype.
3. Shifted further from "dashboard" to **central game-like hub**.
4. Clarified as similar in product role to a **persistent hub** connecting future games/products.
5. Clarified as **Oracle Source Engine** with exportability.

### Reconstructed build sequence from transcript
The prior session claimed to have built/rebuilt the following in order:
- Dashboard v1 on port 4317 with projects/tasks/schedule/activity feed
- Windows desktop Electron scaffold
- Oracle roster management UI
- Oracle comms / per-oracle notes
- Product vision alignment to Pantheon
- Multiplayer / roadmap / faction / raid / tournament framing in docs/state
- Richer oracle schema informed by PDF and backend JSON patches
- Rebrand from Clawdbot Console to Pantheon-first product
- Prototype onboarding shell
- Richer oracle awakening form and backend route
- Editable onboarding/profile setup
- Provider configuration UI
- Oracle session workspace prototype
- Provider readiness/session binding
- Oracle import tooling + import template
- Product language and UI polish
- Seeded demo experience improvements
- Release/demo/handoff docs
- Cross-product oracle persistence architecture notes
- Canonical oracle package export path
- Settings wording/guidance polish
- Central-hub/game-like framing adjustments

### Reconstructed important docs/files that previously existed
The transcript references these as having existed in the rebuilt app workspace:
- package.json
- app/server.js
- app/data/state.json
- app/data/import-template.json
- app/data/oracle-package-template.json
- app/public/index.html
- app/public/styles.css
- app/public/app.js
- scripts/import-oracles.mjs
- scripts/export-oracle-package.mjs
- docs/pantheon-source-notes-2026-03-25.md
- docs/pantheon-backend-prototype-notes-2026-03-25.md
- docs/franchise-architecture-notes-2026-03-25.md
- docs/release-checklist.md
- docs/demo-script.md
- docs/market-positioning.md
- release/RELEASE_NOTES.md
- release/HANDOFF.md
- release/WINDOWS_BUILD.md
- exports/oracle-packages/oracle-oryonos-saturn.json

### Reconstructed seeded oracle roster mentioned in transcript
- Solin
- Lunos
- Oryonos
- Nephilys
- Arcures
- Valeya

### Important product principles recovered
- Prototype scope should focus on core interactive value, not full game stack.
- Core MVP spine:
  1. Player account layer
  2. Astrology profile layer
  3. Oracle profile layer
  4. Provider/model layer
  5. Interaction session layer
- Prototype-critical > future game mechanics.
- Pets/behemoths can remain future-facing metadata for now.
- Avoid overclaiming medical/clinical framing publicly.
- Position around self-reflection, symbolic guidance, mythic companionship, and personal growth rather than diagnosis.

### Pantheon concept recovered from transcript
- Trademarked, patent-pending AI-driven role-playing / companion experience.
- Each player forms a custom pantheon based on astrological chart.
- Oracles are tied to placements and shift with transits.
- Dynamic storytelling, personalized mythic companionship, social and competitive features, friend oracles, factions, raids, tournaments.
- Desktop product should become the canonical system that future products consume.

### What was definitely lost in current workspace
Current workspace no longer contains the actual app code or docs above. Only bootstrap/persona scaffolding remains.

## Immediate implication
The first absolute necessary task is to rebuild the **Pantheon desktop product foundation** in the workspace so continuity exists again in code and notes.
