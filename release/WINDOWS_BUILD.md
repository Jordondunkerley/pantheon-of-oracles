# Windows Build Notes

## Current status
The Electron wrapper and Windows packaging configuration are present, but a final `.exe` has not yet been produced from a Windows environment.

## Current verified state
- `npm install --include=dev` succeeds
- `npm start` succeeds
- `npm run dist:win` reaches Electron Builder packaging successfully
- final artifact generation on this Linux host is blocked by missing `wine`

So the remaining blocker is no longer broken package scripts. It is specifically the Windows packaging environment.

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
