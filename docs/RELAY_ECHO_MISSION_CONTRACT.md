# Relay Echo Mission Contract

## Status

- Mission ID: `relay_echo`
- Campaign: `frontier_campaign`
- Lifecycle: `contracted_not_playable`
- Catalog status: `planned`
- Runtime entrypoint: none
- Prerequisite: completed `ares_reach`
- Downstream unlock on eventual completion: `phobos_vector`

This document describes an executable contract, not completed mission content. The machine authority is `game/data/relay_echo.py`, and `tools/phase2_campaign_audit.py` rejects any mismatch between this contract, the campaign catalog, and the Phase 2 truth manifest.

## Intended journey

Relay Echo is a 22–32 minute fictionalized Mars mission at Noctis Relay. Its committed objective order is:

1. Reach Noctis Relay.
2. Recover signal fragments under adaptive pressure.
3. Triangulate the echo source.
4. Breach the relay core.
5. Commit an echo alignment with downstream consequences.
6. Extract before the relay collapses.

The critical path and checkpoint order are authored. Procedural systems may vary optional routes and encounter composition only behind a deterministic seed; they may not reorder objectives or move checkpoint boundaries.

## Failure and retained understanding

Failure must advance understanding rather than erase it. The contract defines explicit recovery semantics for:

- player defeat,
- a broken signal-fragment chain,
- relay overload,
- alignment desynchronization,
- a missed extraction window.

Each failure state identifies its recovery boundary, retained transactional save keys, and telemetry-insight delta. Runtime implementation may not replace these policies with an unbounded full-mission reset.

## Checkpoint and save boundary

Seven ordered checkpoints cover insertion through completion. Every objective commits through a matching checkpoint. The future runtime save extension must persist only validated Relay Echo state inside the existing checksummed transactional envelope.

Eventual mission completion must atomically:

- mark `relay_echo` complete,
- unlock `phobos_vector`,
- persist echo alignment and telemetry insight,
- advance campaign revision,
- return to the campaign navigator.

## Deterministic replay contract

The future reference replay is already specified with:

- a fixed seed,
- a maximum simulation-frame budget,
- exact objective order,
- exact checkpoint history,
- required failure evidence,
- a required `relay_echo_completed` transition,
- stable evidence fields for state, failure, checkpoint, frame, and campaign-transition histories.

The mission remains non-playable until this replay exists and passes twice with identical output.

## Performance budgets

The contract requires:

- 60 Hz simulation,
- update p95 at or below 7.5 ms,
- draw p95 at or below 7.5 ms,
- update plus draw p95 fitting inside one simulation frame,
- a 25 ms hitch threshold,
- at most 4,096 transient allocation bytes per frame,
- soft caps of 14 active enemies and 96 active effects.

These are implementation gates, not claims of current measured performance.

## Accessibility requirements

The complete path must support:

- assist mode,
- adjustable camera shake,
- flash reduction,
- hold/toggle alternatives,
- high-contrast objective treatment,
- reduced motion,
- subtitle backgrounds.

Promotion to implemented also requires keyboard/gamepad complete-path parity and accessibility-path evidence. Those external gates are not yet satisfied.

## Content package requirements

The following packages are required and remain unclaimed:

- environment,
- encounters,
- audio,
- VFX,
- presentation,
- UI,
- localization.

All player-facing strings are represented by `mission.relay_echo.*` content keys. Final copy, art, music, animation, effects, and authored encounter assets do not yet exist merely because their contracts do.

## Promotion rule

`relay_echo` may move from `planned` to `implemented` only when all committed implementation gates exist and pass:

- runtime entrypoint,
- transactional mission save state,
- deterministic reference replay,
- objective and failure-state tests,
- accessibility-path verification,
- performance-budget evidence,
- authored content package,
- campaign completion transaction.

Until then, the campaign navigator must continue to display `PLANNED` and runtime routing must reject launch.
