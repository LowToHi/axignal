# Private Pilot Deployment

## Status

This runbook creates an authenticated private deployment for demonstrations and
bounded design-partner use. `AX-F8-T14` authorises the exact
`ted-search-non-personal-projection@0.1.0` runtime in this pilot.

It does not authorise a public launch, public trial, billing, unrestricted TED
queries, another live source, complete XML procurement analysis or general
availability. Those remain governed by later gates, including `AX-F9-T15` and
F12.

## Prerequisites

- Linux host with Docker Engine and Compose v2;
- a private domain pointing to the host for automatic TLS;
- an exact accepted repository commit SHA;
- a private environment file derived from `infra/pilot/env.example`;
- firewall allowing only SSH, HTTP and HTTPS;
- backup destination outside the application volume;
- outbound HTTPS resolution from the dedicated `ted-egress` worker network.

## Secret preparation

Generate independent random values for every database runtime, the web session,
identity assertion and participant salt. Generate the password Scrypt value with
the repository authentication procedure. Never commit the resulting environment
file.

Identity assertions are internal server-to-server credentials with a maximum
lifetime of 300 seconds. They must remain behind TLS and the private backend
network.

## Preflight

```bash
python scripts/verify_pilot_candidate.py
python scripts/verify_demo_contract.py
python scripts/verify_ted_product_runtime.py
python scripts/verify_ted_security_review.py
docker compose --env-file /secure/axignal-pilot.env \
  -f infra/pilot/compose.yaml \
  -f infra/pilot/remote/compose.standalone.yaml config >/dev/null
```

The deployed `AXIGNAL_BUILD_SHA` must equal the checked-out accepted commit.

Confirm the rendered configuration contains:

```text
AXIGNAL_PERSISTENT_RESEARCH_ENABLED=true
AXIGNAL_TED_PROCUREMENT_ENABLED=true
AXIGNAL_TED_LIVE_SOURCES_ENABLED=true
AXIGNAL_TED_PROCUREMENT_UI_ENABLED=true
AXIGNAL_LIVE_SOURCES_ENABLED=false
```

The API, database, Valkey and web services must not join `ted-egress`. Only the
`research-worker` may join both `backend` and `ted-egress`.

## Start core

```bash
docker compose --env-file /secure/axignal-pilot.env \
  -f infra/pilot/compose.yaml \
  -f infra/pilot/remote/compose.standalone.yaml up --build --detach --wait
```

The core starts PostgreSQL, credential hardening, persistent Valkey, API, web
and the private edge. It does not expose PostgreSQL, Valkey or API host ports.

## Start the bounded TED worker

```bash
docker compose --env-file /secure/axignal-pilot.env \
  -f infra/pilot/compose.yaml \
  -f infra/pilot/remote/compose.standalone.yaml \
  --profile workers up --build --detach research-worker
```

Do not start another source worker merely because the `workers` profile exists.
The TED worker has outbound connectivity, but the connector itself still fixes
the HTTPS host, path, query, fields, page and response budget.

Observability is optional:

```bash
docker compose --env-file /secure/axignal-pilot.env \
  -f infra/pilot/compose.yaml \
  -f infra/pilot/remote/compose.standalone.yaml \
  --profile observability up --detach
```

## Verification

- open `/api/health` through the configured domain;
- authenticate and open `/demo`;
- create a `TED_PROCUREMENT` ResearchRun from Navigator;
- observe `QUEUED → RETRIEVING → PROPOSING → ADMISSION_PENDING → COMPLETED`;
- verify the dossier includes TED attribution and `api_redistribution=false`;
- verify `model_calls=0`;
- verify a different tenant receives no ResearchRun;
- verify no service except the private edge publishes host ports;
- verify the global live-source flag remains disabled;
- execute the workflow and source kill-switch tests before partner access.

A live TED failure must produce a bounded failed ResearchRun. It must not fall
back to a fixture, arbitrary browsing, another source or a model-generated
answer.

## Backup and restore

```bash
export AXIGNAL_PILOT_ENV_FILE=/secure/axignal-pilot.env
export AXIGNAL_PILOT_COMPOSE_EDGE_FILE=infra/pilot/remote/compose.standalone.yaml
bash infra/pilot/backup.sh /secure/backups/axignal-before-change.dump
bash infra/pilot/restore-rehearsal.sh
```

Keep the dump and its SHA-256 file outside Docker volumes. A deployment change
is blocked when the restore rehearsal fails.

## Upgrade

1. create and verify a backup;
2. record the current commit and image digests;
3. check out the approved target SHA;
4. run all preflight gates and Compose validation;
5. rebuild the core and TED worker with `--wait` where supported;
6. verify health and one bounded live TED ResearchRun;
7. retain the previous images and backup until the meeting cycle is complete.

## Rollback

Three independent controls stop new TED execution:

```text
AXIGNAL_TED_PROCUREMENT_ENABLED=false
AXIGNAL_TED_LIVE_SOURCES_ENABLED=false
axignal_global.sources.kill_switch=true for src_ted_search_api_v3
```

Stop the `research-worker`, redeploy the previous exact SHA and restore the
pre-upgrade dump only when schema or data compatibility requires it. Never
delete append-only canonical or audit history. The tested source kill switch
leaves zero new Evidence, Candidate Claim, canonical Claim or dossier residue.

## Meeting package

Prepare the private URL, temporary operator credential, six-step demo script,
architecture summary, current gate table, security review, metric artifact,
backup proof and a recorded fallback demonstration.

State explicitly:

- the bounded TED runtime is accepted for the authenticated private pilot;
- qualified B2G research and willingness to pay remain in `AX-F9-T15`;
- public trial, billing and general availability remain disabled;
- the product does not predict winning, profitability or legal eligibility and
  does not submit or represent bids.
