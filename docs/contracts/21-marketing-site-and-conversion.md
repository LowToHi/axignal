# 21 — Marketing Site, Organic Discovery and Conversion Contract

Version: `0.2.0`
Status: `NORMATIVE CANDIDATE / PUBLIC ACTIVATION BLOCKED`
Goal ID: `AXIGNAL-GOAL-001`
Governing programme: `Contract 31 / ADR-016`
Primary implementation phases: `P23`, `P26`, `P27`

## 1. Purpose

The AXIGNAL public web system is a governed product-acquisition surface. It must convert qualified B2G demand into understanding, trust, Tender Alerts, passwordless signup, a controlled trial, completed product value and explicit paid conversion.

```text
Product application
→ deliver investigation, pursuit and retention value

Public website and intelligence pages
→ capture demand, prove method, obtain consent and convert
```

A visually impressive landing without qualified acquisition is incomplete. A large public SEO inventory without product value, rights or indexability governance is also incomplete.

## 2. Product and market positioning

Parent product:

> **AXIGNAL — Global Opportunity Intelligence & Operations**

First commercial shell:

> **Business-to-Government (B2G) Opportunity Intelligence**

First acquisition universe:

> **Public contracts and global tenders**

The site must explain that AXIGNAL helps Business-to-Government teams:

- discover admitted public opportunities;
- qualify them against declared capabilities and constraints;
- investigate buyer, award, supplier and ownership context;
- preserve evidence, contradictions and uncertainty;
- make human bid/no-bid decisions;
- coordinate a pursuit through outcome and learning.

It must not position AXIGNAL as:

- a generic research chatbot;
- a TED search interface;
- a commodity tender database;
- an autonomous bid agent;
- a legal eligibility service;
- a source of guaranteed wins;
- a publicly launched product before P27.

## 3. Priority audiences

Initial candidate audiences:

- B2G business-development leaders;
- bid, tender and capture managers;
- public-sector sales teams;
- tender and market-entry consultancies;
- technology, engineering, defence, energy, health and infrastructure suppliers;
- companies expanding public-sector sales across countries;
- governed procurement-intelligence teams.

Investor, general-strategy and non-procurement audiences remain subordinate to separately admitted product shells. They must not dilute the first B2G landing.

## 4. Core conversion contract

```text
qualified search, referral or outreach
→ explicit B2G value proposition
→ admitted public intelligence or faithful product proof
→ use-case recognition
→ evidence and methodology
→ Tender Alert, sample investigation or trial CTA
→ consent or passwordless identity
→ trial eligibility and risk decision
→ first admitted AI operation starts trial
→ relevant opportunity shortlist
→ evidence-linked investigation
→ bid/no-bid or pursuit value
→ explicit paid-plan decision
→ retention and expansion
```

Every major section must justify its role in this sequence.

## 5. Landing hero

The first viewport must state:

1. Business-to-Government and B2G;
2. public contracts or global tenders;
3. the buyer outcome;
4. the differentiated evidence and context mechanism;
5. the intended professional audience;
6. one primary action;
7. one lower-commitment action.

Current candidate message contract:

```text
BUSINESS-TO-GOVERNMENT (B2G) OPPORTUNITY INTELLIGENCE

Find the public contracts your business is built to pursue.

Turn global procurement into a qualified B2G pipeline.
```

Primary candidate CTA:

```text
Request your 7-day B2G trial
```

Secondary candidate CTA:

```text
See a public-contract investigation
```

The copy must not claim instant self-service while activation remains controlled.

## 6. Narrative architecture

The B2G landing should explain:

1. fragmented global procurement;
2. declared company capabilities and target markets;
3. discovery across admitted sources;
4. normalisation and lifecycle reconstruction;
5. capability-based qualification;
6. contracting-authority and award history;
7. supplier, ownership and partner context;
8. requirements, deadlines, amendments and risk;
9. traceable evidence and visible uncertainty;
10. human bid/no-bid authority;
11. pursuit workspace and team operation;
12. controlled trial and candidate plans.

## 7. Product proof

A faithful proof must demonstrate:

```text
company scope
→ public opportunity discovery
→ qualification
→ source and document inspection
→ buyer and award context
→ contradiction and unknown review
→ human decision
→ pursuit workspace
```

Illustrative or synthetic data must be explicitly labelled. Public proof cannot show a capability, source, geography or status unavailable in the tested product.

## 8. Public organic-discovery architecture

The public system may expose:

- `TENDER_HUB` pages;
- `MARKET_INTELLIGENCE` pages;
- selectively admitted `TENDER_DETAIL` pages;
- methodology and source pages;
- evidence-linked reports;
- glossary and documentation;
- Tender Alert landing surfaces.

Arbitrary facets, saved searches, account data and workspaces remain `noindex`.

## 9. IndexabilityGate

Programmatic page generation is not publication authority.

```text
dataset
→ page candidate
→ deterministic IndexabilityGate
→ founder review
→ versioned expiring snapshot
→ public page and sitemap
```

Indexability must consider:

- active inventory;
- buyer diversity;
- search demand;
- data quality;
- uniqueness;
- source coverage;
- content depth;
- freshness;
- synthetic-data exclusion;
- rights and attribution.

```text
dataset ≠ page
page generated ≠ page indexable
page indexable ≠ page published
crawlable ≠ indexed
indexed ≠ ranked
```

Mass creation of country × sector × keyword combinations without material public value is prohibited.

## 10. Transactional page contract

An admitted procurement hub or Market Intelligence page should expose:

- geography and sector;
- current opportunity count under a declared definition;
- buyer diversity;
- known and undeclared value separately;
- procedures and classifications;
- upcoming deadlines;
- buyer activity;
- source and coverage limitations;
- exact as-of time;
- methodology version;
- source links;
- relevant opportunities;
- contextual CTA.

Metrics must come from the same versioned snapshot used for visible content and structured data.

## 11. Tender detail pages

A tender notice should become an indexable page only when AXIGNAL adds material value such as:

- normalised lifecycle;
- lots;
- buyer resolution;
- classifications and geography;
- value and currency semantics;
- requirements and deadlines;
- amendment and correction history;
- official documents;
- related awards or contracts;
- source provenance;
- explicit limitations.

Republishing a title and source description is insufficient.

## 12. Structured data and AI-readable surface

Public structured data may include valid:

- `CollectionPage`;
- `Dataset`;
- `Organization`;
- source `isBasedOn` references;
- `dateModified`;
- spatial and temporal coverage;
- methodology.

Structured data must match visible content.

`llms.txt` may explain the public information contract. It cannot override robots, create a second hidden corpus or grant crawler access.

## 13. Crawler policy

When public indexing is independently authorised, admitted public pages may be discoverable by approved search crawlers.

Private routes remain excluded:

- `/admin/`;
- `/api/`;
- `/workspace/`;
- `/account/`;
- invitation and verification routes;
- alert-confirmation tokens;
- private search and saved state.

Crawler policy must distinguish search discovery from model-training access where technically supported.

## 14. GEO, AEO and AI citations

AXIGNAL should optimise for source-grounded usability by humans and answer engines through:

- original data and analysis;
- stable entities;
- clear questions and answers;
- visible methods;
- freshness;
- source links;
- structured semantics;
- honest limitations.

It must not claim that schema, `llms.txt` or keyword repetition guarantees citation.

Observed citation events are evidence only:

```text
AI citation ≠ endorsement
AI citation ≠ ranking
AI citation ≠ qualified acquisition
AI citation ≠ canonical claim
```

## 15. Tender Alerts

Tender Alerts are an independent consent and acquisition product.

```text
email and scope
→ server-side bot verification
→ PENDING_CONFIRMATION
→ email delivery
→ explicit POST confirmation
→ ACTIVE
```

Opening a link must not confirm consent.

A Tender Alert must not create:

- an identity;
- a tenant;
- a seat;
- a trial;
- a paid package.

The email must provide real value and a clear unsubscribe path.

## 16. Passwordless signup and trial conversion

Public signup, when authorised, should use:

- email verification for address control;
- passkey-first WebAuthn;
- opaque revocable sessions;
- server-resolved tenant;
- risk and abuse decision;
- one trial per tenant or economic identity.

The seven-day clock starts on first admitted AI use, not account creation.

The initial candidate trial:

- no card;
- two seats;
- 1,000,000-token ceiling;
- internal cost ceiling;
- one concurrent ResearchRun;
- no silent conversion.

## 17. Candidate pricing presentation

Current technical candidate price book:

| Plan | Candidate amount | Seats |
|---|---:|---:|
| Controlled trial | `0 EUR` | 2 |
| Professional | `149 EUR/month` | 3 |
| Team | `399 EUR/month` | 15 |
| Enterprise | Quote only | Contracted |

Every displayed amount remains `CANDIDATE_ONLY` until P27.

The pricing surface must disclose:

- price status;
- flat-tier seats;
- source and library scope;
- operational limits;
- taxes;
- upgrade and downgrade;
- cancellation;
- retention;
- no silent conversion.

## 18. CRM boundary

The acquisition CRM may store:

- contact and organisation data voluntarily supplied;
- source;
- consent;
- acquisition lifecycle;
- lead score;
- owner;
- activity;
- next action.

```text
CRM contact ≠ user
CRM stage ≠ risk decision
lead score ≠ entitlement
trial stage ≠ active trial
customer stage ≠ paid provider state
```

## 19. Google Search Console

A DNS TXT verification record has been provided for `axignal.com` and is recorded as user-attested evidence.

```text
DNS verification ≠ API access
API access ≠ public indexing authority
Search impressions ≠ qualified demand
clicks ≠ customer value
```

Search Console data may be imported only after official API, least-privilege, secret, audit, retention and revocation gates pass.

It may inform diagnostics but cannot publish pages or override the IndexabilityGate.

## 20. GSC MCP candidate

The user-provided MCP catalogue URL is a discovery record only.

A Google Search Console MCP must pass connector and tool admission before use. It starts deny-by-default and read-only if probed.

Destructive operations are prohibited by default:

- add or delete sites;
- submit or delete sitemaps;
- change users or permissions;
- change DNS;
- expose credentials;
- execute arbitrary shell or browser automation.

## 21. Trust and methodology

Trust content must explain:

- claim classes;
- evidence and provenance;
- contradiction and uncertainty;
- source rights;
- coverage and freshness;
- AI and deterministic authority;
- translation provenance;
- identity and tenant isolation;
- trial and abuse controls;
- public-page methodology;
- citation limitations;
- correction and retraction.

## 22. Social proof

The site must not invent:

- customer logos;
- testimonials;
- endorsements;
- usage figures;
- source counts;
- market coverage;
- performance outcomes;
- waitlist size;
- AI-citation claims.

Until proof exists, rely on faithful product evidence and transparent methodology.

## 23. Accessibility and performance

Public surfaces target WCAG 2.2 AA and require:

- keyboard operation;
- visible focus;
- semantic headings and landmarks;
- reduced motion;
- responsive layouts;
- accessible charts and tables;
- text alternatives;
- content useful before heavy visuals load;
- performance budgets;
- no critical conversion dependent on animation.

## 24. Analytics and attribution

Acquisition instrumentation must connect:

```text
landing or intelligence page
→ Tender Alert or signup
→ trial readiness
→ first admitted AI use
→ completed B2G value workflow
→ paid conversion
→ retention
```

Attribution remains an estimate. Search Console, UTMs, referrers and AI citations cannot establish causal revenue without further evidence.

## 25. Prohibited practices

The public web system must not use:

- fake urgency or scarcity;
- fabricated countdowns;
- invented social proof;
- hidden plan limits;
- undisclosed overages;
- fake discounts;
- preselected paid conversion;
- inaccessible cancellation;
- bundled consent;
- thin mass-generated SEO pages;
- misleading coverage;
- unadmitted source data;
- hidden or inconsistent structured data;
- visuals or claims the product cannot reproduce.

## 26. Activation gate

Public indexing, signup, Tender Alerts and pricing remain independently blocked until their production evidence and P27 authority pass.

The marketing contract advances only when:

1. B2G buyers understand category, outcome and limits;
2. product proof is faithful;
3. IndexabilityGate and snapshot authority pass;
4. consent and email delivery pass;
5. signup, trial and abuse governance pass;
6. candidate pricing is understood and truthful;
7. Search Console is admitted or excluded from launch scope;
8. every connected MCP is admitted;
9. accessibility and performance pass;
10. acquisition is connected to completed customer value;
11. no unsupported public claim exists;
12. P27 accepts the final exact head.

## 27. Current authority

```text
B2G LANDING ENGINEERING           PASS
ORGANIC DISCOVERY ENGINEERING     PASS
TENDER ALERT ENGINEERING          PASS
CRM FOUNDATION ENGINEERING        PASS
SEARCH CONSOLE DNS EVIDENCE       USER-ATTESTED
SEARCH CONSOLE API                NOT PROVEN
GSC MCP                           NOT ADMITTED
PUBLIC INDEXING                   BLOCKED
PUBLIC TENDER ALERTS              BLOCKED
PUBLIC SIGNUP                     BLOCKED
PUBLIC PRICING                    NOT VALIDATED
PUBLIC LAUNCH                     NO_GO
```
