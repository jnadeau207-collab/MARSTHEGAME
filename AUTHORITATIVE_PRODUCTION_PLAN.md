# AUTHORITATIVE PRODUCTION PLAN V8: MARSTHEGAME

## 1. Authority

This document is the founder-controlled product and engineering authority for MARSTHEGAME.

The project has exactly one human founder, `jnadeau207-collab`, and one AI software collaborator, ChatGPT. There are no employees, contractors, departments, other human contributors, or implied production seats.

Repository evidence outranks aspirational prose. No phase, feature, content quantity, visual-quality level, or release state may be claimed without executable or directly reviewable evidence.

Founder direct visual rejection outranks automated image thresholds. A rendered frame may be technically valid and still fail the product standard.

## 2. Product standard

MARSTHEGAME is a Windows-first, custom-engine action game with an AAA-quality target.

AAA is an earned quality result. It is not established by budget, engine choice, language, polygon count, confidence, or marketing language. Representative shipping content must eventually demonstrate:

- exceptional movement and combat feel,
- production-quality character and environment presentation,
- coherent physically based materials and lighting,
- high-quality animation, camera, VFX, UI, and audio,
- stable frame pacing and measured CPU, GPU, memory, streaming, and hitch budgets,
- polished controls, accessibility, onboarding, saves, recovery, and failure handling,
- crash-free start-to-finish sessions,
- professional procedural-content and authoring tooling,
- representative external playtests meeting committed completion and emotional-response gates.

Until those gates pass, the only truthful description is **custom-engine game with an AAA-quality target**.

## 3. Permanent technical architecture

The game runtime is native-only:

- **C++23** owns platform integration, engine systems, gameplay, memory, procedural content, animation, audio, native tools, and runtime orchestration.
- **Direct3D 12** is the primary Windows graphics backend.
- **HLSL compiled with DXC** owns programmable GPU work.
- **CMake and Ninja** own reproducible project generation and builds.
- The Windows SDK and narrowly scoped platform libraries may be used when they do not become the game architecture.

There is no Python or Pygame product runtime. There is no browser runtime and no Three.js shipping dependency. No third-party game engine may replace the project architecture.

The production path does not assume an external asset library. Geometry, terrain, structures, materials, textures, animation data, effects, and audio content must be created by project-owned code and project-owned tools. Imported third-party art is not a prerequisite or default escape hatch.

Cross-platform renderer abstraction is deferred until the Windows vertical slice is proven. Premature backend generalization is prohibited.

## 4. Product identity

### Design pillars

1. Mythic Kinetic Earnestness
2. Player Agency Through Mastery
3. Multiplanetary Progression
4. Procedural + Directed Composition
5. Accessibility-First Feel

The emotional target is earnest determination. The work must not collapse into parody, empty spectacle, or motivational wallpaper.

### Identity and legal boundary

The fictionalized identity track is the default production path. Real-world names, likenesses, and marks may not be publicly marketed, monetized, submitted to platforms, or used in external playtests without written clearance from qualified counsel.

External game screenshots, presentations, and production breakdowns may be used for study. Their protected characters, environments, marks, UI, assets, and distinctive designs may not be copied into the project.

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

## Phase 4 — native scene, procedural content, animation, and gameplay production

### Current delivered tranches

The native executable and runtime now contain:

- deterministic fixed-step C++ gameplay state,
- keyboard and XInput gamepad mapping,
- bounded collision-aware traversal,
- follow camera,
- native mission objective, checkpoint, save, replay, and reset state,
- transactional native saves with validation and corruption handling,
- strict C++ gameplay and input tests,
- native-only CI with CTest and validation-enabled rendered-frame evidence.

The versioned scene pipeline now contains:

- a project-authored Ares Reach source scene with stable entity identifiers,
- strict source parsing and validation,
- deterministic entity ordering,
- a native scene cooker,
- a checksummed runtime package with source provenance,
- a versioned content manifest binding the authored scene source, canonical generated mesh hashes, mesh-catalog identity, world-composition identity, and aggregate content identity,
- runtime recomputation and fail-closed rejection of corrupted or mismatched packaged content,
- transactional cooked-package replacement and corruption rejection,
- scene-driven render instances, collision, player spawn, checkpoint, and objective data.

The code-authored content and renderer path now contain:

- deterministic generated hard-surface geometry,
- seeded irregular Mars-rock topology,
- generated cylindrical structural and beacon geometry,
- seeded elevated Mars terrain with generated normals and color variation,
- one canonical procedural mesh catalog shared by cooker and runtime compilation,
- deterministic mesh hashing and fail-closed topology validation,
- validated 32-bit vertex/index atlas construction,
- cooked-scene mesh identity for cube, rock, column, and terrain geometry,
- per-instance D3D12 draw-range selection,
- deterministic project-generated base-color, tangent-space normal, and packed roughness, metallic, mask, and occlusion texture-array layers aligned to the canonical mesh slots,
- deterministic material parameters, aggregate material hashing, and fail-closed material-catalog validation,
- world-space triplanar generated-material sampling without an external texture or UV-authoring dependency,
- a shader-visible material SRV heap and static anisotropic sampler,
- default-heap residency for immutable vertex, index, and texture resources,
- a dedicated upload command path with explicit copy transitions, upload-fence synchronization, monotonic fence retirement, and staging-resource lifetime tracking,
- a persistently mapped upload heap reserved for per-frame CPU-written scene constants rather than immutable content,
- startup verification and diagnostics proving completed staging batches are retired before first render,
- an Ares Reach technical composition containing generated terrain, rocks, radial elements, and hard-surface elements,
- strict topology, seed-divergence, density, elevation, cooked-scene, aggregate-manifest, generated-material determinism, material-corruption rejection, fence-retirement ordering, runtime-composition, DXIL-package, D3D12 validation, resize, and GPU-readback evidence.

### Remaining Phase 4 systems

- scalable mesh, texture, material, sampler, descriptor, mip, streaming, and shader-variant management,
- physically based metallic/roughness material path suitable for authored material families,
- project-owned skeletal hierarchy, skinning, clips, blending, root-motion policy, and animation state machines,
- combat, interaction, campaign progression, settings, and accessibility completion,
- project-owned audio synthesis, procedural ambience, authored sequencing, and runtime mixing,
- debug visualization and native authoring support sufficient for the replacement visual slice,
- deterministic previsualization camera and screenshot-viewpoint support.

### Phase 4 exit gate

A native Ares Reach graybox must be playable from start to finish with:

- deterministic progression,
- native save and replay evidence,
- keyboard and gamepad completion,
- collision and interaction parity,
- generated project-owned geometry and material content,
- no dependence on a removed compatibility runtime or external asset library,
- validation-clean rendering,
- measured CPU, GPU, memory, and hitch behavior.

A Phase 4 exit proves engine and gameplay infrastructure. It does not imply production art.

## 7. Remaining production phases

Exactly five major phases remain.

## Phase 4 — native scene, procedural content, animation, and gameplay production

Status: **in progress**.

## Phase 5 — art-directed AAA visual hero sequence

Status: **previous candidate invalidated; recovery in progress**.

### Invalidation record

On 2026-07-27 the founder directly launched and visually rejected the previous Phase 5 candidate. The build and automated tests proved renderer and runtime function, but the visible result remained a technical graybox with primitive character construction, arena-like environment composition, weak material identity, undirected lighting/post-processing, and prototype UI.

The prior candidate may not be represented as Phase 5 complete or visually approved. See:

- `docs/PHASE5_INVALIDATION_AND_RECOVERY.md`
- `docs/PHASE5_REFERENCE_BOARD.md`
- `docs/PHASE5_HERO_SEQUENCE_ART_DIRECTION.md`
- `docs/PHASE5_SCREENSHOT_APPROVAL_GATE.md`

### Replacement goal

Produce one continuous, playable Ares Reach hero sequence — **First Light at Relay 03** — that is visually and aurally credible against modern high-end action-game references while remaining original, project-owned, native, deterministic, performant, accessible, and legally distinct.

The sequence must establish:

- a professional human-scale field-engineer character,
- an authored Mars basin with foreground, route, worksite, and vista layers,
- a functionally legible relay installation,
- deliberate continuous camera staging,
- calibrated material families rather than universal procedural noise,
- restrained lighting, atmosphere, exposure, bloom, focus, and motion treatment,
- minimal accessible UI subordinate to the world,
- a physical relay-restoration payoff with authored VFX and audio.

### Required systems

- deterministic previsualization and screenshot viewpoints,
- HDR linear-light rendering and controlled tone mapping,
- image-based lighting and production PBR materials,
- stable direct shadows, sky fill, local practical lights, and authored activation lighting,
- bounded atmosphere, fog, dust, sky, and distance treatment,
- deliberately composed terrain, geology, worksite, and vista structures,
- temporal stability without visible smearing or crawling,
- configurable exposure, reflections, ambient occlusion, bloom, and motion treatment,
- project-authored VFX,
- proportional project-generated or project-authored character geometry, skeleton, skinning, clips, blending, interaction, and camera presentation,
- project-authored or synthesized ambience, sound design, music, relay signal, and mix,
- professional scalable text and HUD layout,
- capture workflow and automated regression comparisons that do not claim aesthetic approval.

### Exit gate

The exact candidate head must pass:

- strict native build and automated tests,
- WARP and reference-hardware rendering,
- validation, resize, startup/shutdown, save, replay, input, frame-time, memory, and hitch evidence,
- deterministic H1–H4 captures defined in `docs/PHASE5_SCREENSHOT_APPROVAL_GATE.md`,
- hostile internal review with no binary veto condition,
- founder direct play,
- founder explicit screenshot and visual approval.

Founder approval cannot be inferred from merge authorization, CI, numerical thresholds, assistant confidence, or prose. Any rejection invalidates the candidate and prevents Phase 6 advancement.

## Phase 6 — campaign production

### Goal

Produce the smallest complete campaign that preserves quality rather than maximizing mission count.

### Required work

- complete Ares Reach,
- complete Relay Echo,
- implement Phobos Vector only after its contract, procedural-content plan, technical risks, and replay path are approved,
- implement Frontier Burn only if the quality budget supports it,
- create reusable objective, encounter, checkpoint, cinematic, dialogue, environment-composition, and procedural-content systems,
- produce final fictionalized narrative and localization-ready content.

### Exit gate

Every shipping mission must be complete, replayable, accessible, persistent, visually coherent, performant, and stable. Scope is reduced before quality.

## Phase 7 — optimization, tooling, packaging, and soak

### Goal

Turn the complete game into a supportable Windows product.

### Required work

- procedural-content compilation, caching, versioning, and patch strategy,
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

Technical infrastructure is retained when useful, but no sunk cost protects rejected art, composition, UI, animation, or presentation from replacement.
