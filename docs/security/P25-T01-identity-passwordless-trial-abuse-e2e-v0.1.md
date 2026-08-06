# P25-T01 — Identity, Passwordless Authentication & Trial Abuse Governance

Task: `AX-GE2E-P25-T01`

Status: `IMPLEMENTED_NOT_PUBLIC`

## Decision

AXIGNAL does not grant a trial to a browser account. It grants one governed trial to a tenant or economic identity after identity verification and a versioned risk decision.

```text
verified email bootstrap
→ required WebAuthn user verification
→ opaque revocable session
→ tenant resolved by the server
→ trial-risk decision
→ governed trial grant
→ first admitted AI request starts seven days
→ token, cost and concurrency ledgers
```

## Authentication

The public authentication design is passkey-first:

- discoverable WebAuthn credentials;
- user verification required;
- relying-party and origin verification performed by the API;
- no password in the public signup path;
- email verifies address control but is not the persistent authenticator;
- the browser receives an opaque `HttpOnly` session cookie;
- session state is stored and revocable in PostgreSQL;
- the browser cannot choose a tenant;
- the API receives a signed assertion with a maximum lifetime of 60 seconds.

The previous environment-configured email/password boundary remains available only when the P25 runtime feature flag is disabled. It is retained for frozen pilot and historical E2E compatibility and is not the public-launch design.

## Session policy

```text
idle timeout:      1 hour
absolute timeout: 24 hours
API assertion:    60 seconds
```

Production cookie:

```text
__Host-axignal_session
Secure
HttpOnly
SameSite=Lax
Path=/
no Domain attribute
```

Sessions rotate after every completed passkey ceremony. Logout and recovery revoke the server-side session immediately.

## Recovery

Every registration produces eight one-time recovery codes. Recovery:

1. requires the verified email identity and one unused code;
2. revokes all active sessions;
3. places the identity in `RECOVERY_ONLY`;
4. requires registration of a new passkey;
5. revokes previous authenticators when the new passkey is bound;
6. produces a new recovery-code set.

## Trial ownership

A trial belongs to `tenant_id`, not `user_id`, email text, cookie or device.

```text
one tenant
→ one trial_grant
→ one seven-day clock
→ one shared token and cost budget
→ two governed seats
```

A second member, a changed owner, another browser or another account does not create another trial.

## Trial start

Email verification and passkey registration prepare the trial but do not start the clock.

```text
trial READY
→ first admitted /v1/ai/authorize request
→ entitlement and owner seat materialised atomically
→ trial ACTIVE
→ expires_at = started_at + 7 days
```

Direct activation through `/v1/trials/activate` is blocked while P25 is enabled.

## Abuse signals

Strong claims:

- canonical email identity;
- verified telephone;
- payment-instrument fingerprint.

Weak claims:

- first-party installation identifier;
- bounded network prefix;
- verified or observed domain.

Weak signals cannot independently produce `BLOCK_ABUSE`. They may produce `ALLOW_RESTRICTED`, `STEP_UP_REQUIRED` or `MANUAL_REVIEW`.

Gmail and Googlemail addresses are canonicalised so dots and `+` aliases do not manufacture new strong email identities.

Low-entropy values are stored as namespaced HMAC-SHA-256 values under a versioned secret pepper. Raw IP addresses and installation identifiers are not persisted by the identity schema.

## Risk decisions

```text
ALLOW
ALLOW_RESTRICTED
REUSE_EXISTING_TRIAL
STEP_UP_REQUIRED
MANUAL_REVIEW
BLOCK_ABUSE
```

A duplicate strong claim reuses the existing tenant/trial. It does not create another entitlement.

## Economic controls

The trial has simultaneous limits:

- seven days;
- two seats;
- 1,000,000-token ceiling;
- internal estimated-cost ceiling;
- one concurrent research run;
- restricted bulk export and private connectors.

Token reservations create corresponding cost reservations inside the same database transaction. Reconciliation or release updates both ledgers. A run cannot be admitted when either budget is exhausted.

## Bot and velocity controls

Signup and authentication have route-specific rate limits keyed by HMAC digests of email identity, installation and network prefix. Production requires server-side bot verification. The deterministic provider is confined to an explicitly enabled test environment.

## Data model

Global identity authority lives in `identity_private`:

- `users`;
- `organisations`;
- `user_organisations`;
- `email_challenges`;
- `bootstrap_tickets`;
- `webauthn_challenges`;
- `webauthn_credentials`;
- `identity_sessions`;
- `recovery_codes`;
- `identity_rate_limits`;
- `security_events`;
- `trial_grants`;
- `trial_risk_decisions`;
- `trial_subject_claims`;
- `trial_usage_accounts`;
- `trial_cost_reservations`;
- `trial_abuse_events`.

Security, risk and abuse-event ledgers are append-only.

## Evidence requirements

The phase is not complete until exact-head CI proves:

- passkey registration with real WebAuthn verification;
- passkey authentication after logout;
- opaque `HttpOnly` cookie;
- session revocation;
- canonical alias trial reuse;
- weak-signal step-up without independent blocking;
- no entitlement before first AI request;
- seven-day start and expiry timestamps;
- two-seat trial capacity;
- token and cost budget enforcement;
- one concurrent research run;
- append-only ledgers;
- direct identity-table access denied to the application role;
- public signup, external payment and commercial activation remain disabled.

## Truth boundaries

```text
implemented authentication ≠ public signup enabled
email verified ≠ trial granted
account created ≠ new trial
trial prepared ≠ trial started
risk score ≠ proof of fraud
step-up passed ≠ paid customer
CI pass ≠ production provider approval
```
