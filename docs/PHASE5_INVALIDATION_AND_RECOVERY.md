# Phase 5 Invalidation and Recovery

## Decision

The previous Phase 5 visual-slice candidate is **rejected and invalidated** as of 2026-07-27.

The founder directly launched the native build and reviewed the rendered result. The result proved that the custom Windows runtime, scene cooker, Direct3D 12 renderer, generated-content path, animation plumbing, synthesized audio, readback, and automated verification were functional. It did **not** demonstrate production-quality art direction, character presentation, environment composition, material authorship, lighting, UI, animation, or a credible AAA visual benchmark.

Phase 5 therefore did not pass its mandatory founder visual-approval gate. No prior green build, numerical image threshold, rendered-pixel count, or performance result overrides that rejection.

## What remains valid

The following work remains useful infrastructure and is not reverted by this decision:

- native Win32 runtime ownership,
- Direct3D 12 device, swap-chain, command, resource, synchronization, and capture systems,
- DXC shader packaging,
- HDR render targets and tone-mapping path,
- generated-content and scene-cooking contracts,
- deterministic gameplay, saves, input, replay, and collision,
- GPU timing, memory, readback, WARP, resize, and validation evidence,
- project-owned procedural geometry, materials, animation data, and synthesized audio foundations.

These systems constitute an early custom game engine and runtime foundation. They are not themselves visual quality.

## What is explicitly invalidated

The following claims are prohibited:

- Phase 5 complete,
- Phase 5 visually approved,
- AAA visual slice delivered,
- production-quality character delivered,
- production-quality environment delivered,
- production-quality art direction delivered,
- automated image thresholds standing in for visual judgment.

The rejected output is classified as a **technical graybox with experimental rendering features**.

## Root causes

The rejected candidate failed because it attempted to derive visual quality from systems rather than from directed visual authorship:

1. The scene was an arena assembled from sparse primitive-scale elements rather than a composed place.
2. The character was a block-based articulated test rig without professional human proportion, silhouette, garment construction, or surface detail.
3. Generated textures created uniform procedural noise instead of material identity and geological structure.
4. Lighting, fog, bloom, and exposure were applied globally rather than staged to direct attention.
5. The objective was represented by an oversized emissive marker and a dominant debug-like banner.
6. The camera recorded gameplay but did not stage a hero reveal, preserve strong silhouettes, or establish cinematic scale.
7. Numerical image tests measured non-black pixels, luminance, edges, and highlights, but did not measure taste, believability, composition, or emotional impact.

## Recovery law

Phase 5 restarts around one tightly art-directed, founder-reviewable hero sequence. The replacement must be built from explicit visual references and project-owned content. It must not attempt to improve the rejected arena incrementally until it becomes acceptable.

The recovery sequence is defined in `PHASE5_HERO_SEQUENCE_ART_DIRECTION.md` and governed by `PHASE5_SCREENSHOT_APPROVAL_GATE.md`.

No Phase 6 work may begin before the replacement sequence passes founder direct play and screenshot approval.
