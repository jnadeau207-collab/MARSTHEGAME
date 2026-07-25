# STARMAN: An Elon Odyssey

A side-scrolling / arena-hybrid narrative action game.  
You are Elon. The arc is mythic, kinetic, and earnest — grit to multiplanetary resolve.

**Pure Python + Pygame.** No external asset packs. Procedural + hand-authored shapes. Original simple audio hooks ready for expansion.

## Requirements

- Python 3.11+ (tested on 3.12)
- pygame ≥ 2.5

```bash
pip install -r requirements.txt
```

## Run

```bash
cd starman   # or the repo root if files are at top level
python main.py
```

## Controls

| Action    | Keyboard              | Gamepad (typical) |
|-----------|-----------------------|-------------------|
| Move      | A/D or ←/→            | Left stick        |
| Jump      | Space / K             | A / Cross         |
| Dash      | L-Shift / J           | X                 |
| Attack    | J / Z                 | B                 |
| Interact  | E / F                 | Y                 |
| Pause     | Esc / P               | Start             |
| Confirm   | Enter / Space         | A                 |

**Feel:** coyote time, jump buffering, responsive dash, light hit-stop & screen shake.

## Story Arc (all chapters present)

1. **Pretoria Streets** — polished vertical slice: combat, scavenging, escape  
2. **Crossing (Canada)** — timing + code terminals  
3. **College & Zip2** — pressure, rivals, “ship the product”  
4. **X.com / PayPal Wars** — scaffolded arena waves  
5. **Tesla Factory Floor** — scaffolded production run  
6. **SpaceX: Failures Before Flight** — scaffolded workshop / pad  
7. **Starship to Mars** — scaffolded vertical ascent sequence  
8. **Mars Colony** — scaffolded first landing / outpost claim  

Chapters 1–3 are fully playable loops. 4–8 each contain a solid encounter and goal so the full narrative can be walked end-to-end. Completing a chapter auto-advances and saves progress (one JSON slot).

## Architecture

```
main.py
game/
  core/       engine, input, camera, particles, save, settings
  entities/   player, enemy, collectible
  scenes/     title, chapter select, level, credits
  data/       levels.py  (data-driven chapter defs)
  ui/         (reserved)
  systems/    (reserved)
assets/       images, sounds, fonts (empty – shapes are procedural)
```

- Scene stack / state machine  
- Data-driven levels (dict) — new Mars missions can be added without engine rewrites  
- One save slot: `savegame.json`  
- Settings: volume placeholders, fullscreen (F11), FPS toggle  

## Design Notes

- **Tone:** earnest, larger-than-life, quiet determination between chaos. Not parody, not documentary.  
- **Art:** limited intentional palettes per chapter, readable silhouettes, high contrast.  
- **Juice:** particles, hit-stop, subtle shake. Damage numbers omitted for clarity.  
- **Audio:** no copyrighted music. Mixer initialized; expand with procedural chiptune / ambient layers.  

## What to expand next

1. **Art pass** — replace rect silhouettes with cohesive pixel / low-poly-inspired frames (still original).  
2. **Audio** — procedural or hand-authored chiptune beds per chapter; SFX for dash, hit, terminal, boom.  
3. **Mars depth** — base-building lite, oxygen/power/water loops, rover exploration, multi-mission campaign.  
4. **Chapter 4–7 systems** — negotiation QTEs, factory automation puzzles, rocket assembly + failure meta, docking / G-force rhythm.  
5. **Polish** — more enemy variety, boss-lite encounters, rebind UI, accessibility options.  

## License / Assets

All code and procedural art direction original for this project.  
No scraped or paid asset packs. Elon Musk / company names used in a narrative, transformative, non-commercial fan-work spirit; replace or license appropriately for any commercial release.

---

*Failure is progress. The frontier is open.*
