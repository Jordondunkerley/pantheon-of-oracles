# Windows Build Notes

## Current status
The Electron wrapper and Windows packaging configuration are present, but a final `.exe` has not yet been produced from a Windows environment.

## Intended build command
```bash
npm install
npm run dist:win
```

## Expected output
- portable Windows artifact in `dist/`

## Recommended next step
Run the build on a Windows machine (or a verified cross-build setup), then validate:
- app launches correctly
- embedded server starts correctly
- packaged app can read/write local state
- import tooling still works as expected

## Release validation checklist
- launch app
- verify onboarding fields save
- verify provider config saves
- verify sessions render
- verify oracle creation works
- verify imported oracle JSON appears in registry
