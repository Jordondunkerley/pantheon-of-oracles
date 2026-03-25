# Pantheon of Oracles – Astrology Chart Generation Plan

## Product requirement
The product should be able to generate a user's astrology chart from birth data directly.
Users should not be forced to provide a precomputed chart.

## User experience goal
The smooth path should be:
1. enter birth date
2. enter birth time
3. enter birth location
4. system generates chart
5. system awakens the pantheon

Importing a chart should remain optional, not mandatory.

## Canon alignment
This matches the Pantheon backend direction where astrology profile generation is core to onboarding and Oracle creation.

## External-source guidance from user
Preferred external sources for comparison / reference:
- Astro-Seek
- Startek by Cam White

## Recommended architecture
### Tier 1 – native generation
Best long-term solution:
- calculate chart directly from birth data inside the product/backend
- avoid dependency on fragile scraping or manual uploads

### Tier 2 – comparison / validation path
If needed during prototyping:
- compare outputs against reputable sources like Astro-Seek
- use trusted sources as validation references while refining native generation

### Tier 3 – fallback import
Allow optional import/upload when users already have a chart.
This should not be the primary flow.

## Product principle
The system should seek the most accurate chart generation path available, but the user experience should remain streamlined and low-friction.

## Immediate implication for current prototype
The onboarding/product shell should start clearly indicating:
- birth data is the intended primary input
- chart generation is expected to happen inside the product
- external sources are validation or fallback references, not the ideal long-term dependency
