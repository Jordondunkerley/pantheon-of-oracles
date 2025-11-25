# Immersive Mode Technical Plan

## Tech Stack and Integration Approach
- **XR runtimes and engines**: Use **Unity with OpenXR** for cross-platform VR, plus **ARCore/ARKit** plugins for mobile AR extensions. Unity XR Interaction Toolkit for input abstraction and locomotion providers.
- **Backend integration**: Maintain the existing HTTP/WS API surface; add a lightweight **gRPC Gateway** for low-latency event streams (ritual state, raid phases). Use **Protobuf contracts** shared with backend for deterministic state sync. Auth via existing token flow; store device entitlement and session metadata in Supabase.
- **Content distribution**: Asset bundles hosted on current CDN/Supabase storage; signed download URLs provided by backend. Incremental patching via Unity Addressables.
- **Build targets**: PC VR (OpenXR), Quest (OpenXR/Android), and optional AR (ARCore/ARKit) sharing core logic through scriptable render pipeline (URP) profiles.

## Interaction Models
- **Oracle rituals**: Guided sequences with spatialized audio, haptic pulses, and gesture gates (hand-tracked or controller). State machine synchronized through backend events; local prediction for minor steps to hide latency.
- **Raids**: 4–8 player co-op. Roles defined by loadouts; synchronized boss phases and telegraphs via snapshot + delta updates. Voice handled by platform SDK; text chat over existing WS.
- **Codex exploration**: 3D library with diegetic UI (scrolls, pedestals). Search and tagging issued to backend; entries streamed as rich text + media. Persistent bookmarks synced to player profile.

## Asset and Content Pipeline
- **Source of truth**: Narrative/design assets in Git; 3D assets in DCC tools (Blender/Maya) exported to **glTF/FBX** then processed by Unity import pipeline.
- **Addressables**: Group by feature (rituals, raids, codex). Use texture atlasing and mesh LODs; generate lightmaps and occlusion data during CI builds.
- **CI/CD**: Automated asset validation (polycount, texture sizes), automated bundle builds per platform, upload to storage with manifest versioning. Content authors push to branch; build agents produce signed bundles.
- **Localization**: String tables maintained alongside JSON lore files; baked into asset bundles with fallback to English.

## Performance Targets
- **Frame time**: 90 FPS for PC VR (11.1 ms), 72–90 FPS for Quest (13.8–11.1 ms). GPU frame budget enforced via Unity Profiler CI thresholds.
- **Frame stability**: Motion-to-photon latency < 20 ms on PC VR; under 40 ms on standalone. CPU main thread < 5 ms, render thread < 6 ms for complex scenes.
- **Memory**: < 2.5 GB on Quest; < 5 GB on PC VR. Streaming-enabled scenes and pooled object reuse.

## Input Schemes
- **Controllers**: Default XR ITK mappings (teleport + smooth locomotion, snap/smooth turn, context-sensitive interact). Haptics tuned per ritual step and raid telegraph.
- **Hand tracking**: Pinch + grab gestures for Codex; palm-up menu, ritual gestures with tolerances. Use OpenXR hand tracking extension with fallback to controllers.
- **Accessibility**: Seated mode, left-handed bindings, remappable inputs, subtitles/visual cues for all audio signals.

## Comfort and Safety
- **Locomotion**: Offer teleport, dash, and optional smooth locomotion with vignette + counter-lean options. Default comfort mode enabled for new users.
- **Playspace**: Guardian checks and boundary warnings surfaced; pause on boundary breach signals.
- **Content safety**: Intensity sliders for audio/visual effects; photosensitivity-safe shaders and optional reduced-particle mode. Age-gating hooks integrated with backend policy flags.
- **Session health**: Enforce breaks (soft reminders), quick-reset for camera origin, and panic button that freezes gameplay and opens system menu.

## Networking and Sync Details
- **Authoritative backend** for ritual/raid state; clients run interpolated playback with server reconciliation. Input throttling + client-side rate limiting to prevent spam.
- **Matchmaking**: Backend orchestrates lobbies; Unity client consumes WS/gRPC streams. Host migration not required (server authoritative).
- **Telemetry**: Perf counters (FPS, frame timing, dropped frames) and comfort flags sent to analytics endpoint for live ops.

## Open Questions / Next Steps
- Validate backend capacity for gRPC streaming; confirm Supabase latency budget.
- Define Protobuf schemas for ritual/raid events and Codex search results.
- Build prototype scene to benchmark performance budgets on target devices.
