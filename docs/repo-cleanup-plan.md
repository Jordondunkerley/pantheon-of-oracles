# Pantheon of Oracles Repo Cleanup Plan

## Goal
Prepare the Pantheon of Oracles repository for public/product distribution without publishing private workspace or backend-source material.

## Keep in public product repo
- `app/` product runtime and templates
- `electron/` desktop wrapper
- `scripts/` import/export utilities that support the sellable product
- `README.md`
- `package.json`
- `package-lock.json`
- selected `docs/` useful for product/release/testing context
- selected public-safe exported oracle package examples if desired
- `release/` docs if intentionally force-added and public-safe

## Remove from public product repo
- `.openclaw/`
- `AGENTS.md`
- `HEARTBEAT.md`
- `IDENTITY.md`
- `MEMORY.md`
- `SOUL.md`
- `TOOLS.md`
- `USER.md`
- `memory/`
- raw backend/source files from `/home/node/.openclaw/media/inbound/`

## Important rule
The updated backend patch/template files should inform product implementation, but should not be shipped as downloadable public repo assets if they are private source canon.

## Next steps
1. Remove private workspace files from git tracking.
2. Confirm public repo structure.
3. Add remote once Jordon provides Pantheon of Oracles repo URL.
4. Push cleaned product repo only.
