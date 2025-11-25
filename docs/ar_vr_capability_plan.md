# Pantheon of Oracles AR/VR Capability Plan

This plan outlines how to deliver immersive AR and VR experiences that extend the existing backend/game systems to SteamVR (PC) and ARCore/ARKit (mobile). It aligns with patch directives for rituals/raids/divination while preserving server authority and cross-platform account linking.

## Goals
- Provide spatial rituals, raids, and Codex exploration with consistent game rules across flat/mobile/VR clients.
- Use a single backend (Supabase + Python services) with deterministic server authority for combat/ritual outcomes.
- Ensure performance, comfort, and safety standards for VR; battery/thermal-conscious AR overlays on mobile.
- Ship via Steam (OpenXR/SteamVR) and mobile stores (ARCore/ARKit) with shared progression and cosmetics.

## Tech Stack & Client Architecture
- **Engine**: Unity (OpenXR) for VR/PC and AR Foundation (ARCore/ARKit) for mobile AR to maximize shared assets and code.
- **XR API**: OpenXR abstraction; SteamVR runtime on PC; AR Foundation for AR plane/anchor handling, occlusion, light estimation.
- **Networking**: Reuse existing REST/WebSocket contracts; deterministic simulation on server for combat/ritual resolution; clients submit intents.
- **SDK bridges**: gRPC/WebSocket bindings to Python backend; platform SDKs for entitlement (Steamworks), IAP (Apple/Google), and presence (Discord overlay optional on PC).
- **Asset pipeline**: Shared URP asset setup with LODs; addressables backed by CDN; patch-aware versioning per milestone.

## Interaction Models
- **Rituals**: Spatial circles, sigils, and altar objects anchored to real world (AR) or virtual temple (VR); gesture/click/pose-based rune tracing with haptics/audio feedback.
- **Raids/Battles**: Board-style arena with turn/phase overlays; gaze/controller targeting (VR) and tap/drag targeting (AR); quick-time channeling segments consistent with server turn timers.
- **Codex Exploration**: Spatial shelves and constellation viewers; hand ray/pinch/laser pointers in VR; tap/drag + AR anchors for mobile; voice narration optional.
- **UI/UX**: Diegetic panels for stats/logs; comfort-first locomotion (teleport + snap turn), vignette options; mobile AR uses minimal intrusive chrome.

## Performance, Comfort, and Safety
- **Targets**: 72–90 FPS on VR (SteamVR baseline), 30–60 FPS on mobile AR with dynamic resolution and foveated rendering where available.
- **Comfort**: Snap turn defaults, teleport locomotion, seated/standing modes, vignette during motion, motion-sickness QA checklist, guardian checks (SteamVR) and AR session safety prompts.
- **Thermal/Battery (AR)**: Limit session length, throttle particle density, adaptive quality based on device metrics.
- **Accessibility**: High-contrast UI options, subtitles for chants/narration, configurable gesture sensitivity, color-blind safe sigils.
- **Safety/Moderation**: Server-authoritative outcomes; anti-cheat telemetry (pose/velocity anomalies), secure intent signing; rate limits on matchmaking and ritual submissions.

## Backend & Services Alignment
- **Session layer**: WebSocket rooms for raids/rituals with reconnection tokens; state snapshots for VR/AR resume; server tick alignment for deterministic outcomes.
- **Content services**: Endpoint for ritual layouts (anchors, sigils, audio cues); encounter generator extended with spatial metadata (placement hints, VFX tiers).
- **Progression**: Shared oracle stats/inventory; VR/AR-specific cosmetics tracked in inventory; cross-platform unlock flags and receipts validation (Steam wallet/IAP).
- **Telemetry**: Frame time, reprojection %, motion sickness aborts, crash dumps; funnel events for ritual completion, raid success, Codex interactions.

## Content & Asset Pipeline
- **Authoring**: Use Unity scene templates for ritual rooms/AR prefabs; scriptable objects for encounters/spells; patch-aware versioning tied to content IDs in Supabase.
- **Build artifacts**: Addressable bundles per platform (PCVR high, Mobile AR medium/low); CDN + signed manifest; cache-busting via semantic versions.
- **Live-ops**: Toggleable rituals/raids via feature flags; schedule-based content drops with prefetch; analytics-driven balancing loops.
- **Localization**: Subtitles/VO triggers keyed to localization files; asset variants for text meshes; RTL support in diegetic panels.

## Testing & QA Strategy
- **Automation**: Playmode tests for gesture recognition, anchor stability, and network intent flows; unit tests for deterministic combat resolution.
- **Device matrix**: SteamVR (Index, Vive, Quest via Link), Windows MR; Android ARCore tiered devices; iOS ARKit (A12+). Thermal/profiling passes on mobile.
- **Soak/Load**: Multi-hour VR soak with motion profiles; load tests on WebSocket sessions with synthetic clients; CDN fetch validation per platform.
- **Compliance**: Store platform checks (SteamVR entitlement, Apple/Google AR permissions, privacy prompts, comfort warnings), seizure warnings, data privacy review.

## Immediate Next Actions
- Define WebSocket message schemas for VR/AR intents (gesture events, anchor placements) and deterministic resolution paths.
- Extend encounter/ritual content schema with spatial metadata and VFX tiers; draft Supabase migration outline.
- Establish Unity project boilerplate with OpenXR + AR Foundation profiles; set up addressables and CI build jobs for PCVR/Android/iOS.
- Prototype a ritual room and AR altar flow using existing backend endpoints for oracle state and ritual resolution.
- Add telemetry events (frame time, reprojection, nausea exits) to analytics schema and client contracts.
