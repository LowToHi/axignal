# 20 — Design System, Typography and Motion Contract

Version: `0.2.0-candidate`
Status: `NORMATIVE CANDIDATE / ITERATIVE VALIDATION REQUIRED`
Goal ID: `AXIGNAL-GOAL-001`

## 1. Purpose and non-freeze rule

This contract defines the current candidate architecture for AXIGNAL branding, interface styling, visual semantics, data visualisation and motion.

It is normative about **separation of concerns, accessibility, semantic integrity, implementation discipline and validation requirements**. It is deliberately non-final about exact colours, typefaces, dimensions, radii, shadows, durations, easing curves and aesthetic direction.

No candidate value in this document becomes a permanent brand or production token merely because it appears in a prototype or codebase. Final freezing requires the acceptance gate in Section 25 and a superseding accepted ADR.

A later visual iteration MAY replace any candidate value when it produces stronger evidence of:

- professional trust;
- distinctiveness;
- comprehension;
- accessibility;
- multilingual resilience;
- analytical calm;
- product performance;
- semantic precision.

The development agent MUST preserve this non-freeze rule. It MUST NOT silently promote candidate tokens to immutable brand rules.

## 2. Design thesis

AXIGNAL MUST feel cinematic in scale, institutional in detail and calm under analytical pressure.

The visual system MUST NOT imitate crypto exchanges, retail trading terminals, gaming dashboards or generic AI chat products.

The WOW effect MUST come from:

- continuity between Globe, Graph, Timeline, Claims and Evidence;
- meaningful transformations between spatial and relational views;
- exact information hierarchy;
- depth and motion tied to product semantics;
- world-scale exploration with immediate evidential drill-down.

Decoration MUST remain subordinate to comprehension. Visual intensity MUST NOT imply opportunity quality, expected return, truth or urgency unless a declared variable explicitly supports that interpretation.

## 3. Visual-system architecture

AXIGNAL MUST maintain four coordinated but separately governed colour systems.

### 3.1 Brand palette

The brand palette exists to make AXIGNAL recognisable. It SHOULD remain compact and SHOULD NOT be forced to encode all analytical meaning.

Candidate core roles:

- `AXIGNAL Ink` — primary dark identity field;
- `AXIGNAL Paper` — primary light identity field;
- `AXIGNAL Signal` — restrained signature accent.

A secondary mineral or warm accent MAY be tested for editorial, institutional or premium contexts, but MUST NOT collide with semantic contradiction or warning colours.

### 3.2 Structural UI palette

The structural UI palette governs:

- canvas backgrounds;
- panels;
- raised surfaces;
- active surfaces;
- borders;
- text hierarchy;
- overlays;
- focus and interaction states.

It SHOULD remain primarily neutral so analytical colours retain meaning.

### 3.3 Epistemic semantic palette

The epistemic palette governs declared states such as:

- observed;
- calculated;
- supporting;
- contradicting;
- inferred;
- predicted;
- unknown;
- expired;
- retracted or critically invalidated.

These colours belong to product semantics, not to the logo. They MUST remain consistent across Globe, Graph, Timeline, Claims, Evidence, tables, exports and Navigator explanations.

### 3.4 Data-visualisation palettes

Data visualisation requires independent palettes for:

- sequential magnitude;
- diverging values around a meaningful centre;
- categorical distinction;
- density;
- uncertainty;
- missing coverage;
- temporal comparison.

The AXIGNAL brand accent MUST NOT be applied automatically to every series, heatmap, node or flow. Scientific legibility takes precedence over decorative brand repetition.

## 4. Theme model

AXIGNAL MUST support dark and light themes from semantic tokens.

Dark is the candidate default for the immersive investigation shell. Light is a first-class mode for reading, comparison, accessibility, printing and export.

Theme changes MUST preserve:

- semantic meaning;
- relative hierarchy;
- accessible contrast;
- colour-independent redundancy;
- visualisation legibility;
- selected and focus states.

The light theme MUST be designed independently. Naive inversion is prohibited.

A high-contrast theme or operating-system forced-colour compatibility MUST be evaluated before production freeze.

## 5. Candidate brand directions

At least three materially different directions MUST be compared before visual freeze.

### 5.1 Signal Teal

Current leading candidate:

- deep neutral canvas;
- restrained cyan-teal signal accent;
- cartographic and technical character;
- calm institutional UI.

Strengths to test:

- world-scale exploration;
- signal and transmission metaphor;
- readability over dark cartography;
- technical precision without retail-finance green.

Risks to test:

- generic AI or cybersecurity appearance;
- similarity to climate-tech products;
- insufficient differentiation if teal is overused.

### 5.2 Mineral Intelligence

Alternative candidate:

- petroleum or mineral neutrals;
- restrained copper, stone or warm institutional detail;
- reduced dependence on startup-tech cyan.

Strengths to test:

- premium authority;
- historical and macroeconomic depth;
- differentiation.

Risks to test:

- collision with warning semantics;
- excessive luxury signalling;
- reduced cartographic clarity.

### 5.3 Monochrome Signal

Alternative candidate:

- black, white and neutral hierarchy;
- one high-precision accent;
- strong typographic and geometric identity.

Strengths to test:

- timelessness;
- clarity;
- distinctive editorial character.

Risks to test:

- insufficient analytical separation;
- overreliance on typography and layout;
- weaker dense-visualisation usability.

The candidate directions MAY evolve or be replaced if later research produces a stronger alternative.

## 6. Candidate dark foundation

Exact values remain provisional and subject to testing.

| Token role | Current candidate | Intended function |
|---|---:|---|
| `--ax-bg-canvas` | `#070A0E` | immersive primary canvas |
| `--ax-bg-panel` | `#0E141C` | primary analytical panels |
| `--ax-bg-raised` | `#171F2B` | raised surfaces and overlays |
| `--ax-bg-active` | `#202B39` | active or strongly selected structural surface |
| `--ax-border-subtle` | `#1D2835` | low-emphasis separation |
| `--ax-border-default` | `#344255` | normal structural boundary |
| `--ax-border-strong` | `#526176` | high-emphasis boundary |
| `--ax-fg-primary` | `#F3F6FA` | primary content |
| `--ax-fg-secondary` | `#B1BAC7` | supporting content |
| `--ax-fg-tertiary` | `#828D9C` | metadata and de-emphasised context |
| `--ax-fg-disabled` | `#5D6775` | disabled content only |

The original surface candidates `#0D1219`, `#131A24` and `#263244` remain useful reference points but SHOULD NOT be assumed final. Prototype review identified a risk that adjacent surface levels could merge perceptually on lower-quality displays.

The structural system SHOULD therefore validate:

- distinguishability of adjacent panels without relying on shadow;
- border visibility under different monitor calibration;
- readable hierarchy in dark ambient conditions;
- stable interpretation on compressed screenshots and video exports.

## 7. Candidate brand and semantic accents

Exact values remain provisional.

| Token role | Current candidate | Meaning |
|---|---:|---|
| `--ax-brand-signal` | `#48CBD0` | AXIGNAL identity and active system signal |
| `--ax-selection` | `#72A7FF` | focus, selection and navigation |
| `--ax-observed` | `#48CBD0` | directly observed state where semantically appropriate |
| `--ax-calculated` | `#72A7FF` | deterministically calculated state |
| `--ax-support` | `#70D6A4` | supporting evidence |
| `--ax-contradiction` | `#F5B45B` | contradiction or contested evidence |
| `--ax-inferred` | `#B79CFF` | inferred or modelled state |
| `--ax-predicted` | `#D68CE8` | prediction or scenario projection |
| `--ax-unknown` | `#8994A3` | unknown or incomplete coverage |
| `--ax-expired` | `#697483` | expired, stale or unavailable state |
| `--ax-critical` | `#FF7182` | retraction, security failure or critical invalidation only |

The final brand signal MAY move toward cyan, teal or another hue if testing improves distinctiveness. The support colour SHOULD remain sufficiently separated from the brand signal to prevent confusion between:

- system activity;
- selected object;
- supporting evidence;
- favourable financial movement.

Contradiction SHOULD use amber-like tension rather than universal red because contradiction does not necessarily mean falsehood, danger or loss.

Critical red or pink MUST remain scarce. It MUST NOT become the default colour for weak markets, bearish scenarios, ordinary contradictions or negative financial values.

## 8. Semantic token families

A single colour value per state is insufficient. Every semantic role SHOULD expose a family such as:

```text
--ax-<role>-fg
--ax-<role>-bg
--ax-<role>-border
--ax-<role>-muted
--ax-<role>-emphasis
--ax-<role>-pattern
```

Component implementations MUST use semantic tokens rather than hard-coded hex values.

No semantic state may rely only on colour. Shape, label, iconography, pattern, line style or position MUST provide redundant meaning.

## 9. Data-visualisation colour rules

### 9.1 Sequential scales

A sequential scale MUST represent one ordered magnitude. It SHOULD be perceptually progressive and MUST declare:

- metric;
- direction;
- transform;
- minimum and maximum;
- clipping;
- missing-value treatment.

A sequential scale MUST NOT be created merely by changing opacity over an arbitrary basemap when that produces non-uniform perception.

### 9.2 Diverging scales

A diverging scale MAY use cool and warm poles around a declared neutral point.

The visual MUST state what each pole means. Warm MUST NOT automatically mean negative and cool MUST NOT automatically mean positive.

### 9.3 Categorical scales

Categorical palettes MUST maximise separation between object classes and MUST include redundant shape, symbol or label encoding where misclassification would be material.

### 9.4 Heatmaps

Heatmaps MAY use established perceptually uniform scientific scales when they communicate data more accurately than the brand palette.

Missing coverage MUST use an explicit mask, hatching, boundary or label. It MUST NOT be rendered as the minimum observed value.

### 9.5 Graphs

Node appearance SHOULD primarily encode object type. Semantic status SHOULD use secondary channels such as border, halo, badge, pattern or lane.

Edge appearance MUST encode relation type, direction and epistemic basis. Inferred or hypothetical edges MUST NOT look identical to measured flows or observed relations.

## 10. Contrast and accessibility requirements

WCAG 2.2 AA is the minimum. High-value professional workflows SHOULD target stronger contrast where density permits.

Every token pair MUST be tested in its actual use, including:

- text on canvas;
- text on filled status chips;
- borders between adjacent surfaces;
- selected objects over maps;
- graph edges over variable backgrounds;
- semi-transparent overlays;
- printed and exported views;
- colour-vision deficiency simulations;
- forced-colour and high-contrast environments.

A contrast ratio for a foreground colour over the primary canvas does not prove that the same colour is valid as a filled button or as a translucent cartographic layer.

Structural separation SHOULD use a combination of tone, border, spacing and position. Shadow alone MUST NOT be required to perceive panel hierarchy.

## 11. Typography architecture

Candidate typography stack:

- `Geist Sans` for interface, long-form analytical reading and dense controls;
- `Geist Mono` for identifiers, methods, API values, tabular data and technical metadata;
- `Noto Sans SC` for Simplified Chinese;
- system fallbacks with metric adjustment to minimise layout shift.

`Sora` or another distinctive open-source display face MAY be evaluated for:

- wordmark exploration;
- marketing display typography;
- major section headings;
- editorial or report covers.

The product shell MUST NOT depend on a display face for core legibility. The final AXIGNAL wordmark SHOULD become a customised SVG asset rather than an unchanged font rendering.

A later licensed typeface MAY be adopted only through:

- an ADR;
- licence review;
- loading-performance review;
- six-language regression testing;
- documented fallback metrics.

Requirements:

- no serif dependency for the core product shell;
- tabular numerals for analytical data;
- explicit locale-aware number, date, currency and unit formatting;
- Chinese line breaking and punctuation tested independently;
- no meaning dependent on uppercase styling;
- translated strings allowed to expand without losing meaning;
- no blocking web fonts.

## 12. Candidate type scale

The following scale is a prototype starting point, not a frozen production scale:

```css
--ax-text-xs: 0.6875rem;
--ax-text-sm: 0.75rem;
--ax-text-body-sm: 0.8125rem;
--ax-text-body: 0.875rem;
--ax-text-md: 1rem;
--ax-text-lg: 1.125rem;
--ax-text-xl: 1.5rem;
--ax-text-2xl: 2rem;
--ax-text-display: clamp(2.5rem, 5vw, 5rem);
```

Text below 12 px MUST NOT carry critical content. Dense modes MAY reduce spacing before reducing essential text size.

## 13. Spacing and density

The candidate spacing foundation uses a 4 px base rhythm:

```css
--ax-space-1: 0.25rem;
--ax-space-2: 0.5rem;
--ax-space-3: 0.75rem;
--ax-space-4: 1rem;
--ax-space-5: 1.25rem;
--ax-space-6: 1.5rem;
--ax-space-8: 2rem;
--ax-space-10: 2.5rem;
--ax-space-12: 3rem;
```

The product MUST support:

- `FOCUS` — lower density for discovery, onboarding and focused reading;
- `PROFESSIONAL` — default analytical density;
- `DENSE` — optional advanced mode for tables and multi-panel comparison.

Density MUST NOT change epistemic content, remove caveats, suppress contradictions or make unknown coverage invisible.

## 14. Shape, borders and elevation

Candidate radii:

```css
--ax-radius-xs: 4px;
--ax-radius-sm: 6px;
--ax-radius-md: 10px;
--ax-radius-lg: 14px;
--ax-radius-pill: 999px;
```

AXIGNAL SHOULD avoid excessive rounding that makes the product resemble a consumer lifestyle application.

Pills SHOULD be reserved for compact statuses, filters and tags. Main analytical surfaces SHOULD feel integrated into one instrument rather than a collection of unrelated floating cards.

Elevation SHOULD rely primarily on hierarchy, boundaries and spacing. Shadows MAY be used for overlays, dialogs, drawers and temporarily raised controls.

Candidate shadows:

```css
--ax-shadow-panel:
  0 1px 0 rgb(255 255 255 / 0.03),
  0 12px 32px rgb(0 0 0 / 0.28);

--ax-shadow-overlay:
  0 20px 60px rgb(0 0 0 / 0.42);
```

Persistent glassmorphism is prohibited. Blur MAY be used sparingly for command surfaces or floating controls over Globe when contrast and performance remain acceptable.

## 15. Layout primitives

Canonical shell regions:

- global command and context bar;
- lens selector `AUTO / GLOBE / GRAPH / DUAL`;
- primary Globe or Graph canvas;
- persistent Claim and Evidence Rail;
- persistent Timeline;
- optional Navigator panel;
- context-aware comparison and investigation-trail controls.

Candidate desktop variables:

```css
--ax-command-height: 60px;
--ax-rail-width: clamp(340px, 27vw, 440px);
--ax-timeline-height: 84px;
--ax-panel-gap: 1px;
```

These values MUST remain responsive and user-testable. The evidence rail SHOULD support collapse, resizing and conversion to a drawer on constrained screens.

The layout MUST preserve selected subject, time, filters, claims and evidence across lens changes.

## 16. Component system

shadcn/ui provides accessible primitives, not final visual identity.

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

Components MUST encode contracts, interaction states and accessibility rules, not only styling.

Every interactive component MUST define:

- default;
- hover where applicable;
- focus-visible;
- active;
- selected;
- disabled;
- loading;
- error;
- stale;
- restricted or entitlement-limited.

Hover MUST NOT be the only way to reveal material information.

## 17. CSS architecture

The global CSS layer MUST remain small and auditable. It SHOULD contain:

1. primitive tokens;
2. semantic tokens;
3. reset and base typography;
4. theme definitions;
5. accessibility defaults;
6. global motion defaults;
7. print and export rules;
8. narrowly scoped structural utilities.

Recommended candidate structure:

```text
styles/
├── globals.css
├── tokens/
│   ├── primitives.css
│   ├── semantic.css
│   ├── epistemic.css
│   ├── visualisation.css
│   ├── typography.css
│   ├── spacing.css
│   └── motion.css
├── themes/
│   ├── dark.css
│   ├── light.css
│   └── high-contrast.css
└── print.css
```

Component-specific layout, data-driven styling and renderer-specific rules MUST NOT accumulate in `globals.css`.

Hard-coded semantic colours inside component selectors are prohibited. Component variants SHOULD map typed domain state to semantic tokens.

## 18. Candidate global token implementation

The following fragment is illustrative and MAY change during implementation:

```css
:root {
  color-scheme: dark;

  --ax-brand-ink: #070a0e;
  --ax-brand-paper: #f4f7f9;
  --ax-brand-signal: #48cbd0;

  --ax-bg-canvas: #070a0e;
  --ax-bg-panel: #0e141c;
  --ax-bg-raised: #171f2b;
  --ax-bg-active: #202b39;

  --ax-fg-primary: #f3f6fa;
  --ax-fg-secondary: #b1bac7;
  --ax-fg-tertiary: #828d9c;
  --ax-fg-disabled: #5d6775;

  --ax-border-subtle: #1d2835;
  --ax-border-default: #344255;
  --ax-border-strong: #526176;

  --ax-selection: #72a7ff;
  --ax-support: #70d6a4;
  --ax-contradiction: #f5b45b;
  --ax-inferred: #b79cff;
  --ax-predicted: #d68ce8;
  --ax-unknown: #8994a3;
  --ax-critical: #ff7182;
}
```

This fragment MUST be treated as a prototype seed, not as an accepted brand asset.

## 19. Motion hierarchy

### Level 0 — none

Used for reduced-motion preference and critical analytical reading.

### Level 1 — microinteraction

Candidate duration: `80–180 ms` for hover, focus, selection confirmation and compact control state.

### Level 2 — contextual continuity

Candidate duration: `180–350 ms` for panel movement, claim preview, rail transitions and lens controls.

### Level 3 — semantic transformation

Candidate duration: `350–800 ms` for Globe-to-Graph transformation, time-state transitions and investigation restoration.

Longer sequences require explicit user initiation and MUST remain interruptible.

Candidate motion tokens:

```css
--ax-duration-instant: 80ms;
--ax-duration-fast: 140ms;
--ax-duration-base: 240ms;
--ax-duration-slow: 420ms;
--ax-duration-transform: 720ms;

--ax-ease-standard: cubic-bezier(0.2, 0, 0, 1);
--ax-ease-enter: cubic-bezier(0, 0, 0.2, 1);
--ax-ease-exit: cubic-bezier(0.4, 0, 1, 1);
--ax-ease-spatial: cubic-bezier(0.22, 1, 0.36, 1);
```

Motion MUST communicate continuity, causality of interface action or temporal change. Decorative particles, permanent pulsing, urgency animation and spectacle without analytical meaning are prohibited.

## 20. Globe–Graph transformation

The candidate WOW interaction is a meaningful morph between spatial and relational representations:

- geographic anchors become or highlight graph nodes;
- spatial flows become typed edges when semantically valid;
- the selected opportunity remains visually anchored;
- Claim/Evidence Rail and Timeline remain stationary or predictably continuous;
- inferred edges MUST not visually transform as if they were measured flows;
- camera and graph movement MUST stop promptly after user input.

The transition MUST degrade gracefully to an immediate cut under reduced motion or low-performance devices.

Its duration, geometry and interpolation remain candidates until prototype validation.

## 21. Navigator interaction

The Navigator MUST:

- show the interpreted command before or alongside execution;
- visibly distinguish navigation action from generated explanation;
- expose active geography, universe, time and lens;
- allow undo and correction;
- cite claims and evidence when explaining;
- never obscure the primary canvas with a full-screen chat by default.

## 22. Remotion visual exports

Remotion exports MUST use the same semantic tokens, typography, claim grammar and coverage language as the application.

Templates SHOULD include:

- investigation summary;
- Time Machine replay;
- market or opportunity climate change;
- claim-to-evidence explainer;
- Knowledge Tide versus external evidence comparison.

Every export MUST include as-of state, source attribution and a clear distinction between observed and generated content.

## 23. Icons and imagery

- Use a consistent restrained icon system such as Lucide for interface actions.
- Domain-specific epistemic icons MAY be custom but MUST remain simple and labelled.
- Avoid stock photography, coins, upward arrows, brains, rockets and generic AI sparkles.
- Geographic textures and data-driven particles MAY be used only when they encode real state.
- Brand recognition SHOULD rely on wordmark, geometry, cartographic behaviour and composition rather than repeated accent colour.

## 24. Performance requirements

The design system MUST support:

- first meaningful shell render without loading Remotion;
- lazy loading of graph, dense geospatial and video-export packages;
- no blocking web fonts;
- no animated layout shift;
- cancellation of obsolete transitions;
- adaptive layer detail based on device capability;
- stable interaction on the minimum supported professional desktop;
- acceptable degradation on mobile and integrated graphics.

Blur, transparency, filters and large animated shadows MUST be performance-tested on representative hardware.

## 25. Validation and freeze gate

The visual system remains open until evidence supports a freeze.

Prototype v0.2 or successors MUST compare materially different visual directions and demonstrate:

1. professional trust with qualified target users;
2. visual distinctiveness without dependence on generic AI tropes;
3. correct interpretation of observed, calculated, inferred, predicted, supporting, contradicting, unknown and critical states;
4. no confusion between brand signal, system selection, supporting evidence and positive expected return;
5. distinguishable structural surfaces on representative displays;
6. WCAG 2.2 AA across actual component combinations;
7. colour-vision-deficiency resilience through redundant encoding;
8. Globe–Graph continuity without context loss;
9. six-language layout resilience;
10. dark, light, reduced-motion and high-contrast compatibility;
11. acceptable performance on minimum supported hardware;
12. fatigue and comprehension testing during sustained analytical use;
13. correct heatmap, graph and missing-coverage interpretation;
14. no confusion between visual intensity, evidence strength and expected return;
15. export and print legibility.

Evidence SHOULD include:

- moderated usability sessions;
- preference-independent comprehension tasks;
- contrast reports;
- colour-vision simulations;
- multilingual screenshots and overflow tests;
- performance traces;
- comparative prototype recordings;
- design-token audit;
- accessibility audit;
- explicit reasons for accepting or rejecting each visual direction.

A candidate direction MUST be revised or rejected when it:

- causes epistemic-state confusion;
- appears materially similar to generic AI, crypto or trading products;
- creates sustained reading fatigue;
- fails multilingual or accessibility gates;
- depends on expensive visual effects for identity;
- makes Globe, Graph and Timeline feel like unrelated products;
- weakens trust relative to a simpler alternative.

The final freeze requires:

1. an accepted visual-direction ADR;
2. versioned production tokens;
3. regression fixtures for every theme and locale;
4. an approved migration path from candidate tokens;
5. rollback capability;
6. explicit confirmation that later evidence may still justify a superseding version.
