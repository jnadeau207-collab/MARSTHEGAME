# Phase 5 Visual Slice Evidence Contract

Phase 5 evidence is produced by the native Windows executable and repository CI. Repository prose is not sufficient.

## Required executable gates

- strict MSVC C++23 `/W4 /WX` build,
- DXC compilation for shadow, scene, particle, fullscreen, temporal, and final passes,
- all CTest suites,
- validation-enabled Direct3D 12 WARP execution,
- resize-safe reconstruction of HDR, history, depth, and capture resources,
- GPU timestamp collection and non-zero resident-memory evidence,
- project-generated material, environment, character-rig, and audio determinism tests,
- final-frame readback with meaningful-pixel, luminance-range, highlight, shadow, and edge-energy thresholds,
- retained `phase5_visual_slice.bmp` capture in CI artifacts.

## Truthful completion boundary

A green automated run proves implementation integrity and reviewable native visual output. It does not substitute for the founder's direct play and visual approval, and it does not by itself establish an AAA-quality claim.
