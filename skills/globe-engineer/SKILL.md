---
name: globe-engineer
description: Build AXIGNAL's semantic 3D Globe with React Three Fiber, Three.js, GLSL, geospatial layers, exact visual states, fallbacks, and measurable performance budgets.
---

# AXIGNAL Globe Engineer

## Goal

Implement Globe as a first-class evidence lens, never as decorative animation. The landing globe may use a frozen synthetic demonstration dataset, but every marker, arc, colour and transition must have a typed meaning.

## Required stack

- Next.js App Router and React 19.
- Three.js through `@react-three/fiber`.
- `@react-three/drei` only for bounded helpers.
- custom GLSL for atmosphere, day/night blend and marker visibility.
- KTX2/Basis Universal for production textures.
- GSAP only as the narrative controller; React Three Fiber owns rendering.

## Scene architecture

1. Earth surface sphere: albedo, normal/bump, ocean/specular mask.
2. Night-light layer blended by light direction.
3. Cloud sphere at radius `1.006`, independently rotating.
4. Fresnel atmosphere shell rendered back-side.
5. simplified Natural Earth boundaries and coastlines.
6. instanced semantic nodes.
7. typed relationship arcs.
8. HTML HUD outside the canvas whenever possible.

## Canonical geography

Initial framing: Europe, North Africa and Western Asia. The canonical investor demonstration uses Madrid, London, Paris and Berlin. Moscow and Russian real-estate fixtures are not used in the landing narrative.

## Semantic node grammar

- solid teal: fact or admitted evidence-bound signal;
- orbital teal: opportunity;
- amber: inference;
- violet: prediction;
- red: contradiction;
- grey: unknown;
- solid line: supported relationship;
- dashed line: inferred relationship.

## Performance invariants

- desktop target: stable 60 FPS on a representative integrated GPU;
- mobile target: stable 30 FPS with reduced layers;
- desktop node ceiling: 800 instanced nodes;
- mobile node ceiling: 150 instanced nodes;
- clamp DPR to a maximum of 1.5 by default;
- pause rendering when off-screen;
- use KTX2 textures and mipmaps;
- bloom is selective and bounded;
- canvas must not block LCP;
- static poster remains visible before hydration and on failure.

## Accessibility and failure behaviour

- provide a complete non-canvas textual equivalent;
- honour `prefers-reduced-motion` and an explicit in-product motion toggle;
- no information may exist only as colour, movement or hover;
- keyboard selection must mirror pointer selection;
- WebGL failure loads the poster and all narrative copy;
- context loss must not break page navigation or conversion actions.

## Tests

- unit-test lat/lon to Cartesian conversion;
- snapshot scene-state contracts, not raw pixels alone;
- Playwright-test reduced motion, keyboard city selection and WebGL fallback;
- measure frame time, GPU memory proxy, texture bytes and draw calls;
- assert no live-source or canonical-claim mutation from the landing globe.

## Completion gate

Do not call the globe complete until desktop, tablet, mobile, reduced-motion and WebGL-failure paths all retain the complete story and CTA.
