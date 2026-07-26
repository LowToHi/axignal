# ADR-001 — Brand, Domain and Repository Identifier

- Status: `ACCEPTED`
- Date: `2026-07-26`

## Context

The product naming process considered names centred on signals, claims, markets and exploration. The user selected `asignal.com` as the public domain while the GitHub repository had already been created as `LowToHi/axignal`.

Renaming the repository is not required to establish the public brand and could create unnecessary migration work.

## Decision

- Public brand: **ASIGNAL**
- Public domain: **asignal.com**
- Repository and internal technical slug: **axignal**
- Category: **Global Opportunity Intelligence**
- Descriptor: **The global climate system for economic opportunity.**

Code package names MAY use `axignal` where a stable technical namespace is needed. User-facing copy MUST use `ASIGNAL`.

## Consequences

- Brand and technical slug intentionally differ by one character.
- Documentation, deployment and analytics MUST explicitly map both names.
- Automated agents MUST NOT “correct” the repository slug.
- Trademark and domain ownership remain separate legal checks from this engineering decision.

## Alternatives considered

- Axignal as both brand and repository name.
- Marklaim as a claims-focused brand.
- Coineath as an exploration-focused brand.
- Xignals, unavailable as the desired domain.
