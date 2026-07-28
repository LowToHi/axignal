# Remote Pilot Operations

Version: `0.2.0-candidate`
Status: `IMPLEMENTED / CI EVIDENCE REQUIRED / NOT DEPLOYED`
Goal ID: `AXIGNAL-GOAL-001`
Task: `AX-F2-T16`
Decision: `ADR-011`

## Scope and authority

This runbook prepares the private AXIGNAL pilot for the authorised Ubuntu 24.04 VPS at `187.124.220.48` and the hostname `pilot.axignal.com`.

It does not authorise a VPS mutation, public launch, billing, live sources, customer data, Issue #31 closure or an independent acceptance decision. Deployment remains blocked until:

- this change is reviewed and merged;
- the exact merged SHA is selected;
- the ACME contact email is confirmed;
- the initial operator email is confirmed;
- DNS resolves to the authorised host;
- the operator explicitly starts the physical deployment procedure.

## Invariants

- Traefik remains the exclusive owner of host ports `80/tcp` and `443/tcp`.
- AXIGNAL Caddy publishes only `127.0.0.1:<configured-high-port>:80`.
- AXIGNAL adds only `/etc/traefik/dynamic/axignal-pilot.yml`.
- AXIGNAL automation does not restart Traefik or modify unrelated routes.
- UUID, passwords and service secrets are generated only on the authorised host.
- Secret values never appear in arguments, terminal output, logs, CI artifacts, screenshots, evidence or messages.
- All private files are created under `umask 077`, owned by `root` and verified as mode `0600`.
- A deployment may write only `DEPLOYED_AWAITING_ACCEPTANCE`.
- `REMOTE_PILOT_ACCEPTED` is reserved for the independent Issue #31 gate.

## 1. Prepare the controller

Install only the pinned controller dependencies:

```bash
python -m pip install ansible-core==2.18.7
ansible-galaxy collection install -r infra/pilot/remote/requirements.yml
cp infra/pilot/remote/inventory.example.ini infra/pilot/remote/inventory.ini
```

Set the inventory host to `187.124.220.48`, retain `ansible_user=root` only for initial provisioning, and pin the SSH host key. Do not disable host-key checking.

The controller must not contain the tenant UUID, operator password, generated environment or service secrets.

## 2. Confirm the shared-edge preflight

Before any mutation, verify:

- Ubuntu is `24.04` or newer;
- the approved Traefik container is running with host networking;
- Traefik owns public ports `80/443`;
- `/etc/traefik/dynamic` is the active file-provider directory;
- the confirmed ACME email matches the existing Traefik certificate resolver;
- `127.0.0.1:18080` or the selected high port is available;
- existing services are healthy;
- the exact merged SHA is reachable;
- DNS and TLS inputs are confirmed.

Do not stop Traefik to free a port. A failed preflight blocks deployment.

## 3. Run the bootstrap and exact-SHA deployment

After all external gates are satisfied:

```bash
cd infra/pilot/remote
ANSIBLE_CONFIG=ansible.cfg ansible-playbook -i inventory.ini playbook.yml \
  -e axignal_deploy_sha=<approved-40-character-sha> \
  -e axignal_site_address=https://pilot.axignal.com \
  -e axignal_acme_email=<confirmed-acme-email> \
  -e axignal_auth_email=<confirmed-operator-email> \
  -e axignal_auth_subject=usr_pilot_operator \
  -e axignal_edge_mode=shared-traefik \
  -e axignal_internal_http_port=18080 \
  -e axignal_traefik_container_name=traefik-aiwf-traefik-1 \
  -e axignal_traefik_dynamic_dir=/etc/traefik/dynamic \
  -e axignal_traefik_entrypoint=websecure \
  -e axignal_traefik_cert_resolver=letsencrypt
```

The playbook copies the credential generator to the target, sets `umask 077`, generates the UUID and secrets on that host, validates root ownership and mode `0600`, renders the isolated Traefik route, deploys the exact SHA, executes unauthenticated and authenticated smoke tests and enables the backup and watchdog timers.

The playbook never rewrites the Traefik ACME account. A mismatched contact, entrypoint, resolver or file-provider directory blocks deployment and requires a separate reviewed infrastructure change.

The temporary plaintext operator password remains only at:

```text
/etc/axignal/private/operator-password.pending
```

Do not print or copy it through Ansible output. Secure delivery is a separate human-controlled operation.

## 4. Verify topology and non-sensitive metadata

Allowed checks:

```bash
sudo ss -ltnp
sudo stat -c '%U %G %a %n' \
  /etc/axignal/pilot.env \
  /etc/axignal/private/operator-password.pending \
  /var/lib/axignal/ops/credential-metadata.json
sudo systemctl status axignal-pilot-backup.timer
sudo systemctl status axignal-pilot-watchdog.timer
sudo cat /var/lib/axignal/ops/current.json
sudo cat /var/lib/axignal/ops/watchdog.json
```

Required results:

- Traefik still owns `80/443`;
- AXIGNAL exposes only the selected port on `127.0.0.1`;
- private files are root-owned and mode `0600`;
- the health payload contains the exact deployed SHA;
- the state is `DEPLOYED_AWAITING_ACCEPTANCE`;
- `acceptance_status` is `BLOCKED`.

Never display the environment or either password file.

## 5. First access, rotation and secure handoff

The temporary password is marked `rotation_required: true`. Deliver it using an approved out-of-band secret channel without logging or capturing its value. After the operator completes the first authenticated access, rotate immediately:

```bash
sudo /usr/local/sbin/axignal-remote-rotate-operator
```

This command:

- generates a new high-entropy password on the host;
- replaces only the Scrypt verifier in the root-only environment;
- rotates the web session secret and invalidates sessions created with the temporary credential;
- consumes the temporary password file;
- recreates only the AXIGNAL web service;
- verifies authenticated access with the rotated password;
- records non-sensitive lifecycle metadata.

The rotated plaintext exists temporarily at:

```text
/etc/axignal/private/operator-password.rotated
```

Deliver it through the approved secret channel. After the recipient confirms authenticated access, retire the plaintext file:

```bash
sudo /usr/local/sbin/axignal-remote-retire-operator-credential \
  /etc/axignal/private/operator-password.rotated
```

Verify only file absence and metadata status. Credential creation, rotation, handoff and retirement are not deployment or acceptance evidence.

## 6. Physical verification

Run the remote verifier without printing credentials:

```bash
sudo /usr/local/sbin/axignal-remote-verify \
  /opt/axignal/current \
  /etc/axignal/private/operator-password.rotated
```

Collect non-sensitive evidence for:

- external HTTPS health and exact SHA;
- internal API readiness;
- unauthenticated identity boundary;
- authenticated demo;
- tenant resolution;
- persistent PostgreSQL and object-store state;
- loopback Caddy connectivity through Traefik;
- security headers;
- scheduled backup and watchdog state;
- successful restore rehearsal.

Evidence must not contain cookies, password values, environment contents or direct personal contact data.

## 7. Upgrade

An approved upgrade uses:

```bash
sudo /usr/local/sbin/axignal-remote-deploy <new-approved-sha>
```

The command rejects an unsupported edge mode, takes an exclusive lock, verifies candidate contracts, backs up the current state, deploys the exact SHA and rolls back the previous compatible release on failure.

## 8. Rollback

Redeploy the recorded compatible release without changing data:

```bash
sudo /usr/local/sbin/axignal-remote-rollback previous
```

Restore a database only from an explicitly reviewed dump:

```bash
sudo /usr/local/sbin/axignal-remote-rollback <previous-sha> \
  /var/backups/axignal/<backup-set>/database.dump
```

For full pilot removal, stop only the `axignal-pilot` Compose project and remove only:

```text
/etc/traefik/dynamic/axignal-pilot.yml
```

Do not stop or restart Traefik. Verify every pre-existing route and container after rollback.

## 9. Acceptance boundary

CI validates automation, syntax, loopback binding, secret handling and recovery contracts. It cannot produce physical deployment evidence.

The deployment helper intentionally records:

```json
{
  "status": "DEPLOYED_AWAITING_ACCEPTANCE",
  "acceptance_status": "BLOCKED"
}
```

Issue #31 may be updated only with redacted, reproducible physical evidence. An independent reviewer decides whether the reserved acceptance state can be declared.
