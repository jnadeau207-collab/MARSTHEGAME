# Phase 2 Campaign Foundation

## Current verdict

- Phase: 2
- Status: in progress
- Campaign: `frontier_campaign`
- Implemented missions: `ares_reach`
- Contracted missions: `relay_echo`
- Playable candidates not promoted: `relay_echo`
- Planned missions: `relay_echo`, `phobos_vector`, `frontier_burn`
- Full-campaign claim: **not achieved**
- AAA-quality claim: **target not achieved**

## What is implemented

Phase 2 begins with a campaign architecture built around the real Phase 1 Mars mission rather than an invented content roadmap.

The repository now provides:

- stable campaign and mission IDs,
- validated mission prerequisites and ordering,
- cycle, duplicate, missing-reference, and self-dependency rejection,
- explicit implemented versus planned mission states,
- deterministic unlock computation,
- campaign attempt and completion transitions,
- transactional campaign save migration,
- fail-closed runtime mission routing,
- a campaign navigator that labels planned missions as planned,
- a machine-readable Phase 2 state and audit.

## Player-facing behavior

The title screen enters **Frontier Campaign**. The campaign navigator shows all authorized mission nodes and their actual state:

- `PLAYABLE` for implemented unlocked missions,
- `COMPLETE` for completed missions,
- `PLANNED` for unlocked but unimplemented nodes,
- `LOCKED` when prerequisites are incomplete.

Only implemented unlocked missions can launch. Completing `ares_reach` records campaign completion and unlocks `relay_echo`, but `relay_echo` remains non-playable through campaign routing until a separate promotion transaction is accepted.

The title screen also enters a real **Accessibility & Settings** scene with keyboard and gamepad navigation. Classic Mode remains a separate protected eight-chapter path.

## Save and progression contract

Campaign state is stored inside the existing checksummed transactional save envelope. Unlock lists are recomputed from the committed graph and are never trusted from disk.

The save validates:

- campaign ID and schema,
- revision and attempt counters,
- known and uniquely completed missions,
- prerequisite-complete mission history,
- exact derived unlock state,
- a current mission that is known and unlocked.

Old saves without campaign data migrate to the default `ares_reach` state. Corrupt campaign state participates in the existing primary/backup recovery path.

## Relay Echo contract tranche

`relay_echo` has an executable mission contract in `game/data/relay_echo.py`. The contract establishes:

- entry and exit state,
- six ordered objectives and their dependency graph,
- seven checkpoint and persistence boundaries,
- five explicit failure and recovery policies,
- deterministic replay requirements,
- localization-ready `mission.relay_echo.*` content keys,
- accessibility requirements,
- CPU, draw, allocation, hitch, enemy, and effect budgets,
- authored/procedural boundaries,
- eight promotion gates.

## Relay Echo transactional state tranche

`game/core/relay_echo_state.py` and the existing transactional save envelope provide:

- derived objective and checkpoint progression,
- explicit attempt and failure transactions,
- contract-backed retained understanding,
- corruption and forged-state rejection,
- legacy migration,
- campaign prerequisite enforcement,
- completion eligibility that remains separate from campaign completion.

## Relay Echo playable-candidate tranche

The repository contains a complete candidate scene and authored world contract:

- all six objectives are playable in order,
- checkpoints restore from transactional state,
- player defeat and relay overload retain contract-defined insight,
- uncommitted fragment pickups reset correctly,
- the guardian breach and echo alignment commit explicit evidence,
- extraction reaches completion eligibility and returns once to the campaign navigator,
- `tools/relay_echo_replay.py` runs the complete path twice and compares exact evidence.

The candidate is intentionally hidden. `game/core/engine.py` does not import or route to `RelayEchoScene`; the campaign catalog still records `relay_echo` as `planned` with no entrypoint. Candidate completion cannot complete the campaign node or unlock `phobos_vector`.

## Relay Echo accessibility and input-parity tranche

The current tranche adds a user-facing settings surface and an accessibility-compliant candidate layer without modifying campaign routing.

The repository now provides:

- normalized Assist Mode and subtitle-background settings,
- high-contrast objective presentation,
- reduced-motion and flash-reduction behavior,
- larger interaction regions and recovery windows under Assist Mode,
- held-interaction alternatives for terminal activation,
- configurable subtitle visibility, background, and scale,
- stable keyboard and gamepad semantic profiles,
- analog and D-pad gamepad navigation,
- explicit gamepad cancel/back semantics,
- deterministic complete-path keyboard and gamepad replay,
- a deterministic assisted reduced-motion replay,
- fail-closed accessibility and parity audit evidence.

All device and accessibility paths must commit the identical Relay Echo mission state and campaign state. Successful parity evidence still does not promote the campaign node.

## Evidence

- `game/data/campaign.py`
- `game/data/relay_echo.py`
- `game/data/relay_echo_candidate.py`
- `game/core/accessibility.py`
- `game/core/campaign.py`
- `game/core/input.py`
- `game/core/input_profiles.py`
- `game/core/relay_echo_accessibility.py`
- `game/core/relay_echo_state.py`
- `game/core/save.py`
- `game/scenes/campaign.py`
- `game/scenes/relay_echo.py`
- `game/scenes/relay_echo_accessible.py`
- `game/scenes/settings.py`
- `config/phase2_campaign.json`
- `tools/phase2_campaign_audit.py`
- `tools/relay_echo_runtime_audit.py`
- `tools/relay_echo_candidate_audit.py`
- `tools/relay_echo_replay.py`
- `tools/relay_echo_accessibility_replay.py`
- `tools/relay_echo_accessibility_audit.py`
- `tests/test_input_profiles.py`
- `tests/test_relay_echo_accessibility.py`
- `tests/test_relay_echo_accessibility_audit.py`
- `docs/RELAY_ECHO_MISSION_CONTRACT.md`
- `docs/RELAY_ECHO_RUNTIME_STATE.md`
- `docs/RELAY_ECHO_PLAYABLE_CANDIDATE.md`
- `docs/RELAY_ECHO_ACCESSIBILITY_AND_INPUT_PARITY.md`
- `docs/decisions/0011-contract-missions-before-runtime.md`
- `docs/decisions/0012-derived-transactional-mission-state.md`
- `docs/decisions/0013-playable-candidate-before-promotion.md`
- `docs/decisions/0014-accessibility-and-input-parity-before-promotion.md`

## What remains

This tranche must pass the full repository matrix before parity and accessibility gates can be recorded as verified. Campaign promotion then remains a separate, narrow change covering engine routing, catalog status, mission-attempt entry, campaign completion, downstream unlock, and promotion-specific replay evidence.

Founder direct play, final authored assets, packaged-build soak, external playtests, and the AAA-quality target remain unresolved evidence gates.
