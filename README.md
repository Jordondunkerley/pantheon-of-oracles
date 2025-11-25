# Pantheon of Oracles API

This repository powers the multiplayer astrology-based game experience across Discord, GPT, and future platforms.

## 🚀 Release planning

See [`docs/release-plan.md`](docs/release-plan.md) for milestone goals (Alpha → GA), deliverables per stage (UI/UX, matchmaking, monetization, accessibility/localization, store compliance), and the QA strategy that gates each phase.

## 🛰 GPT API Router

A new backend service has been added for full cross-platform command execution between ChatGPT and your multiplayer system.

See [`Pantheon API to GPT Router/READMEAPIGPT.md`](Pantheon%20API%20to%20GPT%20Router/READMEAPIGPT.md) for:
- API endpoint list (register, login, chart upload, create oracle, battle, raids, rituals, Codex entry)
- JWT authentication guide
- Render deployment setup
- Token usage examples for secure GPT integration

This allows players to fully participate via either Discord or GPT—and keeps progress synced across both worlds.

---

**Main project files** remain in this repo’s root for bot, logic, and command structure.

