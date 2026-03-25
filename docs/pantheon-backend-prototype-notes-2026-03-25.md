# Pantheon Backend Prototype Notes (2026-03-25)

## Source files reviewed
- Player_Account_Template JSON
- Oracle_Profile_Template JSON
- Astrology_Profile_Template JSON
- Patches 1-50 (partial read)
- Patches 51-53

## High-confidence prototype-critical systems

### 1. Player Account Layer
Must support:
- player_id / username / email
- birth data and profile metadata
- platform links (discord/openai/youtube, future extensible)
- faction alignment
- access tier / founder status / season status
- oracle ownership
- token balances
- gameplay stats
- sync/status flags
- preferences and notification settings

### 2. Astrology Profile Layer
Must support:
- planets and major bodies
- angles
- houses
- interceptions / duplications
- motion + stationary flags
- decans
- degree marks (future-friendly)

### 3. Oracle Profile Layer
Must support:
- oracle_id / oracle_name / archetype / oracle_type
- astrology subprofile
- faction affiliation
- level / tier / ascended rank / form
- council type / ruler flags / anointed ruler
- voice/tone overlays
- gameplay unlock booleans
- visual attributes
- weapons
- future unit hooks (pet, disciple, legion, behemoth, etc.)

### 4. Prototype Scope Decision
For the first marketable software prototype, prioritize:
- onboarding / account creation flow
- astrology profile ingestion
- oracle registry + oracle workspace
- LLM/provider settings and model-agnostic design
- interaction layer between user and oracle
- transit awareness placeholders

Deprioritize for prototype:
- full combat implementation
- full multiplayer execution
- pets / behemoths / leviathans / legions
- throne worlds / descendants / full expansion packs

### 5. Patch-derived architectural truths
- The full system is enormous and seasonal.
- Many gameplay systems should be treated as later expansion hooks.
- Current prototype should focus on: personal pantheon, interaction, astrology-aware state, and future provider flexibility.
- Patch 51 suggests storyline progression replaces many old level-gated unlock assumptions.
- Patch 52 adds endgame progression concepts but should remain future-facing metadata for now.
- Patch 53 introduces exploration/adventure concepts; not needed for prototype core.

## Recommendation
Restructure the dashboard/app state into these top-level modules:
- product
- currentUser
- llmProviders
- astrologyProfile
- oracles
- interactionSessions
- tasks/activity/schedule
- futureSystems
