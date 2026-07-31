# P23 — Final UX, Landing, Copy and Marketing

Task: `AX-GE2E-P23-T01`

Baseline: P22 exact head `82ad182f7d662cb3deb034f88ea287f1422fc694`.

## Product promise

AXIGNAL is evidence infrastructure for high-stakes research and decisions. It coordinates research, preserves provenance and separates proposed claims from admitted evidence.

The public message must not imply guaranteed truth, zero hallucinations, autonomous decision authority or replacement of professional judgment.

## Final landing copy

### Hero

**Eyebrow:** Research intelligence with an evidence trail

**Headline:** Turn complex questions into decisions you can defend.

**Subheadline:** AXIGNAL coordinates research, preserves provenance and separates proposed claims from admitted evidence so teams can move faster without losing auditability.

**Primary CTA:** Request controlled access

**Secondary CTA:** See how evidence flows

### Problem

Research teams rarely lack information. They lack a reliable way to connect questions, sources, claims, uncertainty and decisions without losing the trail between them.

### Evidence flow

1. Describe the decision or research intent.
2. AXIGNAL creates a bounded investigation context.
3. Sources and claims remain linked to provenance and rights.
4. Proposed conclusions remain separate from admitted evidence.
5. Human reviewers decide what can be relied upon, shared or promoted.

### Product workspace

- Navigator converts intent into a governed research run.
- Libraries preserve reusable evidence with ownership, classification and freshness.
- Investigation Context keeps sources, claims, uncertainty and decisions together.
- Account Workspace exposes tenant, role, review state and pending decisions.

### Governance

AXIGNAL does not treat generated text as truth. Models may propose, summarise and organise. Admission, rights, tenant authority and external publication remain governed separately.

### Enterprise controls

Server-resolved tenant authority, private libraries, bounded integrations, append-only audit evidence and explicit retention and rights controls are designed into the architecture.

### Pricing presentation

Professional: **149 €/month** — candidate sandbox package for 1–3 seats.

Team: **399 €/month** — candidate sandbox package for 4–15 seats.

Prices must be rendered from the server-side versioned price book. Until commercial activation, the landing must label access as controlled and must not imply that Stripe live checkout is available.

### Security and reliability

AXIGNAL is designed against explicit service objectives, immutable release evidence, incident response, encrypted backups and isolated restore exercises. These are engineering objectives until real production evidence and human acceptance exist.

### FAQ

**Does AXIGNAL guarantee that every conclusion is true?**

No. AXIGNAL preserves evidence, provenance, uncertainty and review state so teams can understand what supports a conclusion and what remains unresolved.

**Does AXIGNAL make decisions automatically?**

No. It can coordinate research and produce bounded proposals. Human and policy gates retain decision, admission and publication authority.

**Can we connect private company data?**

The architecture supports tenant-private libraries and bounded integrations, subject to classification, rights, retention and security controls.

**Is the product publicly available?**

Not yet. Access remains controlled until production, security, usability and commercial gates are approved.

### Final CTA

**Bring one difficult research question. Leave with an evidence trail your team can inspect.**

CTA: **Request controlled access**

## Product UX acceptance

The final authenticated experience must preserve four primary journeys:

- research intent to evidence-backed Investigation Context;
- library discovery to governed evidence reuse;
- workspace collaboration without authority confusion;
- pricing and billing understanding without hidden consequences.

Every journey requires explicit loading, empty, failure and recovery states. Errors must preserve work where possible. Destructive actions require confirmation, and cancellation must explain entitlement effects.

## Accessibility

Target: WCAG 2.2 AA.

Automated scanning is necessary but insufficient. Release requires keyboard completion, visible focus, semantic structure, accessible names, reduced-motion support and representative manual assistive-technology review. Any critical accessibility defect blocks publication.

## Analytics and consent

Strictly necessary product measurement is the default. Marketing measurement requires consent. Raw prompts, research content and tenant-private data cannot enter analytics events. Consent rejection must be as easy as acceptance.

## Experimentation

Permitted: headline, section order, CTA label and pricing explanation.

Forbidden: security controls, tenant resolution, rights, billing amount, entitlement logic and evidence admission.

Every experiment declares hypothesis, sample, stopping rule, guardrails and owner before exposure. Negative outcomes remain evidence.

## Marketing sequence

1. Founder-led outreach and controlled design partners.
2. Product demonstrations based on real bounded workflows.
3. Technical content explaining evidence, provenance and governance.
4. Search content with unique reviewed utility.
5. Paid search only after conversion and contribution margin are measured.

Profit may be reinvested into acquisition, data, automation, infrastructure and product improvement only when the channel has positive measured contribution, bounded downside and adequate reserves.

## Publication gates

Public publication requires all of:

- complete primary journeys;
- claims mapped to evidence;
- accessibility, responsive and performance passes;
- Security, Privacy and Legal review;
- SEO and consent validation;
- representative usability acceptance;
- tested rollback;
- typed human Product Release authority.

Public landing publication, production traffic, paid campaigns and Stripe live remain independent gates.
