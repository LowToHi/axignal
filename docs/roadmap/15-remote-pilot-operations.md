# Remote Pilot Operations v0.1

## Status

`IMPLEMENTED / CI-GATED / NOT DEPLOYED / PRIVATE PILOT ONLY`

## Objective

Turn the local Pilot Deployment Candidate into an exact-SHA remote deployment and recovery system for an Ubuntu 24.04 VPS. This unit does not authorise a public launch, billing, live sources, customer data or the F1 human campaign.

## Operational path

```text
controller
→ root-only environment generation
→ Ansible host bootstrap
→ UFW allowlist
→ exact-SHA release fetch
→ candidate contract verification
→ pre-change backup
→ Docker Compose deployment
→ HTTPS and authenticated demo smoke test
→ immutable deployment state
→ watchdog and scheduled backup timers
```

## Invariants

- only a full 40-character commit SHA may be deployed;
- the private environment file is copied with mode `0600` and never committed;
- the plaintext operator password is used only for an optional smoke test and removed from `/run`;
- UFW denies inbound traffic except the configured SSH port, `80/tcp` and `443/tcp`;
- each upgrade creates a PostgreSQL and content-addressed object backup first;
- a failed candidate automatically attempts to restore the previous exact release;
- database restoration during rollback requires an explicit dump argument;
- the watchdog verifies edge health, API readiness, identity boundary and minimum free disk;
- backup and watchdog schedules are systemd timers, not manual calendar promises.

## Acceptance gate

```json
{
  "ansible_syntax": true,
  "ubuntu_24_04_guard": true,
  "exact_sha_only": true,
  "private_environment_mode": "0600",
  "plaintext_password_persisted": false,
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
  "public_launch": false
}
```

## Remaining external gate

`REMOTE_PILOT_ACCEPTED` can only be declared after running the playbook against the real VPS with the real domain, TLS certificate and private secrets. CI validates the automation and recovery contracts but cannot fabricate host access.
