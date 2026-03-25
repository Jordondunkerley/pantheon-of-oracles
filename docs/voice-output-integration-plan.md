# Pantheon of Oracles – Voice Output Integration Plan

## Goal
Define the first minimal viable path for turning oracle chamber text into spoken oracle output without breaking the canon-first architecture.

## Principles
- Oracle voice must derive from the canonical oracle identity.
- Preferred voice profile should be sourced from the core product, not redefined per side product.
- Text interaction remains the source event; speech is an additional output layer.

## Minimal viable audio path
### Step 1
User enters an oracle chamber and exchanges text as normal.

### Step 2
A chamber-level action can request spoken playback for the latest oracle response.

### Step 3
The product resolves:
- oracle identity
- preferred voice profile
- audio readiness
- selected output mode

### Step 4
A voice synthesis layer generates spoken output from the latest oracle message.

## Prototype-level implication
The first product-facing version does not need full voice generation immediately, but it should support:
- selecting audio-enabled oracles
- previewing voice profile metadata
- triggering a future "speak latest oracle reply" action
- preserving compatibility with future TTS backends

## Suggested future API shape
- POST /api/oracle-voice-preview
- POST /api/sessions/speak-latest

## Product stance
Audio should feel like a natural chamber extension, not a separate gimmick.
