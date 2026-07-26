# Decision 0004: Sole-founder and AI-collaborator operating model

- Status: Accepted; supersedes the earlier functional-seat interpretation
- Date: 2026-07-26
- Authority: Direct founder correction to `AUTHORITATIVE_PRODUCTION_PLAN.md`

## Decision

Operate the project through exactly one human founder and one AI software collaborator. There are no employees, contractors, other human contributors, departments, leadership team, or functional seats.

The founder retains final product, release, budget, legal, scope, and merge authority. ChatGPT may research, propose, implement, test, document, and recommend, but cannot independently approve irreversible decisions.

Work is organized into workstreams. A workstream is a category of work shared by the founder and AI collaborator; it is not a person, position, department, or unit of headcount.

The operating model is machine-readable in `config/phase0_organization.json` and validated in CI.

## Rationale

The previous 12–20-seat interpretation followed an unrealistic staffing assumption from the production plan and created misleading organizational language. The founder explicitly clarified that the team is only the founder and ChatGPT. Repository governance must represent reality exactly.

AAA-quality is a product and evidence standard, not a staffing claim. The project will use measurable player-facing gates instead of headcount as a proxy for quality.

## Consequences

- CI rejects invented seats, departments, FTEs, employees, contractors, or additional humans.
- The AI collaborator remains bounded by founder authority.
- Phase 1 scope must be achievable by the actual founder + AI collaboration model.
- The game may target AAA quality but may not claim to have achieved it before the playable slice passes the committed gates.

Failure is progress. The frontier is open.
