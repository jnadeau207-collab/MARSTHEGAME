# ADR 0014: Verify Accessibility and Input Parity Before Mission Promotion

- Status: Accepted
- Date: 2026-07-26

## Context

A complete mission path can still exclude players or behave differently across devices. A single replay driven by abstract action tokens cannot prove keyboard/gamepad parity, and a list of accessibility settings cannot prove that the mission consumes those settings correctly.

Relay Echo already has a verified contract, transactional runtime state, hidden playable candidate, and deterministic complete-path replay. The campaign node remains planned and has no runtime entrypoint.

## Decision

Relay Echo will not be promoted until a separate tranche verifies accessibility and input parity.

The tranche must:

1. expose a user-facing accessibility settings scene;
2. normalize every mission accessibility capability at the runtime boundary;
3. implement mission behavior for assist, reduced motion, flash reduction, high contrast, held-interaction alternatives, and subtitle presentation;
4. provide stable keyboard and gamepad input profiles;
5. include D-pad and cancel/back semantics in the gamepad hardware boundary;
6. execute the complete mission path twice for each device profile;
7. execute a complete assisted reduced-motion path using held interactions;
8. require identical committed mission and campaign outcomes;
9. preserve the planned, hidden campaign state throughout verification.

## Consequences

- Device parity is proven through distinct input representations rather than duplicated abstract inputs.
- Accessibility settings become player-facing product behavior instead of configuration-only data.
- Mission accessibility can evolve independently of the verified transactional state core.
- Replay and audit costs increase, but regressions become attributable and fail closed.
- Successful parity evidence still does not imply campaign promotion, final content, external playtest approval, or AAA quality.

## Rejected alternatives

### Promote first and patch accessibility later

Rejected because it would make an inaccessible or device-divergent path player-facing.

### Treat virtual action replay as gamepad evidence

Rejected because it does not prove physical gamepad mapping, D-pad navigation, or cancel/back semantics.

### Verify settings existence without a complete mission path

Rejected because stored settings do not prove mission behavior, completion, recovery, or transactional equivalence.
