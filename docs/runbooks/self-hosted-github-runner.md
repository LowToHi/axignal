# AXIGNAL Self-Hosted GitHub Runner Runbook

Status: `CANDIDATE / DO NOT EXECUTE AS ROOT`
Host: `187.124.220.48`

## Security boundary

The SSH administration account may be `root`, but the GitHub Actions runner process MUST run under a dedicated unprivileged user such as `axignal-runner`.

The host is for CI, tests and benchmarks. It MUST NOT contain production databases, production credentials, customer data or unrestricted deployment keys.

Provisioning MUST stop before runner registration when the host contains production or unrelated stateful workloads. A dedicated Linux user, rootless Docker or filesystem permissions reduce blast radius but do not make production/CI colocation compliant.

## Mandatory preflight

Run as the administrative account without printing environment values or file contents:

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

Fail closed if any of the following is true:

- production or unrelated persistent databases, applications or credentials are present;
- the runner would require `/var/run/docker.sock` or membership in the rootful `docker` group;
- the host cannot reserve sufficient CPU, memory and disk for bounded CI workloads;
- outbound access, patching, cleanup or incident isolation cannot be demonstrated.

## Provisioning outline

1. Patch the operating system and enable unattended security updates.
2. Create `axignal-runner` with no interactive password and a dedicated home directory.
3. Configure a firewall allowing only required SSH administration and outbound GitHub/container/package traffic.
4. Install Docker in rootless mode for the runner account; do not grant access to `/var/run/docker.sock`.
5. Register the runner with repository labels:
   - `self-hosted`
   - `linux`
   - `x64`
   - `axignal-ci`
6. Install the runner as a service owned by `axignal-runner`.
7. Configure workspace cleanup after every job.
8. Add disk, CPU, memory, runner queue and job-duration telemetry.
9. Configure runner update monitoring and a tested unregister/re-register procedure.

The repository acceptance controls are:

- `.github/workflows/runner-acceptance.yml`;
- `scripts/runner/verify-host-boundary.sh`;
- `scripts/runner/cleanup-workdir.sh`.

Configure `scripts/runner/cleanup-workdir.sh` as the `ACTIONS_RUNNER_HOOK_JOB_STARTED` and `ACTIONS_RUNNER_HOOK_JOB_COMPLETED` hook only after verifying that `/home/axignal-runner/actions-runner/_work` is the exact runner work directory. The script refuses any other target.

## Workflow trust policy

### Untrusted pull requests

Untrusted fork or external pull-request code MUST NOT run on the persistent self-hosted runner.

Allowed options:

- lightweight GitHub-hosted validation;
- static metadata checks without checking out untrusted code;
- explicit maintainer-approved trusted branch before self-hosted execution.

### Trusted workloads

The self-hosted runner MAY execute:

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
- no host Docker socket unless the workflow is trusted and the risk accepted;
- no access to other job workspaces;
- explicit network policy when testing untrusted source payloads.

## Initial acceptance test

The runner gate passes when a trusted workflow:

1. checks out the repository;
2. validates naming, schemas, registry and OpenAPI;
3. starts disposable PostgreSQL/PostGIS/pgvector and Valkey services;
4. executes a synthetic integration test;
5. destroys containers and workspace;
6. leaves no secret, process or writable artifact outside the approved cache;
7. reports resource and duration metrics.

The acceptance workflow is manual-only (`workflow_dispatch`) and has `contents: read`. It must be dispatched from a trusted repository revision after the runner is online. Pull-request events, especially forks, never target the persistent runner.

## Incident response

On suspected compromise:

1. disable or remove the runner in GitHub immediately;
2. stop the service and isolate the host;
3. revoke all credentials accessible to the job;
4. preserve relevant logs;
5. rebuild the host from a trusted image rather than attempting in-place cleanup;
6. record the incident under the AXIGNAL severity model.
