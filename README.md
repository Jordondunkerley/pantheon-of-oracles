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
- A scheduled GitHub Action (`.github/workflows/autonomous-builder.yml`) runs hourly to keep the Pantheon of Oracles build loop active without manual prompting and now restores a cache of `autonomous/state.json` so patch digests persist across runs.
- The action executes `python scripts/autonomous_builder.py --workflow-mode --only-on-change --write-summary --write-outputs --validate-patches --require-patches`, which ingests the GPT patch files, records their digests, validates metadata, and produces an action plan using OpenAI (if `OPENAI_API_KEY` is provided as a repo secret). Patch discovery is glob-driven (`--patch-glob`), so new patch drops are picked up automatically.
- Reports are saved to `autonomous/outputs` during the run and uploaded as build artifacts; a local run writes to `autonomous/reports` for quick inspection. Each run also emits a structured JSON artifact (`last_report.json`) containing digests, change flags, and parsed tasks for downstream automation. GitHub Action runs also write a concise summary to the workflow run page when `--write-summary` is enabled.
- GitHub Actions runs can also export run status, reasons, repository metadata (branch, commit, dirty flag), discovered patch digests, detected changes, and the generated report path as step outputs by adding `--write-outputs`, enabling downstream steps to branch on builder health.
- Reports now include repository metadata (branch, commit, dirty flag) in both the markdown and JSON outputs, and the GitHub Actions step summary echoes the same context so operators can trace each plan back to a specific checkout.
- Each report and JSON artifact carries a run status (`ok`, `warning`, `error`, or `skipped`) with a reason, and the GitHub Actions step summary mirrors the status so downstream automation can react to degraded runs.
- Reliability helpers capture warnings (for example, missing `OPENAI_API_KEY` or Supabase connectivity problems) in the report and GitHub Actions step summary so scheduled runs stay visible even when optional services are unavailable.
- Add `--fail-on-warnings` when you want the builder (including watch mode) to exit non-zero anytime warnings are produced, such as OpenAI credential gaps, Supabase sync failures, or smoke-test issues.
- Optional Supabase seeding (`--sync-supabase`) and FastAPI smoke tests (`--smoke-tests --smoke-base-url <url>`) can be enabled to validate Supabase rows and API health alongside the planning report.
- Add `--validate-patches` to capture JSON/metadata validation results in both the markdown and JSON reports; validation warnings also surface in the GitHub Actions step summary so malformed patch drops are visible without manual inspection.
- Combine `--validate-patches` with `--fail-on-validation-errors` when you want the builder to exit non-zero if malformed patch files are detected. Use `--require-patches` to fail fast when the expected GPT patch files are missing for the configured glob.
- The builder now tracks patch digests between runs, highlights file changes, and can stay on continuously with `--watch --interval <seconds>` to keep monitoring the patch files and regenerating reports whenever they change.
- Reduce noise in long-running sessions by combining `--watch` with `--only-on-change` to skip regenerating reports when no patch digests shift after the initial baseline.
- Optional Supabase syncing (`--sync-supabase`) will upsert oracle definitions from the discovered patch files into your Supabase project when `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are provided.
- To test locally: `pip install -r requirements.txt && python scripts/autonomous_builder.py --preview-limit 500`.
