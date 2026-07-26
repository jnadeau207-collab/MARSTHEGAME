# ADR 0012: Derive Mission Runtime State From Transaction Evidence

## Status

Accepted — July 26, 2026

## Context

Relay Echo has a validated mission contract but no playable runtime. Its objective, checkpoint, failure, and persistence model must be reliable before scene implementation begins.

Persisting every runtime field independently would allow saves to claim impossible combinations—for example a late checkpoint without completed objectives, retained insight without failures, or campaign completion without a playable mission.

## Decision

Mission runtime state is transactional and derived wherever possible.

For Relay Echo:

- objective completion is an ordered prefix of the contract,
- checkpoint position follows objective completion,
- current state and objective follow checkpoint position,
- telemetry insight follows validated failure history,
- revision follows attempt, objective, and failure transactions,
- completion eligibility follows the complete objective path,
- campaign completion remains a separate transaction unavailable while the mission is planned.

The state is stored inside the existing checksummed transactional save envelope. Legacy saves migrate to the default state. Runtime progress is valid only after the campaign prerequisite is complete and Relay Echo is unlocked.

## Consequences

- Corrupt or hand-edited saves fail closed instead of creating contradictory mission state.
- Scene code will consume a stable transaction API rather than mutate arbitrary dictionaries.
- Deterministic replay can compare emitted transition evidence.
- Failure retains understanding through explicit history instead of ad hoc scene fields.
- Reaching the final runtime checkpoint does not silently promote a planned mission or unlock downstream content.
- Future mission runtime models should use the same evidence-first pattern unless a documented reason requires another design.
