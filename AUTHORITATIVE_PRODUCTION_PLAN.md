# AUTHORITATIVE PRODUCTION PLAN: STARMAN — AAA TITLE TRANSFORMATION

## DOCUMENT PURPOSE AND CONSUMPTION RULES
This document is the single source of truth for transforming the existing pure-Python + Pygame concept prototype located at the public repository https://github.com/jnadeau207-collab/MARSTHEGAME into a full AAA-scale commercial title.
Target executor: autonomous LLM agent system designated Fable 5.
All subsequent generation, code synthesis, asset pipelines, design iteration, and production orchestration must treat this plan as immutable core directive unless explicitly versioned and approved by human oversight.
Do not interpret as suggestion. Execute phase-sequentially. Maintain full audit log of every decision, generated artifact, and deviation.
Preserve core narrative identity: mythic, kinetic, earnest arc of grit-to-multiplanetary-resolve. Player is Elon. Tone is neither parody nor documentary. Failure is progress. The frontier is open.
Commercial constraints: all real-world names, likenesses, trademarks require legal clearance or full fictionalization before any public release or monetization. The current prototype is transformative non-commercial fan-work only.
Target platforms at launch: native PC (Windows + Linux, Steam + Epic), PlayStation 5, Xbox Series X|S. Day-one cloud save. Cross-play where relevant. Optional later handheld.
Target rating: T for Teen.
Budget envelope: $80–150M USD development + marketing. Peak team 150–300 FTEs. Timeline 4.5–6 years from greenlight.

Critical technical mandate: ZERO third-party game engines. No Unreal, Unity, Godot, Bevy, or any equivalent. The entire runtime is custom raw code built from first principles on top of the existing repository architecture. High-performance custom systems written in C, C++, Rust, or tightly optimized Python+Cython/C-extensions will outperform general-purpose engines through radical specialization, data-oriented design, zero-overhead abstractions, and direct hardware control (Vulkan / Metal / DirectX 12, custom physics, custom audio mixer, custom asset pipeline).

## SOURCE PROTOTYPE STATE (AUTHORITATIVE BASELINE — LIVE REPOSITORY)
Repository: jnadeau207-collab/MARSTHEGAME (main branch).
Structure:
- main.py
- requirements.txt (pygame only)
- game/
  - core/          engine.py, input.py, camera.py, particles.py, save.py, settings.py, gfx.py
  - entities/      player.py, enemy.py, collectible.py
  - scenes/        base.py, title.py, chapter_select.py, level.py, credits.py
  - data/          levels.py (full data-driven chapter definitions for all 8 chapters)

Current implementation details confirmed by direct source inspection:
- Scene-stack state machine in Engine
- Data-driven levels (dict of solids, enemies, collectibles, narration, goals, sky colors)
- Player: coyote time, jump buffer, dash, double-jump unlock at chapter 6, attack hitbox, invulnerability frames, procedural detailed sprite with shading and state-based animation
- Level scene: multi-layer parallax, procedural stars/dust/rays, bevel platforms, vignette, narration triggers, terminals, goal flag
- 8 complete chapters with working progression and single JSON save slot
- Tone and juiciness already present (hit-stop, screen shake, particles, procedural art)

All future work must keep the exact current 8-chapter sequence playable as “Classic Mode” forever. New systems are additive layers on top of this foundation.

## DESIGN PILLARS (NON-NEGOTIABLE)
1. Mythic Kinetic Earnestness
2. Player Agency Through Mastery
3. Multiplanetary Progression
4. Procedural + Authored Hybrid (retain and expand the existing procedural generation spirit)
5. Accessibility-First Feel (coyote, buffering, rebind, difficulty, color-blind, narrative assist from day one)

## HIGH-LEVEL VISION TARGET
25–40 hour main campaign + 15–25 hours side/post-game content.
Seamless 2.5D/3D hybrid side-scrolling action-platforming, arena combat, light base-building and resource loops on Mars, vehicle sections, and systemic failure-to-success simulation.
Full custom high-performance rendering, physics, audio, and tools.
Cinematic production values achieved through custom pipelines, not engines.
Core campaign complete and fully offline at day one. Light live ops only after launch.
Critical target: 85+ Metacritic.

## TECHNICAL FOUNDATION (RAW CODE ONLY)
- Base language progression path: keep Python as high-level orchestration and data layer; rewrite all hot paths (physics resolution, particle systems, rendering submission, collision, audio mixing) first as Cython or C extensions, then as standalone C/C++/Rust shared libraries called from Python, then (if scale demands) full native rewrite of the runtime while preserving the exact same data-driven level format and scene architecture.
- Rendering: custom Vulkan (primary), with Metal and DX12 backends. Immediate-mode or retained-mode hybrid built from scratch. Procedural geometry and shaders authored in-house.
- Physics: custom 2D/2.5D solver (AABB + swept tests initially, expanding to continuous collision and soft constraints). No Box2D or third-party physics library.
- Audio: custom mixer with procedural generation capabilities + streamed banks. Expand the existing pygame.mixer hooks into a full hierarchical adaptive system.
- Asset pipeline: custom tooling written in the same language family. Levels remain pure data (JSON/Python dict/ binary blob).
- Tools: in-house level editor, particle editor, animation tool, and profiler, all talking the same data format as the runtime.
- Platform layer: thin abstraction over OS windowing, input, and file I/O only. No engine middleware.

## PHASE 0: LEGAL, IP, FOUNDATION, AND REPOSITORY HARDENING (0–3 MONTHS)
- Dual-track IP bible (licensed vs fully fictionalized) produced and version-controlled inside the repository.
- All future code and assets must be able to switch tracks without architectural change.
- Harden the existing repository: add continuous integration, automated Classic Mode regression tests that replay all 8 chapters, code formatting, static analysis, and a clear CONTRIBUTING / ARCHITECTURE document.
- Establish performance baselines on the current Python code so every subsequent rewrite can be measured.
- Core leadership roles defined and staffed.
- Vertical-slice team of 12–20 formed around the existing codebase.

## PHASE 1: VERTICAL SLICE ON THE EXISTING ARCHITECTURE (MONTHS 3–12)
Goal: one fully playable, high-production chapter (recommended: expanded Chapter 6–7 hybrid or new Mars landing) that proves every design pillar while remaining 100% on the custom raw-code stack.
- All hot paths profiled and accelerated (C/Cython/Rust modules).
- Expanded audio (procedural + authored beds and SFX).
- First pass of higher-fidelity procedural + authored art while keeping the silhouette language of the current player and environments.
- Failure-recovery loop, one resource interaction, one vehicle/ascent sequence demonstrated.
- External playtests with quantitative gates (completion ≥80%, session length, emotional response matching “earnest determination”).
- Greenlight only if the slice exceeds internal quality bars while staying engine-free.

## PHASE 2: PRE-PRODUCTION AND FULL PIPELINE (MONTHS 12–18)
- Complete GDD and Technical Design Document derived from this plan and the live repository.
- Narrative bible expanding the 8 chapters into a 5-act structure while preserving Classic Mode.
- Custom tool chain locked (level editor, asset compilers, audio middleware, profiler).
- Full data-oriented architecture specification (SoA layouts, job system if needed, streaming for large Mars maps).
- Team ramp to 80–120.

## PHASE 3: PRODUCTION (MONTHS 18–48)
Parallel streams on the single custom codebase:
- Narrative & Level Design: expand to full campaign; all levels remain data-driven and loadable by the same LevelScene architecture.
- Gameplay Systems: combat variety, progressive mobility, Mars colony resource loops (non-mandatory), failure meta that always advances the player.
- Rendering & Art: custom high-fidelity pipeline; procedural generation retained and expanded; destruction and VFX authored in-house.
- Audio: full adaptive score and complete SFX set.
- Platform & Performance: native ports, accessibility suite, cloud save, certification targets.
Continuous integration against Classic Mode. Content lock at month 42–44. Peak team 200–300.

## PHASE 4: POLISH, CERTIFICATION, LAUNCH (MONTHS 48–60+)
Bug bash, performance optimization, platform certification, marketing assets that lead with the mythic arc and “failure is progress”.
Day-one patch pipeline and light live-ops foundation ready.

## POST-LAUNCH
Seasonal Mars content, narrative expansions, metrics-driven iteration. Core single-player remains complete and offline.

## RISK REGISTER
- IP: dual-track always live.
- Scope: every feature must map to the five pillars and pass vertical-slice quality.
- Tone: weekly audits against “earnest, not parody”.
- Technical debt: every acceleration step must preserve Classic Mode bit-for-bit behavior until deliberately extended.
- Performance: continuous measurement against the original Python baselines; raw custom code must demonstrably exceed them.
- Culture: sustainable process; failure in production is data.

## SUCCESS METRICS
Vertical slice: ≥80% completion, strong emotional response.
Alpha: full campaign completable on custom runtime.
Beta: internal scores ≥82, full accessibility, localization ready.
Launch: day-one reviews ≥85, strong retention and narrative completion.

## EXECUTION DIRECTIVES FOR FABLE 5
1. Ingest this document and the live repository state as permanent context.
2. Begin with Phase 0: produce dual IP naming bibles and harden the existing repository (CI, regression tests for all 8 chapters, architecture docs).
3. All code changes are made directly against the public repository using the connected GitHub tools.
4. Never introduce a third-party game engine.
5. Every performance or systems rewrite must keep Classic Mode playable and regression-tested.
6. Log every decision against the design pillars.
7. Prefer original, high-fidelity, data-oriented solutions that grow directly from the existing player, level, and scene code.
8. Preserve the closing sentiment in every path: Failure is progress. The frontier is open.

END OF AUTHORITATIVE PLAN.
All further work is execution of the above against the live repository.
