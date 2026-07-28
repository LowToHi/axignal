# F1 Controlled Study v1

Version: `1.0.0`  
Study ID: `AXIGNAL-F1-CONTROLLED-001`  
Status: `FROZEN_PRE_RECRUITMENT`  
Harness baseline: `03471bd3764e8696b86380fd8a83f6356ac92f7a`

## Purpose

Test whether qualified users can classify authority, trace evidence and identify unknowns with AXIGNAL at least as reliably as with a linear control surface containing the same information.

This protocol freezes the experiment before participant recruitment. Technical tests, synthetic fixtures and CI results validate the study machinery only; they are not human-study evidence.

## Frozen design

```text
qualified participant
→ HMAC-pseudonymised identity
→ frozen task
→ deterministic AXIGNAL or CONTROL assignment
→ equivalent content
→ append-only session and response
→ pseudonymised analyst export
→ intention-to-treat analysis
→ human gate decision
```

The assignment algorithm is SHA-256 parity over `participant_id_hash|task_id|experiment_version`. Re-randomisation and condition mutation are prohibited.

## Cohort and stopping rule

The first campaign requires at least:

- six distinct qualified participants;
- twelve eligible sessions;
- four sessions in each condition.

The campaign is checked after every completed session and stops at the first checkpoint satisfying all sample minima. It has a hard cap of twenty-four eligible sessions. Performance-based early stopping is prohibited.

## Analysis population

The primary analysis is intention-to-treat. Eligible sessions that are incomplete or abandoned count as not completed; they are not silently removed. Exclusion is limited to wrong protocol version, unqualified frozen profile, a documented technical failure before a response was possible, or a duplicate participant/task session. Outcome- or condition-based exclusion is prohibited.

## Decision interpretation

The analysis tool emits one of:

- `NOT_READY`: sample minima are not met;
- `FAIL_CANDIDATE`: a zero-tolerance guardrail or AXIGNAL absolute threshold fails;
- `PASS_CANDIDATE`: sample, guardrails, absolute thresholds and comparative non-inferiority margins pass;
- `INCONCLUSIVE`: absolute thresholds pass but a comparative margin does not.

All outputs require a human gate. The script cannot declare F1 normatively `PASSED` or `FAILED`.

## Data boundary

The analyst export contains only pseudonymous participant hashes, frozen profiles, task IDs, condition, state, timestamps and scored booleans. It excludes names, email, answer text, task payloads, answer keys and source documents. The analyst credential has no direct table access and no canonical or evidence mutation authority.

## Operational prerequisites

Before issuing the first participant credential, the operator must:

1. record the manifest SHA-256;
2. verify the baseline and source locks;
3. document participant information and consent outside the analytical dataset;
4. provision separate validation-runtime and analyst credentials;
5. confirm all incident counters start at zero;
6. confirm no task, threshold, exclusion or stopping-rule change is pending.

## Prohibited claims

Until real sessions are closed and analysed, do not claim that AXIGNAL improves comprehension, traceability, accuracy, speed or confidence calibration.
