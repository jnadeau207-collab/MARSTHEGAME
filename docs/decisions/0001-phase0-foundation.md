# Decision 0001: Phase 0 foundation ratchet

- Status: Accepted
- Date: 2026-07-26
- Authority: `AUTHORITATIVE_PRODUCTION_PLAN.md`, Phase 0

## Decision

Begin implementation by protecting the existing game before expanding it. Add a dual-track narrative identity registry, headless lifecycle replay for all eight Classic Mode chapters, deterministic save/data tests, CI across supported Python versions, and per-commit performance evidence.

Static analysis and formatting start as a ratchet over new Phase 0 infrastructure. Existing gameplay files are not mass-reformatted because a broad cosmetic diff would obscure behavior and weaken the baseline. Legacy files enter the ratchet when changed intentionally.

## Design-pillar mapping

1. **Mythic Kinetic Earnestness** — both identity tracks preserve the same tone and closing sentiment.
2. **Player Agency Through Mastery** — Classic Mode movement/progression remains untouched and regression-protected.
3. **Multiplanetary Progression** — the complete chapter 1–8 sequence and final credits transition are executable in CI.
4. **Procedural + Authored Hybrid** — the current data-driven level and procedural rendering architecture remains the protected base.
5. **Accessibility-First Feel** — future input/accessibility work now has a stable replay and CI surface.

## Consequences

- Every subsequent tranche receives immediate evidence if it breaks chapter loading or progression.
- Performance claims can be compared against machine-readable baselines.
- Fictionalization can proceed without forking gameplay architecture.
- The replay is a lifecycle regression, not yet a full input-path bot. Recorded deterministic input replays remain a later Phase 0 enhancement.
