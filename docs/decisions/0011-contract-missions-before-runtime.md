# ADR 0011: Contract Campaign Missions Before Runtime Promotion

## Status

Accepted — July 26, 2026

## Context

The campaign graph supports planned missions that are visible but non-playable. A title, location, and prerequisite edge are insufficient to guide production or prevent an unfinished mission from being promoted prematurely.

Relay Echo is the first mission after `ares_reach`. It needs a stable production boundary before gameplay implementation begins.

## Decision

Every planned mission must receive an executable mission contract before runtime work can promote it to `implemented`.

The contract must define and validate:

- stable identity and prerequisites,
- entry and exit state,
- ordered objectives and dependencies,
- failure and recovery semantics,
- checkpoints and transactional persistence keys,
- rewards and downstream unlocks,
- deterministic replay requirements,
- accessibility obligations,
- localization-ready content keys,
- performance and allocation budgets,
- authored and procedural content boundaries,
- explicit promotion gates.

A contracted mission remains `planned`, has no runtime entrypoint, and cannot launch. The campaign audit must cross-check the contract, catalog, and machine-readable Phase 2 truth manifest.

## Consequences

- Runtime implementation begins from a stable, testable scope.
- Objective order, save boundaries, accessibility, replay, and performance cannot be postponed until late polish.
- Procedural systems remain bounded by authored critical-path and checkpoint contracts.
- A contract does not imply finished content, playability, external evidence, or AAA quality.
- Promotion requires real runtime, content, tests, replay, budgets, and campaign-transition evidence.

## First application

`game/data/relay_echo.py` is the first authoritative contracted mission. `relay_echo` remains planned and non-playable until every implementation gate in that contract passes.
