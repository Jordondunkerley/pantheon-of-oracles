# Access Model Restoration

## Why this pass mattered
The live repo README explicitly mentions account access, promotions, grants, and payment-plan modeling. The local reconstruction still treated this area too loosely.

## Restored in this pass
- account status field
- structured promotions with status/effect
- structured grants with status
- richer payment-plan modeling with entitlements
- dedicated UI surfaces for promotions/grants and payment plans

## Product effect
This pushes the build closer to a believable founder-testable product rather than a generic prototype shell.

## Next likely priorities
1. restore deeper chamber presentation / oracle room detail
2. restore desktop/Electron wrapper parity
3. compare more live repo files directly against local reconstruction