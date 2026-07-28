# ADR-001 — Brand, Domain and Repository Identifier

- Status: `ACCEPTED`
- Original date: `2026-07-26`
- Corrected: `2026-07-26`

## Context

The product naming process considered names centred on signals, claims, markets and exploration. During early drafting, the public brand and domain were incorrectly recorded as `ASIGNAL` and `asignal.com`.

The user explicitly corrected the canonical identity twice. That correction supersedes the earlier mistaken wording.

## Decision

- Public brand: **AXIGNAL**
- Public domain: **axignal.com**
- Repository and internal technical slug: **axignal**
- Repository: `LowToHi/axignal`
- Goal ID: `AXIGNAL-GOAL-001`
- Category: **Global Opportunity Intelligence**
- Descriptor: **The global climate system for economic opportunity.**

User-facing copy, contracts, schemas, APIs, analytics, deployment metadata and agent instructions MUST use `AXIGNAL` and `axignal.com`.

## Naming guard

The following strings are forbidden in active artifacts:

```text
ASIGNAL
asignal.com
ASIGNAL-GOAL-001
```

Historical commits may contain the earlier mistake, but active branch content, indexes, releases and customer surfaces MUST not.

## Consequences

- Brand, domain, repository and technical slug are aligned.
- No one-character public/technical distinction remains.
- CI MUST enforce canonical naming.
- Existing active documents and prototypes require a naming migration.
- Trademark and domain ownership remain separate legal checks from this engineering decision.

## Alternatives considered

- ASIGNAL with `asignal.com` — rejected by explicit user correction.
- Marklaim as a claims-focused brand.
- Coineath as an exploration-focused brand.
- Xignals, unavailable as the desired domain.
