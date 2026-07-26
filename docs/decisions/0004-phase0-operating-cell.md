# Decision 0004: Founder-accountable Phase 0 operating cell

- Status: Accepted
- Date: 2026-07-26
- Authority: `AUTHORITATIVE_PRODUCTION_PLAN.md`, Phase 0

## Decision

Operate Phase 0 through one named human authority and fourteen explicit functional seats. The founder retains final product, release, budget, legal-retention, staffing, and merge authority. Autonomous agents own bounded implementation lanes and remain accountable to the founder.

The organization is machine-readable in `config/phase0_organization.json` and validated in CI. The manifest explicitly records the human-headcount claim separately from the number of functional seats.

## Rationale

The project needs clear ownership and a 12–20-seat vertical-slice structure before Phase 1 work can be sequenced. At the same time, the repository must not misrepresent agent lanes as employees or claim external hiring that has not happened. Separating human accountability, functional ownership, and future funded recruitment provides an executable operating model without fabrication.

## Consequences

- Every active lane has an owner and escalation path.
- Agents cannot approve irreversible product, legal, financial, staffing, release, or merge decisions.
- The vertical-slice team charter is actionable immediately.
- Human expansion remains a funded Phase 1 business action, not a false Phase 0 repository claim.

Failure is progress. The frontier is open.
