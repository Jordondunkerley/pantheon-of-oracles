# Pantheon Import / Export Architecture

## Purpose
Restore the source-engine behavior described in the transcript: the desktop Pantheon product should act as the canonical oracle system that future products can consume.

## Import path
- `app/data/import-template.json` defines baseline structure
- `scripts/import-oracles.mjs` imports user profile, astrology profile, and oracle records into live state
- imported oracles automatically receive chamber sessions

## Export path
- `scripts/export-oracle-package.mjs <oracle_id>` exports a canonical oracle package
- output location: `exports/oracle-packages/<oracle_id>.json`

## Design intent
This is the bridge between:
- Pantheon desktop hub
- future mobile product
- Pantheon of Oracles: Clash
- future retro/2D prototypes

## Recovery note
This layer was restored because the transcript clearly established cross-product oracle persistence as a core architectural rule.