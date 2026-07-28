---
name: accessibility-auditor
description: Audit AXIGNAL's animated landing and Globe for keyboard access, screen-reader parity, reduced motion, contrast and non-visual equivalents.
---

# AXIGNAL Landing Accessibility Auditor

## Required controls

- visible skip link;
- logical heading hierarchy;
- keyboard-operable city and scenario selection;
- focus never trapped by pinned sections;
- explicit pause/reduce-motion control;
- `prefers-reduced-motion` respected in CSS and JavaScript;
- SplitText keeps an accessible text equivalent;
- canvas has a concise accessible name and adjacent detailed description;
- all city, opportunity and evidence content has DOM equivalents;
- no autoplaying motion is essential to conversion.

## Tests

Keyboard-only traversal, screen-reader landmarks, high contrast, 200% zoom, reduced motion, no-WebGL, touch-only and narrow viewport. Fail when the CTA becomes inaccessible or evidence classifications rely only on colour.
