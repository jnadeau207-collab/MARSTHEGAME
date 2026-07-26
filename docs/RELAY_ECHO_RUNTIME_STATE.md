# Relay Echo Transactional Runtime State

## Status

Relay Echo now has a validated runtime-state model, but it remains a planned, non-playable campaign node with no engine scene or runtime entrypoint.

Machine authorities:

- `game/core/relay_echo_state.py`
- `game/core/save.py`
- `tools/relay_echo_runtime_audit.py`
- `config/phase2_campaign.json`

## Derived state model

The runtime state stores only contract-backed mission evidence. Critical fields are recomputed or cross-validated rather than trusted independently:

- completed objectives must be an exact prefix of the committed objective order,
- checkpoint ID and history are derived from completed objectives,
- current state and current objective are derived from checkpoint position,
- telemetry insight is derived from failure history,
- revision equals attempt, objective, and failure transactions,
- active state is derived from attempt and completion state,
- completion eligibility requires the complete six-objective path.

Forged objective order, checkpoint jumps, future evidence, duplicate history, mismatched insight, invalid recovery policy, and impossible revision state fail closed.

## Transactions

The state machine emits deterministic evidence for:

- attempt preparation,
- objective completion,
- failure recording and recovery,
- Relay Echo completion eligibility.

Objective evidence is committed only at objective boundaries:

- three signal fragments,
- a stable echo-source ID,
- an opened relay core,
- a stable echo-alignment ID.

Evidence cannot appear in the save before its matching objective commits.

## Failure and retained understanding

Each recorded failure must be valid for the current objective and match the recovery policy in the mission contract. Failure history records:

- sequence,
- failure ID,
- objective ID,
- checkpoint at failure,
- transaction revision,
- recovery rule.

Telemetry insight is recomputed from those entries, preventing an edited save from inventing or deleting retained understanding.

## Save integration

Relay Echo state is part of the existing schema-versioned, checksummed, transactional save envelope.

- Older saves without the field migrate to the runtime default.
- Runtime progress requires completed `ares_reach` and an unlocked `relay_echo` node.
- Corrupt Relay Echo state participates in existing primary/backup recovery.
- Reset restores the exact runtime default.
- Runtime state round-trips without trusting derived fields from disk.

## Deliberate boundary

Completing every runtime-state objective produces `completion_eligible: true` and the deterministic `relay_echo_completed` state event. It does **not** complete the campaign mission or unlock `phobos_vector` while Relay Echo remains planned.

Promotion still requires:

- a real runtime entrypoint and playable scene,
- authored mission and encounter content,
- deterministic complete-path replay,
- measured mission performance evidence,
- accessibility and keyboard/gamepad path verification,
- the campaign completion transaction.
