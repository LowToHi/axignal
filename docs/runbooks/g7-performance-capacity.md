# G7 — Performance, load, soak and capacity

## Purpose

G7 proves that the AXIGNAL release candidate has explicit, reproducible capacity
limits. It does not infer production capacity from a unit test, a successful API
request or an ephemeral GitHub-hosted runner.

## Authority baseline

```text
authority branch  release/axignal-rc6r-55ed7fb
authority SHA     55ed7fb6d73bee8ca22ccdcaeaf4c5a550819a22
G7 state          IN_PROGRESS
public launch     NO_GO
```

The G7 implementation branch may add measurement tooling and correct defects
exposed by that tooling, but it does not modify source admission, rights, billing,
entitlement or launch authority.

## Active contract

The active measurement contract is:

```text
AX-G7-PERFORMANCE-CAPACITY-v0.2
```

`v0.2` supersedes, but does not delete, `v0.1`. The revision was created only
after the first exact-head campaign showed that concurrent `/readyz` traffic was
mixing dependency readiness with application liveness and that the queue needed an
explicit amplification bound. The revised contract separates:

- concurrent and sustained `/healthz` liveness traffic;
- low-frequency `/readyz` dependency probes;
- authenticated `ResearchRun` enqueue and completion;
- queue peak and queue residue;
- resource, restart and tenant-fairness evidence.

Threshold revisions require a new contract version. A failed result is never
relabelled or deleted.

## Evidence profiles

### CI_CHARACTERISATION

Runs on an ephemeral GitHub-hosted runner. It validates the campaign harness,
checks regressions and measures a bounded internal workload.

Minimum workload:

```text
liveness requests    200 burst + sustained soak traffic
readiness requests   10
research runs        12
soak                  60 seconds
research workers      2
```

A pass means only:

```text
G7 harness executable
bounded CI regression thresholds met
G7 remains IN_PROGRESS
```

It cannot close G7 because runner hardware, contention and network conditions are
not a declared production environment.

### PRODUCTION_REPRESENTATIVE

Runs only by explicit `workflow_dispatch` on a stable self-hosted Linux x64
runner. The retained artifact includes a content-derived machine fingerprint,
Docker version, CPU count, memory, disk capacity, exact Git head, resource samples,
queue samples and all latency distributions.

Minimum campaign:

```text
liveness requests    5000
readiness requests   600
research runs        400
soak                  3600 seconds
research workers      4
source retrieval      frozen local fixture
external source calls 0
```

The workflow rejects smaller values. Passing the thresholds still leaves G7
`IN_PROGRESS` until `SRE_OPERATIONS` and `PRODUCT_CAPACITY_AUTHORITY` issue typed
acceptance against the retained campaign digest, exact SHA, machine fingerprint
and declared topology.

## Workload

The campaign exercises:

1. API liveness under concurrent burst load;
2. dependency readiness at a bounded probe cadence;
3. authenticated, server-resolved, tenant-isolated `ResearchRun` creation;
4. transactional outbox publication with `FOR UPDATE SKIP LOCKED`;
5. Valkey queue depth, amplification, residue and backpressure;
6. compare-and-set acquisition from `QUEUED` to `RETRIEVING`;
7. multiple workers consuming a frozen World Bank fixture;
8. tenant-isolated polling to terminal state;
9. continuous Docker CPU and memory sampling;
10. container restart inspection and a sustained liveness soak.

Two equal synthetic tenants are interleaved. Fairness is the ratio between the
lower and higher tenant p95 completion latency. A value of `1.0` is perfect
parity; production-representative acceptance requires at least `0.8`.

## Safety boundary

The performance override forces:

```text
AXIGNAL_LIVE_SOURCES_ENABLED=false
AXIGNAL_TED_LIVE_SOURCES_ENABLED=false
```

No TED request, model call, customer data, production credential or public action
is required. Synthetic credentials are scoped to the isolated Compose project,
kept outside retained artifacts and deleted during cleanup. All Compose volumes
are removed after evidence capture.

The AXIGNAL API remains attached only to the internal backend network. A pinned,
ephemeral Caddy proxy bridges that network to a dynamically allocated loopback
port for the campaign; no application port is exposed directly.

## CI evidence chronology

### Failure 1 — duplicate processing and readiness contention

```text
exact head       67e43afa74ad65a44221134475bb8a8f6a69fef8
workflow run     30721958777
artifact         8825180402
artifact digest  sha256:acf95b352ed980a9d8c156dc03011afd1fa625ee392e8bf2534c5961cb9548b6
result           FAIL
```

The campaign retained 12/12 terminal runs but exposed readiness `503` responses,
a worker restart, queue amplification and a duplicate dossier constraint failure.
The result was not retried selectively or represented as capacity evidence.

### Failure 2 — processing race fixed, API publisher race retained

```text
exact head       49c5734f9f245b14c4e64c66005f132c14cb4cb9
workflow run     30722443738
artifact         8825321096
artifact digest  sha256:9efb6985ddb6a90425d5beedc04ea5749d832a478c8327841b54b83f47e6f007
result           FAIL
```

The worker compare-and-set removed duplicate dossier writes and restarts, and
liveness/readiness reached zero errors. However, the API endpoints still
instantiated the non-concurrent repository when publishing the outbox. Twelve
concurrent POST requests amplified the queue to 65 entries; completion p95/p99
rose to 62.72 seconds.

### Passing CI characterisation — full publication boundary corrected

```text
exact head       7523909423b0582e2f2d99466d1797be22218c2a
workflow run     30722731238
artifact         8825393684
artifact digest  sha256:4171646314d2b656f2f9c4c79a844869428a005427225b1936268baf847915d4
result           PASS
```

Measured result:

```text
liveness                         320/320 HTTP 200
liveness p95 / p99               188.66 ms / 216.82 ms
readiness                        12/12 HTTP 200
readiness p95                    11.77 ms
research accepted/completed      12/12
research failed/timed out        0/0
completion p95 / p99             10.60 s / 10.60 s
throughput                       1.108 completed runs/s
maximum queue depth              10
queue residue                    0
tenant fairness                  0.9988
container restarts               0
maximum memory-limit utilisation 0.153
findings                         none
```

This is regression evidence on ephemeral CI hardware, not production capacity and
not G7 closure authority.

## Local or self-hosted execution

```bash
export AXIGNAL_EXACT_SHA="$(git rev-parse HEAD)"
export AXIGNAL_G7_PROFILE=CI_CHARACTERISATION
export AXIGNAL_G7_OUTPUT_DIR=artifacts/g7-local
export AXIGNAL_G7_HEALTH_REQUESTS=200
export AXIGNAL_G7_RESEARCH_RUNS=12
export AXIGNAL_G7_SOAK_SECONDS=60
bash scripts/run_g7_compose_campaign.sh
```

For the launch-representative profile, use at least the contractual minima and a
stable host with no unrelated workload. Record host ownership, deployment class,
expected production topology and the reason the host represents the intended
launch topology in the human acceptance record.

## Stop conditions

Stop and retain evidence when any of these occurs:

- liveness, readiness or enqueue error budget is exceeded;
- research runs fail or time out;
- queue peak exceeds the contractual amplification bound;
- queue depth does not return to zero;
- any container restarts;
- memory limit utilisation exceeds the profile threshold;
- production memory growth exceeds 128 MiB/hour;
- tenant fairness falls below the profile threshold;
- exact-head identity differs from the dispatched SHA.

A stopped or failed campaign is evidence. Do not delete, rerun selectively or
adjust thresholds after observing the result. Any threshold revision requires a
new contract version and a new exact-head campaign.

## Closure contract

G7 can close only after:

1. the production-representative campaign passes on declared hardware;
2. the retained artifact is content-addressed and bound to one exact SHA;
3. the machine fingerprint and topology are accepted as representative;
4. launch capacity, worker count, backpressure and stop thresholds are documented;
5. SRE/Operations and Product Capacity Authority sign current decisions;
6. aggregate release workflows pass on the same eventual canonical release SHA.

Until then:

```text
CI CHARACTERISATION = PASS ON RECORDED SHA
PRODUCTION CAMPAIGN  = NOT EXECUTED
HUMAN ACCEPTANCE     = MISSING
G7                   = IN_PROGRESS
G8                   = NOT CLOSED
G9                   = NOT CLOSED
G10                  = NOT CLOSED
PUBLIC LAUNCH        = NO_GO
```
