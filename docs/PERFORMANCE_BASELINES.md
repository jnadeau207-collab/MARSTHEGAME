# Performance Baseline Protocol

`tools/performance_baseline.py` records the current Python runtime's median per-chapter:

- scene construction and `on_enter` time,
- update time per frame with live entities and neutral input,
- offscreen draw time per frame at 1280×720.

CI captures a short non-gating sample and uploads JSON with the commit SHA, Python version, platform, parameters, and chapter results. Local engineering runs should use the default longer sample before and after performance-sensitive changes.

Do not compare results from different machines as a hard regression verdict. Use same-machine before/after runs for optimization claims. Hardware-normalized benchmark runners and statistical thresholds will be introduced after enough history exists to establish variance.
