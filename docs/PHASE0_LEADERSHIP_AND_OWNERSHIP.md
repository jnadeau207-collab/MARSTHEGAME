# Phase 0 Leadership and Ownership

## Operating truth

Phase 0 is operated by one named human authority, `jnadeau207-collab`, with bounded autonomous-agent execution. The repository does **not** claim fourteen employees, contractors, or paid full-time equivalents. It establishes fourteen active functional seats so work has explicit ownership, review paths, and decision boundaries before funded human expansion.

The machine-readable authority is `config/phase0_organization.json`; CI validates it with `tools.validate_phase0_organization`.

## Core leadership

| Role | Assignment | Authority |
|---|---|---|
| Founder / Product and Creative Director | `jnadeau207-collab` | Final vision, pillars, scope, release, legal-retention, and merge decisions |
| Executive Producer / Program Lead | `jnadeau207-collab` (interim) | Priorities, milestones, budget envelope, and staffing approval |
| Technical Director | `agent:technical-direction` | Architecture proposals, technical sequencing, and verification design; accountable to founder |
| Quality and Release Lead | `agent:quality-release` | Test gates, regression evidence, and release recommendation; accountable to founder |

Agents may propose and execute reversible repository work. They may not independently approve public release, spending, legal positions, licensing, hiring, destructive scope changes, or merges that alter the product authority.

## Decision protocol

1. `AUTHORITATIVE_PRODUCTION_PLAN.md` and the five design pillars control product intent.
2. Architecture changes require a decision record under `docs/decisions/`.
3. Gameplay and runtime changes require Classic Mode regression evidence.
4. Performance claims require same-runner before/after evidence.
5. Conflicts involving scope, identity, release, budget, or irreversible decisions escalate to the founder.
6. Real-world-track public use remains blocked until qualified counsel provides written clearance.

## Ownership continuity

Every active leadership or vertical-slice lane has one owner. Every agent lane names the accountable human. The organization validator rejects missing disciplines, duplicate seats, inactive ownership, unbounded agent authority, or inflated human-headcount claims.

This structure completes the repository-operating requirement for Phase 0 while preserving an honest distinction between an active agent-assisted production cell and later funded human staffing.
