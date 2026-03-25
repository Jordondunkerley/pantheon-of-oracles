# Pantheon Franchise Architecture Notes (2026-03-25)

## Core rule
Oracles must persist across all Pantheon products.

That means the desktop app, future mobile app, and future games should all derive from the same **core oracle identity system**, rather than creating disconnected versions of the same oracle.

## Implication
The core Pantheon system should become the canonical source for:
- oracle identity
- astrology structure
- voice/personality profile
- visual design metadata
- combat style metadata
- progression/state where appropriate
- future export/sync format

## New branch concept
### Pantheon of Oracles: Clash
A fighting-game branch of the franchise.

Potential versions:
1. Full 3D / Soulcalibur-style aspiration
2. Simpler 2D prototype first
3. Even simpler Game Boy-like version for systems testing and cross-connectivity validation

## Strategic recommendation
Do **not** build Clash as a separate identity model.
Instead, define the desktop/core app as the **Oracle Source Engine** and let side products consume exports from it.

## Suggested architecture
### Core Pantheon app owns:
- canonical player profile
- canonical astrology profile
- canonical oracle profiles
- oracle voice/profile rules
- visual/combat descriptors
- exportable oracle package format

### Parallel products consume:
- oracle package exports
- shared ids
- shared lore/identity schema
- optionally shared progression data

## Immediate implication for current prototype
Even before building a game, the desktop product should start storing or preparing for:
- combat style
- weapon signature
- silhouette/theme cues
- exportability
- stable oracle ids

This increases future franchise leverage without requiring the whole game now.
