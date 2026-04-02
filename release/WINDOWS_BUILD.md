# Windows Build Notes

## Restored packaging shape
The local reconstruction now includes:
- `electron/main.js`
- `npm run desktop`
- `npm run dist:win`
- Electron Builder config in `package.json`

## Expected packaging path
```bash
npm install --include=dev
npm run dist:win
```

## Current packaging note
The live repo README indicates Windows packaging reaches Electron Builder packaging successfully, but final packaging on Linux requires `wine`.

So final founder-testable Windows artifact generation should be run either:
- on a Windows machine, or
- on a Linux host with Wine configured for Electron Builder

## Validation still needed
- dependency install
- local desktop launch test
- packaging test
- icon/assets parity if present in the live repo
