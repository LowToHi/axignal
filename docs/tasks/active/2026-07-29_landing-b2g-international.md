# AX-F2-T18 — International B2G landing

Goal ID: `AXIGNAL-GOAL-001`
State: `IN_PROGRESS`
Phase: `F2`

## Objective

Replace the legacy Global Opportunity Intelligence landing narrative with the authorised first commercial expression: B2G Public Procurement Intelligence for organisations that sell to government.

## Context

Contract 28 and ADR-013 define the commercial wedge and candidate packaging. The current landing consumes one explicit projection of the TED Search API bounded product profile: `PRODUCT_ADMITTED → PRIVATE_AUTHENTICATED_PILOT → PUBLIC_ACCESS_DISABLED`. This projection does not rewrite historical source-admission evidence. Billing and unrestricted source use remain disabled, and all product demonstrations are synthetic and explicitly labelled.

## Affected systems

- `apps/landing`;
- public intake endpoint;
- locale, metadata and analytics contracts;
- globe asset provenance;
- landing CI, browser tests and evidence documentation.

## Implementation plan

1. Add six locale routes and parity-checked JSON dictionaries.
2. Replace the old narrative with one six-scene, pinned and scrubbed B2G investigation story.
3. Keep one mounted Globe Canvas from the hero through Europe, fragmentation, evidence, InvestigationContext and dossier assembly.
4. Add consent-aware analytics and a two-step, fail-closed Design Partner intake.
5. Add SEO, accessibility, reduced-motion, low-capability and performance safeguards.
6. Produce automated, visual, security and provenance evidence.

## Blockers

- KTX2 output remains conditional on an available deterministic encoder; WebP is the bounded GPU texture fallback.
- Production marketing, billing and source availability remain blocked by independent gates.

## Decisions

- `/` is canonical English; `/en` permanently redirects to `/`.
- `/es`, `/fr`, `/pt`, `/de` and `/it` are equivalent commercial landing routes under the explicit current user decision.
- Commercial prices and calculator outputs remain candidate hypotheses.
- Only the bounded TED pilot profile is styled as admitted; discovery systems remain visibly non-admitted.
- Historical `TECHNICAL_PROBE` artifacts remain unchanged and are not used as current landing copy.

## Risks

- Six-locale copy drift.
- WebGL regressions on low-capability devices.
- Intake abuse or accidental PII telemetry.
- Visual implication of coverage beyond admitted sources.

## Validation checklist

- [ ] task JSON validates;
- [ ] TypeScript strict check;
- [ ] production build;
- [ ] unit tests;
- [ ] six-locale browser contract;
- [ ] reduced-motion and keyboard flow;
- [ ] desktop and mobile captures;
- [ ] intake negative cases;
- [ ] asset hashes and attribution;
- [ ] independent GSAP audit record.

## Rollback considerations

No canonical source-ledger migration is introduced. Reverting the landing bundle removes its current TED projection and restores the previous public page and intake shape; the deployment can be rolled back independently.
