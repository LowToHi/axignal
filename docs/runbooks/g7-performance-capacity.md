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

The G7 implementation branch may add measurement tooling, but it does not modify
source admission, rights, billing, entitlement or launch authority.

## Evidence profiles

### CI_CHARACTERISATION

Runs on an ephemeral GitHub-hosted runner. It validates the campaign harness,
checks regressions and measures a bounded internal workload. A pass means only:

```text
G7 harness executable
bounded regression thresholds met
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
health requests       5000
research runs         400
soak                  3600 seconds
research workers      4
source retrieval      frozen local fixture
external source calls 0
```

The workflow rejects smaller values. Passing the thresholds still leaves G7
`IN_PROGRESS` until `SRE_OPERATIONS` and `PRODUCT_CAPACITY_AUTHORITY` issue typed
acceptance against the retained campaign digest and machine fingerprint.

## Workload

The campaign exercises:

1. API readiness under concurrent burst load;
2. authenticated, tenant-resolved `ResearchRun` creation;
3. Valkey queue publication and backpressure;
4. multiple research workers consuming a frozen World Bank fixture;
5. tenant-isolated polling to terminal state;
6. queue residue and container restart inspection;
7. continuous Docker CPU/memory and queue-depth sampling;
8. a sustained readiness soak.

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
is required. Synthetic credentials are scoped to the isolated Compose project and
all volumes are deleted during cleanup.

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
expected production topology and reason the host is representative in the human
acceptance record.

## Stop conditions

Stop and retain evidence when any of these occurs:

- health or enqueue error budget is exceeded;
- research runs fail or time out;
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
4. launch capacity and stop thresholds are documented;
5. SRE/Operations and Product Capacity Authority sign current decisions;
6. aggregate release workflows pass on the same eventual canonical release SHA.

Until then:

```text
G7 = IN_PROGRESS
G8 = NOT CLOSED
G9 = NOT CLOSED
G10 = NOT CLOSED
PUBLIC LAUNCH = NO_GO
```
