# Relay Echo Accessibility and Input Parity

## Status

Relay Echo has a verified hidden playable candidate. This tranche proves that the complete candidate path remains semantically equivalent across keyboard and gamepad input and remains completable through the mission accessibility profile.

This work does **not** promote Relay Echo into the campaign. The campaign catalog still records the mission as `planned`, its entrypoint remains `None`, and the engine does not import either Relay Echo candidate scene.

## User-facing settings

The title screen now routes to a real **Accessibility & Settings** scene instead of toggling the FPS counter. Keyboard and gamepad users can change:

- Assist Mode
- Reduced Motion
- Camera Shake
- Flash Intensity
- High-Contrast Objectives
- Hold / Toggle Alternative
- Subtitles
- Subtitle Background
- Subtitle Size

Settings are normalized through the existing settings boundary and saved through the existing settings store.

## Relay Echo mission profile

`RelayEchoAccessibilityProfile` derives the mission behavior from normalized runtime settings and covers every obligation in the mission contract:

- `assist_mode` enlarges interaction regions, extends the relay-overload window, and lengthens recovery invulnerability.
- `camera_shake_scale` is inherited from normalized presentation policy.
- `flash_reduction` is derived from bounded flash intensity.
- `hold_toggle_alternatives` lets a held interaction activate a terminal after entering its interaction region; a fresh edge is no longer mandatory.
- `high_contrast_objectives` changes objective markers, outlines, warnings, and HUD contrast.
- `reduced_motion` disables camera shake and mission cinematic motion emphasis.
- `subtitle_background` controls the high-opacity subtitle plate.

Subtitle visibility and size remain independently configurable.

## Input parity model

Parity is proven with two stable deterministic profiles rather than by feeding both runs the same abstract token stream:

- **Keyboard:** physical binding tokens such as `a`, `d`, `space`, `j`, `e`, `return`, and `backspace`.
- **Gamepad:** semantic actions emitted by the hardware boundary.

The gamepad hardware mapping now includes:

- analog movement,
- D-pad navigation,
- confirm,
- cancel/back,
- jump,
- attack,
- dash,
- interact,
- pause.

The parity replay executes the complete Relay Echo path twice per profile and requires identical committed mission state, campaign state, milestones, transition, audio events, and presentation events.

## Accessibility reference path

The accessibility replay uses the gamepad profile with:

- Assist Mode enabled,
- Reduced Motion enabled,
- camera shake disabled,
- reduced flash intensity,
- high-contrast objectives,
- held-interaction alternatives,
- subtitle background enabled,
- subtitle scale at `1.5×`.

It intentionally enters terminals while `interact` is already held and triangulates from outside the standard interaction radius but inside the assisted radius. The final transactional mission and campaign outcome must remain identical to the standard keyboard and gamepad paths.

## Fail-closed evidence

The tranche is not verified unless all of the following agree:

- input-profile validation,
- D-pad and cancel hardware tests,
- accessibility-profile validation,
- settings-scene routing tests,
- keyboard replay repeated twice,
- gamepad replay repeated twice,
- assisted accessibility replay repeated twice,
- identical committed outcomes,
- zero camera shake in reduced-motion presentation evidence,
- campaign node still planned and hidden,
- all inherited Phase 0, Phase 1, Phase 2, Relay Echo runtime, and candidate audits.

## Remaining promotion gates

Even after this tranche passes, Relay Echo remains unpromoted. Remaining gates include the campaign completion transaction, final authored content packages, direct founder play approval, packaged-build soak, external playtests, and the broader AAA-quality evidence standard.
