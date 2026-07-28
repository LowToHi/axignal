# ADR-002 — Economic Observation, Not Personalised Advice

- Status: `ACCEPTED`
- Date: `2026-07-26`

## Context

AXIGNAL will structure historical, current and forecast economic claims across multiple opportunity and asset classes. Some covered domains may include financial instruments. Personal recommendations, execution or portfolio management would materially increase regulatory and operating complexity.

## Decision

Foundation AXIGNAL is an information, research, observation and exploration platform.

It MAY:

- describe observed and calculated conditions;
- provide non-personalised scenarios;
- expose objective filters;
- map relationships and opportunity climates;
- let users save observation interests.

It MUST NOT:

- present an instrument as personally suitable;
- allocate a user’s portfolio;
- execute or route orders;
- custody assets;
- rebalance accounts;
- guarantee outcomes.

Any expansion beyond this boundary requires a new legal and architecture ADR before implementation.

## Consequences

- Onboarding captures observation preferences rather than suitability data.
- The UI scores evidence and conditions, not “buy” suitability.
- Financial-instrument research still requires review for rules governing public investment recommendations.
- Product language must distinguish inspiration and observation from advice.

## Alternatives considered

- Become a regulated adviser from launch.
- Partner immediately with a regulated execution provider.
- Exclude all financial-instrument data.

The selected boundary preserves broad intelligence value while controlling initial risk.
