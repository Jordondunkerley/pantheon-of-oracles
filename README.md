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

---

**Main project files** remain in this repo’s root for bot, logic, and command structure.


## 🤖 Autonomous builder loop
- A scheduled GitHub Action (`.github/workflows/autonomous-builder.yml`) runs hourly to keep the Pantheon of Oracles build loop active without manual prompting.
- The action executes `python scripts/autonomous_builder.py --workflow-mode`, which ingests the GPT patch files, records their digests, and produces an action plan using OpenAI (if `OPENAI_API_KEY` is provided as a repo secret). Patch discovery is glob-driven (`--patch-glob`), so new patch drops are picked up automatically.
- Reports are saved to `autonomous/outputs` during the run and uploaded as build artifacts; a local run writes to `autonomous/reports` for quick inspection. Each run also emits a structured JSON artifact (`last_report.json`) containing digests, change flags, and parsed tasks for downstream automation.
- The builder now tracks patch digests between runs, highlights file changes, and can stay on continuously with `--watch --interval <seconds>` to keep monitoring the patch files and regenerating reports whenever they change.
- Optional Supabase syncing (`--sync-supabase`) will upsert oracle definitions from the discovered patch files into your Supabase project when `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are provided.
- To test locally: `pip install -r requirements.txt && python scripts/autonomous_builder.py --preview-limit 500`.
