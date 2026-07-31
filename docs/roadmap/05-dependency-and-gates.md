# 05 — AXIGNAL Dependency and Gate Graph

Version: `1.5.0`
Status: `NORMATIVE CANDIDATE / HUMAN APPROVAL REQUIRED`
Goal ID: `AXIGNAL-GOAL-001`
Governing contract: `31`
Decision: `ADR-016`

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
→ P21 Commercial runtime and seats
→ P22 Production/security/DR framework
→ P23 Product UX and B2G shell
→ P24 Acceptance framework
→ P25 Passwordless identity and trial abuse
→ P26 Organic discovery and Founder Operations
→ P27 Final exact-head public-launch gate
```

## Engineering exception

Later phases may be developed as bounded engineering before earlier canonical gates close when:

- structural contracts are frozen;
- work is isolated and reversible;
- no source or product state is admitted;
- no public or commercial activation occurs;
- evidence is labelled engineering-only;
- dependency failure remains visible;
- canonical acceptance remains blocked.

This exception explains the current stacked engineering programme. It does not waive dependencies.

## Gate rule

Every canonical transition requires:

- typed task evidence;
- contract compliance;
- skill evidence;
- Goal Lock answers;
- rights and privacy disposition;
- unresolved-risk register;
- observability;
- rollback or kill-switch evidence;
- exact-head binding;
- independent gate evaluation;
- human approval where required.

Critical unverifiable evidence is `FAIL_CLOSED`.

## Dispositions

Engineering gate dispositions:

- `ENGINEERING_E2E_PASS`;
- `ENGINEERING_EVIDENCE_READY`;
- `ENGINEERING_REJECTED`;
- `SUPERSEDED`.

Canonical gate dispositions:

- `CANONICALLY_ACCEPTED`;
- `CANONICAL_ACCEPTANCE_BLOCKED`;
- `PRODUCT_ADMITTED`;
- `COMMERCIAL`;
- `SUSPENDED`;
- `REVOKED`;
- `REJECTED`.

P27 launch dispositions:

- `ACCEPTED_FOR_PUBLIC_LAUNCH`;
- `IN_PROGRESS`;
- `REJECTED`.

## Universal checks

1. Goal remains aligned.
2. Canonical naming passes.
3. Engineering and canonical states are not conflated.
4. Proposal, canonical truth and operational decisions remain separated.
5. Security and privacy are complete for scope.
6. Source rights and redistribution are explicit.
7. Multilingual impact is addressed.
8. Observability and ownership exist.
9. Rollback is tested where acceptance requires it.
10. No hidden manual process is represented as automated.
11. Known limitations are visible.
12. No phase weakens the no-partial-public-launch rule.
13. Catalogue breadth is not represented as admitted coverage.
14. Candidate pricing is not represented as validated.
15. Public signup cannot bypass identity, risk or seat authority.
16. SEO pages cannot bypass the IndexabilityGate.
17. Tender Alerts cannot create accounts, trials or entitlements.
18. Search Console data cannot publish pages or grant authority.
19. MCP catalogue presence cannot grant tool access.
20. Founder UI controls must map to durable server-side authority.

## Parallelisation

P08–P16 engineering may run concurrently when shared contracts exist. Canonical acceptance of P17 still requires canonical acceptance of all nine library phases.

Research, source probes, MCP probes and Search Console probes may begin early only when:

- non-authoritative;
- least privilege;
- read-only by default;
- rights-safe;
- reversible;
- incapable of changing public, customer, billing or canonical state.

## P24 rule

P24 is an acceptance framework, evidence manifest and stop-condition engine. After Contract 31, it cannot return the final public-launch decision.

## P25 rule

P25 cannot be canonically accepted until production identity providers, email delivery, bot controls, recovery, abuse, privacy and operational evidence pass on the accepted environment.

## P26 rule

P26 is complete only when T01–T04 pass.

```text
T01 growth foundation
+ T02 commercial administration
+ T03 trust, source and abuse administration
+ T04 operations and DR administration
= P26 candidate for canonical acceptance
```

## Search Console and MCP rule

```text
DNS verification
≠ API access
≠ Search Analytics evidence
≠ MCP admission
≠ publication authority
```

Every MCP tool is denied until exact server and tool admission. Destructive tool classes remain denied by default.

## Private acceptance rule

Private acceptance is permitted only for explicitly admitted organisations under controlled terms.

It MUST NOT include:

- open signup;
- public-beta positioning;
- paid media representing launch;
- unsupported coverage claims;
- unaudited billing or access;
- public availability of an incomplete product.

Private acceptance is not a P27 disposition.

## P27 rule

P27 binds the exact accepted heads and renewed evidence for P00–P26.

A final-head change invalidates:

- the acceptance-manifest digest;
- security approval;
- SRE approval;
- Finance/Billing approval;
- Legal/Privacy approval;
- Product acceptance;
- launch authority.

Missing critical evidence keeps the result `IN_PROGRESS` or `REJECTED`.

## Gate ledger

Every decision records:

- gate and task;
- engineering and canonical state;
- date;
- exact commit;
- contract and ADR versions;
- skill versions;
- evidence links and digests;
- thresholds;
- unresolved conditions;
- disposition;
- human authorities;
- next authorised task;
- rollback or kill switch.
