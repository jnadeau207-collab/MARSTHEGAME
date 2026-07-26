# Decision 0007: Fixed-step simulation and frame-pacing evidence

- Status: Accepted
- Date: 2026-07-26
- Authority: `AUTHORITATIVE_PRODUCTION_PLAN.md` V2, Phase 1

## Decision

Run gameplay on a deterministic 60 Hz simulation scheduler rather than passing variable render-frame time directly into gameplay.

The runtime now:

- accumulates real frame time,
- emits zero or more fixed simulation steps,
- caps catch-up work,
- records dropped wall time instead of allowing an unbounded spiral,
- preserves interpolation alpha for future render interpolation,
- records bounded frame-time history, hitches, percentiles, and dropped time,
- latches hardware input edges until one simulation step consumes them,
- advances input buffers in simulation steps rather than render frames.

## Rationale

Action timing, replay behavior, checkpoints, combat tuning, and future multiplayer or rollback experiments require a stable simulation cadence. A variable-step loop makes gameplay outcomes dependent on rendering performance and cannot support trustworthy tuning or diagnostics.

Input must be sampled independently from simulation. Otherwise a fast render frame can lose a press before simulation runs, while a slow frame can apply one press repeatedly across several catch-up steps.

## Consequences

- Existing scene code continues receiving `dt=1.0`, preserving the frame-tuned Classic Mode contract.
- Rendering can occur with zero, one, or multiple simulation steps per frame.
- Catch-up is bounded to protect responsiveness.
- Dropped time and frame hitches become observable evidence instead of hidden behavior.
- Future rendering work may interpolate between simulation states using `render_alpha` without changing simulation results.
