---
name: performance-engineer
description: Enforce measurable CPU, GPU, network, memory and Core Web Vitals budgets for AXIGNAL's animated landing and Globe.
---

# AXIGNAL Landing Performance Engineer

## Budgets

- LCP target: <= 2.5 s at p75 on mobile field data;
- CLS target: <= 0.1;
- INP target: <= 200 ms;
- initial route JavaScript excluding deferred globe: <= 180 KB gzip;
- deferred globe JavaScript: <= 500 KB gzip target;
- initial poster: <= 220 KB desktop and <= 120 KB mobile;
- compressed production texture set: <= 12 MB desktop, <= 3 MB mobile;
- long tasks over 50 ms during scroll: zero in the normal path;
- active draw calls target: <= 40;
- active GPU texture memory target: <= 150 MB desktop.

## Adaptive quality

Use a capability tier selected from reduced-motion, device memory, DPR, WebGL support and measured frame time. Degrade bloom, clouds, node counts, texture resolution and antialiasing before reducing semantic content.

## Evidence

CI records bundle sizes, image dimensions, manifest validity and deterministic scene contracts. Browser acceptance records reduced-motion and no-WebGL fallbacks. Performance claims require Lighthouse or equivalent measured evidence, not visual judgement.
