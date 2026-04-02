# Canonical Pantheon Schema

## Purpose
This schema defines the source-of-truth structure for the first Pantheon of Oracles product and future cross-product oracle persistence.

## MVP spine
1. Current user profile
2. Astrology profile
3. Oracle registry
4. Provider/model layer
5. Interaction sessions
6. Oracle package export surface

## Design rule
Prototype-critical fields come first. Future game systems remain hooks, not blockers.

## Canonical oracle shape
### Identity
- oracle_id
- oracle_name
- title
- archetype
- voice
- mission
- notes

### Astrology
- ruling_planet
- dominant_sign
- house_placement
- aspects[]
- transit_modifiers[]

### Faction / role
- faction
- planetary_faction
- role

### Visual / game-facing
- weapon
- color_scheme
- spirit_animal
- silhouette
- combat_style

### Guidance / relational
- guidance_style
- relationship_mode
- session hooks

## Cross-product rule
Every oracle should be exportable as a canonical package consumable by:
- core desktop hub
- future mobile app
- Pantheon of Oracles: Clash
- future retro/2D test products

## Recovery note
This schema is reconstructed from transcript evidence and should be refined further as backend patch files are reintroduced.