# ADR 0018: Native-only product runtime

- Status: Accepted
- Date: 2026-07-27
- Decision owner: Founder

## Decision

MARSTHEGAME ships as a native Windows game. C++23 owns engine and gameplay code, Direct3D 12 owns rendering, HLSL/DXC owns shaders, and CMake/Ninja/MSVC own the supported build.

The Python/Pygame runtime and its product-facing compatibility path are removed. Future gameplay, campaign, save, replay, asset, animation, audio, and tooling work must advance the native runtime directly.

## Consequences

- no dual runtime
- no Python fallback
- no Three.js shipping dependency
- no third-party game engine
- all new product behavior requires native tests and native execution evidence
- historical design intent may inform migration, but removed code is not a shipping contract

## Current evidence

The native executable contains deterministic movement, a follow camera, a Mars graybox scene, a mission objective, completion/reset state, strict C++ tests, validation-enabled WARP rendering, and GPU frame readback.
