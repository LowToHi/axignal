# 29 — Bounded AI Assistance and Usage Governance

Version: `0.2.0`
Status: `NORMATIVE CANDIDATE / FAIL-CLOSED / CONTRACT 31 SUBORDINATE`
Goal ID: `AXIGNAL-GOAL-001`
Governing programme: `Contract 31 / ADR-016`
Primary phases: `P19`, `P21`, `P25`, `P27`

## 1. Purpose

This contract defines the maximum permitted role of generative AI inside AXIGNAL and the usage-governance policy for trials and paid packages.

AXIGNAL provides bounded opportunity intelligence and operations. It must not become a general-purpose chatbot merely because Navigator accepts natural language.

Where this contract is more restrictive than a subordinate capability contract, this contract governs unless Contract 31 or a later approved contract explicitly supersedes it.

## 2. AI authority ceiling

Generative AI may:

- interpret bounded user intent;
- retrieve and rank candidate evidence;
- extract candidate structures;
- classify and translate;
- propose entity links;
- propose Candidate Claims;
- propose Opportunity or workflow actions;
- explain admitted state;
- draft customer work for human review;
- generate an AXIGNAL report in PDF form from admitted evidence.

Generative AI may not:

- admit a source;
- admit canonical claims;
- overwrite evidence or ledgers;
- choose tenant or role authority;
- grant seats, trials or entitlements;
- publish SEO pages;
- confirm consent;
- mutate billing provider state;
- submit, sign, file or represent a customer;
- approve bid/no-bid or capital decisions;
- install or widen MCP tools;
- authorise launch.

## 3. Required separation

```text
model proposal
≠ structural validation
≠ policy admission
≠ human operational approval
≠ external action
```

Every model-mediated path must preserve:

- model and provider identity;
- prompt and policy version where retainable and lawful;
- input evidence references;
- output classification;
- confidence or uncertainty status;
- deterministic validation result;
- admission or rejection;
- cost and latency;
- user-visible limitations where material.

## 4. AI contexts

Permitted contexts include:

- `NAVIGATION`;
- `RETRIEVAL`;
- `EXTRACTION`;
- `CLASSIFICATION`;
- `TRANSLATION`;
- `ENTITY_LINK_PROPOSAL`;
- `CLAIM_PROPOSAL`;
- `OPPORTUNITY_PROPOSAL`;
- `WORKSPACE_DRAFTING`;
- `EXPLANATION`;
- `SCENARIO_PROPOSAL` only under P19 controls.

Every context has explicit tools, data classes, output schema, cost ceiling and authority ceiling.

## 5. Data and tool boundary

Models receive only data admitted for the declared purpose and tenant scope.

They must not receive:

- unrelated tenant data;
- secrets or credentials;
- unrestricted source documents;
- billing or payment secrets;
- raw abuse signals beyond purpose-limited representations;
- Founder Admin authority tokens;
- destructive MCP tools;
- prohibited personal data;
- data lacking required rights.

Tool access is deny-by-default and context-specific.

## 6. Prompt-injection boundary

External documents, pages, search results, connector output and MCP output are untrusted evidence.

They must not:

- change system authority;
- add tools;
- reveal secrets;
- widen tenant scope;
- bypass rights;
- alter output contracts;
- grant publication or launch authority.

Prompt-injection handling must include isolation, content labelling, tool allowlists, output validation and audit.

## 7. Trial usage governance

The controlled trial has a visible token ceiling and additional server-side economic controls.

```text
duration                    7 days from first admitted AI use
seat capacity               2
token ceiling               1,000,000
internal cost ceiling       server-side
ResearchRun concurrency     1
private connectors          restricted
bulk export                 restricted
```

The trial belongs to a tenant or economic identity. A new account does not create a new budget.

Token and cost reservations are transactional. An operation is denied when either budget or concurrency is unavailable.

## 8. Paid-package usage governance

Paid packages must not be marketed primarily as token bundles or impose unpredictable token-overage billing without a future approved contract.

The current candidate commercial design may present paid AI as included within governed operational capacity, subject to:

- fair-use and abuse controls;
- concurrency;
- document and page limits;
- workspace capacity;
- source and rights scope;
- export limits;
- provider and workflow cost controls;
- security state;
- explicit hard-stop or approved upgrade behaviour.

```text
unlimited label
≠ unbounded compute
≠ unrestricted automation
≠ unlimited documents
≠ provider-cost immunity
```

Internal token accounting remains mandatory for cost, safety and capacity even when the customer does not buy tokens.

## 9. Candidate package boundary

Current technical package candidates:

| Package | Public token quota | Internal usage governance |
|---|---|---|
| Controlled trial | 1,000,000 visible ceiling | Token, cost and concurrency ledgers |
| Professional | No validated monthly token product | Internal workflow, cost, concurrency and abuse controls |
| Team | No validated monthly token product | Internal workflow, cost, concurrency and abuse controls |
| Enterprise | Contract-specific if approved | Quotas and controls defined in agreement and entitlement policy |

No paid package may promise unrestricted AI before economic and abuse evidence.

## 10. Reservation and reconciliation

Before an expensive operation:

```text
identity and tenant authority
→ package and trial state
→ source rights
→ operation policy
→ token estimate
→ cost estimate
→ concurrency reservation
→ provider or local execution
→ actual usage reconciliation
→ ledger and audit
```

Failure must release or reconcile reservations idempotently.

The browser cannot declare token, cost or concurrency availability.

## 11. Provider routing

Provider selection must consider:

- allowed data class;
- jurisdiction and residency;
- model capability;
- context window;
- cost;
- latency;
- availability;
- contractual rights;
- retention and training terms;
- approved fallback.

A cheaper provider cannot weaken evidence, privacy or security authority.

Local or deterministic methods should be preferred when they satisfy the task.

## 12. Model outputs and claims

A model output may become:

- rejected proposal;
- candidate extraction;
- Candidate Claim;
- draft explanation;
- draft workspace content;
- scenario proposal.

It cannot become an admitted claim solely because:

- JSON validates;
- confidence is high;
- multiple model samples agree;
- the user prefers it;
- a provider labels it factual;
- an MCP returns it.

## 13. Scenarios and predictions

Predictive outputs require P19:

- temporal holdout;
- as-of evidence;
- calibration;
- frozen thresholds;
- outcome reconciliation;
- demotion;
- visible uncertainty.

No win probability, margin forecast, eligibility prediction or recommendation may be shown as accepted without its domain-specific gate.

## 14. Abuse controls

AI abuse controls may include:

- route and tenant rate limits;
- concurrency;
- cost ceilings;
- maximum document and context size;
- file-type and malware controls;
- export limits;
- automation detection;
- provider circuit breakers;
- trial risk decisions;
- human review;
- suspension and kill switches.

Weak identity or network signals cannot independently prove abuse.

## 15. Observability

The runtime must record, at an appropriate privacy level:

- operation and context type;
- tenant and package pseudonymous identifiers;
- provider/model;
- prompt-policy version;
- input and output units;
- estimated and actual cost;
- latency;
- retries and fallback;
- validation and admission result;
- error class;
- user cancellation;
- safety or abuse decision.

No log may expose secrets or unnecessary customer content.

## 16. Customer transparency

Customer-facing surfaces must explain:

- where AI is used;
- where deterministic and human gates apply;
- plan and trial limits;
- hard-stop or upgrade behaviour;
- data and source limitations;
- model error and uncertainty;
- whether content is a proposal, admitted claim or customer draft.

## 17. Economic gate

AI usage is acceptable only when:

- variable cost is measurable;
- cost reservations and reconciliation pass;
- trial abuse is controlled;
- provider failure does not corrupt canonical state;
- paid-package margin remains viable;
- support burden is measured;
- high-cost enrichment delivers customer value;
- fallback and kill switches exist.

A token-cost model is not a pricing validation model.

## 18. Reinvestment

Additional AI spend may be funded only by accepted revenue and conditioned on margin, measured customer value, reserves, provider risk and workflow ROI.

AXIGNAL must not universally enrich every record merely because a model is inexpensive.

## 19. Acceptance gate

This contract advances only when:

1. every AI context has a tool and authority contract;
2. tenant and data-class isolation pass;
3. prompt-injection and untrusted connector output pass;
4. proposal/admission separation passes;
5. trial token, cost and concurrency governance passes;
6. paid-package operational limits are reproducible;
7. provider usage and cost are observable;
8. customer limitations are visible;
9. abuse, suspension and kill switches pass;
10. scenarios and predictions remain gated;
11. margin and value evidence are accepted;
12. P27 accepts the final exact head.

## 20. Current authority

```text
TRIAL TOKEN CEILING            1,000,000
TRIAL COST GOVERNANCE          ENGINEERING PASS
TRIAL CONCURRENCY              ENGINEERING PASS
PAID TOKEN PRODUCT             NOT VALIDATED
PAID AI                        INCLUDED CANDIDATE WITH BOUNDED CONTROLS
PROVIDER LIVE ACCEPTANCE       MISSING
MCP PRODUCTION ACCESS          BLOCKED
PUBLIC SIGNUP                  BLOCKED
PUBLIC BILLING                 BLOCKED
PUBLIC LAUNCH                  NO_GO
```
