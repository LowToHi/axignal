# P03 — Security, Identity and Rights by Design

Version: `0.1.0`  
Task: `AX-GE2E-P03-T01`  
Status: `DRAFT ENGINEERING FOUNDATION / CANONICAL ACTIVATION BLOCKED`  
Stacked base: `AX-GE2E-P02-T01@1800d5e7944e49cb85f52abeb9c1ce51af666d08`

## 1. Purpose

P03 defines the minimum reusable security contract for a multiuser AXIGNAL system before source-admission factories, additional libraries or public product surfaces are allowed to expand.

The phase covers:

- principals and authentication;
- organisations, tenants and workspaces;
- memberships, role templates and capabilities;
- server-resolved authorization;
- PostgreSQL row-level security;
- data classification and privacy flags;
- P02 source-rights enforcement;
- governed exports;
- audit integrity;
- break-glass access;
- threat controls and adversarial tests.

This increment is a **design and executable-contract layer**. It does not claim that every runtime, migration, API or user interface has already implemented the design.

## 2. Dependency and transition boundary

The normative programme records:

```text
AX-GE2E-P01-T01  IN_PROGRESS
AX-GE2E-P02-T01  BLOCKED canonically by P01
AX-GE2E-P03-T01  BLOCKED canonically by P02
```

P02 nevertheless has an exact-head engineering-evidence branch with its ontology, sixteen library contracts, adversarial semantics and byte-exact rollback validated.

Human Product Authority has authorised starting P03 engineering on top of that frozen P02 head. This permits schemas, threat models, policy contracts, deterministic tests and rollback evidence. It does **not** permit:

- P02 or P03 canonical activation;
- merge to `main`;
- source admission;
- public launch;
- commercial availability;
- fabricated P01 buyer evidence;
- runtime authority not independently implemented and tested.

P03 remains a stacked draft until P02 is accepted or a normative ADR explicitly supersedes the dependency.

## 3. Trust model

The design follows these non-negotiable rules:

1. Deny by default.
2. Missing, stale, ambiguous or conflicting authority fails closed.
3. Authentication identifies a principal but does not select tenant, workspace, role or capability.
4. Tenant and workspace context are resolved by trusted server policy.
5. Effective authority is the intersection of active principal, session, membership, binding, capability, resource scope, purpose, classification and source rights.
6. Browser input, model output and worker payloads have zero authority to widen access.
7. RLS is mandatory defence in depth, not a substitute for service-layer authorization.
8. Revocation and kill switches override caches, queues and prior approvals.
9. Unknown classification and rights default to `RESTRICTED`.
10. Security decisions are auditable without copying secrets or unnecessary personal content.

## 4. Identity, organisation and membership

### 4.1 Principals

Canonical principal types are:

- `HUMAN_USER`;
- `SERVICE_PRINCIPAL`;
- `WORKLOAD_IDENTITY`;
- `BREAK_GLASS_PRINCIPAL`.

Email addresses and display names are attributes, never authorization identifiers. Principal IDs are opaque and immutable. Suspended, revoked or expired principals contribute zero capabilities.

Service and workload identities cannot receive interactive owner authority, approve exports or use break-glass.

### 4.2 Organisations, tenants and workspaces

These are distinct resources:

```text
Organisation
└── Tenant
    └── Workspace
```

Every workspace belongs to exactly one tenant and every tenant to exactly one organisation. Client-supplied organisation, tenant or workspace identifiers are selectors only; they never establish authority.

Unknown and foreign resources use the same external non-disclosing result.

### 4.3 Memberships

Membership is explicit, time-bounded and independently revocable. Organisation membership does not imply access to every tenant or workspace. Any membership change invalidates cached decisions.

## 5. Roles, capabilities and separation of duties

Roles are versioned templates. They do not carry authority by themselves. Effective authority is calculated from active bindings and explicit capabilities.

Initial capability vocabulary:

```text
organisation:read       organisation:manage
membership:manage       security:manage
rights:review           research:read
research:create         research:review
evidence:read           claim:read
export:create           export:approve
audit:read              service:execute
billing:manage
```

Critical separation rules:

- sensitive export creation and approval require different human principals;
- break-glass request and approval require different human principals;
- workers cannot manage memberships, security, rights, billing or approvals;
- rights review cannot be delegated to a model, parser or connector.

`INDETERMINATE` is enforced as `DENY`.

## 6. Session security

The browser receives only an opaque server session using:

```text
Secure
HttpOnly
SameSite=Strict
Path=/
```

Sessions rotate after authentication and privilege changes, bind to credential version, enforce idle and absolute expiry, protect state-changing requests against CSRF and detect replay.

Credentials and session identifiers are prohibited in URLs, browser-readable storage, ordinary logs and exports.

## 7. Row-level security

Protected tables use both:

```text
ENABLE ROW LEVEL SECURITY
FORCE ROW LEVEL SECURITY
```

Runtime roles:

- do not own protected tables;
- do not possess `BYPASSRLS`;
- receive transaction-local trusted context only after service authorization.

Required scope includes `tenant_id` and `workspace_id`. Missing or malformed context yields zero visible or mutable rows.

`SECURITY DEFINER` functions must pin `search_path`, validate scope and expose the minimum operation.

## 8. Data classification and privacy

Confidentiality levels:

```text
PUBLIC
INTERNAL
CONFIDENTIAL
RESTRICTED
```

Independent flags include:

```text
PERSONAL
SENSITIVE_PERSONAL
SECRET
SOURCE_RESTRICTED
LICENSED
EXPORT_CONTROLLED
```

Unknown classification defaults to `RESTRICTED`. Automated processes may propose a higher classification but cannot silently lower an existing classification.

Secrets never enter evidence, claims, exports or ordinary audit payloads.

## 9. Source-rights enforcement

P03 consumes the complete ten-dimensional P02 rights snapshot:

- collection;
- transient processing;
- persistent storage;
- model input;
- derived calculations;
- internal display;
- customer display;
- export;
- API redistribution;
- model training or evaluation.

Every protected operation is version-pinned to one or more rights snapshots. Missing, ambiguous, expired, suspended, revoked or conflicting rights deny the action.

Technical accessibility never overrides legal or contractual rights. A kill switch invalidates cached allows and blocks queued materialisation or export.

## 10. Export control

`research:read` does not imply `export:create` or `export:approve`.

Every export binds:

- requester and approvers;
- organisation, tenant and workspace;
- declared purpose and destination;
- enumerated resources;
- data classifications;
- source-rights snapshots;
- redaction profile;
- deterministic manifest hash;
- policy version;
- expiry and state.

Sensitive delivery is short-lived and audience-bound. Public or reusable object URLs are prohibited.

Rights, classification, approval and expiry are re-evaluated at materialisation and delivery.

## 11. Audit and break-glass

Security events are append-only and hash-chained. Denied and indeterminate decisions retain stable reason codes.

Audit readers cannot mutate policy or operational resources.

Break-glass requires:

- an incident reference;
- independent human approval;
- strong authentication;
- minimum capability and resource scope;
- short expiry;
- continuous audit;
- post-event review.

Break-glass cannot override source rights or create new export permission.

## 12. Threat model and adversarial coverage

The machine-readable threat model uses:

```text
STRIDE
+ source rights
+ privacy
+ epistemic authority
```

It freezes 24 threats and 24 one-to-one adversarial cases, including:

- browser tenant spoofing;
- cross-tenant IDOR;
- role and capability injection;
- confused-deputy workers;
- stale membership caches;
- `BYPASSRLS` and table-owner bypass;
- unsafe `SECURITY DEFINER`;
- session fixation, replay and CSRF;
- export exfiltration;
- stale rights approval and kill-switch bypass;
- model-generated authorization;
- automated classification downgrade;
- secret or personal-data leakage into audit;
- resource enumeration;
- break-glass self-approval;
- public export URLs;
- incomplete cache keys;
- audit-chain tampering;
- cross-workspace aggregation;
- sensitive export self-approval;
- purpose reuse;
- token leakage.

## 13. Machine-readable artifacts

```text
schemas/security-identity-rights-registry.schema.json
schemas/security-threat-model.schema.json
data/security/security-identity-rights-registry.v0.1.json
data/security/p03-threat-model.v0.1.json
data/security/p03-rollback-plan.v0.1.json
scripts/verify_p03_security_identity_rights.py
scripts/verify_p03_rollback.py
```

The verifier proves:

- schema validity;
- exact dependency and fail-closed state;
- principal, organisation, membership and session semantics;
- capability vocabulary and role-template containment;
- worker authority ceiling;
- separation of duties;
- RLS controls;
- classification and no-downgrade rules;
- complete P02 rights-dimension inheritance;
- governed export semantics;
- audit and break-glass controls;
- 24 threat/case one-to-one bindings;
- canonical activation remains blocked.

## 14. Rollback

P03 rollback is measured against the frozen P02 exact head:

```text
1800d5e7944e49cb85f52abeb9c1ce51af666d08
```

The rehearsal removes only P03 artifacts, restores the inherited Contract Validation workflow and compares the complete resulting tree byte-for-byte with the P02 baseline.

P02's own rollback is executed separately in a detached worktree at the frozen P02 head. This prevents P03 files from contaminating P02 evidence.

## 15. Acceptance path

Canonical P03 activation requires:

1. P02 acceptance or a normative superseding ADR.
2. Satisfaction or explicit supersession of the transitive P01 dependency.
3. Registry and threat-model validation.
4. Identity, organisation, membership and session contracts.
5. Capability and separation-of-duties validation.
6. RLS and cross-tenant non-disclosure tests.
7. Rights-revocation and kill-switch tests.
8. Classification downgrade tests.
9. Export authorization and manifest tests.
10. Break-glass tests and post-event review.
11. Audit-chain and secret-exclusion tests.
12. Byte-exact rollback.
13. Human Security Authority approval.
14. Human Product Authority approval.

## 16. Explicit exclusions

This increment does not implement or claim completion of:

- identity-provider integration;
- production session storage;
- database migrations or production RLS policies;
- authorization APIs;
- user or organisation administration UI;
- production export delivery;
- security operations centre integration;
- source admission;
- public coverage;
- billing;
- commercial activation;
- public launch.
