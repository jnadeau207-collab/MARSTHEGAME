# Contributing to STARMAN

## Start with the authority

Read `AUTHORITATIVE_PRODUCTION_PLAN.md`, `ARCHITECTURE.md`, and `docs/PHASE0_COMPLETION.md` before changing code. Work must map to the five design pillars and may not reduce the permanent Classic Mode compatibility surface.

## Local setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install --upgrade pip -r requirements.txt -r requirements-dev.txt
```

Run the game with `python main.py`.

## Required checks

```bash
python -m compileall -q main.py game tools tests
ruff check game/core/gfx.py game/core/input.py game/core/settings.py \
  game/data/classic_replays.py game/data/content.py game/data/ip_tracks.py \
  game/scenes/credits.py game/scenes/title.py tools tests
ruff format --check game/core/gfx.py game/core/input.py game/core/settings.py \
  game/data/classic_replays.py game/data/content.py game/data/ip_tracks.py \
  game/scenes/credits.py game/scenes/title.py tools tests
python -m unittest discover -s tests -v
python -m tools.classic_mode_replay --json-out build/classic-mode-replay.json
python -m tools.performance_baseline --warmup-rounds 2 --rounds 7 \
  --json-out build/performance-baseline.json
python -m tools.validate_phase0_organization \
  --json-out build/phase0-organization.json
```

Use dummy SDL drivers in headless environments:

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m unittest discover -s tests -v
```

The pull-request workflow performs the hard performance verdict by measuring the base revision, the candidate, and the base revision again on one runner. Do not replace that comparison with unrelated historical or cross-machine numbers.

## Change rules

- Never add Unreal, Unity, Godot, Bevy, or another game engine.
- Keep level geometry, narrative content, and replay tracks data-driven.
- Preserve all eight Classic Mode chapters and their progression order.
- Route identity-sensitive player-facing copy through stable keys in `game/data/content.py`.
- Use virtual gameplay actions rather than platform key codes in replay data.
- Add or update regression coverage for every behavior change.
- Do not claim a performance improvement without same-runner before/after JSON evidence.
- Do not loosen `config/performance_thresholds.json` merely to turn CI green.
- Keep every agent-owned operating lane accountable to the human authority in `config/phase0_organization.json`.
- Never inflate functional seats into an unsupported human-headcount claim.
- New branded names or likenesses must enter through the dual-track identity registry.
- Record significant architectural decisions under `docs/decisions/`.

## Pull requests

Use focused `agent/<description>` branches. Explain the design-pillar mapping, Classic Mode impact, tests run, performance verdict, organizational impact, and any legal/IP implications. Open incomplete work as a draft.

Failure is progress. The frontier is open.
