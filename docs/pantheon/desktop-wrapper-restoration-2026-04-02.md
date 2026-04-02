# Desktop Wrapper Restoration

## Why this pass mattered
The live repo README explicitly presents Pantheon of Oracles as a desktop-first founder build with an Electron wrapper and Windows packaging path.

## Restored in this pass
- Electron main entrypoint at `electron/main.js`
- package metadata changed to desktop wrapper entrypoint
- `desktop` script added
- `dist:win` script added
- Electron Builder config scaffold added

## Current limitation
This restores structure and expected repo shape, but dependencies still need installation and build validation in the active environment.

## Product effect
The local reconstruction is now substantially closer to the live repo’s desktop-first identity rather than only a browser-served prototype.