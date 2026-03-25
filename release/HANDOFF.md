# Pantheon of Oracles: The Council Chamber – Handoff Guide

## What this is
A founder-testable desktop-first product prototype for Pantheon of Oracles: The Council Chamber.

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
- native chart generation is still prototype-backed rather than fully implemented
- intended as a founder-testable prototype / pre-release product shell

## Best demo path
1. Open product shell
2. Show onboarding
3. Show astrology profile
4. Show oracle registry
5. Show seeded oracle sessions
6. Show provider setup
7. Show import pipeline
