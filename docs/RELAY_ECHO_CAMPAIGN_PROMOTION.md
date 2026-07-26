# Relay Echo Campaign Promotion

## Status

Relay Echo is promoted from a hidden candidate to an implemented campaign mission in this tranche.

The campaign catalog now records:

- `ares_reach`: implemented, `vertical_slice`
- `relay_echo`: implemented, `relay_echo`
- `phobos_vector`: planned, no entrypoint
- `frontier_burn`: planned, no entrypoint

Promotion does not claim the full campaign, final authored assets, packaged-build approval, external playtest approval, or AAA quality.

## Atomic launch transaction

`prepare_relay_echo_launch` computes campaign and mission state before assigning either one.

A valid launch requires:

1. Ares Reach is complete.
2. Relay Echo is unlocked and implemented.
3. Relay Echo has not already completed.
4. Campaign attempt state validates.
5. Relay Echo attempt state validates.
6. The combined state saves successfully once.

If validation or persistence fails, both campaign and Relay Echo state are restored.

An active incomplete attempt resumes its Relay Echo checkpoint while recording a new campaign launch attempt. A completed mission does not silently reset; replay reset remains a separate future transaction.

## Atomic completion transaction

`complete_relay_echo_campaign` computes the final mission objective and campaign completion before assigning either state.

The transaction must prove:

- `extract_before_collapse` is the current objective,
- Relay Echo reaches checkpoint 6 and completion eligibility,
- Relay Echo is recorded in campaign completion history,
- `phobos_vector` becomes unlocked,
- campaign current mission advances to `phobos_vector`.

The promoted scene saves the combined result once. A persistence failure restores both state objects.

## Scene architecture

The promoted route deliberately wraps the verified layers:

1. `RelayEchoScene` owns the authored candidate and transactional objective/failure flow.
2. `AccessibleRelayEchoScene` applies assist, reduced motion, contrast, subtitles, and held-interaction behavior.
3. `PromotedRelayEchoScene` adds only atomic campaign completion.

This keeps campaign mutation out of the candidate and accessibility layers.

## Campaign navigator behavior

The navigator launches implemented, unlocked, incomplete missions.

A completed Relay Echo node is displayed as complete but cannot be launched again until an explicit replay-reset transaction is designed and verified. The UI reports that replay is not yet authorized instead of entering an invalid completed state.

Phobos Vector becomes visible and unlocked after Relay Echo completion, but remains `PLANNED` and cannot launch.

## Deterministic promotion replay

`tools/relay_echo_promotion_replay.py` runs the complete promoted mission twice and requires exact equality.

It verifies:

- combined launch transaction,
- player-down recovery,
- fragment collection,
- relay-overload recovery,
- triangulation,
- guardian breach,
- echo alignment,
- extraction,
- combined completion transaction,
- Relay Echo in campaign completion history,
- Phobos Vector unlocked and selected as current mission,
- Phobos Vector still planned and non-playable,
- one return to the campaign navigator.

## Remaining gates

The following remain unresolved after promotion:

- completed-mission replay/reset design,
- founder direct-play approval,
- final authored asset completion,
- packaged-build soak,
- external playtests,
- later campaign missions,
- full-campaign completion,
- AAA-quality evidence.
