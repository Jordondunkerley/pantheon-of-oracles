# Clawdbot Console

A desktop-friendly operations dashboard for tracking Clawdbot projects, tasks, schedule, and activity.

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
This project includes an Electron wrapper so the dashboard can open like a normal desktop app.

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

## Notes
- State is stored locally in `app/data/state.json`
- The dashboard auto-refreshes every 5 seconds
- This is v1 and should later gain auth, richer task editing, and background service support
