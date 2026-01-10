# Pantheon of Oracles API

This repository powers the multiplayer astrology-based game experience across Discord, GPT, and future platforms.

## Configuration

Create a `config.env` file (see `config.env.example`) and define the runtime
secrets required by the FastAPI service and Discord bot:

```
API_KEY=...
SUPABASE_URL=...
SUPABASE_SERVICE_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
DISCORD_TOKEN=...
DISCORD_GUILD_ID=...
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-3.5-turbo
RELEASED_PATCHES=base
```

These environment variables are loaded by the applications at startup. Keeping
them out of the codebase prevents accidental exposure of credentials. `RELEASED_PATCHES`
controls which game content patches players can access; by default only `base` content is enabled.

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

## Discord Bot Commands

The Discord bot listens for mentions and also exposes management commands. These
require that the bot has the appropriate permissions in your server.

- `!oracle <name>` – fetch oracle data from the API
- `!create_channel <name>` – create a new text channel
- `!assign_role @user <role>` – give a user a role (creates it if missing)
- `!kick @user [reason]` – remove a user from the server
- `!ban @user [reason]` – ban a user from the server

