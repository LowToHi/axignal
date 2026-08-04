# AXIGNAL motion contract

This reference operationalises Contracts `05`, `12`, `13`, `18`, `20`, and `21` for GSAP work. The contracts and Goal Lock remain authoritative.

## Motion hierarchy

| Level | Purpose                                            | Candidate duration | Reduced-motion result                           |
| ----- | -------------------------------------------------- | -----------------: | ----------------------------------------------- |
| 0     | Critical analytical reading                        |               0 ms | Immediate stable state                          |
| 1     | Hover, focus, selection, compact controls          |          80–180 ms | Color/outline/state change without travel       |
| 2     | Panels, claim previews, rails, lens controls       |         180–350 ms | Immediate placement or short opacity transition |
| 3     | Globe/Graph, temporal state, investigation restore |         350–800 ms | Immediate cut preserving context and focus      |

Longer sequences require explicit user initiation and must remain interruptible. Exact durations and eases are prototype candidates, not frozen brand values.

Candidate token mapping:

```ts
export const axMotion = {
  duration: {
    instant: 0.08,
    fast: 0.14,
    base: 0.24,
    slow: 0.42,
    transform: 0.72,
  },
  ease: {
    standard: "power2.inOut",
    enter: "power2.out",
    exit: "power2.in",
    spatial: "power3.out",
  },
} as const;
```

Use repository tokens when they exist. Do not duplicate or freeze this candidate mapping in multiple components.

## Surface patterns

### Globe to Graph continuity

- Keep the selected entity visually anchored.
- Morph only relationships that remain semantically valid across lenses.
- Preserve geography, universe, time, filters, provenance, and selection in the shared `InvestigationContext`.
- Keep the Claim/Evidence Rail and Timeline stationary or predictably continuous.
- Use Flip for shared component identity and MotionPath only where the path reflects real topology.
- Do not transform inferred edges as though they were measured flows.
- On interruption, settle at a valid Globe or Graph state; never strand the UI between models.

### Timeline and Time Machine

- Drive progress from canonical material state changes, not arbitrary animation frames.
- Pause at claim admission, contradiction, opportunity-state, coverage, or scenario-version changes when material.
- Keep map, graph, rail, and metrics on the same `as_of` state.
- Announce material state changes through an accessible live region.
- Under reduced motion, step discretely through states.

### Claim and Evidence Rail

- Animate hierarchy and continuity, not truth or confidence theatre.
- Supporting and contradicting evidence receive equal structural affordance.
- Preserve source, as-of, method, coverage, and contradiction visibility.
- Never delay evidence access until a flourish finishes.

### Graph

- Force/layout motion settles promptly.
- Pinned positions survive updates and lens changes.
- Edge motion encodes declared direction or temporal change only.
- Dense graphs degrade to aggregation and an accessible relationship list.

### Globe and spatial flows

- Camera movement follows explicit navigation or selection.
- Stop promptly when the user acts again.
- Avoid perpetual orbit, parallax, or zoom in analytical reading.
- Particles or path velocity may encode real, declared flow only; they cannot stand for “opportunity” generically.

### Navigator and commands

- Show interpreted intent before or alongside execution.
- Distinguish navigation from generated explanation.
- Keep active geography, universe, time, and lens visible.
- Make command effects undoable or correctable.
- Do not cover the primary canvas with a full-screen conversational layer by default.

### Marketing narrative

- Build a useful static page first; animation progressively reveals continuity.
- Keep product, pricing, methodology, FAQ, and primary CTA usable without motion.
- Use real reproducible product states and declared evidence.
- Do not animate toward guaranteed outcomes, artificial urgency, fake scarcity, or fabricated social proof.

## High-leverage creative directions

These are starting points, not templates:

1. **World to proof** — a spatial signal resolves into typed relationships, then lands in source evidence without losing the selected anchor.
2. **Evidence parallax without scroll hijacking** — the analytical canvas remains stable while independently verifiable evidence layers enter at natural reading points.
3. **Temporal sedimentation** — prior states remain legible as history while the current state resolves, preserving retractions and contradictions.
4. **Lens continuity** — Flip preserves entity identity while Globe, Graph, and Dual reorganise around the same context.
5. **Traceable path reveal** — DrawSVG or MotionPath reveals a declared geographic or relational path and stops at its evidential boundary.
6. **Calm command response** — Navigator interpretation, scope change, and canvas update form one reversible timeline.

Invent stronger directions when the brief calls for them. Every effect still needs a semantic owner, an accessible equivalent, and a stable fallback.

## Acceptance evidence

| Risk                | Required evidence                                                                        |
| ------------------- | ---------------------------------------------------------------------------------------- |
| Context loss        | Before/after state assertions for selection, time, filters, lens, and rail               |
| Reduced motion      | Automated media-query coverage plus browser recording                                    |
| Keyboard/focus      | Tab order, focus restoration, escape/cancel, and non-drag operation                      |
| Semantic confusion  | State fixtures for support, contradiction, inferred, predicted, unknown, and unavailable |
| Lifecycle leak      | Mount/unmount or route-transition test with no stale triggers/listeners                  |
| Performance         | Trace on representative desktop, integrated graphics, and mobile fallback                |
| Scroll instability  | Dynamic-content and font-load refresh test; no production markers                        |
| Multilingual layout | Representative long-string and non-Latin fixtures                                        |
| Gate authority      | Independent review for material design direction or phase acceptance                     |

## Prohibited motion

- decorative permanent particles or pulsing;
- price-ticker, casino, trading-terminal, rocket, coin, generic AI sparkle, or game-reward language;
- animation that equates green/up/fast/large with truth, return, or suitability;
- inaccessible drag-only, hover-only, color-only, or motion-only state;
- full-screen transition that hides evidence or blocks escape;
- layout animation that produces cumulative layout shift;
- animation driven by private preference or aggregate attention as if it were economic evidence;
- arbitrary Timeline interpolation that leaks future evidence into an earlier state.
