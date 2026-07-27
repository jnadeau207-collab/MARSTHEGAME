# Phase 5 Automated Thresholds

The WARP evidence path requires a non-zero capture checksum, broad meaningful-pixel coverage, both dark and highlight regions, non-zero average and peak luminance, non-trivial edge energy, non-zero CPU and GPU frame timing, non-zero resident GPU bytes, and successful resize before capture.

Threshold values live in executable code and tests so documentation cannot silently weaken them.
