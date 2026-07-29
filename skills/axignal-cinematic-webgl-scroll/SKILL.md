# AXIGNAL Cinematic WebGL Scroll

Skill ID: `axignal-cinematic-webgl-scroll`

Version: `0.1.0`

State: `CONTRACTED`

Goal ID: `AXIGNAL-GOAL-001`

Owner: `globe-engineer`

Conflict precedence: `165`

## Purpose

Build, repair and audit AXIGNAL WebGL experiences in which Globe, geographic evidence, Graph and dossier form one continuous and meaningful product narrative. The Skill governs texture quality, GPU rendering, semantic zoom, GSAP ScrollTrigger choreography, responsive degradation, accessibility, performance evidence and licensing.

It does not grant authority to invent product states, source coverage, evidence, claims, buyers, metrics or commercial availability.

## Activate when

Activate this Skill for tasks involving any of the following:

- AXIGNAL Globe or geographic product surface;
- Three.js, React Three Fiber or WebGL;
- globe textures, KTX2, Basis, mipmaps or anisotropy;
- semantic zoom or regional level of detail;
- shaders, atmosphere, Fresnel, clouds, night lights or day/night terminator;
- GSAP ScrollTrigger, pinned narratives or scroll-controlled camera movement;
- visual fidelity, Globe performance or WebGL fallback;
- transitions between Globe, Evidence, Claims, Graph and dossier.

Required complementary Skills:

- `goal-keeper`;
- `contract-router`;
- `task-orchestrator`;
- `gate-evaluator`;
- `naming-guardian`;
- `security-reviewer`;
- `privacy-reviewer`;
- `observability-engineer`;
- `globe-engineer`;
- `visualisation-designer`;
- `interaction-architect`;
- `visual-fidelity-auditor`;
- `accessibility-auditor`.

## Governing contracts

- Contract 05 — experience and accessibility;
- Contract 08 — evidence and acceptance gates;
- Contract 12 — canonical investigation interaction;
- Contract 13 — visualisation semantics;
- Contract 18 — development-agent governance;
- Contract 20 — visual identity and reference fidelity;
- Contract 21 — truthful acquisition surface.

Higher-authority contracts and the active typed task always prevail.

## Required inputs

Before implementation, obtain:

1. active task ID, branch and permitted file scope;
2. current Globe component and parent scene;
3. current texture inventory and provenance;
4. viewport targets and supported device tiers;
5. current Canvas configuration and renderer capabilities;
6. intended scroll scenes and semantic state transitions;
7. product-state projection to display;
8. accessibility and reduced-motion requirements;
9. performance budget and validation environment.

Missing required input results in `BLOCKED`, not improvisation.

## Required outputs

A completed activation must produce:

- initial rendering diagnosis;
- texture manifest with dimensions, formats, sizes, roles and licences;
- Canvas/GPU capability report;
- one continuous scene architecture;
- global and regional LOD strategy;
- ScrollTrigger scene contract;
- responsive and reduced-motion behavior;
- accessible non-WebGL equivalent;
- performance measurements;
- deterministic scene captures;
- visual acceptance report;
- rollback and fallback behavior;
- exact git state and known limitations.

## Non-negotiable principles

### One semantic Globe

Use one mounted Globe scene as the principal visual instrument. Do not replace it with unrelated hero art, a second Globe or a static image between narrative stages.

### Assets and rendering are separate concerns

Raster textures may represent physical surface data. They must not contain baked UI, borders, markers, arcs or claims. Atmosphere, halo, markers, boundaries, arcs and product state use shaders, vector geometry or instanced geometry.

### Resolution is a pipeline

Perceived detail depends on all of:

```text
asset density
→ GPU format
→ texture filtering
→ anisotropy
→ Canvas drawing buffer
→ effective DPR
→ camera distance
→ regional LOD
→ lighting and color management
```

Do not claim that replacing PNG alone solves resolution.

### Regional zoom requires LOD

A single equirectangular global texture cannot support unrestricted regional close-up. When Europe becomes a dominant viewport region, preload and blend a documented regional detail layer or use a tile/clipmap strategy.

### Performance is adaptive

Quality tiers must respond to viewport, DPR, GPU limits and measured frame behavior. Do not load desktop 8K assets indiscriminately on mobile.

### Scroll controls state, not decoration

A single master timeline or explicitly coordinated state machine governs camera, Globe orientation, LOD, overlays, Graph transition and dossier formation. Independent viewport fades do not satisfy cinematic choreography.

### Product semantics remain explicit

Visual states must preserve distinctions between:

- Source;
- Evidence Object;
- Candidate Claim;
- Admitted Claim;
- Contradiction;
- Unknown;
- InvestigationContext;
- Dossier.

Animation never upgrades epistemic authority.

## Execution protocol

### 1. Preflight

Read:

- `AGENTS.md`;
- active task and governing contracts;
- this file;
- every file under `references/`;
- relevant templates and scripts;
- current Globe implementation and asset-preparation scripts.

Verify registration by searching the union of:

```text
skills/registry.yaml
skills/*.registry.yaml
```

The Skill is registered when exactly one `skill_id: axignal-cinematic-webgl-scroll` exists and its version is `0.1.0`.

### 2. Audit before editing

Record:

- texture path, format, dimensions, file size and licence;
- CSS viewport and drawing-buffer dimensions;
- device DPR and effective Canvas DPR;
- WebGL version, maximum texture size and maximum anisotropy;
- color space, tone mapping and antialiasing;
- poster and fallback stacking state;
- scene draw calls, triangles and texture count;
- current timeline, ScrollTriggers and cleanup behavior.

Classify each defect as asset, Canvas, filtering, shader, LOD, choreography, fallback, accessibility or performance.

### 3. Build the rendering pipeline

Follow `references/globe-rendering-contract.md` and `references/texture-quality-contract.md`.

Required layers:

```text
Earth albedo
night lights
clouds
atmosphere
Fresnel rim
country boundaries
territory markers
opportunity points
activity arcs
source fragments
evidence relations
Graph transition
```

### 4. Build the narrative

Follow `references/scroll-choreography-contract.md`.

Minimum labelled states:

```text
SCENE_GLOBAL
SCENE_EUROPE_APPROACH
SCENE_PUBLIC_RECORDS
SCENE_EVIDENCE
SCENE_GRAPH
SCENE_DOSSIER
```

### 5. Adapt by device and preference

Follow `references/responsive-performance-budget.md`.

Mobile and reduced-motion experiences must retain semantic parity, not merely hide animation-heavy content.

### 6. Validate

Run or adapt the scripts in `scripts/` without adding dependencies silently.

Required checks:

- texture inventory;
- source contract scan;
- WebGL capability capture;
- deterministic scroll-scene capture;
- desktop, mobile and reduced-motion review;
- console, page and WebGL errors;
- overflow and fallback;
- typecheck, lint and production build.

Apply `references/visual-acceptance-gates.md` fail-closed.

## Prohibited actions

Do not:

- copy third-party tutorial code or assets without an explicit compatible licence;
- use the DEV article or its repository as normative authority;
- ship unlicensed Earth imagery;
- present a poster as an interactive Globe;
- keep the poster visibly over the initialized Canvas;
- use an uncompressed 8K PNG albedo without measured justification;
- bake country borders, markers, arcs or UI into the Earth texture;
- zoom regionally without LOD;
- set a fixed high DPR for all devices;
- allocate geometry, materials or arrays every frame;
- create multiple competing ScrollTriggers for one scene state;
- approve simple fades as scroll choreography;
- remove semantic content for reduced motion;
- invent FPS, memory, LCP or texture metrics;
- modify backend, source-admission or canonical product state as a visual shortcut;
- commit, push or open a PR before required visual review when the task forbids it.

## Licensing boundary

Use original implementation and authoritative documentation. Third-party articles may inform patterns but must not be copied as source code. Every asset must record origin, licence, transformation and attribution requirements.

Preferred primary references:

- Three.js documentation;
- React Three Fiber documentation;
- GSAP ScrollTrigger documentation;
- Khronos KTX 2.0 documentation;
- Natural Earth licensing and data notes;
- NASA or other imagery only under verified terms applicable to the selected asset.

## Telemetry

Record:

- Skill activation and version;
- asset tier and active LOD;
- Canvas viewport, drawing buffer and effective DPR;
- GPU capability class without persistent fingerprinting;
- time to first Globe frame;
- average FPS, p95 frame time and sustained degradation;
- texture bytes and estimated GPU memory;
- draw calls, triangles and WebGL errors;
- fallback and reduced-motion activation;
- visual-gate failures.

Do not store raw GPU-identifying strings as durable user identifiers.

## Deactivation and rollback

Recommended kill switch:

`NEXT_PUBLIC_AXIGNAL_CINEMATIC_GLOBE_ENABLED=false`

Rollback must preserve a truthful, accessible geographic summary and the canonical InvestigationContext. It must not fall back to misleading product claims or remove evidence access.

## Acceptance

The Skill may be promoted from `CONTRACTED` only after its scripts, templates and gates are exercised on an AXIGNAL Globe implementation and independently reviewed. The implementing agent cannot self-approve the gate.
