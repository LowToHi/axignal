# AXIGNAL Actions Storage Governance

## 1. Authority and purpose

This document governs GitHub Actions artifact retention, storage reclamation and the isolated `axignal-trusted` self-hosted runner.

The purpose is to stop uncontrolled storage growth without deleting contractual E2E evidence or exposing the public repository to a persistent runner.

Canonical evidence remains defined by:

- `docs/contracts/AX-GE2E-FINISH-003.md`;
- `docs/roadmap/AXIGNAL_E2E_FINISH_LEDGER.json`;
- explicit protected artifact and run identifiers in `config/actions-storage-policy.json`;
- the exact `main` SHA and every open pull-request head SHA at audit time.

## 2. Observed baseline

The remediation started after the repository reached approximately:

```text
artifact_count        55,001
stored_mib            11,193.8 before initial reclamation
initial_freed_mib     314.674
estimated_after_mib   10,879.13
active_workflows      141
```

The initial deletion was independently verified through `404` responses for all six removed workflow runs. It validated the deletion mechanism, but did not solve the structural production of artifacts.

## 3. Non-negotiable controls

```text
destructive cleanup default       DISABLED
scheduled heuristic deletion      FORBIDDEN
issue-triggered deletion           FORBIDDEN
public PR on self-hosted runner    FORBIDDEN
artifact retention without value   FORBIDDEN once enforcement is enabled
canonical evidence deletion        FORBIDDEN
```

`actions-storage-governance.yml` is audit-only. Its token permissions are limited to:

```yaml
permissions:
  actions: read
  contents: read
```

No workflow in this governance layer calls a GitHub `DELETE` endpoint and no audit report is uploaded as an Actions artifact.

## 4. Artifact classes

### 4.1 Ephemeral

Temporary build and test output that can be reproduced.

Maximum retention:

```text
1 day
```

### 4.2 Diagnostic

Coverage, Playwright, screenshots, traces, videos, browser output and temporary E2E diagnostics.

Maximum retention:

```text
2 days
```

### 4.3 Contractual

Attestations, canonical contracts, certificates, closure bundles, evidence bundles, manifests, provenance, restore evidence, SBOMs and signatures.

Maximum ordinary retention:

```text
30 days
```

Contractual evidence referenced by a canonical authority is protected independently of its name or ordinary retention tier.

## 5. Tooling

### 5.1 Static and remote audit

```bash
python3 scripts/ops/audit_actions_storage.py
```

Complete remote inventory with a token that has Actions read access:

```bash
GH_TOKEN=... python3 scripts/ops/audit_actions_storage.py \
  --inventory-artifacts \
  --max-pages 0
```

The auditor:

- scans every workflow YAML;
- detects `actions/upload-artifact` in expanded and compact step forms;
- records explicit, missing, dynamic and excessive `retention-days`;
- counts `actions/cache` usage;
- detects self-hosted labels exposed to public PR events;
- inventories all artifacts when requested;
- normalizes SHA, digest, timestamp and numeric suffixes into artifact families;
- reports counts and bytes by class and family;
- derives protected IDs, runs and SHAs from canonical authorities;
- never mutates GitHub.

### 5.2 Retention migration

Dry-run:

```bash
python3 scripts/ops/migrate_actions_artifact_retention.py
```

Apply after reviewing the dry-run report:

```bash
python3 scripts/ops/migrate_actions_artifact_retention.py --apply
```

The migrator changes only recognized `actions/upload-artifact` `with:` mappings. It:

- inserts a missing `retention-days`;
- reduces a numeric value above the class maximum;
- preserves values already inside policy;
- rejects dynamic or malformed values;
- does not modify workflow triggers, jobs, commands or artifact paths.

### 5.3 Regression tests

```bash
python3 tests/ops/test_actions_storage_policy_tools.py
```

The suite covers compact upload steps, missing retention, retention reduction, diagnostic classification, dynamic-value rejection and artifact-family normalization.

## 6. Trusted runner design

The runner is isolated from any LowToHi runner:

```text
user          runner-axignal
install       /opt/actions-runner-axignal
work          /var/lib/axignal-runner/work
cache         /var/cache/axignal
logs          /var/log/axignal-runner
labels        self-hosted, linux, x64, axignal, trusted
cache budget  25 GiB
```

Pinned runner release:

```text
version  2.336.0
sha256   04cf0be1aff4c3ec3554466c39124ca250e3effd8873bb7e8d68535aa9505d5d
```

Preparation without registration:

```bash
sudo REGISTER_RUNNER=false \
  bash scripts/ops/install_axignal_trusted_runner.sh
```

Expected marker:

```text
AXIGNAL_TRUSTED_RUNNER_PREPARED=PASS
AXIGNAL_TRUSTED_RUNNER_REGISTERED=NO
```

Registration is permitted only after trusted workflows are migrated and reviewed:

```bash
sudo REGISTER_RUNNER=true \
  RUNNER_REGISTRATION_TOKEN=... \
  bash scripts/ops/install_axignal_trusted_runner.sh
```

The pre-job hook blocks:

- repositories other than `LowToHi/axignal`;
- `pull_request` and `pull_request_target` events;
- jobs while the local cache storage guard is blocked.

Docker access is disabled by default. `ALLOW_DOCKER=true` is an explicit, security-sensitive opt-in because membership in the Docker group is root-equivalent on the host.

## 7. Cache policy

The local cache guard runs hourly and after each job:

```text
below 70%   no deletion
70%+        remove files not accessed for 14 days
85%+        remove files not accessed for 3 days
92%+        create BLOCKED_STORAGE and reject new jobs
```

Managed roots:

```text
/var/cache/axignal/npm
/var/cache/axignal/pnpm
/var/cache/axignal/pip
/var/cache/axignal/playwright
/var/cache/axignal/buildkit
```

This local cache does not replace GitHub artifact retention. Any continued use of `actions/upload-artifact` still consumes GitHub Actions storage.

## 8. Required rollout order

```text
1. Merge audit-only governance.
2. Execute complete static audit.
3. Execute retention migration dry-run.
4. Resolve every rejected ambiguous step manually.
5. Apply retention migration.
6. Re-run static audit until violations are zero.
7. Migrate only trusted, heavy exact-head jobs to axignal-trusted labels.
8. Prepare runner without registration.
9. Verify pre-job, post-job and cache guards.
10. Register runner with a one-time registration token.
11. Execute a complete remote artifact inventory.
12. Review the protected and candidate pools.
13. Perform a separately authorized reclamation run.
14. Verify every deletion through 404 and preserve the JSON report.
```

## 9. Closure gates

The structural storage phase is closed only when all markers are supported by evidence:

```text
AXIGNAL_ACTIONS_STORAGE_STATIC_AUDIT=PASS
AXIGNAL_ACTIONS_RETENTION_MIGRATION=PASS
AXIGNAL_ACTIONS_STORAGE_AUDIT_ONLY=PASS
AXIGNAL_TRUSTED_RUNNER_PREPARED=PASS
AXIGNAL_TRUSTED_RUNNER_SECURITY_GUARD=PASS
AXIGNAL_ACTIONS_STORAGE_REMOTE_INVENTORY=PASS
AXIGNAL_ACTIONS_STORAGE_STRUCTURAL_RECLAMATION=PASS
```

Until then:

```text
AXIGNAL_ACTIONS_STORAGE_STRUCTURAL_GOVERNANCE=IN_PROGRESS
```
