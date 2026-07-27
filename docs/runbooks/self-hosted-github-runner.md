# AXIGNAL Self-Hosted GitHub Runner Runbook

Status: `OPTIONAL / DEFERRED / DO NOT EXECUTE AS ROOT`
Runner host: `NO COMPLIANT HOST ASSIGNED`
Application host candidate: `187.124.220.48`

## Scope boundary

This runbook governs only a persistent self-hosted GitHub Actions runner for trusted CI, tests and benchmarks.

It does **not** prohibit AXIGNAL from using `187.124.220.48` for application hosting, staging, APIs, workers, PostgreSQL/PostGIS/pgvector, Valkey or other product services. Those workloads are governed by the deployment, security and operations contracts applicable to the product environment.

The current server remains eligible as an AXIGNAL application or staging host after normal deployment hardening. It is not approved, in its present shared state, as a persistent self-hosted CI runner with Docker control.

GitHub-hosted runners remain the canonical and sufficient CI path. A self-hosted runner is an optional optimisation for heavy trusted workloads; its absence does not block product development, testing, review, deployment or operation.

## Security boundary

The SSH administration account may be `root`, but the GitHub Actions runner process MUST run under a dedicated unprivileged user such as `axignal-runner`.

A runner host or isolated runner VM is for CI, tests and benchmarks. It MUST NOT contain production databases, production credentials, customer data or unrestricted deployment keys.

Runner provisioning MUST stop before registration when the proposed runner boundary contains production or unrelated stateful workloads. A dedicated Linux user, rootless Docker or filesystem permissions reduce blast radius but do not make production/CI colocation compliant.

A strongly isolated virtual machine on a shared physical server MAY qualify when it has an independent operating system, storage, network policy, Docker daemon, resource limits and no access to host or product secrets.

## Mandatory runner preflight

Run against the proposed runner host or isolated VM as the administrative account without printing environment values or file contents:

```bash
id
cat /etc/os-release
systemctl list-units --type=service --all 'actions.runner.*'
docker ps --format '{{.Names}}|{{.Image}}|{{.Status}}|{{.Ports}}'
df -h /
free -h
systemctl is-active unattended-upgrades
ufw status
```

Fail closed for runner registration if any of the following is true:

- production or unrelated persistent databases, applications or credentials are present inside the runner boundary;
- the runner would require `/var/run/docker.sock` or membership in the rootful `docker` group;
- the boundary cannot reserve sufficient CPU, memory and disk for bounded CI workloads;
- outbound access, patching, cleanup or incident isolation cannot be demonstrated.

A failed runner preflight does not reject the server as an AXIGNAL application host. It rejects only that runner topology.

## Canonical CI path

Until a compliant runner boundary exists:

- Contract Validation runs on GitHub-hosted runners;
- Executable Spine runs on GitHub-hosted runners;
- builds, Playwright, FastAPI, PostgreSQL/PostGIS/pgvector and Valkey tests continue there;
- development and merge readiness do not depend on self-hosted acceptance;
- `.github/workflows/runner-acceptance.yml` remains dormant and manual-only.

## Optional runner provisioning outline

Provision only after a repeated preflight proves that the runner boundary is dedicated or strongly isolated. Keep the one-time registration token in an interactive shell variable; never place it in shell history, a file, process arguments, logs or repository content.

1. Patch the operating system and enable unattended security updates.
2. Create `axignal-runner` as a system account with `/home/axignal-runner`, no password and no membership in `sudo` or rootful `docker`.
3. Configure a default-deny inbound firewall allowing only the existing administrative SSH path. Do not interrupt the current administrative session.
4. Install Docker in rootless mode for `axignal-runner`; verify that its client targets the user socket and cannot read or write `/var/run/docker.sock`.
5. Download the current GitHub Actions runner release from GitHub, verify its published SHA-256 checksum and extract it under `/home/axignal-runner/actions-runner`.
6. Register it at repository scope as `axignal-ci-01` with:
   - `self-hosted`
   - `linux`
   - `x64`
   - `axignal-ci`
7. Install the runner service and prove its `User=` is exactly `axignal-runner`.
8. Copy the reviewed cleanup hook outside `_work`, owned and writable only by `axignal-runner`:

   ```text
   /home/axignal-runner/actions-runner/hooks/cleanup-workdir.sh
   ```

9. Set both `ACTIONS_RUNNER_HOOK_JOB_STARTED` and `ACTIONS_RUNNER_HOOK_JOB_COMPLETED` to that absolute path in the runner service environment.
10. Add disk, CPU, memory, runner queue and job-duration monitoring.
11. Dispatch `.github/workflows/runner-acceptance.yml` only from a trusted immutable revision.
12. Keep the runner disabled if either acceptance job fails.

The repository acceptance controls are:

- `.github/workflows/runner-acceptance.yml`;
- `scripts/runner/verify-host-boundary.sh`;
- `scripts/runner/cleanup-workdir.sh`.

Install a reviewed copy of `scripts/runner/cleanup-workdir.sh` at the hook path above. Configure it as both the `ACTIONS_RUNNER_HOOK_JOB_STARTED` and `ACTIONS_RUNNER_HOOK_JOB_COMPLETED` hook only after verifying that `/home/axignal-runner/actions-runner/_work` is the exact runner work directory. The script refuses any other target.

The completed-job hook is independently checked by the second acceptance job, which runs without checkout and requires the previous workspace to be empty.

## Workflow trust policy

### Untrusted pull requests

Untrusted fork or external pull-request code MUST NOT run on a persistent self-hosted runner.

Allowed options:

- GitHub-hosted validation;
- static metadata checks without checking out untrusted code;
- explicit maintainer-approved trusted branch before self-hosted execution.

### Trusted workloads

A compliant self-hosted runner MAY execute:

- container builds;
- Playwright browser suites;
- integration tests;
- database migration and restore tests;
- benchmark fixtures;
- Remotion rendering tests;
- dependency and contract validation;
- trusted branch or manually authorised workflows.

## Secret policy

- No personal access token from an individual account.
- Minimum GitHub token permissions.
- No production SSH key or production `.env` file.
- Short-lived test credentials only.
- Secrets scoped by environment and workflow.
- Logs and artifacts MUST be reviewed for accidental secret or dataset leakage.

## Isolation requirements

Each heavy job SHOULD run in a disposable container with:

- read-only repository checkout where practical;
- bounded CPU and memory;
- bounded disk and artifact retention;
- no host Docker socket;
- no access to product databases, application secrets or other job workspaces;
- explicit network policy when testing untrusted source payloads.

## Initial acceptance test

The optional runner gate passes when a trusted workflow:

1. checks out the repository;
2. validates naming, schemas, registry and OpenAPI;
3. starts disposable PostgreSQL/PostGIS/pgvector and Valkey services;
4. executes synthetic integration tests;
5. destroys containers and workspace;
6. leaves no secret, process or writable artifact outside approved caches;
7. reports duration plus bounded CPU, memory, workspace and host-disk metrics;
8. schedules a second job that proves the completed-job hook left no checkout, test port, process, container, volume or forbidden credential path.

The acceptance workflow is manual-only (`workflow_dispatch`) and has `contents: read`. Pull-request events, especially forks, never target the persistent runner.

## Incident response

On suspected compromise:

1. disable or remove the runner in GitHub immediately;
2. stop the service and isolate the runner boundary;
3. revoke all credentials accessible to the job;
4. preserve relevant logs;
5. rebuild the boundary from a trusted image rather than attempting in-place cleanup;
6. record the incident under the AXIGNAL severity model.

## Rollback and deprovisioning

1. Disable the runner in GitHub before host changes.
2. Stop the runner service as the administrative account.
3. Unregister using a fresh short-lived removal token without logging it.
4. Preserve service and runner diagnostic logs when an incident is suspected.
5. Remove the dedicated runner directory and account only after their exact resolved paths and evidence-retention requirements are verified.
6. Rebuild a compromised runner boundary from a trusted image; do not return an in-place cleaned boundary to service.
