# Decision 0009: Separate playable Mars slice outside Classic Mode

- Status: Accepted
- Date: 2026-07-26
- Authority: `AUTHORITATIVE_PRODUCTION_PLAN.md` V2, Phase 1

## Decision

Implement the Phase 1 Mars-landing journey as a separate fictionalized scene and data contract rather than adding chapter 9 or mutating chapter 8.

The slice uses:

- `game/data/phase1_slice.py` for authored world, checkpoint, resource, sentinel, narration, and ascent data,
- `game/entities/mars_sentinel.py` for readable commit-and-recover combat,
- `game/scenes/vertical_slice.py` for journey state, retained learning, resource consequences, checkpoint persistence, ascent, and completion,
- `tools/phase1_slice_replay.py` for deterministic complete-path evidence.

## Rationale

Classic Mode is a permanent compatibility surface with exactly eight chapters. Phase 1 needs freedom to establish a new quality bar without silently changing chapter-eight progression, saves, credits, or replay expectations.

A complete slice must also prove more than traversal. Failure retains telemetry, increasing sentinel warning time. Three power cells disrupt the relay, reducing high-tier durability and charge speed. The player therefore changes the next encounter through a resource decision.

## Consequences

- Classic Mode remains exactly chapters 1–8.
- The title screen exposes a separate Phase 1 path.
- Phase 1 checkpoint, failure, phase, completion, and relay state persist transactionally.
- The slice can evolve without changing Classic Mode save semantics.
- CI requires a deterministic start-to-finish journey replay.
- Playability does not grant an AAA-quality claim; authored content, direct play, packaged soak, accessibility closure, and external evidence remain mandatory.
