# Decision 0006: AAA quality is an evidence state

- Status: Accepted
- Date: 2026-07-26
- Authority: `AUTHORITATIVE_PRODUCTION_PLAN.md` V2

## Decision

The project uses three quality states:

1. `target_not_achieved`
2. `candidate_pending_evidence`
3. `achieved`

Only the founder may move the project to `achieved`, and only after the committed slice gates, external fictionalized-track playtests, direct founder play, stability evidence, accessibility evidence, and performance evidence all pass.

CI rejects unsupported claims and fabricated playtest results.

## Consequences

- The repository currently records `target_not_achieved`.
- Strong implementation progress does not automatically change the claim.
- Missing evidence is reported as pending work, not inferred success.
- Marketing language must follow the machine-readable quality state.
