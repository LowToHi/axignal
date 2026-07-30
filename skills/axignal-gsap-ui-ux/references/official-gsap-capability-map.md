# Official GSAP capability map

Use this reference while implementing or reviewing GSAP code. It condenses the official GreenSock AI Skills snapshot identified in [upstream-attribution.md](upstream-attribution.md); consult the linked official documentation for an API detail that may have changed.

## Dependency and registration

GSAP and its plugins are distributed through the public `gsap` package. React integration uses `@gsap/react`.

```ts
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { Flip } from "gsap/Flip";
import { useGSAP } from "@gsap/react";

gsap.registerPlugin(ScrollTrigger, Flip, useGSAP);
```

Register plugins once before first use. Do not create a private registry configuration, auth token, or membership flow. Use the repository package manager, pin the resolved dependency in its lockfile, and verify current installation guidance at <https://gsap.com/docs/v3/Installation/>.

## Capability selection

| Need                           | GSAP capability                    | Required discipline                                                       |
| ------------------------------ | ---------------------------------- | ------------------------------------------------------------------------- |
| One dynamic transition         | `gsap.to`, `from`, `fromTo`, `set` | Prefer transform aliases and store the tween when it needs control        |
| Coordinated sequence           | `gsap.timeline`                    | Use labels and position parameters; do not chain delays                   |
| Responsive or reduced motion   | `gsap.matchMedia`                  | Revert the media context and provide an immediate stable state            |
| Scroll-linked sequence         | ScrollTrigger                      | Register once, scope and clean up, refresh only after real layout changes |
| Layout/state continuity        | Flip                               | Capture state, mutate DOM, animate from prior state                       |
| Drag or inertia                | Draggable + InertiaPlugin          | Bounds, keyboard alternative, focus preservation, explicit teardown       |
| Wheel/touch/pointer intent     | Observer                           | Do not trap native navigation or scroll without a usable fallback         |
| Character/word/line typography | SplitText                          | Split only required units, retain accessible semantics, revert on cleanup |
| Draw or reveal a path          | DrawSVGPlugin                      | Path must encode meaningful state and have a visible stroke               |
| Transform one SVG shape        | MorphSVGPlugin                     | Test shape alignment and semantic continuity; avoid decorative ambiguity  |
| Move along a path              | MotionPathPlugin                   | Use real topology or an intentional interaction path                      |
| Scroll to a location           | ScrollToPlugin                     | Preserve native focus and anchor behavior                                 |
| Smooth native scroll           | ScrollSmoother                     | Treat as progressive enhancement and validate accessibility/performance   |
| Custom easing                  | CustomEase                         | Prefer AXIGNAL motion tokens and documented curves                        |
| Development scrubbing          | GSDevTools                         | Development only; never ship it                                           |

Official plugin index: <https://gsap.com/docs/v3/Plugins/>.

## Core patterns

Prefer camelCase properties and transform aliases:

```ts
const transition = gsap.to(target, {
  x: 24,
  scale: 1.02,
  autoAlpha: 1,
  duration: 0.24,
  ease: "power2.out",
  overwrite: "auto",
});
```

Use a timeline when order matters:

```ts
const timeline = gsap.timeline({
  paused: true,
  defaults: { duration: 0.24, ease: "power2.out" },
});

timeline
  .addLabel("depart")
  .to(origin, { autoAlpha: 0.4 }, "depart")
  .to(sharedAnchor, { x: destinationX }, "depart")
  .addLabel("settled")
  .to(destination, { autoAlpha: 1 }, "settled-=0.08");
```

Put ScrollTrigger on a top-level tween or timeline, not on a child tween. Do not combine `scrub` and `toggleActions` on the same trigger. Remove `markers: true` from production. For horizontal `containerAnimation`, use `ease: "none"`.

Official core and ScrollTrigger documentation:

- <https://gsap.com/docs/v3/GSAP/>
- <https://gsap.com/docs/v3/Plugins/ScrollTrigger/>

## React and Next.js

Prefer `useGSAP()` with scope and client-only execution:

```tsx
"use client";

import { useRef } from "react";
import { gsap } from "gsap";
import { useGSAP } from "@gsap/react";

gsap.registerPlugin(useGSAP);

export function InvestigationTransition() {
  const root = useRef<HTMLDivElement>(null);

  useGSAP(
    () => {
      const media = gsap.matchMedia();

      media.add(
        {
          fullMotion: "(prefers-reduced-motion: no-preference)",
          reduceMotion: "(prefers-reduced-motion: reduce)",
        },
        (context) => {
          if (context.conditions?.reduceMotion) {
            gsap.set("[data-transition-target]", { clearProps: "all" });
            return;
          }

          gsap.from("[data-transition-target]", {
            y: 16,
            autoAlpha: 0,
            duration: 0.24,
          });
        },
      );

      return () => media.revert();
    },
    { scope: root },
  );

  return <div ref={root}>{/* canonical content */}</div>;
}
```

Use `contextSafe()` for callbacks that create GSAP objects after the hook executes. When `@gsap/react` is unavailable, create animations inside `gsap.context()` and call `context.revert()` in the effect cleanup. Never call browser-only animation during server rendering.

Official React guidance: <https://gsap.com/resources/React/>.

## Other frameworks

- Create animation only after the component DOM is mounted.
- Scope selectors with `gsap.context(callback, componentRoot)`.
- Revert the context in `onUnmounted`, `onDestroy`, or the framework-equivalent cleanup.
- Refresh ScrollTrigger only after async content or font changes alter layout.
- Register plugins at application level, not on every render.

## Performance rules

- Prefer transforms and opacity over `width`, `height`, `top`, `left`, margin, or padding.
- Use `quickTo()` for rapidly updated pointer-following properties.
- Read layout together, then write animation state; avoid interleaved layout thrashing.
- Animate only visible items in long lists and dense visualisations.
- Do not promote every element with `will-change` or `force3D`.
- Pause or kill inactive animation and cancel obsolete transitions.
- Pin only what is necessary and test scrub/pin on low-end hardware.
- Lazy-load route-specific plugins when bundle cost is material.

Official performance source: `gsap-performance` in the upstream snapshot.

## Update protocol

Before revising this reference:

1. compare the pinned upstream commit with `greensock/gsap-skills` `main`;
2. inspect the changed official Skill modules and linked GSAP documentation;
3. update this capability map and `upstream-attribution.md`;
4. rerun the Skill structure, contract, self-test, and naming validations;
5. increment the AXIGNAL Skill version and preserve the prior evidence.
