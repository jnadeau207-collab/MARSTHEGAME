# Contributing to STARMAN

## Start with the authority

Read `AUTHORITATIVE_PRODUCTION_PLAN.md` and `ARCHITECTURE.md` before changing code. Work must map to the five design pillars and may not reduce the permanent Classic Mode compatibility surface.

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
ruff check game/data/ip_tracks.py tools tests
ruff format --check game/data/ip_tracks.py tools tests
python -m unittest discover -s tests -v
python tools/classic_mode_replay.py --json-out build/classic-mode-replay.json
python tools/performance_baseline.py --json-out build/performance-baseline.json
```

Use dummy SDL drivers in headless environments:

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m unittest discover -s tests -v
```

## Change rules

- Never add Unreal, Unity, Godot, Bevy, or another game engine.
- Keep level and narrative content data-driven.
- Preserve all eight Classic Mode chapters and their progression order.
- Add or update regression coverage for every behavior change.
- Do not claim a performance improvement without before/after JSON baselines.
- New branded names or likenesses must enter through the dual-track identity registry.
- Record significant architectural decisions under `docs/decisions/`.

## Pull requests

Use focused `agent/<description>` branches. Explain the design-pillar mapping, Classic Mode impact, tests run, baseline impact, and any legal/IP implications. Open incomplete work as a draft.

Failure is progress. The frontier is open.
