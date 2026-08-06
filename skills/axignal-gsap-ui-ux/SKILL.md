---
name: axignal-gsap-ui-ux
description: Design, implement, reconstruct, and audit ambitious AXIGNAL UI/UX motion with GSAP. Use for animation, interaction choreography, page transitions, scroll narratives, Globe/Graph/Timeline continuity, SVG motion, morphing, drag or gesture interfaces, microinteractions, cinematic marketing surfaces, React/Next.js GSAP work, reduced-motion behavior, or animation performance. Trigger when a user asks for GSAP, GreenSock, a premium or cinematic interface, a highly interactive experience, or gives the agent creative freedom over UI motion.
---

# AXIGNAL GSAP UI/UX

Create interaction systems with maximum creative range inside the AXIGNAL Goal Lock. Treat GSAP as an orchestration engine, not as permission to add spectacle without meaning.

This skill adapts the official GreenSock AI Skills to AXIGNAL. Read [references/official-gsap-capability-map.md](references/official-gsap-capability-map.md) for API and framework patterns, and [references/axignal-motion-contract.md](references/axignal-motion-contract.md) for product-specific semantics and gates.

## Operating modes

Infer the mode from the request and proceed without unnecessary clarification:

- **Directed build** — faithfully implement the requested motion or reference.
- **Creative direction** — when the brief is open, invent a coherent motion thesis and implement the strongest viable direction.
- **Exploration** — produce two or three materially different concepts, select one with explicit reasons, then prototype it.
- **Reconstruction** — reproduce interaction behavior from a reference without copying protected assets or unsupported product claims.
- **Audit and repair** — inspect existing motion, identify semantic, lifecycle, accessibility, or performance defects, then fix them if authorised.

Creative freedom applies to composition, timing, choreography, spatial continuity, input and visual treatment. It never overrides product truth, evidence hierarchy, user agency, accessibility, performance, or explicit user direction.

## Required workflow

### 1. Lock scope and truth

1. Confirm `AXIGNAL-GOAL-001`, the active task, affected phase, and governing contracts.
2. Inspect the current implementation, framework, package manager, design tokens, shared `InvestigationContext`, responsive behavior, and existing motion primitives.
3. Preserve the canonical AXIGNAL experience: Navigator, Globe, Graph, Timeline, Claim/Evidence Rail, investigation trails, personal interest memory, Knowledge Tides, and research candidate queue.
4. Separate observed, calculated, inferred, predicted, contradicted, unknown, and unavailable states before animating them.

Do not invent data, evidence, coverage, freshness, success, urgency, social proof, or financial outcomes to make a sequence feel more impressive.

### 2. Write a compact motion brief

Before code, define:

- user intent and interaction trigger;
- semantic reason for motion;
- start, transition, and settled states;
- what remains visually anchored;
- interruption, reversal, cancellation, and focus behavior;
- reduced-motion and low-performance fallback;
- target devices, languages, and performance budget;
- deterministic acceptance evidence.

For a small microinteraction, this may be a short comment or task note. For a multi-surface transformation, use a state table or sequence diagram.

### 3. Choose the smallest capable GSAP system

- Use CSS for a trivial binary transition that needs no sequencing or runtime control.
- Use GSAP core for dynamic values, interruption, coordinated transforms, and reusable playback control.
- Use a timeline for two or more dependent animation steps; use labels and the position parameter instead of chained delays.
- Use Flip when layout or component identity must remain continuous across DOM state changes.
- Use ScrollTrigger for scroll-linked narratives, pinning, scrub, or viewport activation.
- Use Draggable and Inertia for direct manipulation; provide keyboard controls and a non-drag equivalent.
- Use Observer for normalized wheel, touch, pointer, or gesture intent; never trap normal navigation.
- Use SplitText only for purposeful typography and preserve accessible reading order.
- Use DrawSVG, MorphSVG, or MotionPath only when path motion communicates real topology, flow, transformation, or brand behavior.
- Use ScrollSmoother only after native scroll, focus, anchor navigation, reduced motion, and low-end performance have been proven.

Load the detailed plugin selection matrix only when implementing: [references/official-gsap-capability-map.md](references/official-gsap-capability-map.md).

### 4. Implement safely

1. Reuse installed packages when compatible. If GSAP is absent and adding it is in scope, use the repository package manager and update its lockfile. Do not use private GreenSock registries, auth tokens, or legacy membership instructions.
2. Register every plugin once before use. Lazy-load route-specific heavy plugins where the framework supports it.
3. In React or Next.js, prefer `useGSAP()` with a component scope. Keep execution client-side, wrap delayed handlers with `contextSafe()`, and ensure teardown.
4. In other frameworks, create animations after mount inside `gsap.context()` and call `context.revert()` on unmount.
5. Use `gsap.matchMedia()` for responsive choreography and `prefers-reduced-motion`.
6. Prefer `x`, `y`, `scale`, `rotation`, `autoAlpha`, and CSS custom properties over layout-changing animation.
7. Store timelines or tweens that need control. Make long or user-driven sequences pauseable, reversible, seekable, or killable.
8. Cancel obsolete transitions. Use scoped selectors and stable element references.
9. Keep critical content, actions, focus targets, and evidence available before, during, and after animation.
10. Animate visual state from canonical application state; never make animation state the source of truth.

### 5. Apply AXIGNAL motion semantics

Use the hierarchy and surface patterns in [references/axignal-motion-contract.md](references/axignal-motion-contract.md).

Mandatory behavior:

- reduced motion resolves to a stable state without travel, parallax, scrub, or delayed access;
- Globe-to-Graph motion preserves the selected entity and shared investigation context;
- Timeline playback advances by material state changes and pauses at meaningful transitions;
- Claim and Evidence motion gives supporting and contradicting material equal structural status;
- graph forces settle promptly and preserve pinned positions;
- camera motion stops promptly after user input;
- continuous ambient motion exists only when it encodes live, declared state and can be stopped;
- no pulse, bounce, particle density, velocity, glow, or scale may imply opportunity quality or expected return unless a declared variable explicitly owns that encoding.

### 6. Validate and leave evidence

Run the deterministic audit against changed UI source:

```bash
node skills/axignal-gsap-ui-ux/scripts/audit-gsap-motion.mjs <changed-path> [...]
```

Then verify:

- type, lint, unit, integration, and relevant browser tests;
- keyboard-only completion and visible focus;
- screen-reader reading order and material state announcements;
- reduced-motion and high-contrast modes;
- mobile, integrated graphics, and representative desktop behavior;
- no layout shift, stale triggers, detached-node updates, or leaked listeners;
- no development markers or GSDevTools in production;
- screenshots or recordings at initial, transition, interruption, and settled states;
- performance trace for multi-surface, scroll, blur, filter, canvas, SVG, or large-list motion;
- rollback path and known limitations.

The implementing agent may report evidence, but may not mark its own material design direction or phase gate accepted.

## Hard stops

Refuse or redesign motion that:

- renames AXIGNAL, changes `axignal.com`, or drifts from `AXIGNAL-GOAL-001`;
- obscures evidence, contradictions, unknowns, source provenance, coverage, or as-of state;
- implies certainty, urgency, guaranteed return, personal suitability, or product capability not supported by canonical state;
- blocks interaction or critical content until an animation completes;
- moves focus without an explicit user action or loses focus during a transition;
- depends only on color, motion, hover, drag, or pointer input;
- overrides reduced-motion preferences;
- continuously moves the camera or analytical canvas without user value;
- uses unscoped component selectors, omits cleanup, or runs browser-only animation during SSR;
- adds secrets, legacy private registries, or unpinned dependencies;
- freezes provisional design tokens or motion values as final brand decisions without the required evidence and ADR.

## Upstream provenance

This skill is an AXIGNAL-specific adaptation of GreenSock's official `greensock/gsap-skills` project. Preserve the provenance and MIT notice in [references/upstream-attribution.md](references/upstream-attribution.md) when redistributing substantial adapted material.
