# Pantheon of Oracles API

This repository powers the multiplayer astrology-based game experience across Discord, GPT, and future platforms.

## 🛰 GPT API Router

A new backend service has been added for full cross-platform command execution between ChatGPT and your multiplayer system.

See [`Pantheon API to GPT Router/READMEAPIGPT.md`](Pantheon%20API%20to%20GPT%20Router/READMEAPIGPT.md) for:
- API endpoint list (register, login, chart upload, create oracle, battle, raids, rituals, Codex entry)
- JWT authentication guide
- Render deployment setup
- Token usage examples for secure GPT integration

This allows players to fully participate via either Discord or GPT—and keeps progress synced across both worlds.

### GPT Model Switcher

Set the `PANTHEON_GPT_MODEL` environment variable to select which OpenAI model the router will use (for example, `gpt-5` or `gpt-4o-mini`).
If not set, the service defaults to `gpt-4o-mini`. This enables rapid upgrades to new GPT releases without code changes.

---

**Main project files** remain in this repo’s root for bot, logic, and command structure.

