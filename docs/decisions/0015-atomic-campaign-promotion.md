# ADR 0015: Promote Missions Through Atomic Campaign Transactions

- Status: Accepted
- Date: 2026-07-26

## Context

Relay Echo has a verified contract, transactional mission state, complete playable candidate, deterministic replay, keyboard/gamepad parity, and accessibility-path evidence.

Campaign promotion introduces two new cross-domain boundaries:

- launching the campaign node must update both campaign attempt state and mission attempt state;
- completing extraction must update both mission completion state and campaign completion/unlock state.

Sequential mutation or sequential saves could leave the campaign and mission state disagreeing after a validation or persistence failure.

## Decision

Relay Echo promotion uses two pure in-memory combined transactions:

1. `prepare_relay_echo_launch`
2. `complete_relay_echo_campaign`

Each transaction computes and validates both state objects before assigning either one. The engine or promoted scene then persists the combined state exactly once. On persistence failure, both original state objects are restored.

The promoted scene subclasses the verified accessibility scene and overrides only the final-objective persistence boundary. Candidate gameplay and accessibility behavior remain independently testable.

Completed Relay Echo missions cannot launch again until an explicit replay-reset transaction exists. Phobos Vector may be unlocked by completion while remaining planned and non-playable.

## Consequences

- Campaign and mission progression cannot be partially committed by the promoted route.
- Launch and completion failures are attributable and recoverable.
- Candidate, accessibility, and campaign-mutation responsibilities stay separated.
- Promotion replay can verify the exact launch-to-successor lifecycle.
- Completed-mission replay is intentionally unavailable rather than implicitly resetting durable state.
- Promotion does not imply final content, external approval, full-campaign completion, or AAA quality.

## Rejected alternatives

### Save campaign launch before preparing mission state

Rejected because a mission-state failure would leave a recorded campaign attempt without a valid mission attempt.

### Save final objective before campaign completion

Rejected because a campaign-state failure would leave Relay Echo complete without unlocking its successor.

### Reset completed state automatically on launch

Rejected because replay semantics, retained evidence, campaign attempts, and checkpoint history require a separate explicit design.

### Put campaign completion in the candidate base scene

Rejected because it would entangle the previously verified candidate and accessibility layers with promotion-specific mutation.
