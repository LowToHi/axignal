# AXIGNAL Self-Hosted GitHub Runner Runbook

Status: `HYBRID CI / SHARED BUILD RUNNER CANDIDATE`
Application host candidate: `187.124.220.48`
Shared build runner: `axignal-build-01`
Dedicated integration runner: `NOT ASSIGNED`

## Scope boundary

This runbook governs CI runners only. It does **not** prohibit AXIGNAL from using `187.124.220.48` for application hosting, staging, APIs, workers, PostgreSQL/PostGIS/pgvector, Valkey or other product services.

The current VPS may host AXIGNAL application services after normal deployment hardening. Its shared workload topology is compatible with a restricted non-privileged build runner, but not with a Docker-capable CI runner that controls the host daemon.

GitHub-hosted CI remains the canonical fallback and the default for untrusted code and Docker-backed integration.

## Approved hybrid topology

```text
187.124.220.48
├── existing application services and databases
├── existing LowToHi runner boundary
└── axignal-build-01
    ├── user: axignal-runner
    ├── no root
    ├── no Docker socket or docker group
    ├── no application networks or volumes
    ├── no product or production secrets
    └── build, typecheck, Playwright and FastAPI only

GitHub-hosted runners
├── untrusted pull requests
├── contract validation
├── PostgreSQL/PostGIS/pgvector integration
├── Valkey integration
└── fallback for every AXIGNAL CI job
```

Removing `iamancha.com` is not required for this topology. It would free capacity but would not replace the isolation controls.

## Shared build runner preflight

The administrative account may be `root`, but the runner MUST execute as `axignal-runner`.

Verify without printing secrets:

```bash
id
cat /etc/os-release
free -h
df -h /
systemctl list-units --type=service --all 'actions.runner.*'
docker ps --format '{{.Names}}|{{.Image}}|{{.Status}}|{{.Ports}}'
```

The shared build runner gate fails if:

- it executes as `root`;
- it belongs to `sudo` or the rootful `docker` group;
- it can read or write `/var/run/docker.sock`;
- it can access product secret files, persistent volumes or application Docker networks;
- trusted internal revisions cannot be enforced;
- bounded CPU, memory, disk, cleanup and fallback cannot be demonstrated.

Existing application containers and databases do not fail this build-runner gate by themselves because the runner is not allowed to control or join them.

## Shared build runner provisioning

1. Preserve an inventory of all current services and networks.
2. Create `axignal-runner` with a dedicated home, no interactive password, no `sudo` and no rootful Docker membership.
3. Prefer an isolated runner container or VM. A systemd-sandboxed process is acceptable only when equivalent filesystem, network and privilege boundaries are demonstrated.
4. Do not mount `/var/run/docker.sock`, `/var/lib/docker`, application volumes, `/etc/traefik`, SSH keys or project `.env` files.
5. Place the runner under `/home/axignal-runner/actions-runner` with work directory `_work`.
6. Register it as `axignal-build-01` with labels:
   - `self-hosted`
   - `linux`
   - `x64`
   - `axignal-build`
7. Configure workspace cleanup before and after every job.
8. Limit CPU, memory, process count and writable disk.
9. Execute `scripts/runner/verify-shared-build-boundary.sh` before any build.
10. Run `.github/workflows/shared-build-runner-acceptance.yml` from a trusted revision.
11. Disable the runner immediately when acceptance fails; GitHub-hosted CI remains active.

## Allowed workloads

The shared build runner MAY execute:

- frozen pnpm installation;
- strict TypeScript;
- Next.js product and landing builds;
- Playwright browser suites;
- FastAPI lint and unit tests;
- non-privileged benchmarks;
- trusted internal revisions only.

It MUST NOT execute:

- Docker or Compose commands;
- database migration or restore tests;
- workflows containing product secrets;
- fork or external pull-request code;
- deployment commands;
- jobs requiring access to product networks or persistent data.

## Dedicated integration runner

Docker, PostGIS/pgvector/Valkey integration, migration, restore and other privileged workloads MAY move to a future runner labelled `axignal-ci` only inside a dedicated host or strongly isolated VM with rootless Docker.

The existing `.github/workflows/runner-acceptance.yml` and `scripts/runner/verify-host-boundary.sh` govern that future tier.

## Secret policy

- No personal access token from an individual account.
- Minimum GitHub token permissions.
- No production SSH key, `.env` file, database credential or unrestricted deployment key.
- No inherited environment values from application services.
- Logs and artifacts MUST be reviewed for accidental leakage.

## Acceptance evidence

`axignal-build-01` passes only when a trusted acceptance run proves:

1. exact runner name and labels;
2. non-root `axignal-runner` identity;
3. no rootful Docker socket or group access;
4. no forbidden environment variable, key path or product mount;
5. frozen install, typecheck, builds, Playwright and FastAPI tests passing;
6. bounded CPU, memory, disk and duration;
7. empty workspace and no residual processes after completion;
8. GitHub-hosted fallback still passes with the runner disabled.

## Incident response and rollback

1. Disable the runner in GitHub.
2. Stop its service or isolated container without changing application workloads.
3. Revoke short-lived registration material.
4. Preserve logs if compromise is suspected.
5. Remove only the exact runner boundary and work directory.
6. Re-run GitHub-hosted Contract Validation and Executable Spine.
7. Rebuild a compromised runner boundary rather than cleaning it in place.
