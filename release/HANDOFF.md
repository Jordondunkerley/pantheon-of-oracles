# Pantheon of Oracles Desktop Prototype – Handoff Guide

## What this is
A desktop-first product prototype for Pantheon of Oracles.

## Primary run modes
### Browser mode
```bash
npm start
```
Open `http://127.0.0.1:4317`

### Desktop mode
```bash
npm install
npm run desktop
```

### Windows packaging target
```bash
npm run dist:win
```

## Oracle import
```bash
npm run import:oracles -- ./path/to/oracles.json
```

Starter schema:
- `app/data/import-template.json`

## Important current limitations
- prototype provider config stores readiness/status, not production-grade secrets
- live oracle inference is not yet wired
- intended as a polished prototype / pre-release product shell

## Best demo path
1. Open product shell
2. Show onboarding
3. Show astrology profile
4. Show oracle registry
5. Show seeded oracle sessions
6. Show provider setup
7. Show import pipeline
