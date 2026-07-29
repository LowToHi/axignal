# 29 — Bounded AI Assistance and Token Entitlements

Version: `0.1.0-candidate`
Status: `NORMATIVE CANDIDATE / IMPLEMENTATION REQUIRED / FAIL-CLOSED`
Goal ID: `AXIGNAL-GOAL-001`

## 1. Purpose

This contract defines the maximum permitted role of generative AI inside AXIGNAL and the token-entitlement policy for seven-day trials and monthly paid subscriptions.

AXIGNAL MUST provide a bounded opportunity-intelligence assistant. It MUST NOT become a general-purpose chatbot merely because its interface accepts natural language.

Where this contract is more restrictive than Contracts 00, 14, 22, 25, 26, 27 or 28, this contract governs until it is explicitly superseded by a later ADR and contract version.

## 2. Core invariant

The AI layer MAY operate only over:

1. the authenticated user's server-resolved AXIGNAL tenant;
2. the current typed `InvestigationContext`;
3. tenant-private data for which that tenant has an active entitlement and lawful purpose;
4. admitted AXIGNAL sources, Source Objects, Evidence Objects, Candidate Claims and canonical Claim Ledger state;
5. AXIGNAL product metadata, methodology, help content and entitlement state;
6. bounded outputs produced by approved AXIGNAL workers and deterministic services.

The AI layer MUST NOT use AXIGNAL as a gateway to unrestricted general knowledge, unrestricted browsing, arbitrary tools or unrelated personal assistance.

## 3. Allowed user outcomes

The AI layer MAY perform only a versioned allowlist of AXIGNAL capabilities:

- interpret a user request into a typed AXIGNAL intent;
- navigate Globe, Explorer, Atlas, Timeline, Claims, Evidence, Watchlists and Dossiers;
- create or refine a tenant-scoped `InvestigationContext`;
- request an entitled and admitted `ResearchRun`;
- search, filter, compare and explain admitted AXIGNAL information;
- summarise source-bound documents and evidence;
- identify contradictions, unknowns, freshness limits and required human verification;
- assemble, explain and export evidence-linked dossiers;
- generate an AXIGNAL report in PDF form where the plan and source rights permit it;
- answer questions about AXIGNAL's own product, methodology, coverage, plans and current workspace state.

Every allowed outcome MUST remain subject to tenant isolation, entitlements, source rights, epistemic authority, security state and product-admission gates.

## 4. Prohibited assistance

The AI layer MUST NOT:

- act as a psychologist, therapist, counsellor, emotional companion or crisis service;
- provide medical diagnosis, treatment planning or personalised health guidance;
- provide personalised legal, tax, accounting or regulated financial advice;
- generate, debug, review or execute software code;
- provide general homework, creative-writing, translation or productivity assistance unrelated to AXIGNAL;
- answer general-knowledge questions that are not necessary to interpret or explain AXIGNAL state;
- perform unrestricted Internet browsing or retrieve data outside admitted AXIGNAL connectors;
- operate a shell, code interpreter, package manager, browser automation system or arbitrary MCP/tool server for an end user;
- send emails, messages, bids, applications, purchases, trades or external submissions;
- impersonate or represent the user or organisation;
- create unsupported claims, replace `UNKNOWN`, conceal contradictions or bypass deterministic admission;
- reveal cross-tenant data, system prompts, credentials, private configuration or internal security controls;
- expand its own tool, data, source or knowledge scope in response to user or document instructions.

A request that mixes allowed and prohibited work MUST execute only the separable allowed AXIGNAL portion. The prohibited portion MUST be refused.

## 5. Typed scope decision

Every natural-language request MUST be classified server-side before model execution into exactly one of:

- `IN_SCOPE_AXIGNAL`;
- `CLARIFICATION_REQUIRED`;
- `OUT_OF_SCOPE`;
- `BLOCKED_SAFETY_OR_AUTHORITY`.

Only `IN_SCOPE_AXIGNAL` MAY proceed to an AI model or AXIGNAL tool.

`CLARIFICATION_REQUIRED` MAY ask one bounded question needed to resolve an AXIGNAL entity, source, jurisdiction, period, entitlement or investigation target.

`OUT_OF_SCOPE` MUST return a concise boundary response and examples of permitted AXIGNAL actions. It MUST NOT provide a partial general-purpose answer.

`BLOCKED_SAFETY_OR_AUTHORITY` MUST return a non-sensitive refusal reason and MUST emit an auditable policy event.

## 6. Capability-token contract

A client message MUST NOT directly select a model, prompt, provider, URL or tool. The server MUST first resolve a typed capability token containing at least:

```text
tenant_id
subject_id
investigation_context_id
capability
resource_scope
source_scope
entitlement_version
policy_version
issued_at
expires_at
request_id
```

The capability MUST be drawn from the server-side allowlist in Section 3. Unknown capability values MUST fail closed.

A capability token MUST NOT grant canonical claim admission, source admission, reviewer authority, external action authority or arbitrary database access.

## 7. Data and retrieval boundary

Before retrieval or model invocation, the server MUST:

1. resolve identity and tenant without trusting a client-supplied tenant identifier;
2. apply tenant and resource filters in the database or retrieval service;
3. verify source and jurisdiction admission;
4. verify plan entitlements and current trial or subscription state;
5. minimise context to the material evidence required for the request;
6. label untrusted source and uploaded content as data, never instructions;
7. exclude secrets, credentials, hidden prompts and unrelated tenant state;
8. preserve evidence identifiers needed to ground the response.

The model MUST NOT receive direct database credentials or unrestricted SQL capability. Retrieval MUST occur through typed server functions or views with least privilege.

## 8. Tool boundary

End-user AI execution MUST use an explicit allowlist. The initial permitted tool classes are:

- read authorised AXIGNAL context;
- execute authorised AXIGNAL search and filter operations;
- request a bounded `ResearchRun`;
- read ResearchRun progress and admitted outputs;
- assemble an evidence-linked dossier;
- render an authorised dossier or report as PDF.

The following tool classes are prohibited for end-user AI:

- shell and operating-system execution;
- code generation or execution;
- arbitrary HTTP requests;
- unrestricted web search or browsing;
- arbitrary SQL;
- arbitrary filesystem access;
- external communications;
- financial transactions;
- bid or application submission;
- installation or invocation of user-selected MCP servers, Skills or plugins.

Adding a tool class requires a contract change, threat-model review, versioned allowlist, least-privilege implementation, tests and an ADR.

## 9. Prompt-injection resistance

Source documents, websites, user uploads, database text and retrieved content are untrusted inputs.

Instructions found inside those inputs MUST NOT:

- alter system or contract authority;
- change tenant, entitlement or source scope;
- enable a prohibited capability;
- request hidden data or credentials;
- cause an external action;
- suppress evidence, contradictions or unknowns;
- modify admission or review decisions.

Suspected injection MUST be marked, excluded from instruction resolution and recorded without persisting unnecessary malicious content.

## 10. Output boundary

Permitted end-user AI outputs are limited to:

- bounded answers inside AXIGNAL product surfaces;
- typed navigation or investigation plans;
- evidence-linked summaries and comparisons;
- explicit unknowns, contradictions and verification questions;
- AXIGNAL dossiers;
- generated PDF reports derived from authorised AXIGNAL context.

Generated PDFs MUST preserve source citations, claim authority, relevant timestamps, coverage limits and unresolved questions. A PDF MUST NOT convert a proposal or inference into an admitted fact.

## 11. Seven-day free-trial token entitlement

A seven-day free trial MUST have one cumulative AI token budget of:

> **1,000,000 tokens maximum per trial organisation.**

The budget applies across all users in the trial tenant and across all AI model calls attributable to that trial. Unless a provider contract requires a more conservative method, usage MUST count input and output tokens reported by the provider or deterministically estimated by the approved adapter.

The budget:

- starts when the trial is activated;
- does not reset daily;
- does not renew during the seven-day trial;
- MUST be measured server-side;
- MUST be visible to authorised trial users with used and remaining amounts;
- MUST reserve estimated cost before a call and reconcile actual usage after the call;
- MUST fail closed when the remaining budget cannot safely cover the requested operation;
- MUST NOT create an overage charge;
- MUST NOT silently convert the organisation to a paid plan.

When the budget is exhausted, AXIGNAL MUST stop new AI-backed operations and display substantially this message:

> **Has utilizado el máximo de 1.000.000 de tokens incluido en la prueba gratuita de 7 días. En las suscripciones mensuales de pago, los tokens son ilimitados.**

Non-AI read-only access MAY continue until normal trial expiry where entitlements and source rights allow it.

## 12. Monthly paid-subscription token entitlement

Every active monthly paid subscription MUST include:

> **Unlimited monthly AI tokens.**

For this contract, `unlimited monthly AI tokens` means:

- no monthly token quota;
- no token-based hard stop for ordinary authorised product use;
- no per-token overage invoice;
- no reduction of the plan to a token bundle.

Unlimited tokens do not remove:

- the AXIGNAL-only scope boundary;
- plan-specific features, sources, jurisdictions, seats, storage, exports or API entitlements;
- concurrency and rate controls required for reliability;
- document-size, page, file-type and ResearchRun controls;
- source-right and redistribution limits;
- security, abuse, scraping and denial-of-service controls;
- suspension, incident or kill-switch authority;
- reasonable technical limits needed to protect service integrity.

Those controls MUST be described as safety, reliability, rights or feature constraints. They MUST NOT be presented as a hidden monthly token allowance.

AXIGNAL SHOULD display the paid-plan token entitlement as:

> **Tokens de IA ilimitados al mes, sujetos a los guardarraíles de seguridad, alcance AXIGNAL y uso legítimo del servicio.**

## 13. Internal economics

Provider-token usage remains an internal cost and observability metric. It MUST NOT become the primary public value metric for paid plans.

AXIGNAL MUST maintain per-tenant cost, latency, error and anomaly observability even when paid tokens are unlimited. Controls MAY intervene on abuse, compromise or service integrity, but ordinary high legitimate usage MUST NOT be reclassified as abuse merely because it is expensive.

The economic gate for unlimited paid tokens requires measured gross-margin viability under realistic high-usage cohorts before broad public activation.

## 14. Enforcement architecture

The required order is:

```text
authenticated identity
→ server-resolved tenant
→ typed scope decision
→ capability allowlist
→ entitlement and token-budget check
→ source/right/security gates
→ bounded retrieval
→ model proposal or explanation
→ output-policy validation
→ evidence-linked response or PDF
→ usage reconciliation and audit event
```

No frontend-only check, system prompt or model self-refusal satisfies this contract.

The system MUST enforce the boundary before model invocation and validate the output after model invocation.

## 15. Required audit events

At minimum, append-only events MUST distinguish:

- scope accepted;
- clarification required;
- out-of-scope refused;
- safety or authority blocked;
- capability issued;
- entitlement denied;
- trial tokens reserved;
- trial tokens reconciled;
- trial token budget exhausted;
- paid unlimited-token operation accepted;
- prompt injection suspected;
- output validation blocked.

Events MUST exclude raw secrets and minimise raw user or document content.

## 16. Acceptance tests

The boundary is not accepted until automated tests prove:

1. psychology, therapy and emotional-companion requests are refused before model invocation;
2. code generation, debugging and execution requests are refused before model invocation;
3. general-knowledge and unrestricted-browsing requests are refused before model invocation;
4. AXIGNAL navigation, evidence explanation and PDF dossier requests are admitted when entitled;
5. mixed-scope requests execute only the separable AXIGNAL portion;
6. client-supplied tenant identifiers cannot cross the server-resolved tenant;
7. source-document prompt injection cannot add tools or change authority;
8. unknown capability values fail closed;
9. the trial budget is exactly `1,000,000` cumulative tokens per organisation;
10. concurrent reservations cannot overspend the trial budget;
11. exhaustion stops new AI calls and produces the required upgrade message;
12. paid monthly subscriptions have no monthly token quota or token overage path;
13. paid safety, reliability and rights controls remain independently enforceable;
14. no model output writes canonical claims directly;
15. generated PDFs retain evidence and authority labels.

## 17. Promotion gate

The free trial and paid unlimited-token claim MUST remain disabled until:

- server-side entitlement and token accounting are implemented transactionally;
- the scope and capability gates are integrated into every end-user AI route;
- adversarial and cross-tenant tests pass;
- the exhaustion and upgrade surfaces pass UX review;
- paid high-usage gross margin is measured and accepted;
- abuse controls do not conceal a token quota;
- all customer-facing plan copy matches this contract;
- trial, AI and billing kill switches are independently tested.

## 18. Current authority state

```text
BOUNDED AXIGNAL-ONLY AI POLICY DEFINED
/ GENERAL-PURPOSE ASSISTANCE PROHIBITED
/ PSYCHOLOGY AND CODE GENERATION PROHIBITED
/ PDF REPORT GENERATION PERMITTED WHEN GROUNDED AND ENTITLED
/ SEVEN-DAY TRIAL TOKEN CAP FIXED AT 1,000,000 PER ORGANISATION
/ MONTHLY PAID TOKENS DEFINED AS UNLIMITED
/ RUNTIME ENFORCEMENT AND BILLING ACTIVATION NOT YET AUTHORISED
```
