# ADR-006 — Layered visual system remains a validated candidate

Status: `PROPOSED / VALIDATION REQUIRED`
Date: `2026-07-27`
Goal ID: `AXIGNAL-GOAL-001`

## Context

AXIGNAL requires a visual identity capable of supporting a world-scale investigation shell, dense professional analysis, epistemic state communication, multilingual use, accessibility and data visualisation.

A single undifferentiated palette would create material risks:

- brand colour could be confused with analytical meaning;
- supporting evidence could be confused with positive financial performance;
- missing data could appear as a low value;
- graph and map encodings could become inconsistent;
- exact prototype values could be treated as permanent decisions without evidence.

The current Signal Teal direction is promising but remains unvalidated against materially different alternatives.

## Candidate decision

AXIGNAL will use a layered visual-system architecture during prototype validation:

1. compact brand palette;
2. neutral structural UI palette;
3. explicit epistemic semantic palette;
4. independent data-visualisation palettes.

The design system will be implemented through semantic tokens and typed component variants. Exact colours, typefaces, dimensions, radii, shadows, durations and easing curves remain provisional.

At least three materially different visual directions will be compared:

- Signal Teal;
- Mineral Intelligence;
- Monochrome Signal;
- or stronger successors discovered during research.

The current candidate values in Contract 20 are prototype seeds only.

## Consequences

### Positive

- brand identity is separated from epistemic truth and financial direction;
- maps, graphs and timelines can use fit-for-purpose visual scales;
- dark, light and high-contrast themes can preserve semantics;
- candidate implementation can proceed without falsely freezing the final brand;
- visual changes remain auditable and testable.

### Negative

- prototype work must maintain more token layers;
- multiple visual directions require additional design and user-testing effort;
- production components cannot rely on convenient hard-coded colours;
- final brand selection is deferred until evidence exists.

## Validation requirements

The decision may be accepted only when qualified-user and technical evidence demonstrates:

- professional trust;
- visual distinctiveness;
- correct epistemic-state interpretation;
- no confusion between evidence, selection and expected return;
- WCAG 2.2 AA compliance;
- colour-vision resilience;
- six-language layout stability;
- sustained analytical readability;
- acceptable Globe–Graph performance;
- dark, light, reduced-motion, print and export parity.

## Rejection or revision conditions

The candidate architecture or leading direction must be revised when a simpler or materially different system produces better evidence on trust, comprehension, accessibility, performance or differentiation.

## Freeze rule

This ADR does not freeze a final palette or visual identity. Final acceptance requires a superseding ADR containing versioned production tokens, evidence, migration and rollback instructions.
