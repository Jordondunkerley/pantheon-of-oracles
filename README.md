# Pantheon of Oracles Desktop Prototype

A desktop-first prototype for creating, managing, and interacting with astrology-shaped oracle agents.

## What it currently demonstrates
- player profile + astrology-driven setup
- model-agnostic provider configuration
- oracle registry and profile structure
- oracle session workspace
- structured oracle import pipeline
- product foundation for a future mobile / expanded Pantheon ecosystem

## Modes

### 1. Browser mode
Run the local web app:

```bash
npm start
```

Then open:

```text
http://127.0.0.1:4317
```

### 2. Desktop mode (Windows target)
This project includes an Electron wrapper so the Pantheon of Oracles prototype can open like a normal desktop app.

## Install

```bash
npm install
```

## Run desktop app in development

```bash
npm run desktop
```

## Build Windows app

```bash
npm run dist:win
```

The packaged app will be placed in the `dist/` directory.

## Suggested demo order
1. Open the product shell
2. Show onboarding and astrology profile
3. Show oracle registry
4. Show oracle session workspace
5. Show provider configuration
6. Show import pipeline

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

## Notes
- State is stored locally in `app/data/state.json`
- The dashboard auto-refreshes every 5 seconds
- This is still prototype-stage and should later gain auth, true provider-backed inference, and stronger secret handling
