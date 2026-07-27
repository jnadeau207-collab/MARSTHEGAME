# AUTHORITATIVE PRODUCTION PLAN V4: MARSTHEGAME

## 1. Authority and operating reality

This document is the founder-controlled product and engineering authority for transforming the existing Python + Pygame prototype into a commercial, Windows-first, custom-runtime action game with an **AAA-quality target**.

The project has exactly one human founder, `jnadeau207-collab`, and one AI software collaborator, ChatGPT. There are no employees, contractors, departments, other human contributors, or implied production seats. Workstreams are categories of work shared by the founder and AI collaborator, not headcount.

The founder may amend, reject, or replace any part of this plan. Repository evidence outranks aspirational prose. No phase, feature, visual-quality level, content quantity, or release state may be claimed without executable or directly reviewable evidence.

## 2. What AAA means here

AAA is a quality result, not a budget, team size, engine choice, marketing label, feature count, or confidence statement. The game may be called AAA-quality only when representative shipping content demonstrates all of the following:

- exceptional, responsive movement and combat,
- coherent high-fidelity visual direction,
- production-quality character, environment, animation, lighting, material, VFX, camera, and UI work,
- authored and adaptive audio with reliable mixing,
- stable frame pacing and measured performance budgets,
- polished onboarding, controls, accessibility, and failure recovery,
- crash-free, recoverable start-to-finish sessions,
- deterministic replay and save compatibility,
- professional content and iteration tooling,
- representative external playtests meeting committed completion and emotional-response gates.

Until those gates pass, the truthful description is **custom-engine game with an AAA-quality target**.

## 3. Visual target and current truth

### Target

The visual target is modern cinematic 3D presentation, not merely attractive procedural 2D. Representative content must eventually demonstrate:

- physically coherent materials and lighting,
- high-density authored environments with readable composition,
- large-scale terrain and atmospheric depth,
- stable shadows and reflections,
- production skeletal animation and motion transitions,
- GPU-driven particles and authored VFX,
- HDR-aware post-processing and temporal stability,
- scalable quality settings without destroying art direction,
- frame-time, memory, streaming, and hitch evidence on the reference PC.

### Current state

The current Pygame presentation uses procedural 2D surfaces, rectangles, circles, gradients, glows, silhouettes, and text. It is a useful gameplay and systems prototype, but it is **not a candidate shipping renderer and not evidence of AAA graphics**.

The Python runtime remains valuable as:

- the protected Classic Mode compatibility runtime,
- a deterministic gameplay and progression oracle,
- a save/replay contract reference,
- rapid test and content-validation tooling,
- a migration comparison target.

No further campaign-content expansion should be prioritized in Pygame until the native renderer and migration boundary are established.

## 4. Product identity

### Permanent design pillars

1. Mythic Kinetic Earnestness
2. Player Agency Through Mastery
3. Multiplanetary Progression
4. Procedural + Authored Hybrid
5. Accessibility-First Feel

The emotional target is earnest determination. The work must never collapse into parody, empty spectacle, or motivational wallpaper.

### Classic Mode

The existing eight-chapter game remains permanently available as Classic Mode. Its chapter IDs, progression, saves, identity switching, and deterministic replay remain protected in CI. Classic Mode is legacy/prototype content and is not counted as AAA campaign content.

### Identity and legal boundary

The fictionalized identity track is the default clearance-independent production path. Real-world names, likenesses, and marks may not be publicly marketed, monetized, submitted to platforms, or used in external playtests without written clearance from qualified counsel.

## 5. Shipping technical direction

### Primary runtime

The Windows shipping runtime is:

- **C++23** for platform, engine, renderer, gameplay runtime, memory, asset, animation, audio, and shipping systems,
- **Direct3D 12** for the primary Windows graphics backend,
- **HLSL compiled with DXC** for programmable rendering,
- **CMake** for reproducible configuration and build generation,
- Windows SDK and narrowly scoped platform libraries where they do not become the game architecture.

Python is not the final renderer or performance-critical shipping gameplay runtime. Python remains an offline tool, test oracle, compatibility runtime, and migration aid until every required contract has native parity.

### Explicit non-decisions

- Three.js is not the shipping renderer. It is a browser-oriented 3D library and may be considered later only for optional web tooling or visualization.
- No third-party game engine may replace the project architecture.
- No cross-platform renderer abstraction will be built before the Windows Direct3D 12 vertical slice is proven. Premature backend generalization is prohibited.
- Native migration may not discard deterministic gameplay, save, replay, input, accessibility, and campaign contracts.

### Native migration rule

Every migrated system requires:

1. a stable data or event contract,
2. a Python reference case where applicable,
3. native implementation,
4. parity or intentionally versioned divergence tests,
5. measured CPU/GPU/memory behavior,
6. rollback-safe persistence where state is involved.

## 6. Completed foundations

### Phase 0 — repository and truth foundation: complete

Delivered and protected:

- dual real-world and fictionalized identity tracks,
- stable player-facing content keys,
- deterministic replay through all eight Classic Mode chapters,
- save, progression, transition, and credits compatibility,
- pinned formatting and static-analysis gates,
- performance baselines and same-runner regression thresholds,
- truthful sole-founder plus AI-collaborator operation,
- architecture, contribution, legal/IP, and decision records.

### Phase 1 — repository-executable gameplay foundation: complete

Delivered and protected:

- complete fictionalized Ares Reach path separate from Classic Mode,
- deterministic fixed-step simulation and complete-path replay,
- transactional saves and checkpoints,
- crash and frame-pacing diagnostics,
- accessibility-aware camera and presentation systems,
- event-driven audio architecture,
- adaptive combat, failure learning, resource interaction, and ascent sequence,
- machine-readable quality truth that rejects an unearned AAA claim.

This phase did not deliver final authored visuals, animation, music, sound, mix, packaging, external playtests, or AAA evidence.

### Phase 2 — campaign and mission-state foundation: architecture boundary complete

Delivered and protected:

- stable acyclic campaign graph,
- deterministic unlock computation,
- explicit implemented and planned mission states,
- transactional campaign attempts and completions,
- implemented Ares Reach and Relay Echo routes,
- Relay Echo objective, failure, checkpoint, accessibility, and replay contracts,
- atomic Relay Echo campaign promotion and Phobos Vector unlock,
- durable completed-mission replay/reset with preserved campaign history,
- deterministic replay and audit evidence across every implemented route.

The campaign itself is not complete. Phobos Vector and Frontier Burn remain planned and non-playable.

## 7. Remaining production phases

Exactly six major phases remain after the Phase 2 architecture boundary.

## Phase 3 — Windows native renderer foundation

### Goal

Create the smallest production-shaped Direct3D 12 runtime that can render a deterministic native scene and report trustworthy GPU/CPU evidence.

### Required systems

- Win32 window and message loop,
- Direct3D 12 device, command queue, swap chain, descriptor heaps, command allocators, command list, fences, and frame resources,
- debug layer, validation, device-removal diagnostics, and named GPU objects,
- DXC HLSL compilation with reproducible shader inputs,
- explicit resource ownership and lifetime rules,
- render-pass or frame-graph boundary capable of later expansion,
- deterministic camera and transform data,
- native logging, crash boundary, and frame-timing output,
- Windows CI build using the supported Visual Studio toolchain.

### Exit gate

A packaged native executable must open a window, render a stable indexed mesh through HLSL, resize correctly, survive repeated startup/shutdown, report frame timing, pass validation without errors, and build in CI. Pygame remains unchanged except for compatibility fixes.

## Phase 4 — scene, asset, animation, and gameplay migration

### Goal

Turn the renderer kernel into a real 3D game runtime while retaining deterministic gameplay authority.

### Required systems

- versioned scene and entity model,
- glTF 2.0 or equivalently explicit authored-asset ingestion,
- mesh, texture, material, sampler, and shader-variant management,
- physically based metallic/roughness material path,
- skeletal hierarchy, skinning, animation clips, blending, state transitions, and root-motion policy,
- native camera, input, collision, locomotion, combat, and interaction contracts,
- save, replay, campaign, accessibility, and settings bridge,
- asset cooker with hashes, dependency tracking, and deterministic outputs,
- editor/debug visualization sufficient to author the next phase.

### Exit gate

A native graybox of Ares Reach must be playable from start to finish with deterministic progression parity, native save/replay compatibility, keyboard/gamepad completion, and no dependence on Pygame for the active run.

## Phase 5 — AAA visual vertical slice

### Goal

Make one representative native Ares Reach segment visually and aurally credible against modern high-end action-game references.

### Required systems

- HDR linear-light rendering and tone mapping,
- image-based lighting and production PBR materials,
- stable direct shadows and local-light solution,
- atmosphere, fog, dust, sky, and distance treatment,
- terrain and environment composition with authored detail hierarchy,
- temporal anti-aliasing or equivalent temporal-stability solution,
- scalable reflections, ambient occlusion, bloom, exposure, depth of field, and motion treatment,
- GPU particle/VFX pipeline,
- production character model, rig, animation, impact, and camera presentation,
- authored music, ambience, sound design, dialogue/subtitle treatment, and mix,
- capture workflow and automated image/performance comparisons.

### Exit gate

The founder must directly play and approve the native slice. Representative captures must satisfy the committed visual-reference rubric. Frame-time, memory, hitch, accessibility, and crash evidence must pass on the reference PC. The slice may still not be called AAA until external evidence passes.

## Phase 6 — campaign content production

### Goal

Build the smallest complete campaign that preserves quality rather than maximizing mission count.

### Required work

- migrate the complete Ares Reach and Relay Echo experiences into the native runtime,
- implement Phobos Vector only after its contract, art plan, technical risks, and replay path are approved,
- implement Frontier Burn only if the quality budget supports it,
- create reusable encounter, dialogue, objective, checkpoint, cinematic, and environment authoring tools,
- produce final fictionalized narrative and localization-ready content,
- retain Classic Mode as a separate compatibility mode.

### Exit gate

Every shipping mission must be complete, replayable, accessible, persist correctly, and meet the visual/audio/performance bar. Scope is reduced before quality.

## Phase 7 — optimization, tooling, packaging, and soak

### Goal

Turn the complete campaign into a robust Windows product.

### Required systems

- GPU/CPU profiling and budgets by pass and subsystem,
- asset streaming, residency, LOD, culling, and loading policy,
- shader and pipeline caching,
- memory budgets and leak detection,
- packaged builds, installer/update strategy, logs, crash reports, and save migration,
- long-run soak, suspend/resume, display-mode, controller, audio-device, and corruption testing,
- reference-PC and lower-spec scalability evidence,
- reproducible release builds and artifact provenance.

### Exit gate

The packaged build must complete repeated start-to-finish runs without crashes or save loss and meet committed frame-time, hitch, load-time, and memory thresholds.

## Phase 8 — external validation and release evidence

### Goal

Earn, rather than assert, the final quality designation.

### Required evidence

- founder direct-play approval of the shipping candidate,
- representative external fictionalized-track playtests,
- at least 80% completion of the committed test path unless the founder replaces that threshold with a stricter one,
- strong-majority evidence of the intended earnest-determination emotional response,
- accessibility-path and keyboard/gamepad parity on packaged builds,
- final authored asset, audio, UI, legal, and platform checklist completion,
- zero unresolved severity-one defects,
- release-candidate soak and crash evidence.

Only after these gates pass may the repository change `aaa_claim` from `target_not_achieved`.

## 8. Visual reference rubric

Every Phase 5 review must compare captured gameplay against a fixed rubric rather than subjective optimism:

- **lighting:** direction, bounce impression, exposure, shadow stability, night/interior readability,
- **materials:** roughness separation, normal detail, scale consistency, weathering, contact response,
- **environment:** foreground/midground/background composition, density, landmarks, traversal readability,
- **atmosphere:** depth cues, fog/dust integration, sky coherence, silhouette preservation,
- **character:** model quality, deformation, locomotion, facial/upper-body intent where visible,
- **VFX:** timing, scale, integration, overdraw discipline, gameplay readability,
- **camera:** composition, motion, impact, accessibility scaling, temporal stability,
- **UI:** hierarchy, typography, controller navigation, subtitle presentation, visual consistency,
- **performance:** frame time, hitches, GPU memory, CPU cost, scalability.

A visually impressive still is insufficient. The target must survive motion, interaction, failure, camera changes, and sustained play.

## 9. Permanent risk rules

- Scope is cut before quality.
- Evidence is strengthened before standards are lowered.
- The Pygame renderer is compatibility-only after Phase 3 begins.
- Three.js is not introduced into the shipping runtime without a new founder-approved decision record.
- Native rewrites require parity and measured benefit.
- Accessibility is designed with gameplay, not appended later.
- Real-world identity remains legally gated.
- Planned campaign nodes are not playable content.
- The repository must never invent people, staffing, legal clearance, playtest results, campaign completion, visual quality, or AAA status.

## 10. Immediate execution order

1. Establish the Windows C++23/Direct3D 12 build and validation boundary.
2. Render a deterministic native mesh with HLSL and trustworthy frame/device diagnostics.
3. Define versioned scene, transform, camera, material, and asset contracts.
4. Build the native Ares Reach graybox before adding more campaign missions.
5. Produce the AAA visual slice before large-scale content production.
6. Continue through Phases 6–8 without treating infrastructure as finished game content.

Build the smallest complete system that can honestly support the next larger claim. Preserve Classic Mode. Keep the custom architecture. Measure everything important.

Failure is progress. The frontier is open.
