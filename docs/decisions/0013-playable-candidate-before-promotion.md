# ADR 0013: Verify a Playable Candidate Before Campaign Promotion

## Status

Accepted — July 26, 2026

## Context

Relay Echo has a verified mission contract and transactional runtime-state model. Promoting the campaign node at the same time as first implementing the scene would combine too many independent claims:

- that the mission path is complete,
- that state and recovery are correct,
- that deterministic replay passes,
- that the engine should expose the mission to players,
- that downstream campaign progression is authorized.

Those claims need separate evidence and review boundaries.

## Decision

Implement Relay Echo first as a complete playable candidate that is intentionally unreachable through campaign routing.

The candidate must:

- cover the complete contract objective path,
- use the transactional mission-state API,
- restore authored checkpoints correctly,
- exercise retained-understanding failure recovery,
- provide deterministic complete-path replay evidence,
- preserve Classic Mode and existing campaign progression,
- remain absent from engine routing while the catalog status is `planned`.

Campaign promotion is a later transaction. It may occur only after the candidate is green and the remaining release gates are explicitly reviewed.

## Consequences

- Gameplay and replay defects can be repaired without accidentally exposing unfinished content.
- Candidate completion cannot unlock downstream campaign nodes.
- The campaign navigator remains truthful throughout implementation.
- Engine routing, catalog promotion, and campaign-completion behavior become a small, auditable follow-up diff.
- A green candidate still does not constitute final content, external playtesting, accessibility parity, or an AAA-quality claim.
