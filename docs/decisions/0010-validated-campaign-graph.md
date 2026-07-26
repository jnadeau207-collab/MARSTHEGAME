# ADR 0010: Validated Campaign Graph

- Status: accepted
- Date: 2026-07-26
- Decision owner: founder

## Context

Phase 1 produced one complete fictionalized mission. Phase 2 must scale beyond that mission without converting aspirational titles into fake playable content or coupling campaign progress to Classic Mode chapter IDs.

A loose list of levels would allow missing prerequisites, cycles, forged unlocks, unstable IDs, and planned missions to leak into runtime menus.

## Decision

Use a stable, validated campaign graph with:

- lowercase stable mission IDs,
- unique positive sequence numbers,
- explicit prerequisites,
- explicit `implemented` or `planned` status,
- runtime entrypoints only for implemented missions,
- unlocks derived from completed prerequisites,
- transactional attempts and completion events,
- campaign state stored inside the checksummed save envelope.

The Phase 1 Mars slice becomes implemented mission `ares_reach`. Planned missions may appear in the navigator only with truthful planned or locked labels. They cannot launch until promoted through code, content, tests, replay, and audit changes.

## Consequences

- Classic Mode remains independent and protected.
- Campaign save data can migrate without trusting persisted unlock lists.
- Mission order and progression are deterministic.
- Future renderer, localization, and content systems can key against stable mission IDs.
- Adding a title to the graph does not imply that its content exists.
- Campaign progression failures participate in existing save recovery rather than creating a second persistence system.
