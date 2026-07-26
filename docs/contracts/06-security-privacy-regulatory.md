# 06 — Security, Privacy and Regulatory Boundary Contract

Version: `0.1.0`
Status: `NORMATIVE`

## 1. Purpose

AXIGNAL is designed as information, research and economic-observation infrastructure. This contract defines the foundation boundary intended to avoid accidental operation as a broker, custodian, portfolio manager or personalised investment adviser.

This contract is a product and engineering specification. It does not replace jurisdiction-specific legal advice.

## 2. Foundation regulatory posture

AXIGNAL MAY provide:

- structured market and economic data;
- historical analysis;
- claims and evidence;
- non-personalised scenario models;
- objective filters;
- maps, graphs and watchlists;
- general research and methodological commentary;
- alerts about changes in observed data or claim state.

AXIGNAL MUST NOT provide in the foundation scope:

- recommendations presented as personally suitable;
- portfolio allocation percentages;
- automated rebalancing;
- order execution or routing;
- custody;
- copy trading;
- managed accounts;
- guaranteed outcomes;
- undisclosed paid promotion or conflicted rankings.

## 3. Personalisation boundary

Allowed observation preferences:

- geographies;
- sectors;
- universes;
- asset classes;
- ticket bands;
- liquidity bands;
- horizons;
- evidence thresholds;
- update cadence;
- language and currency display.

Blocked foundation inputs when used for suitability:

- total wealth;
- full portfolio composition;
- required return;
- maximum acceptable personal loss;
- age or family circumstances;
- tax situation;
- recommendation to buy, sell or allocate a percentage.

A future suitability feature MUST be disabled until a dedicated legal, product and licensing ADR is accepted.

## 4. Public financial research

Information about listed instruments MAY trigger requirements applicable to investment recommendations even when not personalised.

Any financial-instrument research surface MUST:

- identify the producer;
- show publication time;
- distinguish facts, calculations, interpretations and forecasts;
- disclose methodology;
- disclose material conflicts of interest;
- preserve sources;
- provide correction history;
- avoid misleading presentation;
- receive jurisdiction-specific legal review before public release.

Relevant European references include MiFID II, the Market Abuse Regulation and ESMA guidance. Official starting points:

- `https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32014L0065`
- `https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32014R0596`
- `https://www.esma.europa.eu/`

## 5. Crypto boundary

Crypto data and scenarios MAY be treated as a separate universe. Foundation AXIGNAL MUST NOT:

- execute crypto transactions;
- custody keys or assets;
- provide personalised crypto recommendations;
- market yield as safe or guaranteed;
- obscure smart-contract, liquidity, counterparty or jurisdiction risk.

Any crypto service extension MUST be reviewed against MiCA and applicable national rules.

## 6. Consumer boundary

The first commercial release SHOULD target professional or business users.

Before B2C launch, AXIGNAL MUST implement and legally review:

- consumer pre-contract information;
- cancellation or withdrawal treatment where applicable;
- digital-service conformity obligations;
- complaint handling;
- clear renewal and cancellation;
- non-abusive contract terms;
- marketing and testimonial controls.

## 7. Liability posture

AXIGNAL MUST NOT claim “no responsibility”.

Customer terms MAY define:

- information-only scope;
- no guarantee of completeness or returns;
- source-dependent latency;
- customer duty to conduct independent verification;
- permitted use;
- limitations for indirect loss where lawful;
- contractual liability caps where lawful;
- exclusion of prohibited uses.

Terms MUST NOT attempt to exclude liability that cannot lawfully be excluded.

## 8. Privacy

AXIGNAL MUST apply privacy by design.

### Data minimisation

The platform MUST collect only personal data necessary for:

- account operation;
- security;
- billing;
- workspace collaboration;
- preferences and watchlists;
- support and compliance.

### Sensitive financial profile

Foundation AXIGNAL SHOULD NOT collect detailed personal portfolio or suitability data.

### User rights

Systems MUST support applicable rights such as access, rectification, deletion, portability, restriction and objection.

### Retention

Retention MUST be defined by data class and legal basis. Deletion workflows MUST propagate to derived user-private data and backups according to policy.

### International transfers

Provider and data-location choices MUST be recorded. Cross-border transfers MUST have a documented mechanism where required.

Official European references:

- `https://eur-lex.europa.eu/eli/reg/2016/679/oj`
- `https://www.aepd.es/`

## 9. AI governance

AI components MUST be inventoried by purpose, provider, model, input data, output use and risk.

The system MUST:

- disclose material AI involvement;
- keep human or deterministic control over canonical admission;
- log model versions and prompts;
- test for hallucination and extraction error;
- prevent secret or personal-data leakage;
- document fallback behaviour;
- support provider disabling;
- avoid prohibited or high-risk use cases outside approved scope.

Relevant European reference:

- `https://eur-lex.europa.eu/eli/reg/2024/1689/oj`

## 10. Threat model

Priority threats:

- credential theft;
- tenant-data exposure;
- source credential leakage;
- prompt injection from external documents;
- malicious evidence poisoning;
- supply-chain compromise;
- billing webhook forgery;
- privilege escalation;
- unauthorised exports;
- API scraping;
- graph inference of restricted data;
- model-provider data leakage;
- manipulation of opportunity rankings;
- deletion or rewriting of audit history.

## 11. Security controls

Foundation requirements:

- strong password or federated authentication;
- MFA for privileged roles;
- role-based and attribute-based access control;
- least privilege;
- encrypted transport;
- encryption at rest where supported;
- secure secret storage;
- signed and verified webhooks;
- rate limiting;
- CSRF and XSS protections;
- dependency and container scanning;
- secure headers and CSP;
- audit logs;
- backup encryption;
- vulnerability disclosure channel;
- incident-response runbook;
- periodic restore and access reviews.

## 12. Prompt-injection defence

All external source content MUST be treated as untrusted data.

Document text MUST NOT be allowed to alter system instructions, connector permissions or admission policies.

Model tools MUST use allow-listed actions and typed outputs. Claims extracted from untrusted text remain candidates until deterministic admission.

## 13. Audit log

Security and epistemic audit events MUST be append-only or tamper-evident.

Log at minimum:

- authentication and privilege changes;
- source configuration changes;
- exports;
- claim admission, override, retraction and correction;
- scenario publication;
- billing entitlement changes;
- secret rotation;
- administrator actions;
- data-deletion requests;
- policy-version changes.

## 14. Conflicts of interest

AXIGNAL MUST maintain a conflict register for:

- paid source placement;
- sponsored research;
- holdings or commercial interests of the publisher where legally relevant;
- referral fees;
- data-provider influence;
- enterprise customer restrictions.

Sponsored or conflicted content MUST not silently affect canonical ranking.

## 15. Data licensing security

Source entitlements are security boundaries.

The platform MUST prevent:

- unauthorised raw-data export;
- tenant access to unlicensed universes;
- API redistribution beyond contract;
- persistence beyond allowed retention;
- use of restricted data for model training;
- accidental publication in screenshots or reports.

## 16. Market-abuse safeguards

Before supporting time-sensitive listed-instrument intelligence, AXIGNAL MUST establish controls for:

- material non-public information;
- suspicious source origin;
- embargoed research;
- manipulation attempts;
- coordinated promotion;
- insider-list requirements where applicable;
- rapid takedown and correction.

The platform MUST not ingest customer confidential information into public opportunity products.

## 17. Security acceptance gate

Paid production MUST NOT launch until:

- threat model is reviewed;
- privileged accounts use MFA;
- tenant-isolation tests pass;
- secrets are externalised;
- backup restore is demonstrated;
- dependency scanning is active;
- webhook verification tests pass;
- audit logging is queryable;
- incident-response and breach-notification runbooks exist;
- source-rights enforcement is tested;
- an independent legal review covers the launched universes and jurisdictions.
