# ADR 0016: Windows-native C++23 and Direct3D 12 shipping runtime

- Status: Accepted
- Date: 2026-07-27
- Decision owner: Founder

## Context

The repository began as a pure Python + Pygame 2D prototype. That runtime now provides valuable deterministic gameplay, save, replay, accessibility, and campaign evidence, but its procedural surface-based renderer is not a credible foundation for the committed modern cinematic 3D visual target.

The project prohibits replacing its architecture with a third-party game engine. The project is Windows-first and needs explicit ownership of rendering, frame pacing, memory, assets, diagnostics, and migration contracts.

Three.js was considered because it provides a productive scene, material, camera, and renderer layer for web 3D. It is not selected for the shipping game because it is browser-oriented, would make the browser/WebGPU/WebGL environment part of the runtime architecture, and does not provide the Windows-native control required by the production plan.

## Decision

The shipping runtime will use:

- C++23 as the primary general-purpose runtime language,
- Win32 for the initial platform boundary,
- Direct3D 12 and DXGI for the Windows graphics backend,
- HLSL compiled with DXC for shaders,
- CMake for reproducible Visual Studio build generation.

The existing Python/Pygame runtime is retained during migration as:

- Classic Mode compatibility runtime,
- deterministic gameplay and progression oracle,
- save/replay reference implementation,
- validation and content tooling.

No new campaign mission should be prioritized in Pygame before the native Ares Reach graybox exists.

## Consequences

### Positive

- Direct control over GPU submission, synchronization, memory, diagnostics, and presentation.
- Native Windows packaging and performance analysis.
- A production-shaped route to PBR, animation, streaming, VFX, and high-fidelity presentation.
- Existing deterministic contracts remain useful instead of being discarded.

### Costs

- Substantially more engineering than adopting a commercial engine.
- Platform and GPU correctness become our responsibility.
- HLSL is an additional domain-specific language even though C++ remains the primary runtime language.
- Cross-platform support is deferred until the Windows slice proves the architecture.

## Guardrails

- The D3D12 debug layer is enabled in development builds.
- Every GPU object receives a diagnostic name where practical.
- Device-removal and HRESULT failures are surfaced with actionable context.
- Frame resources and synchronization are explicit; no implicit per-frame GPU waits are accepted as the final design.
- Renderer expansion is gated by validation-clean builds and measured evidence.
- Python parity is required for migrated gameplay/save/replay contracts until a founder-approved versioned divergence exists.

## Rejected alternatives

### Continue with Pygame as the shipping renderer

Rejected. It preserves prototype velocity but does not provide the required modern 3D rendering, asset, animation, GPU, and presentation foundation.

### Three.js/WebGPU shipping runtime

Rejected for the Windows shipping game. It remains eligible for optional web-based tooling only through a separate decision record.

### Adopt Unreal, Unity, Godot, or another full game engine

Rejected by the product constraint that the project own its runtime architecture.

### Build a cross-platform Vulkan/D3D12 abstraction immediately

Rejected as premature. The first proof is a Windows Direct3D 12 vertical slice; portability work must follow measured need.
