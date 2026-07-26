# Vertical-Slice Team Charter

## Mission

Build one exceptional, fully playable custom-runtime chapter that proves all five design pillars without weakening the permanent eight-chapter Classic Mode surface or introducing a third-party game engine.

The recommended content target remains an expanded Chapter 6–7 hybrid or a new Mars-landing chapter. Final selection belongs to the Founder / Product and Creative Director after profiling and scope review.

## Team shape

The Phase 0 operating cell contains fourteen active functional seats, within the authoritative 12–20-seat boundary:

1. Product and creative direction
2. Executive production
3. Technical direction
4. Gameplay engineering
5. Rendering and performance
6. Tools and build engineering
7. Platform runtime
8. Quality automation
9. Level design
10. Narrative design
11. UI, UX, and accessibility
12. Technical art and VFX
13. Audio systems
14. Production operations

Assignments are defined in `config/phase0_organization.json`. Agent-owned seats are execution lanes accountable to the named human authority; they are not represented as human payroll headcount.

## Slice deliverables

- One start-to-finish chapter with production-quality moment-to-moment movement, combat, failure recovery, and one resource interaction.
- One vehicle, ascent, or equivalent spectacle sequence.
- High-fidelity procedural-plus-authored presentation that retains the prototype silhouette language.
- Measured acceleration of identified hot paths with Python parity and fallback until native correctness is proven.
- Expanded authored and procedural audio integrated through the custom stack.
- Accessibility controls, remapping seams, readable feedback, and assist settings designed with the slice rather than added afterward.
- Deterministic replay, save compatibility, benchmark evidence, crash diagnostics, and distributable playtest builds.

## Non-negotiable gates

- No Unreal, Unity, Godot, Bevy, Box2D, or equivalent engine substitution.
- Classic Mode chapters 1–8 remain loadable, playable, completable, and save-compatible.
- Both identity tracks remain structurally interchangeable.
- Every architectural change receives a decision record.
- Every optimization receives same-runner before/after evidence and passes the regression guard.
- External playtesting requires a fictionalized build unless written legal clearance explicitly permits otherwise.

## Operating cadence

- Daily: lane-level implementation and evidence capture.
- At every meaningful commit: compilation, static analysis, formatting, and targeted tests.
- At every pull request: complete Classic Mode replay and same-runner performance guard.
- Weekly: product-pillar, tone, scope, accessibility, and technical-risk review.
- At milestone boundaries: founder approval against exit criteria and risk register.

## Exit criteria for Phase 1 greenlight

The slice may advance only when it:

- demonstrates every design pillar in executable form,
- achieves at least 80% completion in representative external playtests,
- produces the intended emotional response of earnest determination rather than parody,
- passes all Classic Mode, identity, save, deterministic replay, and performance gates,
- demonstrates that the custom runtime can meet quality and iteration requirements without an engine pivot,
- has an approved staffing and budget expansion plan for pre-production.

Failure is progress. The frontier is open.
