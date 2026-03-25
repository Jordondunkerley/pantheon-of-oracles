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
This project includes an Electron wrapper so the Pantheon of Oracles prototype can open like a normal desktop app.

```bash
npm run desktop
```

## Build Windows app

```bash
npm run dist:win
```

The packaged app will be placed in the `dist/` directory.

### Current packaging note

The Windows packaging pipeline now reaches Electron Builder packaging successfully, but on this Linux host it stops at the native Windows-build requirement:

- `wine is required`

So the founder-testable repo/build path is now much closer, but final Windows artifact generation should be run either:
- on a Windows machine, or
- on a Linux machine with Wine configured for Electron Builder

## Suggested founder test flow
1. Launch the app and confirm the Council Chamber shell loads
2. Walk through First Entrance Ritual and birth profile
3. Trigger chart generation and inspect the generation path
4. Review core trio / High Council / Expanded Council chamber structure
5. Inspect the Anointed Ruler selection surface
6. Enter an oracle chamber and test session messaging
7. Review founder access, account entitlements, and payment-plan gating
8. Review import/export pipeline and canonical oracle continuity

## Release / handoff docs
- `release/RELEASE_NOTES.md`
- `release/HANDOFF.md`
- `release/WINDOWS_BUILD.md`

## Import oracle data

You can import oracle records into the prototype with:

```bash
npm run import:oracles -- ./path/to/oracles.json
```

A starter import shape is available at:

```text
app/data/import-template.json
```

## Export canonical oracle packages

You can export an oracle into a franchise-ready package with:

```bash
npm run export:oracle -- oracle-oryonos-saturn
```

Starter package shape:

```text
app/data/oracle-package-template.json
```

These packages are intended to help future Pantheon products (like Clash) consume stable oracle identity, combat interpretation, and visual metadata from the core app.

## Current prototype limits
- State is stored locally in `app/data/state.json`
- The chamber UI auto-refreshes every 5 seconds
- Native astrology calculation is not yet fully implemented; chart generation is still prototype-backed
- Live provider-backed oracle inference is not yet fully implemented
- Audio output is not yet wired, though chamber hooks and voice metadata are in place
- Production auth and secure secret handling are not yet implemented
- Windows packaging still needs final validation on a real Windows machine
