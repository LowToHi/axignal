# P23-T03 — B2G Landing Copy E2E v0.1

**Task:** `AX-GE2E-P23-T03`  
**Baseline:** `4301d02880b65a59fb5aa9fed01abad963a23ffd`  
**Message version:** `b2g-opportunity-v1.0`

## Decision

AXIGNAL's first market shell is explicitly positioned as:

> **Business-to-Government (B2G) Opportunity Intelligence**

The initial wedge is public contracts and global tenders. The product is not positioned as a generic research workspace and is not identified with any single procurement portal or library.

```text
Business-to-Government market
→ public contracts and tenders
→ qualified B2G opportunity pipeline
→ buyer, award, supplier and ownership context
→ traceable evidence
→ human bid / no-bid authority
```

## Why the previous message was replaced

P23-T02 improved comprehension by leading with the buyer outcome, but it remained horizontal:

> Turn scattered sources into a decision your team can verify.

That sentence could describe many research products. It did not state the market, buyer, economic event or acquisition wedge. P23-T03 retains the outcome-first discipline while making the vertical unequivocal.

## Research basis

Current official messaging from Deltek GovWin IQ, Mercell, GlobalGov, Deepbloo, PIVI and drin was reviewed on 2026-07-31.

The market consistently emphasises:

- public-contract discovery and pipeline outcomes;
- earlier qualification rather than more alerts;
- buyer, award and competitive context;
- multi-market procurement coverage;
- tender matching and prioritisation;
- a trial, demo or free entry point;
- source and analyst credibility as reasons to believe.

AXIGNAL adopts the useful market language without copying unsupported claims such as universal coverage, verified win-rate improvement or guaranteed opportunity fit.

## Selected message

### Category

> **BUSINESS-TO-GOVERNMENT (B2G) OPPORTUNITY INTELLIGENCE**

### Headline

> **Find the public contracts your business is built to pursue.**

### Supporting headline

> **Turn global procurement into a qualified B2G pipeline.**

### Subheadline

> AXIGNAL connects public tenders, contracting authorities, awards, suppliers and ownership signals so Business-to-Government teams can discover, qualify and investigate the opportunities worth pursuing—without losing the evidence behind the decision.

### Primary CTA

> **Request your 7-day B2G trial**

### Secondary CTA

> **See a public-contract investigation**

### Proof line

- Public contracts and tenders
- Buyer and award context
- Traceable evidence
- Human bid / no-bid authority

## Narrative architecture

1. Explicit B2G category and public-contract outcome.
2. Fragmented global procurement problem.
3. Company capability profile.
4. Public procurement discovery and normalisation.
5. Capability-based opportunity qualification.
6. Contracting authority and award history.
7. Supplier, ownership and partner context.
8. Requirements, deadlines, amendments and risk.
9. Evidence and human bid / no-bid authority.
10. Controlled seven-day trial, paid plans and B2G intake.

## TED boundary

TED and every other procurement portal remain possible source libraries. No individual library is allowed to define the public product narrative.

```text
TED or another portal = source library
AXIGNAL = B2G opportunity-intelligence product
```

P23-T03 verifies that the word `TED` is absent from the public landing implementation.

## Controlled trial

The landing restores the commercial contract defined in P21:

| Field | Value |
|---|---:|
| Plan | `CONTROLLED_TRIAL_7D` |
| Price | `0 EUR` |
| Duration | `7 days` |
| AI budget | `1,000,000 tokens` |
| Card | Not required |
| Stripe checkout | Not invoked |
| Self-service activation | Disabled |
| Activation | Human-reviewed and controlled |

The trial is the primary acquisition CTA. It is not misrepresented as instant self-service.

## Pricing

Professional and Team remain read directly from the versioned server-side commercial runtime:

| Plan | Candidate price | Seats |
|---|---:|---:|
| Professional | `149 EUR/month` | 1–3 |
| Team | `399 EUR/month` | 4–15 |

The landing fails closed if the trial or paid offers diverge from the price book or become commercially activated without a corresponding contract change.

## Intake evidence

The trial request captures:

- work email;
- B2G role;
- company;
- what the company sells to government;
- target markets, public buyers or tender types;
- current qualification bottleneck;
- consent;
- exact message version.

Persisted records use:

```text
schema  = axignal.b2g-trial-intake.v1
source  = landing_b2g_opportunity_v1_0
message = b2g-opportunity-v1.0
```

No success is recorded if the intake channel is unavailable or unconfigured.

## Truth boundaries

```text
public tender discovered       != qualified opportunity
calculated fit                 != win probability
qualified opportunity          != bid decision
bid decision                    != submission
paid plan                       != universal source coverage
one procurement library        != AXIGNAL product identity
controlled trial requested     != trial activated
trial activated                != customer value completed
```

## Claims not authorised

- guaranteed truth;
- guaranteed win;
- zero hallucinations;
- 100 percent accurate;
- fully autonomous decisions;
- complete global coverage;
- market validated;
- publicly available now.

## E2E acceptance

The phase requires exact-head evidence for:

- explicit `Business-to-Government` and `B2G` language;
- public contracts, tenders and global procurement in the hero;
- TED absent from the public narrative;
- B2G-specific workflow, benefits, FAQ and intake;
- controlled trial from the P21 price book;
- Professional and Team pricing consistency;
- noindex publication boundary;
- fail-closed intake;
- keyboard and reduced-motion access;
- desktop and mobile browser execution;
- production typecheck and build.

## Evidence still pending

Engineering and browser evidence do not validate market performance. The next admissible evidence is:

1. at least five direct interviews with B2G buyers;
2. recorded first-screen comprehension tests;
3. controlled-trial request conversion;
4. qualified request to activated trial rate;
5. activated trial to completed B2G value workflow;
6. independent paid customer and reconciliation evidence.
