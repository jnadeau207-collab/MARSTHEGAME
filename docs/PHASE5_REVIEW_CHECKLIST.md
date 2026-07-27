# Phase 5 Review Checklist

- [ ] strict MSVC `/W4 /WX` build passes
- [ ] all eight DXC shader entry points compile and package
- [ ] all CTest suites pass
- [ ] D3D12 debug validation reports no corruption or error
- [ ] resize reconstructs visual targets safely
- [ ] GPU timing, CPU timing, hitch count, and resident-memory evidence are emitted
- [ ] generated environment, material, character, and audio tests pass
- [ ] final-frame readback satisfies visual-distribution thresholds
- [ ] `phase5_visual_slice.bmp` is retained in CI artifacts
- [ ] founder directly plays and approves the native slice

The final checkbox cannot be automated or inferred from CI.
