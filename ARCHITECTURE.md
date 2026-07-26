# STARMAN Architecture

## Authority and invariants

`AUTHORITATIVE_PRODUCTION_PLAN.md` is the product and technical authority. The current eight-chapter game is **Classic Mode** and is a permanent compatibility surface. New systems are additive until a deliberately approved migration exists.

Non-negotiable runtime invariants:

- No third-party game engine.
- Chapters remain data-driven and loadable through the existing scene architecture.
- Classic Mode chapters 1–8 must continue to load, complete, save, and transition in order.
- The default `real_world` identity must preserve current prototype behavior and copy.
- The `fictionalized` identity must be selectable without gameplay or level-schema changes.
- Performance work must be measured against recorded Python baselines before replacement.

## Current runtime layers

```text
main.py
  -> game.core.engine.Engine
       -> scene stack
       -> input / save / particles / settings
       -> game.scenes.*
            -> game.entities.*
            -> game.data.levels.LEVELS
```

### Core

`game/core` owns the application loop, input abstraction, camera, particles, settings, and save state. Scene code may consume these services through the engine contract but should not create alternate global loops.

### Scenes

`game/scenes` owns title, chapter selection, level runtime, and credits. `LevelScene` is the compatibility boundary for Classic Mode. New campaign and tool work should extend scene/data contracts rather than fork them.

### Entities

`game/entities` owns player, enemy, and collectible simulation/rendering. Hot-path rewrites must retain observable behavior behind the same Python-facing contracts until an explicit versioned migration.

### Data and identity

`game/data/levels.py` remains the authoritative Classic Mode level dataset. `game/data/ip_tracks.py` centralizes switchable narrative identity. `STARMAN_IP_TRACK=real_world` is the current prototype default; `STARMAN_IP_TRACK=fictionalized` selects original names.

## Phase 0 verification architecture

- `tests/test_classic_mode_contract.py` protects the eight-chapter data contract.
- `tools/classic_mode_replay.py` headlessly instantiates every chapter, triggers its goal, verifies save progression, and verifies the next-chapter/credits transition.
- `tools/performance_baseline.py` records scene setup, update, and offscreen draw timings as JSON evidence.
- GitHub Actions runs Python 3.11 and 3.12 quality gates and uploads replay/performance evidence.
- Ruff initially operates as a ratchet over new Phase 0 infrastructure. Legacy files enter the formatting gate as they are deliberately touched and reviewed.

## Planned native boundary

The progression path remains Python orchestration first, then measured acceleration of isolated hot paths through Cython/C/C++/Rust libraries. Native modules must expose narrow deterministic interfaces, preserve level data compatibility, and provide a Python fallback until parity is proven.

Failure is progress. The frontier is open.
