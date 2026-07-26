# STARMAN Architecture

## Authority and invariants

`AUTHORITATIVE_PRODUCTION_PLAN.md` is the product and technical authority. The current eight-chapter game is **Classic Mode** and is a permanent compatibility surface. New systems are additive until a deliberately approved migration exists.

Non-negotiable runtime invariants:

- No third-party game engine.
- Chapters remain data-driven and loadable through the existing scene architecture.
- Classic Mode chapters 1–8 must continue to load, accept controls, complete, save, and transition in order.
- The default `real_world` identity must preserve current prototype behavior and copy.
- The `fictionalized` identity must be selectable without gameplay, geometry, save, or level-schema forks.
- Performance work must be measured against recorded Python baselines before replacement.

## Current runtime layers

```text
main.py
  -> game.core.engine.Engine
       -> scene stack
       -> game.core.input.InputManager
       -> save / particles / settings
       -> game.scenes.*
            -> game.entities.*
            -> game.data.levels.LEVELS
            -> game.data.content stable keys
```

### Core

`game/core` owns the application loop, input abstraction, camera, particles, settings, and save state. Scene code may consume these services through the engine contract but should not create alternate global loops.

`InputManager.update_from_actions()` is the deterministic seam for tests, replay tooling, future accessibility adapters, and gamepad virtual actions. It shares the same pressed/held/released and buffer state used by hardware polling; replay does not use a separate controller implementation.

### Scenes

`game/scenes` owns title, chapter selection, level runtime, and credits. `LevelScene` is the compatibility boundary for Classic Mode. New campaign and tool work should extend scene/data contracts rather than fork them.

### Entities

`game/entities` owns player, enemy, and collectible simulation/rendering. Hot-path rewrites must retain observable behavior behind the same Python-facing contracts until an explicit versioned migration.

### Data, content, and identity

`game/data/levels.py` remains the authoritative Classic Mode geometry and entity dataset. `game/data/ip_tracks.py` centralizes switchable narrative identity. `game/data/content.py` maps stable content keys to complete player-facing copy and applies the selected copy without changing chapter ids or gameplay data. `STARMAN_IP_TRACK=real_world` is the current prototype default; `STARMAN_IP_TRACK=fictionalized` selects original names.

`game/data/classic_replays.py` stores reviewable run-length-encoded action tracks. Tracks contain virtual gameplay actions, not platform-specific key codes, so bindings and future input devices can feed the same action contract.

## Phase 0 verification architecture

- `tests/test_classic_mode_contract.py` protects the eight-chapter geometry, progression, and content-key contract.
- `tests/test_content_catalog.py` proves both IP tracks expose identical stable keys and preserve gameplay data.
- `tests/test_input_manager.py` protects physical bindings, virtual actions, transitions, and buffering.
- `tools/classic_mode_replay.py` runs every recorded input track twice through production gameplay, compares deterministic signatures, then verifies goal completion, save progression, and next-chapter/credits transitions.
- `tools/performance_baseline.py` records scene setup, update, and offscreen draw timings as JSON evidence.
- GitHub Actions runs Python 3.11 and 3.12 quality gates and uploads replay/performance evidence.
- Ruff operates as a ratchet. Legacy files enter the formatting gate as they are deliberately touched and reviewed.

## Planned native boundary

The progression path remains Python orchestration first, then measured acceleration of isolated hot paths through Cython/C/C++/Rust libraries. Native modules must expose narrow deterministic interfaces, preserve level data compatibility, and provide a Python fallback until parity is proven.

Failure is progress. The frontier is open.
