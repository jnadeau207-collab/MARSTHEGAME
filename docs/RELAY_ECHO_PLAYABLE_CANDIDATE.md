# Relay Echo Playable Candidate

## Status

- Mission ID: `relay_echo`
- Candidate ID: `relay_echo_playable_candidate`
- Campaign catalog status: `planned`
- Campaign entrypoint: none
- Player-facing campaign launch: unavailable
- Candidate path: implemented pending verification

This tranche builds and verifies the complete mission path before campaign promotion. The candidate scene exists in the repository, but the engine does not import or route to it and the campaign navigator continues to display `PLANNED`.

## Complete candidate path

The authored candidate implements the contract’s six objectives:

1. Reach Noctis Relay.
2. Recover three signal fragments.
3. Triangulate the subsurface echo source.
4. Defeat the relay guardians and breach the core.
5. Commit the `redirect` echo alignment.
6. Extract before the relay collapses.

Every objective uses the transactional Relay Echo state API. Scene-local flags do not replace objective, checkpoint, failure, or retained-understanding transactions.

## Failure and recovery evidence

The reference path deliberately exercises:

- player defeat before the first objective,
- relay overload during triangulation.

Both failures persist their contract-defined recovery evidence and telemetry insight. Checkpoint restoration rebuilds enemies and collectibles from authored data so uncommitted fragment pickups are reset instead of becoming invisible progress.

## Deterministic replay

`tools/relay_echo_replay.py` runs the complete candidate twice with the committed deterministic seed and compares full output.

The replay verifies:

- objective and checkpoint order,
- player-down recovery,
- relay-overload recovery,
- three committed signal fragments,
- triangulation evidence,
- guardian breach,
- echo alignment,
- extraction,
- one-shot return to the campaign navigator,
- unchanged campaign completion and downstream unlock state.

## Deliberate non-promotion boundary

Candidate completion produces Relay Echo runtime `completion_eligible` evidence only. It does not:

- mark `relay_echo` complete in the campaign,
- unlock `phobos_vector`,
- expose a campaign runtime entrypoint,
- claim final authored assets,
- claim keyboard/gamepad complete-path parity,
- claim founder direct-play approval,
- claim external playtests or AAA quality.

Promotion must remain a separate reviewed transaction after this candidate and its remaining release evidence are accepted.
