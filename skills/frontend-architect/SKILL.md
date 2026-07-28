---
name: frontend-architect
description: Integrate the AXIGNAL landing, R3F globe, GSAP timelines, metadata, fallbacks and typed state into the existing Next.js 16 / React 19 application.
---

# AXIGNAL Frontend Architect — Landing Foundation

## Integration boundaries

- server-render all meaningful copy and metadata;
- dynamically import the WebGL scene with an immediate poster fallback;
- isolate the globe in a client component;
- keep CTAs, navigation, forms and evidence explanations outside WebGL;
- use typed scene states shared by ScrollTrigger and the globe;
- do not introduce a second design-token system;
- avoid global scroll libraries unless independently justified.

## Proposed packages

Versions must be resolved against the current lockfile at implementation time:

- `three`;
- `@react-three/fiber` compatible with React 19;
- `@react-three/drei`;
- `@react-three/postprocessing`;
- `postprocessing`;
- `gsap` with licensed plugins already approved;
- optional `zustand` only when React state is insufficient.

## SEO

Use Next.js metadata APIs for title, description, canonical, Open Graph, Twitter card, icons, manifest, robots and structured data. Canvas content never substitutes semantic headings or copy.

## Security

No remote texture URL is loaded directly in production. Assets are acquired, verified, transformed and served from AXIGNAL-controlled storage with a strict CSP.
