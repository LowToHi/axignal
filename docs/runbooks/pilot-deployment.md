# Private Pilot Deployment

## Status

This runbook creates a private deployment candidate for demonstrations. It does not authorise a public launch, production customer data, billing, live sources or the F1 participant campaign.

## Prerequisites

- Linux host with Docker Engine and Compose v2;
- a private domain pointing to the host for automatic TLS;
- an exact repository commit SHA;
- a private environment file derived from `infra/pilot/env.example`;
- firewall allowing only SSH, HTTP and HTTPS;
- backup destination outside the application volume.

## Secret preparation

Generate independent random values for every database runtime, the web session, identity assertion and participant salt. Generate the password Scrypt value with the repository authentication procedure. Never commit the resulting environment file.

## Preflight

```bash
python scripts/verify_pilot_candidate.py
python scripts/verify_demo_contract.py
docker compose --env-file /secure/axignal-pilot.env \
  -f infra/pilot/compose.yaml \
  -f infra/pilot/remote/compose.standalone.yaml config >/dev/null
```

The deployed `AXIGNAL_BUILD_SHA` must equal the checked-out commit.

## Start

```bash
docker compose --env-file /secure/axignal-pilot.env \
  -f infra/pilot/compose.yaml \
  -f infra/pilot/remote/compose.standalone.yaml up --build --detach --wait
```

The default topology starts PostgreSQL, credential rotation, persistent Valkey, API, web and Caddy. Start bounded workers only after the core is healthy:

```bash
docker compose --env-file /secure/axignal-pilot.env \
  -f infra/pilot/compose.yaml \
  -f infra/pilot/remote/compose.standalone.yaml --profile workers up --detach --wait
```

Observability is optional:

```bash
docker compose --env-file /secure/axignal-pilot.env \
  -f infra/pilot/compose.yaml \
  -f infra/pilot/remote/compose.standalone.yaml --profile observability up --detach
```

## Verification

- open `/api/health` through the configured domain;
- authenticate and open `/demo`;
- follow the six-step guide;
- verify the API internally with `/readyz`;
- verify no service except Caddy publishes host ports;
- verify live sources and validation UI remain disabled.

## Backup and restore

```bash
export AXIGNAL_PILOT_ENV_FILE=/secure/axignal-pilot.env
export AXIGNAL_PILOT_COMPOSE_EDGE_FILE=infra/pilot/remote/compose.standalone.yaml
bash infra/pilot/backup.sh /secure/backups/axignal-before-change.dump
bash infra/pilot/restore-rehearsal.sh
```

Keep the dump and its SHA-256 file outside Docker volumes. A deployment change is blocked when the restore rehearsal fails.

## Upgrade

1. create and verify a backup;
2. record the current commit and image digests;
3. check out the approved target SHA;
4. run preflight and Compose config validation;
5. rebuild and start with `--wait`;
6. verify health and the canonical demo;
7. retain the previous images and backup until the meeting cycle is complete.

## Rollback

Stop workers, redeploy the previous exact SHA and restore the pre-upgrade dump when schema or data compatibility requires it. Never reset or delete real pilot data using the browser demo reset; that control only removes the local synthetic shell state.

## Meeting package

Prepare the private URL, temporary operator credential, six-step demo script, architecture summary, current gate table, limitations, backup proof and a recorded fallback demonstration. State explicitly that human validation is deferred until after deployment and partner engagement.
