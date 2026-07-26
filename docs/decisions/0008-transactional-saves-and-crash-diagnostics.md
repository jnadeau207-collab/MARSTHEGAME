# Decision 0008: Transactional saves and structured crash diagnostics

- Status: Accepted
- Date: 2026-07-26
- Authority: `AUTHORITATIVE_PRODUCTION_PLAN.md` V2, Phase 1

## Decision

Replace direct save-file overwrites with a checksummed transactional checkpoint store and install bounded structured crash diagnostics before the first scene enters.

Save persistence now uses:

- schema-versioned envelopes,
- monotonically increasing generations,
- canonical SHA-256 checksums,
- write-to-temp, flush, file sync, and atomic replacement,
- previous-generation backup,
- checksum and semantic validation before in-memory mutation,
- backup promotion only after semantic validation,
- legacy flat-JSON loading and migration on the next save,
- explicit primary, backup, legacy, repair, generation, and error evidence.

Crash diagnostics now use:

- atomic JSON report writes,
- bounded and sanitized runtime context,
- exception type, message, and traceback,
- scene and chapter identity,
- simulation and frame-pacing evidence,
- save generation and repair provenance,
- recent audio and presentation events,
- report retention limits,
- no environment-variable or credential dump.

## Rationale

A playtest build that can corrupt progress or fail without actionable evidence is not a viable vertical-slice candidate. Save durability must survive interrupted writes, invalid primary data, legacy data, and a previous bad generation. Crash reports must explain the runtime state without creating a new privacy or secret-exposure problem.

## Consequences

- Existing saves remain loadable.
- New saves use the versioned transactional format.
- A corrupted or semantically invalid primary may recover the previous valid generation.
- Failed serialization leaves the prior checkpoint untouched.
- Uncaught main-thread and worker-thread failures generate bounded reports.
- The Phase 1 quality audit requires the checkpoint, save, diagnostic, timing, and engine integration files.
