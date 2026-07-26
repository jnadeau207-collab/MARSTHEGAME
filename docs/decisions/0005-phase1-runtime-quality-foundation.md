# Decision 0005: Shared Phase 1 runtime-quality foundation

- Status: Accepted
- Date: 2026-07-26
- Authority: `AUTHORITATIVE_PRODUCTION_PLAN.md` V2, Phase 1

## Decision

Begin Phase 1 by moving presentation, accessibility, camera motion, and audio out of isolated scene behavior and into shared deterministic runtime systems.

The engine owns:

- normalized accessibility and audio settings,
- a presentation director for flashes, cinematic framing, camera impulses, and hit-stop scaling,
- a deterministic camera using seeded shake and velocity-derived look-ahead,
- an event-driven procedural audio director with explicit buses and silent fallback,
- a machine-readable quality contract that rejects unearned AAA claims.

## Rationale

A polished vertical slice cannot be assembled reliably from one-off effects. Movement, combat, menus, failure, pickups, terminals, and victory need common presentation and audio semantics so tuning, accessibility, replay evidence, and later content production operate through one contract.

Procedural placeholder audio is intentionally generated through the runtime rather than represented as final production content. It proves event routing, buses, fallback behavior, and integration while authored assets remain pending.

## Consequences

- Existing Classic Mode automatically receives shared presentation and audio routing without changing level data.
- Reduced-motion and intensity settings affect the same global systems used by gameplay.
- Camera shake becomes deterministic for identical seeds and updates.
- CI can verify audio and presentation events without requiring audio hardware.
- The game still cannot claim AAA quality; the complete playable slice and external evidence remain mandatory.
