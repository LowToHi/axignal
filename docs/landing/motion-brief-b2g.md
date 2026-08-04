# AXIGNAL B2G Landing Motion Brief

Goal ID: `AXIGNAL-GOAL-001`
Task: `AX-F2-T18`

## Intent

Motion turns one procurement question into a traceable investigation. It clarifies provenance, epistemic state and continuity between Globe, Graph and dossier. It must not imply live global coverage, model certainty or public source access.

## Primary timeline

`investigationCinematic` is the sole narrative timeline. Its `ScrollTrigger` pins one persistent stage and scrubs one continuous progress value through these labels:

1. `SCENE_GLOBAL`
2. `SCENE_EUROPE`
3. `SCENE_FRAGMENTATION`
4. `SCENE_EVIDENCE`
5. `SCENE_INVESTIGATION`
6. `SCENE_DOSSIER`

The same mounted Canvas remains present in every scene. Timeline transforms coordinate Globe camera and light state, territorial opportunities, public-record fragments, evidence states, graph topology, dossier assembly and the final release into pricing.

Static sections may use the bounded `sectionReveal` entrance. It is not part of the product narrative and does not create a competing hero animation.

## State ownership

The GSAP timeline writes one normalized progress ref. The Three.js scene reads that ref in `useFrame` and deterministically derives camera, rotation, scale, lighting, markers and arcs. HTML trace objects persist across fragmentation, evidence, graph and dossier states; they are reorganized rather than replaced by unrelated reveals.

## Breakpoints

- Desktop (`min-width: 901px`): full pin and scrub across `560%`.
- Tablet (`641–900px`): reduced trace geometry and a shorter `430%` pin.
- Mobile (`max-width: 640px`): the real Globe remains mounted with compact overlays and a shorter `340%` pin.
- Reduced motion: no pinned scrub or continuous rotation. The hero keeps the real Globe at a stable Europe-aware state and all six narrative states remain available as ordered document content.

## Performance and cleanup

The timeline is created inside `gsap.context()` and `gsap.matchMedia()` and reverted on unmount. Motion uses transforms and opacity. The Globe uses one Canvas, local textures and bounded DPR; no duplicate WebGL context or perpetual DOM loop is introduced.

## Semantic safeguards

- Glow is not confidence.
- Colour always has a text state label.
- The TED bounded profile uses the admitted treatment only within `PRIVATE_AUTHENTICATED_PILOT`.
- Discovery systems never use the admitted treatment.
- `PUBLIC_ACCESS_DISABLED` and synthetic demonstration labels remain visible.
- Historical `TECHNICAL_PROBE` artifacts are not rewritten by the landing projection.
- Calculator values change only in response to user inputs.
