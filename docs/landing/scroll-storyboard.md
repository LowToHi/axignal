# AXIGNAL Landing Scroll Storyboard v1

## Story thesis

**From signal noise to decision confidence.** The visitor experiences a bounded investigation rather than reading a list of features.

| Act | Buyer question | Stable visual state | Conversion purpose |
|---|---|---|---|
| 1. The Signal Field | What is AXIGNAL? | Europe-facing Globe and primary promise | Category comprehension |
| 2. Too Much Noise | Why is this needed? | Fragmented signals collapse into structure | Problem identification |
| 3. Ask Anything | Is it difficult to use? | Navigator creates a typed investigation | Reduce adoption friction |
| 4. Globe Intelligence | What can I discover? | Madrid, London, Paris and Berlin activated | Product desire |
| 5. Claim & Evidence Rail | Why should I trust it? | Fact/inference/prediction/contradiction/unknown separated | Trust formation |
| 6. Human Review | Who governs edge cases? | Proposal → policy → admission → review | Objection handling |
| 7. Outcomes | What changes operationally? | Reproducible, explicitly synthetic outcome indicators | Value rationalisation |
| 8. Take Action | What happens next? | Globe resolves into AXIGNAL mark and stable CTA | Qualified request access |

## ScrollTrigger contract

Each act owns a labelled GSAP timeline. The Globe consumes a typed `LandingSceneState`; ScrollTrigger never mutates Three.js objects directly. Mobile uses shorter non-pinned chapters. Reduced-motion mode uses discrete crossfades and static diagrams.
