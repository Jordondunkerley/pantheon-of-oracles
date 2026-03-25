# Pantheon of Oracles Desktop Prototype

A desktop-first prototype for creating, managing, and interacting with astrology-shaped oracle agents.

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

## Import oracle data

You can import oracle records into the prototype with:

```bash
npm run import:oracles -- ./path/to/oracles.json
```

A starter import shape is available at:

```text
app/data/import-template.json
```

## Notes
- State is stored locally in `app/data/state.json`
- The dashboard auto-refreshes every 5 seconds
- This is still prototype-stage and should later gain auth, true provider-backed inference, and stronger secret handling
