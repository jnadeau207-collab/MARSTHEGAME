# Phase 5 Automated Thresholds

The WARP evidence path requires a valid capture checksum, broad meaningful-pixel coverage, dark and highlight regions, bounded average and peak luminance, non-trivial edge energy, non-zero CPU and GPU timing, non-zero resident GPU bytes, and successful resize before capture.

Threshold values live in executable code and tests so documentation cannot silently weaken them.

These are integrity and regression thresholds only. They proved insufficient to identify the rejected Phase 5 candidate as visually unacceptable and may never be described as aesthetic, production-quality, screenshot-approval, or AAA thresholds.

The replacement Phase 5 gate is defined by `PHASE5_SCREENSHOT_APPROVAL_GATE.md` and requires founder direct review.
