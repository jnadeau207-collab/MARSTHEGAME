# Native Game Migration

The product runtime is now entirely C++23, Direct3D 12, and HLSL.

## Delivered in this tranche

- removed the Python/Pygame runtime, requirements, tests, tools, and Python CI
- removed compatibility-era configuration and obsolete shader artifacts
- added a renderer-facing native scene contract
- added deterministic fixed-step C++ gameplay state
- added player movement, sprint, reset, objective completion, and follow camera
- added a native Ares Reach traversal graybox with terrain, landing pad, structures, rocks, player marker, and beacon
- expanded the renderer to draw independently transformed and tinted scene instances
- added strict native gameplay tests through CTest
- retained validation-enabled D3D12 WARP rendering and GPU frame readback

## Current quality boundary

The game is now structurally native and playable, but the scene is graybox geometry. It is not final art and does not earn an AAA-quality claim.

## Next implementation tranche

1. versioned scene/entity identifiers and serialized native scene data
2. collision volumes and interaction events
3. gamepad input abstraction
4. native checkpoint/save/replay evidence
5. glTF ingestion and deterministic asset cooking
6. default-heap mesh upload and resource lifetime tracking
7. physically based material pipeline
