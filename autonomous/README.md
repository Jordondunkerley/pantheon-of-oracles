# Autonomous Builder

This directory contains support files for the Pantheon of Oracles autonomous build loop. The goal is to let a scheduled process continually review the GPT patch files and produce the next set of prioritized actions without manual prompting.

Files:
- `outputs/`: workflow run outputs (reports uploaded as artifacts; not committed).
- `reports/`: optional local reports if you run the builder manually.
- `state.json`: lightweight digest cache used to flag when patch files have changed.
- `last_report.md` / `last_report.json`: most recent human-readable and machine-readable plans. JSON includes digests, change flags, and parsed tasks for downstream automation or schedulers.

The automation is driven by `scripts/autonomous_builder.py` and the GitHub Action at `.github/workflows/autonomous-builder.yml`.

Usage examples:
- One-off local plan: `python scripts/autonomous_builder.py --preview-limit 500`
- Continuous monitor: `python scripts/autonomous_builder.py --watch --interval 600`
- Override patch discovery (defaults to `Patches *.JSON`): `python scripts/autonomous_builder.py --patch-glob "Patches *.JSON"`
- Sync oracle definitions into Supabase (requires `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`): `python scripts/autonomous_builder.py --sync-supabase`
