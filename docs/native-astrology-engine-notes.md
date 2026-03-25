# Native Astrology Engine Notes

## Product direction
The first marketable Pantheon product should ultimately generate charts internally from birth data rather than requiring users to bring precomputed charts.

## Immediate structure
The current product now frames chart generation as a workflow:
1. collect birth data
2. generate chart internally
3. validate when needed against trusted references
4. build astrology profile
5. awaken oracle council

## Design principle
Validation sources should support confidence, not replace the core product's intelligence.

## Why native matters
- less user friction
- cleaner onboarding
- stronger product identity
- less dependence on external tools
- better long-term reliability

## Near-term build implication
The product should be architected so a future native astrology module can plug into `/api/chart/generate` without changing the user-facing flow.
