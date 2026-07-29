# ADR-014 — Bounded AXIGNAL AI and Token Entitlements

Status: `PROPOSED / IMPLEMENTATION AND ECONOMIC VALIDATION REQUIRED`
Date: `2026-07-29`
Goal ID: `AXIGNAL-GOAL-001`
Decision owner: Product authority

## Context

AXIGNAL exposes natural-language interaction and uses generative models for bounded proposal and explanation tasks. Without a durable scope boundary, a conversational surface could drift into a general-purpose assistant, create unrelated safety obligations, expose arbitrary tools or data, and consume model resources without relation to AXIGNAL's product value.

The commercial programme also requires a clear distinction between a controlled seven-day acquisition trial and monthly paid subscriptions. The trial needs a finite economic boundary, while paid plans should not be sold as token bundles or interrupt legitimate professional research because a monthly token counter was reached.

## Decision

AXIGNAL will implement a fail-closed, server-enforced AI boundary with these properties:

1. End-user AI operates only over server-resolved AXIGNAL tenant context, admitted AXIGNAL knowledge, authorised tenant-private knowledge and typed AXIGNAL capabilities.
2. Natural-language input does not imply general assistance. Requests are classified before model invocation and only `IN_SCOPE_AXIGNAL` requests may reach a model or tool.
3. Psychology, therapy, emotional companionship, code generation or execution, unrestricted general knowledge, unrestricted browsing, arbitrary tools and external actions are prohibited.
4. Permitted outputs are bounded AXIGNAL answers, navigation and investigation plans, evidence-linked dossiers and grounded PDF reports.
5. The seven-day free trial has one cumulative budget of exactly `1,000,000` AI tokens per organisation, with no daily reset, overage or silent conversion.
6. Active monthly paid subscriptions have unlimited monthly AI tokens: no monthly token quota, token hard stop or token overage invoice.
7. Unlimited paid tokens do not remove safety, source-right, plan-feature, concurrency, document, abuse, security or service-integrity controls. Those controls may not conceal an undeclared monthly token quota.
8. Token usage remains an internal cost and observability metric rather than the primary paid-plan value metric.
9. Contract 29 and its machine-readable policy define the initial capability allowlist and promotion gates.

## Why this decision

- It preserves AXIGNAL as an opportunity-intelligence product rather than a generic chatbot.
- It reduces cross-domain safety, regulatory and support exposure.
- It makes tool and data access auditable and testable outside model prompts.
- It gives the free trial a predictable maximum model cost.
- It gives paid users a simple premium promise aligned with professional outcomes rather than token accounting.
- It preserves reliability and abuse controls without contradicting the unlimited-token proposition.

## Rejected alternatives

### General-purpose assistant with a broad disclaimer

Rejected because a disclaimer or system prompt is not an enforceable capability boundary and would materially expand product scope.

### Model self-classification as the only guardrail

Rejected because the model could be manipulated by user input or retrieved content. Scope and capability checks must be server-side and fail closed.

### Monthly token bundles for paid plans

Rejected as the default model because token bundles obscure professional value, create unpredictable interruptions and reduce AXIGNAL to a model reseller.

### Completely unmetered trial

Rejected because it creates uncontrolled acquisition cost and abuse exposure before conversion and gross-margin evidence exist.

### Unlimited paid use without technical controls

Rejected because unlimited tokens do not justify denial-of-service risk, source-right violations, bulk redistribution or compromised-account abuse.

## Consequences

### Positive

- deterministic product boundary;
- smaller attack and compliance surface;
- predictable trial maximum;
- simpler paid-plan message;
- explicit separation between token entitlement and feature/source entitlements;
- auditable refusals and capability issuance.

### Negative

- some users will expect a general assistant and must receive a clear refusal;
- scope classification and output validation require dedicated engineering and adversarial testing;
- unlimited paid tokens create gross-margin risk that must be measured;
- support must explain the difference between unlimited tokens and safety, rights or reliability limits.

## Implementation requirements

- integrate pre-model typed scope gates into every end-user AI route;
- issue short-lived typed capability tokens from server-resolved tenant state;
- use allowlisted retrieval and tools only;
- implement post-model output validation;
- implement transactional trial token reservation and reconciliation;
- provide paid entitlements with no monthly token quota or token-overage path;
- expose trial usage and exhaustion state in UI;
- add append-only policy and usage events;
- test cross-tenant, prompt-injection, mixed-scope, concurrency and exhaustion cases;
- retain independent AI, trial and billing kill switches.

## Migration

No runtime or billing migration is authorised by this ADR alone. Implementation will require versioned entitlement and usage-ledger persistence before activation. Existing model adapters remain proposal-only and disabled unless separately enabled.

## Rollback

Before activation, revert Contract 29, its policy and this ADR while preserving history.

After activation, rollback MUST disable end-user AI and trial creation fail-closed. It MUST NOT silently replace unlimited paid tokens with a token quota for active contracts; any commercial change requires explicit customer treatment and a superseding ADR.

## Acceptance

This ADR advances only when Contract 29's automated acceptance tests pass, paid high-usage gross-margin evidence is accepted, customer-facing copy is consistent and no AI route can bypass the server-side scope and entitlement gates.
