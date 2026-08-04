# AXIGNAL Landing Scroll Storyboard v2

Goal ID: `AXIGNAL-GOAL-001`
Task: `AX-F2-T18`

## Story thesis

**One public record becomes one defensible investigation.** The visitor follows the same objects from geography to evidence and dossier instead of reading disconnected feature panels.

| Scene label | Buyer question | Continuous visual state | Comprehension purpose |
|---|---|---|---|
| `SCENE_GLOBAL` | What is AXIGNAL? | One active 3D Globe with subtle global arcs and the commercial promise | Category and product comprehension |
| `SCENE_EUROPE` | Where does relevant demand appear? | The same Globe focuses on Europe; territorial opportunities and bounded TED pilot state appear | Scope and current product boundary |
| `SCENE_FRAGMENTATION` | Why is qualification expensive? | Portals, notices, documents and updates separate around the Globe | Fragmentation recognition |
| `SCENE_EVIDENCE` | How is source material governed? | The same fragments reorganize into Evidence Objects, Candidate Claims, admitted claims and unknowns | Epistemic comprehension |
| `SCENE_INVESTIGATION` | How do the product lenses work together? | Globe and graph share one `InvestigationContext`; relationships remain traceable | System-model comprehension |
| `SCENE_DOSSIER` | What usable result is produced? | Graph objects assemble into a reviewable synthetic dossier; the pin then releases into pricing | Outcome and access comprehension |

## ScrollTrigger contract

One labelled GSAP timeline owns pinning, scrub and all coordinated HTML transforms. It writes a normalized progress ref consumed by the same Three.js Canvas throughout. The transition to pricing is part of the final scene release.

Mobile retains the real Globe and six-scene continuity with shorter geometry and pin distance. Reduced motion removes prolonged scrub and continuous movement while preserving every scene as static ordered content.
