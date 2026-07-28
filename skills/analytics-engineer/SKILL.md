---
name: analytics-engineer
description: Define privacy-safe and reproducible landing metrics for qualified access requests, story comprehension and performance without dark patterns.
---

# AXIGNAL Landing Analytics Engineer

## Funnel

`landing_view → act_reached → demo_started → evidence_opened → access_form_started → access_request_submitted`

## Event constraints

- no raw prompt, email or free-text capture in behavioural events;
- no fingerprinting;
- consent state governs non-essential analytics;
- act progress uses coarse buckets, not continuous scroll surveillance;
- separate synthetic demo interactions from real product usage;
- record motion tier and WebGL fallback only as technical dimensions.

## Primary metrics

- qualified access-request completion;
- comprehension of evidence classifications;
- demo completion;
- CTA visibility-to-action rate;
- error and fallback rate;
- Core Web Vitals by capability tier.
