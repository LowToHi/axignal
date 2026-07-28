# ADR-011 — Shared Traefik edge for the private pilot

Status: `PROPOSED / REVIEW REQUIRED`
Date: `2026-07-29`
Owner: Platform and Security
Goal ID: `AXIGNAL-GOAL-001`

## Context

The authorised private-pilot VPS at `187.124.220.48` is a shared application host. Read-only preflight evidence shows that an existing host-network Traefik instance owns `80/tcp` and `443/tcp` for unrelated active services. The original AXIGNAL remote playbook configured Caddy to claim those same host ports.

Running that playbook unchanged would fail to bind Caddy. Stopping or replacing Traefik would interrupt unrelated services and violate the isolation, availability and rollback requirements in Contracts 06, 09, 10, 18 and 19.

The same preflight confirmed an existing watched Traefik file-provider directory. This supports adding an isolated route without changing the incumbent static configuration or restarting the edge.

The original automation also generated credentials on a controller and wrote `REMOTE_PILOT_ACCEPTED` after deployment verification. Those behaviours do not satisfy the required separation between secret custody, physical deployment evidence and independent acceptance.

## Decision

Add an explicit `shared-traefik` edge mode alongside the existing `standalone` mode.

In `shared-traefik` mode:

- Traefik remains the exclusive owner of host ports `80/tcp` and `443/tcp`;
- AXIGNAL Caddy serves plain HTTP only inside the host boundary;
- Docker publishes Caddy exclusively as `127.0.0.1:<configurable-high-port>:80`;
- a dedicated `/etc/traefik/dynamic/axignal-pilot.yml` routes only the approved pilot hostname to that loopback endpoint;
- the playbook verifies the approved Traefik container is running with host networking and that the existing dynamic directory is present;
- the confirmed ACME contact, entrypoint and resolver must match the existing static Traefik boundary;
- the playbook does not restart Traefik or modify unrelated dynamic files;
- the AXIGNAL Compose base publishes no ports; explicit overlays own every host-port decision.

Initial tenant UUID, operator password and service secrets are generated only on the authorised host. The generator sets `umask 077`, writes root-owned mode-`0600` files, emits only non-sensitive metadata and fingerprints, marks the operator password as temporary, and supports rotation plus plaintext-file retirement after secure handoff.

A successful deployment writes `DEPLOYED_AWAITING_ACCEPTANCE` with `acceptance_status: BLOCKED`. Only the independent gate associated with Issue #31 may declare `REMOTE_PILOT_ACCEPTED`.

## Alternatives considered

### Stop the incumbent Traefik and give `80/443` to Caddy

Rejected. It would interrupt unrelated services, broaden rollback impact and make AXIGNAL responsible for existing routes and certificates.

### Publish AXIGNAL on a public high port

Rejected. Docker-published ports can bypass expected firewall semantics, enlarge the attack surface and expose an implementation endpoint outside the approved TLS edge.

### Join Caddy directly to every existing application network

Rejected. It would couple AXIGNAL to unrelated service networks and weaken network isolation.

### Add AXIGNAL labels to the incumbent Traefik Docker provider

Rejected for this host. Traefik uses host networking and an existing watched file provider; a dedicated dynamic file is narrower, auditable and independently removable.

### Move the pilot to a new dedicated VPS

Valid future option, but not required for the authorised private pilot. The current host can satisfy isolation if the loopback and dynamic-route boundary passes physical verification.

## Tradeoffs

- The pilot depends on the incumbent Traefik process and certificate resolver.
- Operators must maintain two explicit edge overlays.
- The AXIGNAL route can temporarily return `502` during a failed first deployment, but unrelated routes remain untouched.
- Rollback must preserve edge-mode compatibility; a release lacking the required shared overlay is rejected.
- Credential delivery remains an external human process and cannot be fabricated by CI.

## Consequences

### Positive

- existing services and their edge ownership remain intact;
- AXIGNAL has no public Docker-published port;
- the public hostname, TLS and application proxy remain separable;
- secret creation and custody stay on the authorised host;
- deploy evidence cannot self-approve the acceptance gate;
- rollback can remove one AXIGNAL-owned route without rewriting Traefik.

### Negative

- the shared host remains a larger operational failure domain than a dedicated VPS;
- the playbook depends on an inventoried Traefik container name, entrypoint, resolver and file-provider directory;
- rotation and secure handoff require an operator procedure before acceptance.

## Migration implications

Existing standalone environments add `compose.standalone.yaml` explicitly. New shared-host environments select `compose.shared-traefik.yaml` and use a separate public site address versus internal Caddy address.

No production data migration is required. Existing releases that do not contain the shared overlay are not valid shared-edge rollback targets.

## Rollback

For code, revert the introducing commit.

For a future physical deployment, stop only the `axignal-pilot` Compose project, remove only `/etc/traefik/dynamic/axignal-pilot.yml`, and verify all pre-existing Traefik routes and containers remain healthy. Do not stop or restart Traefik as part of AXIGNAL rollback.

Credential files are not part of code rollback. Preserve evidence during an incident; otherwise revoke or rotate the credential and remove plaintext files after verified handoff.
