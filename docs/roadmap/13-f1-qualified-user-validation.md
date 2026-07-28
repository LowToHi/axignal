# 13 — F1 Qualified-User Validation

Version: `0.2.0`  
Status: `CONTROLLED STUDY PROTOCOL CANDIDATE`  
Goal ID: `AXIGNAL-GOAL-001`  
Integrated harness baseline: `03471bd3764e8696b86380fd8a83f6356ac92f7a`

## Objective

Measure whether qualified users understand AXIGNAL's authority layers, trace evidence correctly, identify unknowns and complete bounded investigation tasks at least as reliably as with a linear control surface containing equivalent information.

## Integrated harness

The pseudonymised F1 harness is integrated in `main`. It provides six frozen tasks, deterministic AXIGNAL/CONTROL assignment, equivalent participant content, append-only sessions and responses, server-side answer keys, reproducible scoring and zero canonical authority.

## Frozen study candidate

Study `AXIGNAL-F1-CONTROLLED-001` freezes:

- harness baseline and source blob locks;
- experiment version and six-task set;
- assignment algorithm;
- intention-to-treat population;
- primary metrics and absolute thresholds;
- comparative non-inferiority margins;
- exclusions and stopping rule;
- zero-tolerance privacy and authority guardrails.

The analyst boundary exports pseudonymised session outcomes through an execute-only function. It does not expose answer text, task payloads, answer keys, names or email addresses, and it has no direct table or Claim Ledger access.

## Primary metrics

- task completion rate;
- critical error rate;
- evidence traceability rate;
- authority-layer comprehension;
- unknowns identification rate.

## Cohort and stopping rule

The initial campaign requires at least six distinct qualified participants, twelve eligible sessions and four sessions per condition. It stops at the first post-session checkpoint satisfying all minima, with a hard cap of twenty-four eligible sessions. Performance-based optional stopping is prohibited.

## Decision outputs

The reproducible analysis emits `NOT_READY`, `FAIL_CANDIDATE`, `PASS_CANDIDATE` or `INCONCLUSIVE`. Every output remains subject to a human gate; tooling cannot declare the normative phase `PASSED` or `FAILED`.

## Guardrails

- participant PII columns: `0`;
- cross-tenant incidents: `0`;
- canonical mutations: `0`;
- answer-key exposures: `0`;
- condition immutable after session start;
- events and responses append-only;
- production deployment: false.

## External gate

CI and synthetic fixtures validate only the protocol and machinery. F1 remains in `GATE_REVIEW` until real qualified-user sessions are recruited, closed and analysed against the frozen manifest. No product-superiority claim is authorised before that evidence exists.

## Non-goals

No production deployment, recruitment automation, recordings, direct participant PII, OCR, new sources, billing, new model authority or commercial-universe expansion.
