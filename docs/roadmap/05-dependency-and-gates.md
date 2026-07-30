# 05 — AXIGNAL Dependency and Gate Graph

Version: `1.4.0`
Status: `NORMATIVE CANDIDATE`
Goal ID: `AXIGNAL-GOAL-001`
Governing contract: `30`

## Authorisation graph

```text
P00 → P01 → P02 → P03 → P04 → P05 → P06 → P07
                                             ├→ P08 Procurement
                                             ├→ P09 Grants
                                             ├→ P10 Regulatory
                                             ├→ P11 Infrastructure
                                             ├→ P12 Corporate
                                             ├→ P13 Sovereign/Macro
                                             ├→ P14 Trade/Supply
                                             ├→ P15 Energy/Climate
                                             └→ P16 Innovation/IP

P08 + P09 + P10 + P11 + P12 + P13 + P14 + P15 + P16
→ P17 Cross-library
→ P18 Knowledge Tides
→ P19 Scenarios and outcomes
→ P20 Enterprise/API
→ P21 Commercial runtime
→ P22 Production acceptance
→ P23 Final UX/copy/marketing
→ P24 Global launch gate
```

## Gate rule

Every transition requires:

- typed task evidence;
- contract compliance;
- skill evidence;
- Goal Lock answers;
- rights and privacy disposition;
- unresolved-risk register;
- observability;
- rollback or kill-switch evidence;
- independent gate evaluation.

Critical unverifiable evidence is `FAIL_CLOSED`.

## Dispositions

- `PASS`;
- `CONDITIONAL_PASS` only for explicitly non-material conditions;
- `FAIL_CLOSED`;
- `PAUSE`;
- `SUPERSEDE`.

## Universal checks

1. Goal remains aligned.
2. Canonical naming passes.
3. Proposal, canonical truth and operational decisions remain separated.
4. Security and privacy are complete for scope.
5. Source rights and redistribution are explicit.
6. Multilingual impact is addressed.
7. Observability and ownership exist.
8. Rollback is tested where acceptance requires it.
9. No hidden manual process is represented as automated.
10. Known limitations are visible.
11. No phase weakens the no-partial-launch rule.
12. Catalogue breadth is not represented as admitted coverage.

## Parallelisation exception

P08–P16 may run concurrently only after P07 is accepted. Research or source probes may begin earlier when non-authoritative, rights-safe, reversible and incapable of changing product state.

## P24 rule

P24 returns only `ACCEPTED_FOR_PUBLIC_LAUNCH`, `IN_PROGRESS` or `REJECTED`. Missing critical evidence keeps public launch blocked.

## Gate ledger

Every decision records gate, date, commit, contract and skill versions, evidence links, thresholds, unresolved conditions, disposition and next authorised task.
