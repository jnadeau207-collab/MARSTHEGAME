# Phase 5 Visual Evidence Contract

Phase 5 evidence is produced by the exact native Windows executable under review. Repository prose is not sufficient.

## Engineering integrity gates

- strict MSVC C++23 `/W4 /WX` build;
- DXC compilation and packaged-shader verification;
- all CTest suites;
- validation-enabled Direct3D 12 WARP execution;
- reference-hardware execution;
- resize-safe reconstruction of HDR, history, depth, and capture resources;
- GPU timestamp collection and non-zero resident-memory evidence;
- project-owned material, environment, character, animation, and audio determinism tests;
- startup, shutdown, save, replay, input, and corruption-recovery evidence;
- deterministic capture production with exact commit, camera, content-manifest, quality, exposure, timing, GPU, and driver metadata.

## Required visual-review evidence

The exact candidate must produce all four deterministic captures defined by `PHASE5_SCREENSHOT_APPROVAL_GATE.md`:

- H1 — arrival close frame;
- H2 — relay reveal hero frame;
- H3 — traversal material frame;
- H4 — relay activation frame.

The capture set must be reviewed as a set. A single staged image may not conceal weak ordinary gameplay frames.

## Automated image checks

Automation may reject:

- invalid or missing images;
- all-black, all-white, single-color, NaN, or corrupted output;
- missing expected geometry;
- unstable deterministic viewpoints;
- material or temporal regressions outside committed tolerances;
- clipped luminance, broken dimensions, excessive frame time, memory growth, or hitches.

Automation may not assert beauty, production quality, visual approval, reference competitiveness, or AAA quality.

## Truthful completion boundary

A green automated run proves implementation integrity and reviewable native output. It does not substitute for art direction or founder judgment.

The previous candidate satisfied technical checks but failed direct visual review. That failure is the controlling precedent: founder rejection invalidates the candidate regardless of numerical thresholds.

Phase 5 exits only when the founder directly plays the exact candidate and explicitly approves H1–H4 under the binding screenshot rubric.
