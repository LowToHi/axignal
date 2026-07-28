# Remote Pilot Operations

## Scope

This runbook deploys the private AXIGNAL pilot to a single Ubuntu 24.04 VPS. It is not a public-production runbook.

## 1. Prepare controller dependencies

```bash
python -m pip install ansible-core==2.18.7
ansible-galaxy collection install -r infra/pilot/remote/requirements.yml
cp infra/pilot/remote/inventory.example.ini infra/pilot/remote/inventory.ini
```

Pin the VPS SSH host key before the first run. Do not disable host-key checking.

## 2. Generate secrets outside the repository

```bash
python infra/pilot/remote/prepare_env.py \
  --output /secure/axignal-pilot.env \
  --sha <approved-40-character-sha> \
  --site-address https://pilot.example.com \
  --acme-email operator@example.com \
  --auth-email operator@example.com \
  --auth-subject usr_pilot_operator \
  --tenant-id <pilot-tenant-uuid> \
  --operator-password '<temporary-operator-password>'
```

The resulting file must remain `0600`. The plaintext operator password is not stored in it. Store the plaintext temporarily in another `0600` file only when an authenticated smoke test is required.

## 3. Bootstrap and deploy

```bash
cd infra/pilot/remote
ANSIBLE_CONFIG=ansible.cfg ansible-playbook -i inventory.ini playbook.yml \
  -e axignal_deploy_sha=<approved-40-character-sha> \
  -e axignal_env_source=/secure/axignal-pilot.env \
  -e axignal_site_address=https://pilot.example.com \
  -e axignal_operator_password_source=/secure/operator-password
```

The playbook installs Docker, configures UFW, copies root-only operations tooling, deploys the exact SHA, checks HTTPS and enables the backup and watchdog timers.

## 4. Verify on the host

```bash
sudo /usr/local/sbin/axignal-remote-verify /opt/axignal/current /secure/operator-password
sudo systemctl status axignal-pilot-backup.timer
sudo systemctl status axignal-pilot-watchdog.timer
sudo cat /var/lib/axignal/ops/current.json
sudo cat /var/lib/axignal/ops/watchdog.json
```

The deployment state must report `REMOTE_PILOT_ACCEPTED` and the exact approved SHA.

## 5. Upgrade

```bash
sudo /usr/local/sbin/axignal-remote-deploy <new-approved-sha> /secure/operator-password
```

The command takes an exclusive deployment lock, verifies the candidate contracts, backs up the active database and object volume, deploys the candidate and switches `/opt/axignal/current` only after successful verification.

## 6. Rollback

Redeploy the recorded previous release without changing data:

```bash
sudo /usr/local/sbin/axignal-remote-rollback previous '' /secure/operator-password
```

Restore a database dump only when explicitly required and reviewed:

```bash
sudo /usr/local/sbin/axignal-remote-rollback <previous-sha> \
  /var/backups/axignal/<backup-set>/database.dump \
  /secure/operator-password
```

## 7. Backups and retention

The backup timer creates both:

- a PostgreSQL custom-format dump;
- a compressed archive of the content-addressed object volume.

Each file receives SHA-256 evidence and a manifest. The default retention is 14 days and can be changed through the Ansible variable `axignal_backup_retention_days`.

## 8. Monitoring

The watchdog runs every five minutes and fails when:

- the public edge health response is invalid;
- the deployed SHA differs from the expected SHA;
- required security headers are missing;
- PostgreSQL, Valkey or object storage is not ready;
- the unauthenticated demo does not enforce the identity boundary;
- free disk falls below `axignal_min_free_gb`.

Docker remains responsible for bounded service restart. The watchdog records evidence and exits non-zero; it does not mutate canonical data or silently redeploy another release.
