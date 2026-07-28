# 07 — Visual System Validation Work Package

Version: `0.1.0-candidate`
Status: `F1 VALIDATION PLAN / NOT FROZEN`
Goal ID: `AXIGNAL-GOAL-001`

## 1. Purpose

This work package converts Contract 20 and ADR-006 into evidence-producing prototype work. It does not select a final palette, typeface or aesthetic direction.

It maps primarily to:

- `AX-F1-T03` — materially different investigation shells;
- `AX-F1-T06` — Globe–Graph parity and transitions;
- `AX-F1-T09` — six-language fixtures;
- `AX-F1-T10` — moderated comparative testing;
- `AX-F1-T11` — iteration after every two participants;
- `AX-F1-T12` — accept, revise or reject the selected UX architecture.

## 2. Candidate directions

Prototype at least:

1. `SIGNAL_TEAL`;
2. `MINERAL_INTELLIGENCE`;
3. `MONOCHROME_SIGNAL`;
4. any later direction that materially outperforms them.

Each direction MUST use the same representative product content and workflows. Comparison MUST NOT be distorted by giving one direction better data, interaction completeness or copy.

## 3. Required prototype surfaces

Every direction MUST cover:

- command and context bar;
- Globe;
- Graph;
- Dual mode;
- Timeline;
- Claim and Evidence Rail;
- opportunity detail;
- claim/evidence drill-down;
- contradiction state;
- missing coverage state;
- Navigator interpretation;
- one dense table;
- one print or export surface.

## 4. Token evidence

For each direction, produce:

- brand tokens;
- dark structural tokens;
- light structural tokens;
- high-contrast or forced-colour behaviour;
- epistemic semantic tokens;
- sequential, diverging and categorical visualisation palettes;
- typography stack and fallback metrics;
- spacing and density tokens;
- radii, border and elevation tokens;
- motion tokens;
- print/export tokens.

Exact values remain candidate values until the visual freeze gate passes.

## 5. Automated checks

Required automated evidence:

- WCAG contrast matrix for actual foreground/background pairs;
- token reference audit preventing hard-coded semantic colours;
- dark/light semantic parity snapshots;
- colour-vision-deficiency snapshots;
- six-language overflow and truncation tests;
- reduced-motion snapshots;
- screenshot regression for minimum supported viewport;
- typography layout-shift measurement;
- performance trace for Globe–Graph transition;
- print/export snapshot verification.

## 6. Human comprehension tasks

Qualified participants MUST be able to answer:

- which object is selected;
- which claim is observed, calculated, inferred or predicted;
- which evidence supports and contradicts a thesis;
- where data is missing rather than low;
- whether a flow is measured or hypothetical;
- what time state the view represents;
- whether visual intensity represents evidence, activity, magnitude or expected return;
- why an opportunity changed state.

## 7. Brand and trust evaluation

Participants SHOULD evaluate:

- professional credibility;
- distinctiveness;
- perceived analytical seriousness;
- resemblance to crypto, trading, cybersecurity, climate-tech or generic AI products;
- sustained reading comfort;
- confidence using the product for consequential research;
- clarity of the Globe–Graph relationship.

Preference scores alone are insufficient. Comprehension, task performance and observed confusion have priority.

## 8. Display and environment matrix

Test at minimum:

- calibrated desktop display;
- ordinary office monitor;
- lower-quality or low-contrast display;
- integrated-graphics laptop;
- tablet or narrow desktop layout;
- dark ambient environment;
- bright ambient environment;
- browser zoom at 200%;
- reduced motion;
- forced colours or high contrast where available.

## 9. Multilingual matrix

Validate:

- English;
- Spanish;
- French;
- German;
- Brazilian Portuguese;
- Simplified Chinese.

Tests MUST include:

- expanded labels;
- dates, numbers, currencies and units;
- graph labels;
- map tooltips;
- claim cards;
- Navigator interpretation;
- Timeline events;
- print/export layouts.

## 10. Iteration cadence

After every two qualified participants:

1. classify comprehension failures;
2. separate content problems from visual-system problems;
3. update candidate tokens or component grammar;
4. preserve before/after evidence;
5. rerun automated checks;
6. document rejected alternatives.

A change MUST NOT be accepted merely because it appears more visually impressive.

## 11. Gate outcomes

The gate evaluator may return:

- `ACCEPT_DIRECTION_FOR_NEXT_PROTOTYPE`;
- `REVISE_AND_RETEST`;
- `REJECT_DIRECTION`;
- `INSUFFICIENT_EVIDENCE`;
- `FREEZE_VISUAL_SYSTEM_VERSION`.

`FREEZE_VISUAL_SYSTEM_VERSION` requires all Contract 20 acceptance conditions and a superseding accepted ADR.

## 12. Rollback

All candidate token sets and prototype screenshots MUST remain versioned. A later visual iteration MUST be able to restore the previous candidate without rewriting history.
