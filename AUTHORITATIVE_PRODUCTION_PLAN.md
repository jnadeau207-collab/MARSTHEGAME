# AUTHORITATIVE PRODUCTION PLAN V5: MARSTHEGAME

## 1. Authority

This document is the founder-controlled product and engineering authority for MARSTHEGAME.

The project has exactly one human founder, `jnadeau207-collab`, and one AI software collaborator, ChatGPT. There are no employees, contractors, departments, other human contributors, or implied production seats.

Repository evidence outranks aspirational prose. No phase, feature, content quantity, visual-quality level, or release state may be claimed without executable or directly reviewable evidence.

## 2. Product standard

MARSTHEGAME is a Windows-first, custom-engine action game with an AAA-quality target.

AAA is an earned quality result. It is not established by budget, engine choice, language, polygon count, confidence, or marketing language. Representative shipping content must eventually demonstrate:

- exceptional movement and combat feel,
- production-quality character and environment art,
- coherent physically based materials and lighting,
- high-quality animation, camera, VFX, UI, and audio,
- stable frame pacing and measured CPU, GPU, memory, streaming, and hitch budgets,
- polished controls, accessibility, onboarding, saves, recovery, and failure handling,
- crash-free start-to-finish sessions,
- professional asset and content tooling,
- representative external playtests meeting committed completion and emotional-response gates.

Until those gates pass, the only truthful description is **custom-engine game with an AAA-quality target**.

## 3. Permanent technical architecture

The game runtime is native-only:

- **C++23** owns platform integration, engine systems, gameplay, memory, assets, animation, audio, tools that ship with the product, and runtime orchestration.
- **Direct3D 12** is the primary Windows graphics backend.
- **HLSL compiled with DXC** owns programmable GPU work.
- **CMake and Ninja** own reproducible project generation and builds.
- The Windows SDK and narrowly scoped platform libraries may be used when they do not become the game architecture.

There is no Python or Pygame product runtime. There is no browser runtime and no Three.js shipping dependency. No third-party game engine may replace the project architecture.

Cross-platform renderer abstraction is deferred until the Windows vertical slice is proven. Premature backend generalization is prohibited.

## 4. Product identity

### Design pillars

1. Mythic Kinetic Earnestness
2. Player Agency Through Mastery
3. Multiplanetary Progression
4. Procedural + Authored Hybrid
5. Accessibility-First Feel

The emotional target is earnest determination. The work must not collapse into parody, empty spectacle, or motivational wallpaper.

### Identity and legal boundary

The fictionalized identity track is the default production path. Real-world names, likenesses, and marks may not be publicly marketed, monetized, submitted to platforms, or used in external playtests without written clearance from qualified counsel.

## 5. Completed foundations

### Phase 0 — repository and product authority: complete

Delivered:

- founder-controlled production authority,
- fictionalized identity path,
- explicit quality and legal boundaries,
- repository governance and CI discipline.

### Phase 1 — gameplay-system foundation: complete

Delivered as design and behavior authority:

- Ares Reach mission structure,
- movement, combat, checkpoint, failure, accessibility, camera, audio, and presentation requirements,
- deterministic progression and save expectations,
- rejection of an unearned AAA claim.

### Phase 2 — campaign and mission-state architecture: complete

Delivered as product architecture:

- stable mission identities and ordering,
- Ares Reach and Relay Echo campaign placement,
- Phobos Vector and Frontier Burn planning boundaries,
- mission attempt, completion, replay, reset, and unlock requirements.

### Phase 3 — Windows native renderer foundation: complete

Delivered and verified:

- Win32 window and message ownership,
- Direct3D 12 device, high-performance hardware selection, WARP validation path, swap chain, command queue, command allocators, command list, descriptor heaps, depth buffer, fences, and frame ownership,
- DXC shader compilation and packaged shader verification,
- validation-enabled rendering and resize behavior,
- frame timing and device-removal diagnostics,
- GPU back-buffer readback and meaningful-pixel verification,
- strict MSVC `/W4 /WX` builds.

## 6. Active production phase

## Phase 4 — native scene, asset, animation, and gameplay migration

### Current delivered tranche

The native executable now contains the first playable Ares Reach graybox:

- deterministic fixed-step C++ gameplay state,
- WASD/arrow movement and sprint,
- bounded traversal arena,
- follow camera,
- native mission objective and completion state,
- reset behavior,
- independently transformed scene instances,
- Mars terrain, landing pad, structural obstacles, rock formations, player marker, and objective beacon,
- strict C++ gameplay tests,
- native-only CI with CTest and validation-enabled rendered-frame evidence.

### Remaining Phase 4 systems

- versioned scene and entity data,
- glTF 2.0 authored-asset ingestion,
- deterministic asset cooker with hashes and dependency tracking,
- default-heap GPU upload and resource lifetime tracking,
- mesh, texture, material, sampler, and shader-variant management,
- physically based metallic/roughness material path,
- skeletal hierarchy, skinning, clips, blending, root-motion policy, and animation state machines,
- native input abstraction with keyboard and gamepad parity,
- collision, locomotion, combat, interaction, checkpoints, saves, campaign progression, settings, and accessibility,
- debug visualization and authoring support sufficient for the visual slice.

### Phase 4 exit gate

A native Ares Reach graybox must be playable from start to finish with:

- deterministic progression,
- native save and replay evidence,
- keyboard and gamepad completion,
- collision and interaction parity,
- no dependence on a removed compatibility runtime,
- validation-clean rendering,
- measured CPU, GPU, memory, and hitch behavior.

## 7. Remaining production phases

Exactly five major phases remain.

## Phase 4 — native scene, asset, animation, and gameplay migration

Status: **in progress**.

## Phase 5 — AAA visual vertical slice

### Goal

Make one representative Ares Reach segment visually and aurally credible against modern high-end action-game references.

### Required systems

- HDR linear-light rendering and tone mapping,
- image-based lighting and production PBR materials,
- stable direct shadows and local lighting,
- atmosphere, fog, dust, sky, and distance treatment,
- terrain and authored environment composition,
- temporal anti-aliasing or equivalent temporal stability,
- reflections, ambient occlusion, bloom, exposure, depth of field, and motion treatment,
- GPU particles and authored VFX,
- production character model, rig, animation, impacts, and camera presentation,
- authored music, ambience, sound design, dialogue/subtitles, and mix,
- capture workflow and automated image/performance comparisons.

### Exit gate

The founder must directly play and approve the native slice. Captures must satisfy the committed visual-reference rubric. Frame-time, memory, hitch, accessibility, crash, and device-validation evidence must pass on the reference PC.

## Phase 6 — campaign production

### Goal

Produce the smallest complete campaign that preserves quality rather than maximizing mission count.

### Required work

- complete Ares Reach,
- complete Relay Echo,
- implement Phobos Vector only after its contract, art plan, technical risks, and replay path are approved,
- implement Frontier Burn only if the quality budget supports it,
- create reusable objective, encounter, checkpoint, cinematic, dialogue, and environment authoring systems,
- produce final fictionalized narrative and localization-ready content.

### Exit gate

Every shipping mission must be complete, replayable, accessible, persistent, visually coherent, performant, and stable. Scope is reduced before quality.

## Phase 7 — optimization, tooling, packaging, and soak

### Goal

Turn the complete game into a supportable Windows product.

### Required work

- asset cooking and patch strategy,
- build signing and installer packaging,
- crash reporting and diagnostics,
- save migration and corruption recovery,
- scalable quality settings,
- reference-PC and lower-spec performance tuning,
- long-session soak and repeated startup/shutdown testing,
- controller/device matrix,
- accessibility verification,
- release rollback and update procedures.

## Phase 8 — external validation and release evidence

### Goal

Earn the right to call the product complete and determine whether the AAA-quality claim is supportable.

### Required evidence

- representative external playtests,
- completion, comprehension, difficulty, accessibility, and emotional-response data,
- crash-free and recovery evidence,
- final performance and memory evidence,
- legal/IP clearance,
- release-candidate packaging and install/uninstall evidence,
- founder release approval.

## 8. Scope law

The project does not reduce quality to preserve feature count. Missions, systems, platforms, and content are cut before the visual, interaction, stability, accessibility, and performance standards are weakened.
