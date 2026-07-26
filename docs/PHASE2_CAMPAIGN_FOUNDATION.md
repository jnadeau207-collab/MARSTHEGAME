# Phase 2 Campaign Foundation

## Current verdict

- Phase: 2
- Status: in progress
- Campaign: `frontier_campaign`
- Implemented missions: `ares_reach`
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

## Evidence

- `game/data/campaign.py`
- `game/core/campaign.py`
- `game/scenes/campaign.py`
- `config/phase2_campaign.json`
- `tools/phase2_campaign_audit.py`
- `tests/test_campaign.py`
- `tests/test_campaign_save.py`
- `tests/test_phase2_campaign_audit.py`

## What remains

This tranche does not claim that later mission content exists. The next mission must receive data contracts, progression state, encounter design, replay coverage, performance budgets, and a real runtime entrypoint before it can move from `planned` to `implemented`.

All unresolved direct-play, authored-asset, packaged-build, external-playtest, and AAA-quality evidence gates remain active.
