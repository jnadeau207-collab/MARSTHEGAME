# ADR 0021: Phase 5 visual-slice architecture

- Status: Implemented candidate; executable evidence required before promotion
- Date: 2026-07-27

## Decision

The Phase 5 Ares Reach visual slice is implemented inside the project-owned C++23, Direct3D 12, HLSL, procedural-content, animation, and audio architecture. No third-party engine, marketplace asset library, imported character, imported environment, or prerecorded soundtrack is introduced.

The native frame graph is:

1. generated-scene shadow depth,
2. HDR linear-light metallic/roughness scene shading,
3. additive project-generated dust particles,
4. temporal history resolve,
5. exposure, bloom, focus treatment, motion treatment, atmospheric integration, and filmic tone mapping into the swap chain,
6. optional GPU readback and visual evidence capture.

## Project-owned content

- deterministic environment cube generation for ambient and reflected light,
- deterministic generated surface textures and material parameters,
- procedural articulated player rig and locomotion state,
- deterministic synthesized Ares Reach music and ambience,
- procedural dust and atmosphere driven by native scene state.

## Runtime evidence

The renderer records CPU frame time, GPU timestamp duration, hitch count, estimated resident GPU bytes, capture checksum, meaningful-pixel count, luminance distribution, and edge-energy evidence. The WARP validation path writes a reviewable `phase5_visual_slice.bmp` capture.

## Boundaries

This decision does not claim that the product has earned an AAA-quality label or completed external visual approval. Phase 5 is complete only when the exact implementation head passes strict MSVC and DXC builds, all deterministic tests, D3D12 debug-layer validation, resize, GPU readback, visual capture thresholds, performance/memory evidence, and founder visual approval. External playtest and release claims remain prohibited until later phase gates.
