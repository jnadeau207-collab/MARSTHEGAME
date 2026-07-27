# ADR 0020: Generated materials and default-heap GPU residency

- Status: Proposed in Phase 4 implementation
- Date: 2026-07-27
- Decision owner: Repository implementation authority

## Context

The native renderer previously generated project-owned meshes on the CPU but left the immutable vertex and index atlases in upload heaps for their entire lifetime. It also had no project-owned texture, normal, surface-mask, or material resource path. That was sufficient for the renderer foundation, but it is not an acceptable production resource architecture.

## Decision

Phase 4 uses deterministic project-owned code to generate one material definition and one texture-array layer for every canonical procedural mesh slot.

The initial generated material catalog contains:

- RGBA8 base-color texture layers,
- RGBA8 tangent-space normal texture layers,
- packed roughness, metallic, mask, and occlusion texture layers,
- per-material texture scale, normal strength, roughness, metallic, mask strength, and tint parameters,
- a deterministic aggregate material-content hash,
- fail-closed validation of dimensions, layer identity, payload size, finite parameters, and aggregate identity.

The renderer consumes these resources through a shader-visible SRV descriptor heap and a static anisotropic wrap sampler. The first material shader uses world-space triplanar projection so generated meshes do not require an external UV-authoring dependency.

All immutable mesh and texture payloads are created in D3D12 default heaps. CPU-visible upload resources exist only as staging resources. A dedicated upload context records copy commands, transitions resources into their final states, signals an upload fence, retains every staging batch until that fence completes, and releases completed batches deterministically.

The persistently mapped upload heap remains appropriate for per-frame scene constants because those values are rewritten by the CPU. It is not used for immutable mesh or texture residency.

## Invariants

- Static vertex and index buffers are default-heap resources.
- Generated material texture arrays are default-heap resources.
- A staging resource cannot be released before its submission fence completes.
- Fence retirement values are monotonic and decreasing values fail closed.
- The first render cannot consume uploaded resources until the startup upload fence has completed.
- Generated material payloads are deterministic for the same source code and constants.
- No external texture or material library is introduced.

## Deferred work

This decision does not claim the complete physically based material path. Full metallic/roughness BRDF behavior, mip generation, texture streaming, descriptor allocation policy, shader variants, material identity in cooked scene manifests, and production authoring controls remain later Phase 4 work.
