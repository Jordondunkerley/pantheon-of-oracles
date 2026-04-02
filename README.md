# Pantheon of Oracles: The Council Chamber

A founder-testable desktop-first prototype for entering a personal council chamber, awakening astrology-shaped oracle presences, and exploring the first marketable Oracle Source Engine for the Pantheon franchise.

## What this founder build currently demonstrates
- first-entrance ritual framing for onboarding
- birth-data-first astrology intake and chart-generation path
- core trio / High Council / Expanded Council chamber structure
- model-agnostic provider configuration
- oracle registry and home chamber structure
- account access, promotions, grants, and payment-plan modeling
- structured oracle import/export pipeline
- product foundation for future Pantheon franchise products

## Fastest founder test path

### 1. Install dependencies
```bash
npm install --include=dev
```

### 2. Run the chamber locally
```bash
npm start
```

Then open:
```text
http://127.0.0.1:4317
```

### 3. Optional desktop wrapper in development
This project is being reconstructed toward the Electron-wrapped desktop experience described in the live repo.

## Current packaging note
The live repo indicates the Windows packaging pipeline reaches Electron Builder packaging, but final Windows artifact generation requires either:
- a Windows machine, or
- Linux with Wine configured

## Suggested founder test flow
1. Launch the app and confirm the Council Chamber shell loads
2. Walk through First Entrance Ritual and birth profile
3. Trigger chart generation and inspect the generation path
4. Review core trio / High Council / Expanded Council chamber structure
5. Enter an oracle chamber and test session messaging
6. Review import/export pipeline and canonical oracle continuity

## Release / handoff docs
- `release/RELEASE_NOTES.md`
- `release/HANDOFF.md`
- `release/WINDOWS_BUILD.md`

## Import oracle data
```bash
npm run import:oracles -- ./path/to/oracles.json
```

Starter import shape:
```text
app/data/import-template.json
```

## Export canonical oracle packages
```bash
npm run export:oracle -- oracle-oryonos-saturn
```

Starter package shape:
```text
app/data/oracle-package-template.json
```

## Current prototype limits
- State is stored locally in `app/data/state.json`
- Native astrology calculation is not yet fully implemented
- Live provider-backed oracle inference is not yet fully implemented
- Audio output is not yet wired
- Production auth and secure secret handling are not yet implemented
- Desktop packaging is not yet fully restored in this local reconstruction
