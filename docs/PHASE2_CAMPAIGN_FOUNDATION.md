# Phase 2 Campaign Foundation

## Current verdict

- Phase: 2
- Status: in progress
- Campaign: `frontier_campaign`
- Implemented missions: `ares_reach`, `relay_echo`
- Planned missions: `phobos_vector`, `frontier_burn`
- Full-campaign claim: **not achieved**
- AAA-quality claim: **target not achieved**

## Campaign architecture

The campaign is a validated, transactional mission graph with stable IDs, prerequisite ordering, cycle rejection, deterministic unlock computation, attempt history, completion history, and fail-closed runtime routing.

The player-facing navigator reports actual states:

- `PLAYABLE` for implemented, unlocked, incomplete missions,
- `COMPLETE` for completed missions,
- `PLANNED` for unlocked but unimplemented missions,
- `LOCKED` when prerequisites are incomplete.

Classic Mode remains a separate protected eight-chapter path.

## Ares Reach

`ares_reach` remains the campaign start and uses the verified Phase 1 vertical slice. Its completion is transactionally synchronized into campaign state and unlocks Relay Echo.

## Relay Echo implementation history

Relay Echo was built and verified in cumulative layers:

1. executable mission contract,
2. derived transactional mission state,
3. hidden complete playable candidate,
4. keyboard/gamepad and accessibility parity,
5. campaign promotion.

The earlier layers remain independently replayed and audited after promotion.

## Relay Echo promotion

The catalog now records Relay Echo as implemented with entrypoint `relay_echo`.

The promoted route wraps the verified scene layers:

- `RelayEchoScene` owns authored gameplay and transactional objective/failure flow.
- `AccessibleRelayEchoScene` owns assist, reduced motion, contrast, subtitles, and held-interaction behavior.
- `PromotedRelayEchoScene` owns only the final campaign-completion boundary.

### Atomic launch

`prepare_relay_echo_launch` computes campaign-attempt and mission-attempt state together. The engine saves once and rolls both state objects back if persistence fails.

An incomplete active mission resumes. A completed mission does not silently reset; completed-mission replay remains a separate future transaction.

### Atomic completion

`complete_relay_echo_campaign` computes final extraction and campaign completion together. The promoted scene saves once and rolls both state objects back if persistence fails.

Successful completion:

- commits Relay Echo checkpoint 6,
- records Relay Echo in campaign completion history,
- unlocks `phobos_vector`,
- advances campaign current mission to `phobos_vector`,
- returns once to the campaign navigator.

## Phobos Vector boundary

Phobos Vector becomes unlocked after Relay Echo completion but remains `PLANNED` with no entrypoint. It is visible in the campaign graph but cannot launch.

Frontier Burn remains planned and locked behind Phobos Vector.

## Accessibility and input parity

Relay Echo retains verified evidence for:

- keyboard complete-path replay,
- gamepad complete-path replay,
- D-pad and cancel/back semantics,
- Assist Mode,
- Reduced Motion,
- flash reduction,
- high-contrast objectives,
- held-interaction alternatives,
- subtitle visibility, background, and scale.

The exact parity evidence is preserved in manifest field `relay_echo_accessibility_parity_run`.

## Deterministic evidence

CI protects:

- all eight Classic Mode chapters,
- the complete Phase 1 replay,
- the hidden Relay Echo candidate replay,
- the Relay Echo accessibility/input-parity replay,
- the promoted Relay Echo launch-to-Phobos replay,
- Phase 0, Phase 1, Phase 2, runtime, candidate, accessibility, and promotion audits,
- same-runner performance regression policy.

## Remaining work and truth

Relay Echo promotion does not satisfy:

- completed-mission replay/reset design,
- founder direct-play approval,
- final authored assets,
- packaged-build soak,
- external playtests,
- Phobos Vector implementation,
- Frontier Burn implementation,
- full-campaign completion,
- AAA-quality evidence.

The repository must continue to report those gates as unresolved.

## Primary evidence

- `game/data/campaign.py`
- `game/data/relay_echo.py`
- `game/core/campaign.py`
- `game/core/relay_echo_state.py`
- `game/core/relay_echo_promotion.py`
- `game/scenes/relay_echo.py`
- `game/scenes/relay_echo_accessible.py`
- `game/scenes/relay_echo_promoted.py`
- `config/phase2_campaign.json`
- `tools/relay_echo_replay.py`
- `tools/relay_echo_accessibility_replay.py`
- `tools/relay_echo_promotion_replay.py`
- `tools/phase2_campaign_audit.py`
- `tools/relay_echo_runtime_audit.py`
- `tools/relay_echo_candidate_audit.py`
- `tools/relay_echo_accessibility_audit.py`
- `tools/relay_echo_promotion_audit.py`
- `docs/RELAY_ECHO_CAMPAIGN_PROMOTION.md`
- `docs/decisions/0015-atomic-campaign-promotion.md`
