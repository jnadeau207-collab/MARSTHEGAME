# Performance Baseline and Regression Protocol

`tools/performance_baseline.py` measures the permanent eight-chapter Classic Mode compatibility surface. Each chapter records raw samples plus median and median absolute deviation (MAD) for:

- scene construction and `on_enter`,
- simulation update time per frame with live entities and neutral input,
- complete offscreen rendering at 1280×720.

## Measurement discipline

A report is valid only when it uses the same Python major/minor version, resolution, update-frame count, and draw-frame count as the report it is compared against. Every chapter receives two warm-up rounds before seven measured rounds. Raw samples are retained in schema version 2 so a later audit can reproduce the verdict.

Cross-machine historical reports remain evidence, not hard gates. Pull-request regression decisions use the base and candidate revisions on the **same GitHub-hosted runner**. The base revision is measured before and after the candidate to bracket runner drift.

## Regression policy

`config/performance_thresholds.json` is the version-controlled policy. `tools/performance_guard.py` pools both base measurements and computes a robust center and MAD for each chapter and metric.

A chapter passes when the candidate median is no greater than:

```text
base median + max(absolute floor, relative floor, 8 × base MAD)
```

The absolute floor prevents tiny sub-millisecond changes from becoming noise failures. The relative floor protects legitimately variable setup/render work. The MAD term expands only when the same runner actually demonstrated variance.

The guard also applies an aggregate limit across all eight chapters, preventing a broad regression from hiding beneath generous individual noise bands:

| Metric | Individual relative floor | Absolute floor | Aggregate limit |
|---|---:|---:|---:|
| Setup | 35% | 0.15 ms | 18% |
| Update/frame | 25% | 0.02 ms | 12% |
| Draw/frame | 20% | 0.50 ms | 10% |

Any individual or aggregate failure blocks the pull request and produces a machine-readable report. Threshold changes require an architectural decision record and evidence from repeated same-runner measurements; loosening a threshold merely to turn CI green is prohibited.

## Commands

Capture a local engineering report:

```bash
python -m tools.performance_baseline --warmup-rounds 2 --rounds 7 --json-out build/performance.json
```

Compare a candidate against two bracketing base reports:

```bash
python -m tools.performance_guard \
  --baseline build/base-a.json \
  --baseline build/base-b.json \
  --candidate build/candidate.json \
  --policy config/performance_thresholds.json \
  --json-out build/performance-guard.json
```

Performance claims still require same-machine before/after evidence. The CI guard detects regressions; it does not by itself prove an optimization.
