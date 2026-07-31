# P20 — Enterprise, API, Private Data and Integrations

Task: `AX-GE2E-P20-T01`

P20 defines the enterprise control plane for federated identity, SCIM directory
lifecycle, tenant-private libraries, scoped API access, atomic quotas, signed
webhooks, bounded integrations, residency decisions and enterprise audit.

## Truth boundaries

- Federated authentication is not tenant or workspace authority.
- A SCIM group is not an approved application role.
- A private library is not a global or canonical AXIGNAL library.
- An API credential is not user authority and cannot select tenant context.
- API scope never overrides classification, source rights or export controls.
- Available quota is not billing entitlement or commercial availability.
- A webhook `2xx` response is transport receipt, not a business outcome.
- An installed integration is not an admitted source.
- Residency routing is not a legal-compliance guarantee.
- Customer private data is not model-training or evaluation permission.
- Support access is not unrestricted administrator access.
- Enterprise audit output is not canonical evidence.

## Architecture

Eight modules materialise 32 record types and 48 invariants:

1. `ENTERPRISE_IDENTITY_FEDERATION`
2. `SCIM_DIRECTORY_LIFECYCLE`
3. `PRIVATE_LIBRARY_CONTROL_PLANE`
4. `API_CREDENTIAL_SCOPE_GATE`
5. `QUOTA_AND_BUDGET_ENFORCEMENT`
6. `WEBHOOK_DELIVERY_RUNTIME`
7. `ENTERPRISE_INTEGRATION_GATEWAY`
8. `ENTERPRISE_AUDIT_RESIDENCY_EGRESS`

The runtime also defines 12 lifecycle states, 11 pipeline stages, ten identity
modes, ten API scope classes, ten quota dimensions, ten webhook states, ten
integration types, ten residency classes, eight authority classes, ten risks
and twelve readiness gates.

## SSO and SCIM

SAML and OIDC assertions require current metadata, trusted issuer, valid
signature and audience, bounded assertion age, replay protection and a verified
domain. Successful federation only creates an authenticated principal. Tenant,
workspace, membership, role and capability authority remain server-resolved.

SCIM external identifiers are correlation keys, not authorisation keys.
Group-to-role mappings remain proposals until typed human approval. Privileged
roles cannot be created by a SCIM client, service principal, model or worker.
Deprovisioning must revoke sessions, API credentials and memberships before the
operation is acknowledged.

## Private libraries

Private libraries are physically and logically tenant scoped. Every object
carries classification, purpose, retention, rights and residency snapshots.
Private ingestion can create tenant-private candidates and operational records;
it cannot create global canonical evidence or silently contribute customer
content to training or evaluation.

Deletion, revocation and legal hold remain distinct. Cross-tenant joins and
global aggregation are denied unless a separate, explicit and independently
authorised contract exists.

## API and quotas

API credentials are audience-bound, tenant-bound, expiring, rotatable and
revocable. Effective authority is the intersection of credential scopes,
principal capabilities, resource filters, tenant policy and rights. No P20 API
scope grants canonical admission, role approval, source-rights approval,
signature, spending or external-action authority.

Technical quota is reserved atomically before work and reconciled after work.
Retries reuse one idempotency key and cannot reserve twice. Unknown, stale or
exhausted quota fails closed. Pricing, payment and commercial entitlement remain
P21 concerns.

## Webhooks and integrations

Webhook payloads use canonical bytes, a tenant-bound audience, timestamp,
nonce, event identifier and idempotency key. Signature failure, replay,
timestamp skew, tenant mismatch or unsupported event denies delivery. Delivery
is at-least-once and bounded by retry and dead-letter policy.

Integrations use secret references, exact endpoint allowlists, bounded egress
and tenant-specific installations. Installation never implies source admission
or wider model, connector, worker or external-action authority.

## Audit, residency and support access

Enterprise audit events are append-only and hash chained. They exclude
credentials, secrets and unnecessary customer content. Residency and egress
decisions are explicit policy outputs with no automatic claim of legal
compliance.

Support access requires a human principal, incident or support ticket, separate
approval, strong authentication, minimal scope, short expiry and continuous
audit. It cannot bypass rights, residency, deletion or export policy.

## Test surface

P20 includes 40 conformance fixtures and 72 adversarial cases covering
federation misbinding, SCIM privilege escalation, cross-tenant disclosure,
credential escalation, quota races, webhook forgery and replay, integration
secret leakage, residency or training-rights bypass and audit/support abuse.

Every adversarial case preserves zero canonical, external-action, disclosure,
authority-elevation, training and quota-bypass deltas.

## Canonical state

P20 is engineering evidence only. P19 and all transitive dependencies remain
canonically blocked. The PR must remain draft; merge to `main`, public
enterprise availability, production SSO/SCIM, live integrations and commercial
claims are not authorised.
