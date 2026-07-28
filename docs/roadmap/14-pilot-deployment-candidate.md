# 14 — AXIGNAL Pilot Deployment Candidate

Version: `0.1.0`  
Status: `IMPLEMENTED CANDIDATE`  
Public launch: `NOT AUTHORISED`

## Objective

Make AXIGNAL privately deployable, presentable and reproducibly demonstrable for incubator, investor and partner meetings before the deferred F1 human-study gate.

## Scope

- standalone web image and API runtime image;
- private edge through Caddy with automatic TLS when a domain is configured;
- PostgreSQL, persistent Valkey and content-addressed object storage;
- runtime database credential rotation;
- authenticated pilot access;
- guided `/demo` route over the synthetic canonical fixture;
- liveness and dependency-aware readiness;
- backup and restore rehearsal;
- optional workers and OpenTelemetry profiles;
- deployment and rollback runbook.

## Invariants

- only Caddy publishes host ports;
- FastAPI, PostgreSQL and Valkey remain internal;
- live sources remain disabled;
- validation campaign UI remains disabled;
- no billing or public launch;
- no repository secrets;
- demo reset affects browser-local state only;
- demo execution cannot mutate canonical claims;
- backup is required before upgrade;
- deployment is pinned to an exact commit SHA.

## Acceptance

The candidate must prove Docker Compose rendering, Python lint/tests, TypeScript/build, web/API health, authenticated demo availability, database credential rotation, persistent volumes, backup creation, restore rehearsal, security headers and all historical AXIGNAL gates.

## F1 placement

The controlled-study protocol remains frozen, but recruitment and execution move to a post-deployment validation gate after incubator/investor engagement. F1 does not block this pilot candidate.
