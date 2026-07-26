# Dual-Track IP and Naming Bible

> Production architecture and naming policy, not legal advice. Counsel must approve any real-world public or commercial release.

## Purpose

The project supports two interchangeable narrative identity tracks over the same gameplay, chapter IDs, level schema, tools, save format, and future native runtime:

1. `real_world` — preserves the current transformative, non-commercial prototype identity. This track is **not presumed licensed**.
2. `fictionalized` — uses original character and organization names suitable for development toward a clearance-independent release.

Select a track with `STARMAN_IP_TRACK`. The default remains `real_world` so Classic Mode does not silently change.

## Canonical naming matrix

| Role | Real-world prototype | Fictionalized track |
|---|---|---|
| Game | STARMAN: An Elon Odyssey | STARFORGE: An Elias Voss Odyssey |
| Protagonist | Elon | Elias Voss |
| Early startup | Zip2 | LinkForge |
| First payments company | X.com | PulseNet |
| Second payments company | PayPal | VaultPay |
| Automotive company | Tesla | Helios Motors |
| Space company | SpaceX | AstraForge |
| Launch vehicle | Starship | Vanguard |
| Origin streets | Pretoria Streets | Solara Streets |

Mars, rockets, factories, payments, software, and general historical/technical concepts are not reserved identity tokens and may remain where independently appropriate.

## Architectural rules

- Gameplay code stores stable semantic IDs, never brand names as branching logic.
- Saves store chapter IDs and system state, not rendered names.
- UI, dialogue, subtitles, objectives, filenames, asset metadata, telemetry, and localization keys resolve through identity/content registries.
- A track switch cannot change collision, timings, unlocks, level dimensions, progression, difficulty, or save compatibility.
- New content must provide both identity variants before merge unless it is explicitly neutral.
- Real-world likeness art, logos, trade dress, voice imitation, and music references remain blocked pending explicit clearance.

## Tone invariants across both tracks

The protagonist is ambitious, technically driven, flawed, and persistent. The story is mythic, kinetic, and earnest—not parody and not documentary. Failure creates information and forward movement. The final emotional direction remains multiplanetary resolve.

## Clearance gates

Before public marketing, monetization, platform submission, or external playtesting using the real-world track, obtain a written review covering name, likeness, trademark, trade dress, biography, music, platform policy, and jurisdictional risks. Until that review is approved, public builds must use the fictionalized track.

Failure is progress. The frontier is open.
