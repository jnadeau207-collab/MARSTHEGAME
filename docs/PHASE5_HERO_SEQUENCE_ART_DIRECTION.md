# Phase 5 Hero Sequence Art Direction

## Sequence title

**Ares Reach: First Light at Relay 03**

## Authority

This document defines the replacement Phase 5 visual slice. It supersedes any assumption that the rejected arena composition can be promoted through incremental post-processing or additional procedural scatter.

The sequence is one continuous, playable, approximately 75–100 second traversal. It exists to prove that the project-owned native runtime can produce a coherent, emotionally directed, modern high-end gameplay frame.

## Art pillars

### 1. Human Scale

Mars must feel enormous because the astronaut is credible, not because the world is filled with oversized walls. The character, equipment, tracks, handrails, cables, access panels, footprints, and relay hardware establish a consistent human scale.

### 2. Earnest Frontier

The mood is determined, isolated, and hopeful. It is not horror, parody, sterile NASA simulation, retro pixel art, or generic red sci-fi. The environment shows that people worked here, depended on this relay, and left it damaged but recoverable.

### 3. Functional Mars Infrastructure

Every authored structure has a legible purpose. The relay has a foundation, mast, dish or phased-array surfaces, service trunk, power route, access cabinet, status lights, dust protection, and evidence of repair attempts. The landing area has a believable relationship to the relay and traversal path.

## Emotional sentence

> A lone field engineer steps out of the storm shadow, sees the dead relay catch the first sunlight, and crosses a scarred worksite to bring one human signal back online.

Every visual and audio decision must support that sentence.

## Sequence geography

The hero cell is a narrow natural basin approximately 90 meters long and 35–50 meters wide, enclosed by layered eroded ridges rather than walls.

The traversal is an asymmetrical S-curve:

1. **Lander shadow / spawn pocket** — protected foreground enclosure, low visibility, intimate character framing.
2. **Reveal saddle** — a two-to-three meter rise that exposes the relay and distant escarpment.
3. **Service trench** — diagonal midground path with cable, collapsed panel, footprints, and work lights.
4. **Dust cut** — shallow depression producing occlusion, parallax, and a brief loss of direct sightline.
5. **Relay apron** — compact authored worksite with foundation, maintenance deck, and mast.
6. **Activation point** — hand-height interface or cable coupling, not a glowing arcade pillar.

The route must not read as a rectangular corridor. Boundaries come from terrain elevation, fractured rock, equipment placement, and service structures.

## Continuous sequence beats

### Beat 0 — Black-to-image and control acquisition, 0–6 seconds

- Fade from black into the dark lee side of a damaged landing structure.
- Camera begins close enough to read suit materials and breathing motion.
- Wind is muffled by the structure; dust moves in narrow floor-level sheets.
- One amber practical light flickers on the character's pack or shoulder.
- No mission banner appears.
- A small objective caption fades in after the player has visual control: `RESTORE RELAY 03`.

Approval intent: the first frame must immediately disprove the toy-character and flat-red-arena failure.

### Beat 1 — The reveal, 6–18 seconds

- The player walks up a short rise.
- Camera eases laterally and slightly upward without cutting.
- The relay appears in the upper-right third, backlit by a low sun.
- A broken mast frame creates a strong geometric silhouette against the sky.
- The route curves down through a service trench in the lower-left/middle of frame.
- One distant ridge overlaps another to create depth.
- The relay emits no giant marker; two weak amber obstruction lights and a periodic blue service pulse establish identity.

Approval intent: a still image from the reveal must work as the primary store-page-quality benchmark for this tranche.

### Beat 2 — Traverse the worksite, 18–55 seconds

- Camera settles into a stable over-shoulder gameplay position.
- Near-ground rocks and cable guards pass the camera to create parallax.
- The player crosses alternating pools of sun and structure shadow.
- Tracks, dragged cable, and damaged equipment imply a failed repair effort.
- Wind direction is visible through dust streaks and one flexible fabric or cable element.
- The relay is intermittently occluded so anticipation is maintained.
- Audio layers add relay interference as distance closes.

Approval intent: movement must preserve a professional silhouette and material response from multiple angles.

### Beat 3 — Relay approach, 55–78 seconds

- The camera lowers slightly and narrows its composition around the character and mast base.
- Practical lights guide the final meters.
- A service cabinet door is open; one cable end lies disconnected.
- The interaction target is the cable coupling or panel, highlighted by a restrained local pulse.
- No full-screen prompt appears. A compact contextual prompt is anchored near the interaction zone or lower center.

Approval intent: the objective must be unmistakable without undermining the environment.

### Beat 4 — Signal return, 78–100 seconds

- The player connects or activates the relay.
- Power returns in a physical sequence: cabinet status, cable chase, mast rings, then array.
- The sound begins locally and expands outward.
- A narrow volumetric beam or scattered light response is allowed only at the mast, never as a giant opaque pillar.
- The sky and scene exposure do not jump dramatically.
- The relay transmits a short clean signal tone.
- A small confirmation appears: `RELAY 03 ONLINE`.
- Camera holds long enough for founder screenshot capture.

Approval intent: completion should feel earned and physically caused.

## Camera language

### Gameplay camera baseline

- third-person over-shoulder;
- target vertical field of view: approximately 48–55 degrees at 16:9, configurable for accessibility;
- camera distance: approximately 3.0–3.8 meters from the character;
- camera height: approximately 1.55–1.75 meters above ground reference;
- shoulder offset: approximately 0.45–0.65 meters;
- look-ahead blends toward movement direction, never snaps;
- collision-safe compression and recovery are required;
- no uncontrolled bob, roll, or procedural shake.

### Reveal camera

- continuous transition from gameplay camera;
- maximum automated yaw or lateral change must remain small enough that the player never loses orientation;
- relay is placed near a rule-of-thirds intersection;
- player remains below the horizon and does not merge with relay silhouette;
- horizon is not centered by default;
- foreground framing element occupies no more than roughly one quarter of the frame.

### Completion camera

- remains player-controlled or softly biased rather than switching to a detached cinematic camera;
- slight focal tightening may occur through distance and composition, not aggressive depth-of-field blur;
- the character, coupling, mast base, and powered relay response must coexist in one readable shot.

## Character direction

The character is the visual anchor. The existing block rig is not a shippable style and may remain only as an automated skeletal test fixture.

### Proportion target

- adult human proportion approximately 7.5–8 heads tall;
- head and helmet sized to preserve human anatomy beneath the shell;
- shoulders, pelvis, knees, elbows, hands, and boots placed at believable anatomical landmarks;
- limb taper and joint transitions must prevent the `boxes on sticks` read;
- suit bulk is added over the body rather than replacing anatomy;
- silhouette must remain readable from back, three-quarter, and side views.

### Suit construction

The suit is an original field-engineer pressure garment built from five readable material groups:

1. matte woven pressure fabric;
2. semi-matte abrasion panels;
3. painted hard-shell torso, shoulder, knee, and forearm plates;
4. dark exposed metal and polymer mechanisms;
5. visor glass and restrained emissive status elements.

### Silhouette features

- compact life-support pack with asymmetrical tool or antenna detail;
- reinforced shoulders without superhero width;
- articulated elbows and knees;
- substantial boots designed for regolith;
- one recognizable field-tool attachment;
- no cargo tower, prison-suit copying, or recognizable equipment from reference games.

### Color blocking

- primary fabric: low-saturation warm gray or dusty stone;
- hard-shell plates: muted ochre, off-white, or weathered pale alloy;
- mechanisms: charcoal and dark neutral metal;
- limited cyan or cool-white status light;
- one warm safety accent used sparingly;
- dust accumulation reduces saturation near boots, knees, pack edges, and lower torso.

### Animation minimum

- authored idle breathing;
- weight-bearing walk and jog with pelvis, spine, shoulder, and arm coordination;
- terrain-aware foot planting or at minimum stable sole contact on the hero path;
- start, stop, and turn blending;
- interaction pose for cable/panel work;
- pack and tool secondary motion where technically feasible;
- no exaggerated sinusoidal limb swing.

## Environment composition

### Macro forms

The environment requires three scales of authored form:

1. **vista scale** — two or more overlapping ridges, one distinct distant silhouette, sky gradient;
2. **route scale** — basin slope, reveal saddle, trench, relay apron, service route;
3. **contact scale** — fractured stones, compacted regolith, tracks, cable grooves, dust pockets, hardware fasteners.

### Geological vocabulary

- wind-shaped regolith banks;
- dark low-reflectance basaltic or igneous rock exposures;
- layered or fractured sedimentary forms;
- scattered angular ejecta with directional logic;
- erosion channels and compacted work surfaces;
- color variation among brown, tan, gold, pink, yellow, deep chocolate, and neutral dark rock.

A uniform red procedural carpet is prohibited.

### Relay vocabulary

Relay 03 is a field communications installation, not a generic archway.

Required authored components:

- embedded or bolted foundation;
- maintenance apron;
- mast with structural hierarchy;
- array, dish, or panel system with plausible orientation hardware;
- service cabinet with openable door silhouette;
- cable trunk and exposed disconnected coupling;
- obstruction/status lights;
- dust shielding and weathering;
- one damaged or improvised repair element;
- serial markings generated from project-owned typography or decals.

### Environmental storytelling

The player should infer:

- the relay was serviced recently enough for equipment to remain;
- a repair attempt failed during severe weather;
- the cable or power path was physically disconnected or damaged;
- the player is completing practical engineering work, not collecting a glowing token.

## Material direction

### Regolith

- broad macro color variation at 4–15 meter scale;
- medium erosion and compaction detail at 0.3–2 meter scale;
- fine grain response at centimeter scale without high-frequency crawling;
- roughness predominantly high but not uniform;
- darker compacted tracks and protected creases;
- reduced normal amplitude at distance;
- no visible square tiling or universal noise layer.

### Rock

- shape must carry identity before texture;
- weathered faces, fractured edges, dust-settled upward surfaces, and darker sheltered cavities;
- roughness and albedo variation follow geology and orientation;
- silhouette variety must come from authored families, not random scaling of one blob.

### Infrastructure

- painted alloy with chipped edges only where use and impact justify it;
- dust accumulation follows gravity, wind, recesses, and horizontal ledges;
- metalness remains binary or physically plausible rather than decorative;
- roughness breakup is subtle and scaled correctly;
- decals identify function and scale;
- emissives remain below clipping except during the activation beat.

### Character

- material separation must survive neutral light;
- visor reflection must not become an opaque neon rectangle;
- fabric and hard surfaces need distinct normal-frequency ranges;
- skin is not required for the hero sequence if the helmet remains sealed.

## Lighting direction

### Time and weather

Early morning after a dust event. The low sun is visible only indirectly or near frame edge. The air contains residual suspended dust but visibility is sufficient for layered vistas.

### Lighting roles

- **sun:** warm directional key, low angle, long readable shadows;
- **sky:** cool-neutral fill preserving shadow information;
- **ground bounce:** restrained warm return near terrain;
- **practicals:** localized amber work lights and cool service indicators;
- **relay activation:** sequential local emissive response;
- **fog/dust:** depth and light-volume support only.

### Exposure and tone

- no automatic-exposure pumping during reveal or activation;
- protect sky and emissive highlight detail;
- retain readable shadow values without flattening contrast;
- avoid global magenta/pink cast;
- black point remains slightly lifted only where atmospheric depth requires it;
- saturation is concentrated in selected accents, not the full terrain.

### Shadow direction

- character contact shadow must anchor feet;
- relay structural shadows must explain its construction;
- rock and terrain shadows should vary in softness by distance and source size;
- no broad ambient darkness hiding missing assets;
- no shadow acne, detached peter-panning, or unstable cascades in approval shots.

## Atmosphere, VFX, and post-processing

### Fog and dust

- baseline fog begins low;
- distance haze separates ridge layers;
- dust is directional and localized in terrain channels;
- wind particles vary in density and speed but never fill the screen continuously;
- the character may kick small ground-level dust puffs with footfalls;
- no opaque orange curtain.

### Bloom

- bloom threshold begins high;
- only relay indicators, selected practicals, and the activation response produce visible bloom;
- bloom radius is narrow and does not soften the full image;
- the sun/sky does not create a permanent milky veil.

### Motion treatment

- temporal stability is mandatory;
- motion blur defaults near zero and remains user-adjustable;
- depth of field is disabled during normal traversal;
- any completion focal effect must preserve interaction readability and be optional;
- film grain, chromatic aberration, vignette, and lens dirt are off unless a later approved art case proves their value.

## UI direction

### Objective presentation

The giant bottom-screen banner is removed.

Default objective UI:

- compact label in the upper-left safe area;
- maximum width approximately 18–22% of a 16:9 frame;
- two hierarchy levels: small mission label and slightly larger objective;
- fades to reduced prominence after 3–5 seconds;
- no opaque full-width panel;
- no pixel-art font;
- no all-caps text larger than the character's torso in screen space.

### Interaction prompt

- appears only inside interaction range;
- anchored close to the lower-center or projected interaction point without jitter;
- uses one button glyph and one short verb phrase;
- accessible scale and contrast options are preserved;
- prompt disappears immediately after commitment.

### Completion confirmation

- `RELAY 03 ONLINE` appears briefly and quietly;
- environment activation remains the dominant feedback;
- subtitles and accessibility text use a separate configurable treatment.

## Audio direction

### Baseline layers

- suit breathing and subtle mechanism noise;
- wind with terrain-dependent filtering;
- boot contact variation among plate, compacted soil, loose regolith, and rock;
- distant structure resonance;
- intermittent relay interference increasing with proximity;
- no constant musical wall.

### Music

A restrained project-synthesized motif may enter at the reveal and resolve at activation. It must support solitude and determination rather than imitate a reference soundtrack.

### Activation

- local mechanical latch or connector sound;
- power sequence propagating from cabinet to mast;
- interference stabilizing into a clean tone;
- short musical resolution;
- no generic explosion or oversized bass hit.

## Project-owned asset manifest

The following content must be authored by project code and tools:

### Character

- anatomical base mesh generator or project-owned authored parametric mesh;
- pressure-suit garment and plate generators;
- helmet and visor;
- pack, tool, and attachment modules;
- skeleton, skin weights, clips, and interaction animation;
- material masks and surface maps.

### Terrain and geology

- hero basin height/mesh authoring data;
- ridge silhouettes;
- regolith material set;
- at least five rock families with controlled variants;
- tracks, erosion, and compacted-route masks;
- distance vista geometry.

### Relay and worksite

- relay foundation, mast, array, cabinet, cable, coupling, platform, guards, lights, markings;
- damaged and intact state variants;
- activation animation/state sequence;
- collision and interaction data.

### Presentation

- project-owned UI font or vector/glyph generation strategy with professional typography;
- objective and interaction layout;
- dust, wind, footfall, and activation effects;
- synthesized ambience, mechanical layers, relay tones, and music motif.

## Renderer and engine work required

The existing renderer is retained, but Phase 5 recovery requires these capabilities to become content-directed rather than globally hard-coded:

1. authored camera-path and composition triggers with player-safe blending;
2. multiple terrain and rock material families with macro/micro scale separation;
3. artist-controlled material masks and orientation-aware dust accumulation;
4. improved character mesh range and skinning path beyond rigid primitive parts;
5. stable local-light and practical-light authoring;
6. exposure lock or constrained adaptation per sequence beat;
7. localized fog/dust volumes or bounded emitters;
8. configurable bloom, motion blur, focus, and grading profiles;
9. professional UI layout and scalable text rendering;
10. deterministic screenshot viewpoints and metadata capture;
11. image comparison that detects regressions but never claims aesthetic approval;
12. development build diagnostics that remain visible without terminating the retail-style path.

## Production order

### Tranche A — previsualization and truth reset

- invalidate previous Phase 5 claims;
- freeze reference board and art pillars;
- build simple camera/terrain/relay composition with no post-processing camouflage;
- capture four deterministic previsualization viewpoints;
- founder approves composition silhouettes before detailed asset production.

### Tranche B — environment hero forms

- replace arena walls with ridge and basin geometry;
- author path, reveal saddle, trench, apron, and vista;
- build relay structural hierarchy;
- validate traversal and collision;
- capture grayscale/value-only frames.

### Tranche C — character quality anchor

- replace visible block rig with proportional field-engineer mesh;
- establish suit construction and material groups;
- implement credible idle, walk, turn, and interaction presentation;
- approve silhouette before surface detail.

### Tranche D — material and lighting look development

- establish calibrated regolith, rock, painted alloy, fabric, polymer, glass, and emissive response;
- stage sun, sky, practicals, and activation lights;
- lock exposure and tone behavior;
- keep post-processing minimal until the ungraded frame works.

### Tranche E — atmosphere, VFX, UI, and audio

- add localized dust and distance haze;
- implement restrained objective and interaction UI;
- complete activation sequence and audio arc;
- capture final hero set.

### Tranche F — performance and direct approval

- run strict native CI, WARP, hardware validation, frame timing, memory, hitch, resize, save, replay, and startup/shutdown checks;
- founder directly plays the sequence;
- founder reviews the committed screenshot set at native resolution;
- Phase 5 may be restored only after explicit approval.

## Immediate rejection conditions

The hero sequence is rejected without qualification if any approval capture contains:

- visible primitive/block character construction;
- giant objective text or a glowing objective pillar dominating the image;
- featureless arena walls;
- uniform red terrain or obvious universal procedural noise;
- post-processing haze that obscures geometry;
- uncontrolled bloom or exposure clipping;
- random rock scatter without compositional purpose;
- feet floating, penetrating, or lacking contact shadow;
- relay structure without legible function or scale;
- a frame that depends on explanation to identify its focal point;
- copied or recognizably derivative protected content from a reference game.
