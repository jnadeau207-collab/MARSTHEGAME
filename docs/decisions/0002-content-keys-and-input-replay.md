# Decision 0002: Stable content keys and deterministic input replay

- Status: Accepted
- Date: 2026-07-26
- Authority: `AUTHORITATIVE_PRODUCTION_PLAN.md`, Phase 0

## Context

The first Phase 0 tranche protected chapter loading, goal completion, save progression, and transitions, but it still bypassed the production control path by moving the player directly to each goal. The initial IP registry also left player-facing chapter copy duplicated across settings, level data, title presentation, and credits.

That combination created two risks:

1. Input buffering, bindings, gamepad virtual actions, and controller behavior could regress while lifecycle-only replay stayed green.
2. The fictionalized identity could drift because runtime strings were not resolved from one stable-key authority.

## Decision

Add version-controlled, run-length-encoded input tracks for every Classic Mode chapter. Replay them twice through the production `InputManager`, `Player`, `LevelScene`, collision geometry, enemies, collectibles, and camera update path. Compare deterministic gameplay signatures before running the existing goal/save/transition lifecycle verification.

Add a stable content-key catalog for every identity-sensitive title, chapter title, level name, subtitle, description, objective, narration line, and credits identity. Resolve the active track at startup and apply only display copy to the existing level dictionaries. Chapter ids, world geometry, entity placement, unlocks, save semantics, and progression remain unchanged.

The input manager accepts both physical binding tokens and virtual action tokens. This is required for deterministic replay and corrects the existing gamepad mismatch where buttons emitted actions such as `jump` while action queries only inspected physical key bindings.

## Design-pillar mapping

1. **Mythic Kinetic Earnestness** — both identity tracks now resolve the complete chapter arc from one catalog.
2. **Player Agency Through Mastery** — CI now exercises actual movement, jump, dash, attack, and interaction input paths.
3. **Multiplanetary Progression** — all eight chapters retain deterministic replay evidence and lifecycle completion.
4. **Procedural + Authored Hybrid** — authored input recordings execute against the existing procedural scene runtime.
5. **Accessibility-First Feel** — buffering and virtual-action behavior are explicit, injectable, and regression-tested.

## Consequences

- CI evidence identifies each recorded track by SHA-256 digest and reports start/end gameplay signatures.
- A track change is a reviewable data change rather than hidden test logic.
- Fictionalization no longer requires scene or gameplay forks.
- Replay tracks are deterministic smoke routes, not yet autonomous full-level speedruns; lifecycle completion remains a separate explicit check.
- Future localization can reuse the same content keys without altering gameplay data.

Failure is progress. The frontier is open.
