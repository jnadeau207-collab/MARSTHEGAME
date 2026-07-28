# Phase 5 Screenshot Approval Gate

## Principle

Automated rendering tests may reject broken output. They may not approve art.

Phase 5 can exit only after the founder directly plays the exact reviewed build and explicitly approves the committed screenshot set. A green CI run, stable frame time, non-black pixel count, luminance histogram, edge-energy measurement, or screenshot-diff tolerance is necessary engineering evidence but never aesthetic approval.

## Required deterministic captures

The executable must expose deterministic capture viewpoints or replay timestamps for the following frames.

### H1 — Arrival close frame

Purpose:

- prove credible character proportion and suit construction;
- prove local material separation;
- prove restrained UI and post-processing;
- establish intimate human scale before the vista reveal.

Required content:

- character occupies approximately 22–38% of frame height;
- helmet, torso, pack, one arm, pelvis, and boots are readable;
- at least four suit material groups remain visibly distinct;
- feet or lower-body relationship to ground is visible;
- background contains functional lander or shelter detail rather than empty color.

### H2 — Relay reveal hero frame

Purpose:

- primary composition benchmark;
- prove environment scale, route readability, relay identity, and three-band depth.

Required content:

- authored foreground framing;
- readable player silhouette;
- S-curve or diagonal traversal route through the midground;
- Relay 03 near a rule-of-thirds focal region;
- at least two overlapping background silhouettes;
- sun, sky fill, and practical lighting have distinct roles;
- objective is readable without a giant marker or dominant HUD.

### H3 — Traversal material frame

Purpose:

- prove the frame survives ordinary gameplay rather than only one staged vista.

Required content:

- character in locomotion from a three-quarter or side-back angle;
- foot contact and moving silhouette remain credible;
- regolith, exposed rock, infrastructure, and suit read as different materials;
- near-camera terrain detail is stable and correctly scaled;
- relay is partly occluded or reframed to preserve progression;
- no temporal crawling, gross ghosting, or smeared UI.

### H4 — Relay activation frame

Purpose:

- prove objective interaction, local VFX, lighting response, and environmental payoff.

Required content:

- character, interaction point, mast base, and powered relay response share one readable composition;
- activation light propagates through physical components;
- emissives retain color and structure without clipping into white slabs;
- bloom remains local;
- completion UI is subordinate to the scene;
- environment remains visible and correctly exposed.

## Capture metadata

Every approval image must record:

- commit SHA;
- executable build type;
- GPU and driver;
- output resolution and display scale;
- camera transform and field of view;
- sequence time or deterministic replay tick;
- exposure value and adaptation state;
- tone-map and grading profile identity;
- enabled quality settings;
- CPU frame time, GPU frame time, resident GPU memory, and hitch count near capture;
- asset/content manifest hash.

## Founder visual-review rubric

Each image is scored from 0 to 5 in the following categories. A score is a review aid, not a replacement for veto authority.

### Composition and focal hierarchy

- 0: no deliberate focal point;
- 1: focal point exists only through HUD or emissive marker;
- 2: readable but flat or cluttered;
- 3: competent gameplay composition;
- 4: strong authored hierarchy and depth;
- 5: striking, memorable, reference-competitive hero frame.

### Character credibility

- 0: primitive or toy construction;
- 1: humanoid but anatomically implausible;
- 2: proportionally acceptable with visibly crude surfaces/animation;
- 3: credible game character at ordinary distance;
- 4: strong silhouette, materials, equipment, and motion;
- 5: hero-quality presentation that anchors the entire frame.

### Environment authorship

- 0: test arena;
- 1: primitive boundaries and random scatter;
- 2: recognizable location with weak function/story;
- 3: coherent traversable worksite;
- 4: believable, layered place with environmental storytelling;
- 5: distinctive, memorable original location with exceptional craft.

### Material response

- 0: flat colors or universal noise;
- 1: material labels depend on color only;
- 2: basic PBR response with weak scale/variation;
- 3: coherent physically plausible material families;
- 4: convincing multi-scale detail and weathering;
- 5: photographic-quality response under the approved lighting while retaining art direction.

### Lighting and atmosphere

- 0: global tint or unreadable exposure;
- 1: one undirected light plus heavy fog/bloom;
- 2: basic key/fill separation;
- 3: deliberate readable lighting;
- 4: strong emotional staging and depth;
- 5: exceptional light, shadow, color, and atmosphere serving gameplay and story.

### Camera and motion presentation

- 0: accidental framing or unstable view;
- 1: technically follows player but damages composition;
- 2: usable standard camera;
- 3: controlled gameplay presentation;
- 4: reveal, traversal, and interaction are staged without loss of control;
- 5: continuous cinematic-quality gameplay language.

### UI and graphic restraint

- 0: debug/prototype overlay dominates;
- 1: large intrusive objective treatment;
- 2: functional but generic;
- 3: clean and subordinate;
- 4: polished, accessible, and coherent with the world;
- 5: exceptional presentation that communicates with almost no visual burden.

### Original identity

- 0: obvious copy or generic asset-demo look;
- 1: collage of recognizable references;
- 2: derivative genre presentation;
- 3: coherent MARSTHEGAME direction;
- 4: distinctive project identity;
- 5: unmistakable original visual language with benchmark-level execution.

## Minimum review boundary

Before founder review begins:

- no category may score below 3 in an internal hostile review;
- Character Credibility, Composition, Environment Authorship, and Lighting must target 4 or better;
- the aggregate score is not a pass by itself;
- any founder rejection resets the candidate regardless of score.

## Binary veto list

Any one of the following rejects the candidate immediately:

- visible block/primitive character;
- giant objective banner;
- glowing pillar used as primary navigation;
- featureless perimeter walls;
- uniform red ground;
- obvious texture tiling or unstable high-frequency noise;
- global bloom/fog veil;
- feet floating or penetrating terrain;
- unreadable relay function;
- crushed shadows or clipped highlights hiding content;
- copied protected design from a reference title;
- inconsistent frame quality between the four required captures;
- material or lighting quality that collapses in motion;
- screenshot taken from a different build than the tested executable.

## Automated regression checks

Automation may enforce:

- capture dimensions and file validity;
- deterministic camera/replay state;
- non-zero geometry coverage;
- stable checksum or perceptual-diff envelope for unchanged approved content;
- no all-black, all-white, or single-color output;
- bounded luminance and highlight clipping;
- stable temporal output across a short capture burst;
- no NaN/Inf GPU output;
- frame-time, memory, hitch, resize, and device-removal requirements;
- required asset and manifest identities.

Automation may not label a screenshot `AAA`, `beautiful`, `approved`, `production quality`, or equivalent.

## Approval record

When Phase 5 passes, the repository must record:

- the approved commit SHA;
- links or paths to H1–H4 captures;
- founder approval date;
- exact build and hardware evidence;
- unresolved non-blocking visual debt;
- explicit statement that approval applies to this sequence and does not automatically certify the full campaign.
