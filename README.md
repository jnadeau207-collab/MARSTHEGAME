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
python main.py
```

## Controls

| Action    | Keyboard              | Gamepad (typical) |
|-----------|-----------------------|-------------------|
| Move      | A/D or ←/→            | Left stick        |
| Jump      | Space / K             | A / Cross         |
| Double-jump | Space again in air (Ch.6+) | A again     |
| Dash      | L-Shift / J           | X                 |
| Attack    | J / Z                 | B                 |
| Interact  | E / F                 | Y                 |
| Pause     | Esc / P               | Start             |
| Confirm   | Enter / Space         | A                 |

**Feel:** coyote time, jump buffering, responsive dash, double-jump from SpaceX onward, light hit-stop & screen shake.

## Story Arc (all chapters present)

1. **Pretoria Streets** — polished vertical slice: combat, scavenging, escape  
2. **Crossing (Canada)** — timing + code terminals  
3. **College & Zip2** — pressure, rivals, “ship the product”  
4. **X.com / PayPal Wars** — expanded arena with multi-tier platforms  
5. **Tesla Factory Floor** — longer production run, machine blocks  
6. **SpaceX: Failures Before Flight** — scaffold climb + double-jump unlock  
7. **Starship to Mars** — full vertical ascent (platforms tuned for double-jump)  
8. **Mars Colony** — expanded first landing / outpost claim  

Completing a chapter auto-advances and saves progress (one JSON slot).

## Architecture

```
main.py
game/
  core/       engine, input, camera, particles, save, settings
  entities/   player, enemy, collectible
  scenes/     title, chapter select, level, credits
  data/       levels.py  (data-driven chapter defs)
```

- Scene stack / state machine  
- Data-driven levels (dict) — new Mars missions can be added without engine rewrites  
- One save slot: `savegame.json`  
- Settings: volume placeholders, fullscreen (F11), FPS toggle  

## Design Notes

- **Tone:** earnest, larger-than-life, quiet determination between chaos. Not parody, not documentary.  
- **Art:** procedural silhouettes with improved detail (player hair/jacket, enemy brows, platform tops, parallax stars, chapter skies, animated goal flag). Still original — no external packs.  
- **Juice:** particles, hit-stop, subtle shake.  
- **Audio:** mixer initialized; expand with procedural chiptune / ambient layers.  

## Recent improvements

- Stronger base jump + **double-jump** unlocked from chapter 6 (SpaceX) onward  
- Starship ascent platforms re-spaced so the climb is actually completable  
- Chapters 4–8 given denser platforms, more enemies, and more collectibles  
- Visual pass: detailed player, enemies, collectible icons, platform highlights, parallax backgrounds  

## What to expand next

1. **Audio** — procedural or hand-authored chiptune beds per chapter; SFX for dash, hit, terminal, boom.  
2. **Mars depth** — base-building lite, oxygen/power/water loops, rover exploration.  
3. **Chapter 4–7 systems** — negotiation QTEs, factory automation puzzles, rocket assembly + failure meta.  
4. **Polish** — more enemy variety, boss-lite encounters, rebind UI, accessibility options.  

## License / Assets

All code and procedural art direction original for this project.  
No scraped or paid asset packs. Elon Musk / company names used in a narrative, transformative, non-commercial fan-work spirit; replace or license appropriately for any commercial release.

---

*Failure is progress. The frontier is open.*
