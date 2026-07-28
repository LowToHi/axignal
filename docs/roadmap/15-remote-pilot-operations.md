# Remote Pilot Operations v0.2

## Status

`IMPLEMENTED / SHARED-EDGE REVIEW REQUIRED / NOT DEPLOYED / PRIVATE PILOT ONLY`

## Objective

Turn the local Pilot Deployment Candidate into an exact-SHA remote deployment and recovery system for an Ubuntu 24.04 VPS. This unit does not authorise a public launch, billing, live sources, customer data or the F1 human campaign.

## Operational path

```text
controller without pilot secrets
→ Ansible host bootstrap
→ host-only credential generation under umask 077
→ UFW allowlist
→ exact-SHA release fetch
→ candidate contract verification
→ pre-change backup
→ loopback-only Caddy deployment
→ isolated Traefik dynamic route
→ HTTPS and authenticated demo smoke test
→ deployment state awaiting independent acceptance
→ watchdog and scheduled backup timers
```

## Invariants

- only a full 40-character commit SHA may be deployed;
- UUID, operator password and service secrets are generated only on the authorised host;
- the private environment, credential metadata and pending password use `umask 077`, root ownership and mode `0600`;
- plaintext credentials never appear in command arguments, logs, CI, evidence or messages;
- the temporary operator password requires first-access rotation and deletion after verified secure handoff;
- Traefik remains the exclusive owner of public `80/443`;
- shared-edge Caddy binds only `127.0.0.1:<configurable-high-port>:80`;
- AXIGNAL owns one removable Traefik dynamic route and does not restart the incumbent proxy;
- UFW denies inbound traffic except the configured SSH port, `80/tcp` and `443/tcp`;
- each upgrade creates a PostgreSQL and content-addressed object backup first;
- a failed candidate automatically attempts to restore the previous exact release;
- database restoration during rollback requires an explicit dump argument;
- the watchdog verifies edge health, API readiness, identity boundary and minimum free disk;
- backup and watchdog schedules are systemd timers, not manual calendar promises.
- deployment automation records `DEPLOYED_AWAITING_ACCEPTANCE`, never the reserved acceptance state.

## Acceptance gate

```json
{
  "ansible_syntax": true,
  "ubuntu_24_04_guard": true,
  "exact_sha_only": true,
  "private_environment_mode": "0600",
  "plaintext_password_committed_or_logged": false,
  "temporary_password_file_mode": "0600",
  "credentials_generated_on_authorised_host": true,
  "temporary_password_rotation_required": true,
  "traefik_public_port_owner": true,
  "axignal_loopback_only": true,
  "firewall_allowlist": ["ssh", "80/tcp", "443/tcp"],
  "pre_change_backup": true,
  "postgres_backup": true,
  "object_store_backup": true,
  "rollback_previous_release": true,
  "explicit_database_restore": true,
  "https_verification": true,
  "authenticated_demo_verification": true,
  "watchdog_timer": true,
  "backup_timer": true,
  "public_launch": false,
  "deployment_state": "DEPLOYED_AWAITING_ACCEPTANCE",
  "acceptance_status": "BLOCKED"
}
```

## Remaining external gate

The reserved acceptance state can only be declared after the reviewed PR is merged, the exact canonical SHA is deployed to the authorised VPS, both pending emails are confirmed, credential rotation and handoff finish, and Issue #31 contains redacted physical evidence for TLS, Traefik connectivity, tenant resolution, authenticated access, persistence, recovery and exact-SHA traceability. CI validates automation and recovery contracts but cannot fabricate host access or independent acceptance.
