# Decision 0003: Same-runner performance regression guard

- Status: Accepted
- Date: 2026-07-26
- Authority: `AUTHORITATIVE_PRODUCTION_PLAN.md`, Phase 0 and Risk Register

## Decision

Replace non-gating median-only benchmark evidence with a same-runner base-versus-candidate guard. Pull requests measure the base revision, candidate revision, and base revision again on one GitHub-hosted runner. Reports retain seven measured samples after two warm-up rounds for every metric and chapter.

The guard uses median absolute deviation to account for observed noise, fixed absolute and relative floors to prevent sub-millisecond false positives, and aggregate limits to catch broad regressions that remain beneath individual chapter thresholds. The policy is version controlled in `config/performance_thresholds.json`.

## Rationale

Historical cloud-runner results are not hardware-normalized and cannot safely gate unrelated machines. Same-runner bracketing provides a materially stronger comparison without requiring dedicated hardware. Median and MAD resist outliers better than mean and standard deviation for short, noisy runtime samples.

## Consequences

- Pull requests can now fail on demonstrated setup, update, or render regressions.
- Threshold changes are reviewable code changes rather than hidden CI configuration.
- Performance evidence remains machine-readable and auditable.
- The guard detects regressions but does not replace dedicated profiling or prove an optimization.

Failure is progress. The frontier is open.
