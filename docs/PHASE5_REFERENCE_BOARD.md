# Phase 5 Reference Board

## Purpose and legal boundary

This board is a study set for composition, material response, lighting, camera language, character silhouette, UI restraint, and production workflow. Reference screenshots and presentations are not project assets and may not be copied, redistributed, traced into shipping content, or used to reproduce another game's protected characters, environments, marks, or distinctive designs.

The replacement sequence must synthesize general visual principles into original MARSTHEGAME content.

## Primary visual references

### 1. Death Stranding / Death Stranding 2 — terrain, scale, traversal composition

Official reference pages:

- https://www.playstation.com/en-us/games/death-stranding/
- https://www.playstation.com/en-us/games/death-stranding-2-on-the-beach/

Study:

- the player occupies a small, readable percentage of the frame while remaining a strong silhouette;
- foreground grass, stones, or broken terrain establish tactile scale;
- midground traversal routes form curves and diagonals rather than a rectangular arena;
- background ridges overlap in atmospheric layers;
- sparse worlds remain visually rich because macro landforms, material variation, sky, and character equipment carry detail at different scales;
- the route is readable without a giant objective pillar;
- the landscape looks traversed rather than decorated with random rocks.

Do not copy:

- Sam's suit, cargo stack, equipment shapes, bridge technology, iconography, color blocking, or fictional world motifs.

### 2. The Callisto Protocol — character rendering, photographic material validation, warm/cool separation

Official/store visual reference:

- https://store.playstation.com/en-us/concept/10002652

Primary rendering presentation:

- https://advances.realtimerendering.com/s2023/index.html
- `The Rendering of The Callisto Protocol`, SIGGRAPH 2023, Jorge Jimenez and Miguel Petersen.

Study:

- a realistic human-scale silhouette with layered hard and soft suit construction;
- readable separation among fabric, polymer, painted metal, bare metal, glass, skin, and emissive surfaces;
- strong warm/cool lighting that shapes the character rather than tinting the entire frame one color;
- photographic references used to author and directly validate BRDF response;
- local lights and reflections that describe surface curvature;
- controlled fog that catches light locally instead of washing the whole image;
- close camera framing that preserves shoulder, head, weapon/tool, and destination readability.

Do not copy:

- Jacob Lee, the Black Iron Prison suit, health display, weapons, prison architecture, or distinctive UI.

### 3. Dead Space remake — unified pillars, lived-in environment, lighting zones, restrained diegesis

Primary developer sources:

- https://www.ea.com/ea-studios/motive/news/art-developer-livestream
- https://www.ea.com/ea-studios/motive/amp/news/meet-the-team-leading-the-remake-of-dead-space
- https://www.ea.com/en-gb/inside-ea/news/inside-dead-space-4-the-intensity-director

Study:

- a small number of explicit art pillars govern every discipline;
- environment assets communicate prior use, maintenance, damage, and purpose;
- the player travels between deliberately lit islands through darker connective zones;
- fog, smoke, particles, sound, and light are layered to control emotion rather than run at maximum intensity continuously;
- the suit is designed layer by layer around the character's role;
- UI is minimized and integrated into the world where that improves immersion.

MARSTHEGAME translation:

- pillars: **Human Scale**, **Earnest Frontier**, **Functional Mars Infrastructure**;
- every prop must communicate mission function or habitation history;
- guidance is carried by composition, work lights, cable runs, tracks, and relay behavior before HUD text.

### 4. Horizon Forbidden West — believable environment composition and cross-discipline authorship

Official visual reference:

- https://www.playstation.com/en-us/games/horizon-forbidden-west/

Primary environment-art source:

- https://www.guerrilla-games.com/read/guerrilla-spotlight-Myriam-Dufrier

Study:

- environment art begins with narrative, gameplay intention, research, and technical limits;
- level-design boxes are transformed into believable spaces with coherent scale, material, prop, and color choices;
- concept, environment, prop, lighting, level-design, and technical-art decisions are coordinated rather than generated independently;
- environmental storytelling lets the player infer what happened and how a location functions;
- beautiful composition cannot invalidate traversal, cover, collision, or readability.

### 5. Destiny 2 — physically inspired shading serving art direction

Primary source:

- https://www.gdcvault.com/play/1025382/Translating-Art-into

Study:

- choose rendering features from visual goals;
- validate material correctness and consistency;
- use image-based lighting and physically inspired material response as a foundation;
- retain deliberate art direction of the final gameplay frame rather than treating PBR as an automatic beauty system.

### 6. God of War — continuous playable cinematography

Primary source:

- https://www.gdcvault.com/play/1025986

Study:

- camera design is part of emotional storytelling;
- gameplay and cinematics use a consistent visual vocabulary;
- a continuous camera can stage reveals and transitions without taking control away arbitrarily;
- previsualization should establish the shot before final content production.

### 7. NASA Mars imagery — geological and color truth

Primary sources:

- https://science.nasa.gov/mars/facts/
- https://science.nasa.gov/photojournal/perseverances-first-full-color-look-at-mars/
- https://science.nasa.gov/blog/sols-3235-3237-the-colors-of-mars/

Study:

- Mars is not a uniform saturated red surface;
- useful natural colors include brown, gold, tan, pink, yellow, deep chocolate, neutral gray, and low-reflectance dark rock;
- dust produces broad low-frequency color influence while exposed rock, shadowed cavities, fractured surfaces, and sediment layers create local contrast;
- sky and haze can be pale, dusty, and subtly cool near selected conditions rather than flat pink.

## Derived visual laws for Ares Reach

1. **One dominant read per shot.** The character, route, and relay may all be visible, but one must dominate.
2. **Three depth bands minimum.** Every approval frame requires authored foreground, midground, and background silhouettes.
3. **No rectangular arena read.** Traversable boundaries must be geological or infrastructural, never giant featureless perimeter slabs.
4. **No random scatter as composition.** Every rock cluster, cable, light, panel, track, and structure supports route, scale, story, or framing.
5. **Material identity before texture complexity.** Each surface must read by roughness, shape, scale, and response before procedural detail is added.
6. **Light the subject, not the entire world.** Direct light, sky fill, practicals, emissives, fog, and exposure must have separate jobs.
7. **Character is the quality anchor.** A poor human silhouette makes the complete frame look cheap regardless of renderer sophistication.
8. **HUD never becomes the focal point during traversal.** Objective text is small, timed, and subordinate to in-world guidance.
9. **Post-processing cannot conceal weak content.** Bloom, fog, depth of field, motion blur, and grading begin near zero and are added only when a named visual purpose is demonstrated.
10. **Screenshot review precedes phase language.** No system is called visually complete until the founder approves representative captures.
