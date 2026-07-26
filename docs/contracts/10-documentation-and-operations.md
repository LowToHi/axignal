# 10 — Documentation and Operations Contract

Version: `0.1.0`
Status: `NORMATIVE`

## 1. Documentation objective

ASIGNAL MUST remain understandable, reproducible and operable without relying on undocumented institutional memory or model chat history.

## 2. Required documentation classes

### Normative contracts

Located in `docs/contracts/`.

They define required behaviour, boundaries and acceptance criteria.

### Architecture Decision Records

Located in `docs/adr/`.

Every material decision MUST record:

- context;
- decision;
- alternatives;
- consequences;
- migration implications;
- status;
- date and owner.

### Research

Located in `docs/research/`.

Research is informative, not normative. Research MUST NOT silently override a contract.

### Runbooks

Located in `docs/runbooks/`.

Required runbooks include:

- local environment;
- deployment;
- rollback;
- database migration;
- backup and restore;
- source outage;
- source rights revocation;
- credential rotation;
- security incident;
- billing and entitlement mismatch;
- claim correction and retraction;
- model demotion;
- tenant data deletion.

### Data documentation

Every source and dataset MUST have:

- owner;
- purpose;
- schema;
- rights;
- update cadence;
- quality expectations;
- lineage;
- retention;
- downstream dependencies.

### API documentation

OpenAPI is canonical for REST resources. Human guides MUST explain authentication, pagination, entitlements, graph constraints, exports and webhook verification.

## 3. Documentation freshness

Each normative document MUST contain version and status.

Materially stale documentation is a defect. PRs MUST update docs in the same change as behaviour.

## 4. ADR states

- `PROPOSED`
- `ACCEPTED`
- `SUPERSEDED`
- `REJECTED`
- `DEPRECATED`

Superseded ADRs MUST link to replacements.

## 5. Operational ownership

Every production service, source and model MUST have:

- named owning role;
- escalation path;
- dashboard;
- runbook;
- SLO or freshness objective;
- kill switch;
- dependency list.

## 6. Incident management

Incident records MUST include:

- severity;
- start and detection time;
- affected users, universes and claims;
- source or system cause;
- containment;
- recovery;
- correction or retraction impact;
- follow-up actions;
- communication issued.

Post-incident reviews MUST be blameless and evidence-based.

## 7. Claim correction operations

The admin surface MUST support:

- evidence inspection;
- claim quarantine;
- correction proposal;
- retraction;
- supersession;
- affected-opportunity preview;
- user notification preview;
- signed approval;
- propagation status.

No administrator may directly edit history without an event.

## 8. Source operations

The operations surface MUST show:

- source state;
- last retrieval;
- next expected update;
- rights expiry;
- credential expiry;
- quota;
- quality failures;
- parser version;
- dependent claims and opportunities;
- disable control with impact preview.

## 9. Model operations

Model documentation MUST include:

- purpose;
- provider and version;
- prompts or feature set;
- input restrictions;
- evaluation dataset;
- baseline;
- calibration;
- known failure modes;
- cost;
- fallback;
- retirement criteria.

## 10. Change log

Customer-visible releases MUST maintain a change log describing:

- new capabilities;
- corrected claims or methodologies;
- source additions or removals;
- coverage changes;
- API deprecations;
- security-relevant changes when disclosure is appropriate.

## 11. Customer documentation

Before paid beta, ASIGNAL MUST publish:

- product methodology;
- coverage and latency guide;
- claim-status glossary;
- scenario and uncertainty guide;
- export and source-rights limitations;
- account and billing guide;
- security overview;
- privacy notice;
- acceptable-use policy;
- terms of service reviewed for launched jurisdictions.

## 12. Internal documentation quality

Documentation MUST:

- use canonical identifiers;
- distinguish fact, decision and hypothesis;
- avoid contradictory versions;
- link to code, schema or tests where relevant;
- avoid embedding secrets;
- remain readable without private chat context.

## 13. Acceptance criteria

Operations documentation is accepted when:

- a new contributor can run the synthetic system from the repository;
- an operator can disable a source using the runbook;
- a database restore is performed from documentation;
- a claim correction is propagated through documented steps;
- API clients can authenticate from published guidance;
- all production services and sources have owners and runbooks;
- contract and ADR links pass automated checks.
