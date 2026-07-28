# 15 — AXIGNAL Intent Intelligence Contract

Version: `0.3.1`
Status: `NORMATIVE CANDIDATE`
Goal ID: `AXIGNAL-GOAL-001`

## 1. Purpose

AXIGNAL Intent Intelligence learns from how users investigate the world while preserving a strict separation between:

- individual behaviour;
- inferred or confirmed preferences;
- privacy-protected aggregate Knowledge Tides;
- research prioritisation;
- economic claims and opportunities.

## 2. Fundamental rule

> User attention determines what deserves investigation. External evidence and admitted claims determine what AXIGNAL may assert.

A Knowledge Tide MUST NOT prove that an economic opportunity exists, is profitable or is personally suitable.

## 3. Intent event

An eligible user command or direct interaction MAY create a typed `USER_INTENT_EVENT`.

Required fields:

- event ID;
- user and organisation pseudonymous identifiers;
- occurred time;
- original language;
- command class;
- canonical entities, geographies and universes;
- selected time horizon;
- originating surface;
- interpretation confidence;
- whether the event was spontaneous, suggested or campaign-influenced;
- purpose permissions;
- retention class.

Raw prompt text MUST be separately governed and minimised.

## 4. Preference levels

### `OBSERVED_INTEREST`

A user performed an eligible action. It does not establish persistent preference.

### `INFERRED_PREFERENCE`

Repeated, diverse or sustained behaviour supports an inference. The inference MUST expose its basis, confidence and expiry.

### `CONFIRMED_PREFERENCE`

The user explicitly saved, confirmed or configured the interest.

Users MUST be able to inspect, correct and delete inferred and confirmed preferences.

## 5. Knowledge Tide definition

A Knowledge Tide is a time-bounded, aggregate behavioural signal over an eligible user cohort.

Example admissible behavioural claim:

> During the specified 30-day period, 60% of eligible active users independently investigated real-estate opportunities in Moscow.

This may be admitted as an observed quantitative claim about AXIGNAL user behaviour, subject to privacy and data-quality gates. It is not a real-estate market claim.

## 6. Denominator

Canonical share:

```text
intent_share =
unique eligible users expressing the canonical intent
/
unique eligible active users in the same period
```

The denominator MUST define:

- eligibility;
- active-user criteria;
- time window;
- included plans and jurisdictions;
- organisation treatment;
- bot and internal-user exclusion;
- minimum cohort.

Raw query volume MUST NOT replace unique-user share.

## 7. Tide dimensions

Knowledge Tides MUST remain multidimensional:

- `intent_share`;
- `intent_velocity`;
- `unique_user_count`;
- `organisation_diversity`;
- `language_diversity`;
- `user_geographic_diversity`;
- `repeat_interest_rate`;
- `confirmed_preference_rate`;
- `persistence`;
- `novelty`;
- `coverage_gap`;
- `external_evidence_gap`;
- `contradiction_pressure`;
- `research_completion_rate`;
- `manipulation_risk`.

A composite tide rank MAY order research candidates only when dimensions and weights remain visible and versioned.

## 8. Tide states

Suggested states:

- `EMERGING_ATTENTION`
- `ACCELERATING_ATTENTION`
- `PERSISTENT_ATTENTION`
- `BROAD_ATTENTION`
- `DECLINING_ATTENTION`
- `COORDINATION_SUSPECTED`
- `INSUFFICIENT_COHORT`
- `PRIVACY_SUPPRESSED`

These states describe user attention, not economic quality.

## 9. Temporal treatment

The engine MUST support:

- rolling windows;
- explicit comparison periods;
- decay for old unconfirmed interest;
- persistence across periods;
- seasonality checks;
- launch or UI-prompt effects;
- campaign and editorial exposure markers.

A tide MUST not be described as organic when product prompts materially caused it.

## 10. Independence and manipulation controls

The engine MUST detect or downweight:

- repeated prompts from one user;
- concentrated activity from one organisation;
- bots or scripted activity;
- coordinated campaigns;
- referral or promotional bursts;
- copied prompts;
- internally generated test traffic;
- one user using many accounts;
- one suggested prompt driving the majority of traffic.

Minimum cohort, organisation diversity and anomaly thresholds MUST be versioned.

## 11. Privacy

Intent Intelligence MUST apply purpose limitation and privacy by design.

Separate purposes:

1. execute the current investigation;
2. remember private interests;
3. improve product workflows;
4. create aggregate Knowledge Tides;
5. evaluate language or models.

The UI MUST not collapse these purposes into one opaque control.

Users MUST have access to:

- current memory status;
- recorded interests;
- inferred preferences;
- deletion;
- correction;
- memory disablement;
- aggregate-analysis exclusion where applicable;
- data export according to law and contract.

## 12. Tenant separation

- Raw prompts MUST remain tenant-private.
- Organisation-private investigations MUST not become public tide labels.
- Aggregate output MUST meet minimum privacy cohorts.
- Segmentation MUST be suppressed when reidentification risk is material.
- Customer confidential data MUST never enrich the global Claim Ledger without explicit lawful authority.

## 13. Knowledge Tides in the product

A Knowledge Tides lens MAY show:

- attention by geography or concept;
- acceleration;
- persistence;
- coverage gap;
- evidence gap;
- divergence between attention and admitted evidence.

Canonical interpretation matrix:

| User attention | External evidence | Interpretation |
|---|---|---|
| High | High | Strong attention around an evidenced phenomenon |
| High | Low | Priority research gap or narrative risk |
| Low | High | Potentially under-observed evidence |
| Low | Low | Low research priority |
| High | Contradictory | Popular but materially contested narrative |

## 14. Personalisation boundary

Private interest memory MAY improve:

- default filters;
- watchlist suggestions;
- relevant geography and universe discovery;
- continuation of previous research;
- alerts about changed claims.

It MUST NOT silently represent an asset or opportunity as personally suitable.

## 15. Separation from canonical truth

Intent events and tides MUST be stored in a separate bounded context from:

- Claim Ledger;
- Opportunity Engine;
- Scenario Engine.

Permitted bridge:

```text
Knowledge Tide or coverage gap
→ Research Candidate
→ external investigation
→ candidate evidence and claims
→ deterministic admission
```

Prohibited bridge:

```text
high user interest
→ economic opportunity admitted
```

## 16. Metrics

Required quality metrics:

- eligible-user coverage;
- event-classification accuracy;
- unique-user deduplication quality;
- organisation concentration;
- privacy suppression rate;
- manipulation detection rate;
- preference correction rate;
- opt-out propagation time;
- tide-to-research conversion;
- research-to-admitted-claim conversion;
- false-trend audit rate.

## 17. Retention

Retention MUST be defined separately for:

- raw message;
- interpreted intent;
- private preference;
- aggregate statistics;
- research candidates;
- audit evidence.

Raw message retention SHOULD be shorter than canonical aggregate retention unless an explicit product purpose requires otherwise.

## 18. Acceptance criteria

Intent Intelligence is accepted when:

- the 60%-share example is reproducible using unique eligible users;
- one user or organisation cannot manufacture a broad tide;
- minimum cohorts prevent reidentification;
- users can inspect and delete private memory;
- opt-out propagates to future aggregate computation;
- raw prompts never leak across tenants;
- tides trigger research candidates only;
- active UI clearly distinguishes attention from evidence;
- manipulation simulations are detected or suppressed;
- every metric exposes denominator, time window and method version.
