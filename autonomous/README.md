# Autonomous Builder

This directory contains support files for the Pantheon of Oracles autonomous build loop. The goal is to let a scheduled process continually review the GPT patch files and produce the next set of prioritized actions without manual prompting. The GitHub Action caches `autonomous/state.json` so digest comparisons persist across runs, enabling the `--only-on-change` guard to skip redundant reports in CI.

Files:
- `outputs/`: workflow run outputs (reports uploaded as artifacts; not committed).
- `reports/`: optional local reports if you run the builder manually.
- `state.json`: lightweight digest cache used to flag when patch files have changed.
- `last_report.md` / `last_report.json`: most recent human-readable and machine-readable plans. JSON includes digests, change flags, and parsed tasks for downstream automation or schedulers.

The automation is driven by `scripts/autonomous_builder.py` and the GitHub Action at `.github/workflows/autonomous-builder.yml`.

Usage examples:
- One-off local plan: `python scripts/autonomous_builder.py --preview-limit 500`
- Continuous monitor: `python scripts/autonomous_builder.py --watch --interval 600`
- Watch with minimal churn: `python scripts/autonomous_builder.py --watch --interval 600 --only-on-change` (the scheduled workflow also uses `--only-on-change` with a cached digest file so reports only regenerate after patch updates)
- Override patch discovery (defaults to `Patches *.JSON`): `python scripts/autonomous_builder.py --patch-glob "Patches *.JSON"`
- Sync oracle definitions into Supabase (requires `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`): `python scripts/autonomous_builder.py --sync-supabase`
- Run FastAPI smoke tests to verify `/healthz` without manual prompts: `python scripts/autonomous_builder.py --smoke-tests --smoke-base-url http://localhost:8000`
- Write a GitHub Actions step summary: `python scripts/autonomous_builder.py --workflow-mode --write-summary`
- Populate GitHub Actions step outputs (status, reason, repository metadata, patch digests, change list, report path) for downstream jobs: `python scripts/autonomous_builder.py --workflow-mode --write-outputs`
- Validate patch JSON and required metadata, recording results in markdown/JSON outputs: `python scripts/autonomous_builder.py --validate-patches`
- Fail fast on malformed patch files when validating: `python scripts/autonomous_builder.py --validate-patches --fail-on-validation-errors`
- Require patch discovery for the configured glob and exit non-zero otherwise: `python scripts/autonomous_builder.py --require-patches`
- Exit non-zero when any warnings are produced (missing OpenAI credentials, Supabase sync failures, smoke-test errors, etc.): `python scripts/autonomous_builder.py --fail-on-warnings`
- Warnings from missing OpenAI credentials, Supabase sync failures, or smoke-test issues are recorded in the markdown, JSON, and GitHub Actions summaries so the loop keeps running even when optional services are down.
- Each report (markdown + JSON) now includes a run status (`ok`, `warning`, `error`, or `skipped`) and reason, mirrored in GitHub step summaries for downstream automation.
- Repository metadata (branch, commit, dirty flag) is included in the markdown, JSON, and step summary outputs to tie each plan back to a specific checkout.
