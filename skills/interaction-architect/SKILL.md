---
name: interaction-architect
description: Design AXIGNAL's GSAP ScrollTrigger narrative as reversible, responsive, accessible state transitions tied to the product's epistemic model.
---

# AXIGNAL Interaction Architect — Scroll Storytelling

## Narrative contract

The landing journey is:

`signal noise → structured investigation → geographic discovery → evidence classification → human review → outcomes → request access`

## Eight acts

1. The Signal Field.
2. Too Much Noise.
3. Ask Anything.
4. Globe Intelligence.
5. Claim & Evidence Rail.
6. Human Review.
7. Outcomes.
8. Take Action.

## GSAP rules

- use one master timeline per pinned chapter;
- use labels for semantic states, never anonymous magic offsets;
- use `gsap.context()` or `useGSAP()` and revert on unmount;
- use `ScrollTrigger.matchMedia()` for desktop, tablet, mobile and reduced motion;
- SplitText uses `aria: auto`, `autoSplit: true`, and only the minimum split granularity;
- pinned scenes must have normal-flow equivalents;
- scroll position may reveal state but must not be the sole interaction method;
- avoid nested pinning and scroll-jacking;
- call `ScrollTrigger.refresh()` only after fonts/assets/layout settle;
- route globe state through a typed scene-state store, not direct DOM-to-WebGL mutation.

## Motion budget

- no camera movement faster than the user can cognitively track;
- no continuous parallax in reduced-motion mode;
- no more than one dominant motion event at a time;
- use opacity and short transforms rather than blur-heavy full-screen effects;
- preserve CTA stability: conversion controls do not move away while targeted.

## Acceptance

Every act must answer one buyer question and end in a stable visual state. The visitor must understand the product with animations disabled.
