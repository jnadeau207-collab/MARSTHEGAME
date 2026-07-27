# Relay Echo Completed-Mission Replay

## Purpose

A completed Relay Echo mission must be replayable without deleting durable campaign progress or silently overwriting the evidence from the prior run.

The replay transaction preserves:

- Relay Echo in campaign completion history,
- Phobos Vector in campaign unlock history,
- current campaign graph validity,
- prior completed-run evidence,
- accessibility and input-parity behavior.

It resets only the active Relay Echo run state.

## Durable run archive

`relay_echo_replay` is stored inside the existing checksummed save envelope. It contains:

- schema and mission identity,
- a sequential `current_run_id`,
- immutable summaries of prior completed runs.

Each archived summary records attempts, transaction revision, failures, telemetry insight, objective history, checkpoint history, fragment evidence, echo source, relay-core state, and alignment choice.

Run IDs must remain contiguous from one. Corrupt or incomplete summaries fail closed through the existing primary/backup recovery path.

## Replay preparation

A replay can begin only when:

1. Relay Echo is already complete in campaign state.
2. Phobos Vector remains unlocked.
3. The current Relay Echo run is complete.
4. The replay archive validates.

The transaction archives the completed current run, advances the run ID, prepares a clean Relay Echo attempt, and records a new campaign attempt. Campaign completion and unlock lists must remain byte-for-byte equivalent.

## Replay completion

Replay extraction completes only the current Relay Echo run. It increments campaign revision and returns current mission to the next incomplete unlocked node, normally Phobos Vector.

It must not:

- add a duplicate Relay Echo completion,
- remove Phobos Vector,
- change prior completed-run summaries,
- fabricate later campaign content.

## Remaining verification

This tranche still requires save migration, engine and campaign routing, deterministic repeated-replay evidence, all inherited audits, and complete CI verification before merge.
