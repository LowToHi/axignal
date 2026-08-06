---
name: axignal-cinematic-webgl-scroll
description: Audit and upgrade AXIGNAL cinematic Globe rendering in React Three Fiber without replacing its GSAP choreography. Use for texture quality tiers, WebGL color management, adaptive Canvas DPR, drawing-buffer sharpness, GPU capability and memory budgets, regional geographic LOD, shader texture blending, vector boundaries, fallback lifecycle, asset licensing, offscreen rendering, instancing, or measurable visual-sharpness gates.
---

# AXIGNAL Cinematic WebGL Scroll

Improve the existing Globe render pipeline in place. Preserve `AXIGNAL-GOAL-001`, one Canvas, one Globe scene and the canonical `InvestigationContext`.

## Authority boundary

Read `skills/axignal-gsap-ui-ux/SKILL.md` before work involving scroll. That Skill retains authority over GSAP, ScrollTrigger, pin, scrub, labels, lifecycle, responsive motion, reduced motion and semantic continuity.

This Skill owns only:

- texture tiers and licensed derivatives;
- Canvas DPR and drawing-buffer sharpness;
- WebGL capabilities, color spaces and texture memory;
- regional LOD and shader crossfade;
- vector geographic layers;
- R3F performance, fallback and telemetry.

Do not repeat general GSAP rules. Do not replace a valid timeline to solve a rendering defect.

## Workflow

1. Confirm the active task and `AXIGNAL-GOAL-001`.
2. Audit the current Canvas, textures, renderer capabilities, poster lifecycle and active LOD.
3. Preserve the existing Canvas, scene state and scroll progress source.
4. Select `mobile`, `desktop-standard` or `desktop-high` from measured capabilities.
5. Load the global tier first; preload regional LOD before its scene needs it.
6. Crossfade global and regional textures in the Earth shader using canonical scene progress.
7. Render boundaries as an independent geometry layer.
8. Adapt DPR with temporal windows and hysteresis; never change DPR every frame.
9. Pause or degrade offscreen, instance repeated markers, reuse resources and dispose owned GPU resources.
10. Expose runtime telemetry and run the deterministic verifier.
11. Capture the complete scroll path with a self-contained headless browser and hard timeout.
12. Report evidence for human visual acceptance. Do not self-approve.

Read [references/webgl-rendering-contract.md](references/webgl-rendering-contract.md) for tier thresholds, observability fields, licensing and acceptance gates.

## Hard gates

Fail when:

- Europe close-up uses only the global 4K texture;
- no regional LOD is requested, loaded, activated and reversibly blended;
- Canvas effective DPR and drawing buffer are not observable;
- capable desktop hardware cannot reach effective DPR 1.5;
- country boundaries remain only baked into the albedo;
- color textures are not sRGB or use unsuitable filters;
- no sharpness gate exists;
- the poster downloads on the healthy WebGL path;
- asset provenance or rights basis is absent;
- WebGL errors, context loss or LOD failure lack an explicit fallback;
- KTX2 absence is misreported as a failure while `BLOCKED_NO_PINNED_ENCODER` is documented.

## Validation

Run:

```bash
node skills/axignal-cinematic-webgl-scroll/scripts/audit-webgl-globe.mjs
node skills/axignal-cinematic-webgl-scroll/scripts/audit-webgl-globe.mjs --self-test
```

Then run typecheck, production build, applicable landing verifier and bounded browser captures. Record `NOT_MEASURED` with a reason when physical-GPU metrics cannot be measured; never substitute SwiftShader results for a real device claim.

## Prohibited actions

- Do not duplicate or supersede `axignal-gsap-ui-ux`.
- Do not rename or rebuild `investigationCinematic`.
- Do not change its six canonical labels, pin, desktop `scrub: 1`, responsive or reduced-motion behavior.
- Do not add an unpinned texture encoder or runtime dependency.
- Do not download or ship an asset without explicit rights and provenance.
- Do not hotlink production textures.
- Do not use a poster, giant PNG or prerendered video as the healthy WebGL experience.
- Do not claim visual acceptance without human review.
