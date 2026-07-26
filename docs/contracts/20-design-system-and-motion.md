# 20 — Design System, Typography and Motion Contract

Version: `0.1.0-candidate`
Status: `NORMATIVE CANDIDATE / PROTOTYPE VALIDATION REQUIRED`
Goal ID: `AXIGNAL-GOAL-001`

## 1. Design thesis

AXIGNAL MUST feel cinematic in scale, institutional in detail and calm under analytical pressure.

The visual system MUST NOT imitate crypto exchanges, retail trading terminals, gaming dashboards or generic AI chat products.

The WOW effect MUST come from:

- continuity between Globe, Graph, Timeline, Claims and Evidence;
- meaningful transformations between spatial and relational views;
- exact information hierarchy;
- depth and motion tied to product semantics;
- world-scale exploration with immediate evidential drill-down.

## 2. Theme model

AXIGNAL MUST support dark and light themes from tokens, with dark as the candidate default for the immersive investigation shell and light as a first-class research, reading and export mode.

Theme changes MUST preserve semantic meaning and accessibility.

## 3. Candidate colour system

Exact values remain subject to contrast testing and prototype validation.

### Neutral dark foundation

| Token | Candidate | Meaning |
|---|---|---|
| `--ax-bg` | `#070A0E` | primary immersive background |
| `--ax-surface-1` | `#0D1219` | primary panels |
| `--ax-surface-2` | `#131A24` | raised and selected surfaces |
| `--ax-border` | `#263244` | structure and separation |
| `--ax-text` | `#F3F6FA` | primary text |
| `--ax-text-muted` | `#A7B0BE` | secondary text |

### Semantic accents

| Token | Candidate | Meaning |
|---|---|---|
| `--ax-signal` | `#52D3C5` | AXIGNAL signal and active system state |
| `--ax-selection` | `#72A7FF` | focus, selection and navigation |
| `--ax-support` | `#65CDA2` | supporting evidence |
| `--ax-contradiction` | `#F5B45B` | contradiction or contested evidence |
| `--ax-inference` | `#B79CFF` | inferred, modelled or predicted state |
| `--ax-unknown` | `#7E8998` | unknown or incomplete coverage |
| `--ax-critical` | `#FF7182` | retraction, security or critical invalidation only |

No semantic state may rely only on colour. Shape, label, iconography, pattern, line style or position MUST provide redundant meaning.

## 4. Light theme

The light theme MUST be designed independently rather than produced through naive colour inversion.

It SHOULD use warm-neutral whites, dark slate text and equivalent semantic hues adjusted to pass WCAG 2.2 AA.

## 5. Typography

Candidate open-source baseline:

- `Geist Sans` for Latin-script interface and editorial hierarchy;
- `Geist Mono` for identifiers, data, methods, API values and technical metadata;
- `Noto Sans SC` for Simplified Chinese rendering;
- system fallbacks with metric adjustment to minimise layout shift.

Requirements:

- no serif dependency for the core product shell;
- tabular numerals for market and analytical data;
- explicit locale-aware number, date, currency and unit formatting;
- Chinese line breaking and punctuation MUST be tested independently;
- labels MUST not depend on uppercase styling because casing rules differ across languages;
- translated strings MUST be allowed to expand without truncating meaning.

A later licensed typeface MAY replace the Latin display face only through an ADR, licence review and multilingual regression test.

## 6. Density modes

The product MUST support:

- `FOCUS` — lower density for discovery, onboarding and focused reading;
- `PROFESSIONAL` — default analytical density;
- `DENSE` — optional advanced mode for tables and multi-panel comparison.

Density MUST not change epistemic content or hide contradictions.

## 7. Layout primitives

Canonical shell regions:

- global command and context bar;
- lens selector `AUTO / GLOBE / GRAPH / DUAL`;
- primary Globe or Graph canvas;
- persistent Claim and Evidence Rail;
- persistent Timeline;
- optional Navigator panel;
- context-aware comparison and investigation-trail controls.

The layout MUST preserve selected subject, time, filters, claims and evidence across lens changes.

## 8. Component system

shadcn/ui provides accessible primitives, not the final visual identity.

AXIGNAL MUST own a versioned internal registry containing domain components such as:

- `AxignalCommandBar`;
- `LensSwitcher`;
- `InvestigationBreadcrumbs`;
- `ClaimCard`;
- `EvidenceCard`;
- `ContradictionLane`;
- `CoverageLegend`;
- `KnowledgeTidePanel`;
- `ResearchCandidateCard`;
- `TemporalScrubber`;
- `ScenarioBand`;
- `SourceProvenanceDrawer`;
- `InvestigationTrail`.

Components MUST encode contracts and accessibility rules, not only styling.

## 9. Motion hierarchy

### Level 0 — none

Used for reduced-motion preference and critical analytical reading.

### Level 1 — microinteraction

100–180 ms candidate duration for hover, focus, selection confirmation and panel state.

### Level 2 — contextual continuity

180–350 ms candidate duration for panel movement, claim preview, rail transitions and lens controls.

### Level 3 — semantic transformation

350–800 ms candidate duration for Globe-to-Graph transformation, time-state transitions and investigation restoration.

Longer sequences require explicit user initiation and MUST remain interruptible.

## 10. Globe–Graph transformation

The candidate WOW interaction is a meaningful morph between spatial and relational representations:

- geographic anchors become or highlight graph nodes;
- spatial flows become typed edges when semantically valid;
- the selected opportunity remains visually anchored;
- Claim/Evidence Rail and Timeline remain stationary or predictably continuous;
- inferred edges MUST not visually transform as if they were measured flows;
- camera and graph movement MUST stop promptly after user input.

The transition MUST degrade gracefully to an immediate cut under reduced motion or low-performance devices.

## 11. Navigator interaction

The Navigator MUST:

- show the interpreted command before or alongside execution;
- visibly distinguish navigation action from generated explanation;
- expose active geography, universe, time and lens;
- allow undo and correction;
- cite claims and evidence when explaining;
- never obscure the primary canvas with a full-screen chat by default.

## 12. Remotion visual exports

Remotion exports MUST use the same tokens, typography, claim grammar and coverage language as the application.

Templates SHOULD include:

- investigation summary;
- Time Machine replay;
- market or opportunity climate change;
- claim-to-evidence explainer;
- Knowledge Tide versus external evidence comparison.

Every export MUST include as-of state, source attribution and a clear distinction between observed and generated content.

## 13. Icons and imagery

- Use a consistent restrained icon system such as Lucide for interface actions.
- Domain-specific epistemic icons MAY be custom but MUST remain simple and labelled.
- Avoid stock photography, coins, upward arrows, brains, rockets and generic AI sparkles.
- Geographic textures and data-driven particles MAY be used only when they encode real state.

## 14. Accessibility

- WCAG 2.2 AA minimum;
- visible focus;
- full keyboard navigation;
- screen-reader summaries for Globe and Graph;
- textual and tabular equivalents;
- reduced motion;
- contrast tests for every semantic token pair;
- touch targets and zoom support;
- no information encoded solely by hover.

## 15. Performance budgets

The design system MUST support:

- first meaningful shell render without loading Remotion;
- lazy loading of graph, dense geospatial and video-export packages;
- no blocking web fonts;
- no animated layout shift;
- cancellation of obsolete transitions;
- adaptive layer detail based on device capability.

## 16. Acceptance gate

This design system becomes frozen only after prototype v0.2 demonstrates:

- professional trust and visual distinctiveness with qualified users;
- correct interpretation of semantic colours and patterns;
- Globe–Graph continuity without context loss;
- six-language layout resilience;
- reduced-motion equivalence;
- acceptable performance on the minimum supported desktop;
- no confusion between visual intensity, evidence strength and expected return.
