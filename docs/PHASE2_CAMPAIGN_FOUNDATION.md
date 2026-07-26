# Phase 2 Campaign Foundation

## Current verdict

- Phase: 2
- Status: in progress
- Campaign: `frontier_campaign`
- Implemented missions: `ares_reach`
- Contracted but non-playable missions: `relay_echo`
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

Only implemented unlocked missions can launch. Completing `ares_reach` records campaign completion and unlocks `relay_echo`, but `relay_echo` remains non-playable until its entrypoint and content exist.

Classic Mode remains a separate protected eight-chapter path.

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

`relay_echo` now has an executable mission contract in `game/data/relay_echo.py`. The contract establishes:

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

This does not make Relay Echo playable. The campaign catalog still records it as `planned`, its runtime entrypoint remains `None`, and fail-closed routing continues to reject launch. The contract exists to prevent runtime implementation from drifting or claiming completion without evidence.

## Evidence

- `game/data/campaign.py`
- `game/data/relay_echo.py`
- `game/core/campaign.py`
- `game/scenes/campaign.py`
- `config/phase2_campaign.json`
- `tools/phase2_campaign_audit.py`
- `tests/test_campaign.py`
- `tests/test_campaign_save.py`
- `tests/test_phase2_campaign_audit.py`
- `tests/test_relay_echo_contract.py`
- `docs/RELAY_ECHO_MISSION_CONTRACT.md`
- `docs/decisions/0011-contract-missions-before-runtime.md`

## What remains

Relay Echo must remain non-playable until its runtime entrypoint, mission save state, objective and failure state machine, deterministic replay, accessibility path, measured performance evidence, authored content package, and campaign completion transaction all exist and pass.

All unresolved direct-play, authored-asset, packaged-build, external-playtest, and AAA-quality evidence gates remain active.
