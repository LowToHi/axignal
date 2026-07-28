# AXIGNAL local development

Status: `EXECUTABLE SPINE v0.3 / PERSISTENT RESEARCH CANDIDATE`
Goal ID: `AXIGNAL-GOAL-001`

## Prerequisites

- Node.js 22+
- Corepack
- Python 3.13+
- Docker with Compose v2

## Bootstrap

```bash
corepack enable
pnpm install --frozen-lockfile
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
docker compose up --build --detach --wait
```

The repository contains a pnpm `10.12.4` lockfile. CI and local verification fail closed when a manifest and the lockfile diverge.

## Run services

```bash
# Product UI
pnpm --filter @axignal/web dev

# Conversion landing
pnpm --filter @axignal/landing dev

# Product API, including prototype and persistent ResearchRun routers
python -m uvicorn axignal_api.application:app --app-dir apps/api/src --reload --port 8000
```

Endpoints:

- product UI: `http://localhost:3000`
- landing: `http://localhost:3001`
- API docs: `http://localhost:8000/docs`
- API health: `http://localhost:8000/health`
- synthetic ResearchRun: `POST http://localhost:8000/v1/prototype/research-runs`
- persistent ResearchRun: `POST http://localhost:8000/v1/research-runs`

## Persistent ResearchRun spine

The persistent path is disabled unless explicitly enabled.

```bash
export AXIGNAL_DATABASE_URL='postgresql://axignal:axignal@127.0.0.1:5432/axignal'
export AXIGNAL_VALKEY_URL='redis://127.0.0.1:6379/0'
export AXIGNAL_PERSISTENT_RESEARCH_ENABLED='true'
export AXIGNAL_RESEARCH_QUEUE_KEY='axignal:research:queue:v1'
```

For deterministic local and CI verification:

```bash
export AXIGNAL_LIVE_SOURCES_ENABLED='false'
export AXIGNAL_WORLD_BANK_FIXTURE_PATH='apps/api/tests/fixtures/world_bank_rus_inflation.json'
python -m axignal_api.worker --poll-seconds 2
```

Create a persistent ResearchRun:

```bash
curl -sS -X POST http://localhost:8000/v1/research-runs \
  -H 'content-type: application/json' \
  -H 'X-AXIGNAL-Tenant-ID: 11111111-1111-4111-8111-111111111111' \
  -d '{
    "context_id": "ctx_moscow_real_estate_v01",
    "opportunity_id": "opp_moscow_ramenki",
    "question": "Actualiza el contexto de inflación de la oportunidad.",
    "include_private_knowledge": false
  }'
```

The tenant header is a development boundary only. Production exposure is blocked until authenticated identity resolves the tenant server-side.

Run the complete acceptance:

```bash
python scripts/verify_persistent_research_spine.py
```

## Controlled live retrieval

Live World Bank retrieval requires a deliberate operator action:

```bash
export AXIGNAL_LIVE_SOURCES_ENABLED='true'
unset AXIGNAL_WORLD_BANK_FIXTURE_PATH
```

Live mode remains restricted to:

- `https://api.worldbank.org`;
- country `RUS`;
- indicator `FP.CPI.TOTL.ZG`;
- one API request per run;
- ten seconds;
- 512 KiB;
- JSON only;
- no redirects;
- no arbitrary Browser access.

## Quality gates

```bash
pnpm typecheck
pnpm build
pnpm exec playwright install chromium
pnpm test:e2e --project=chromium-desktop
ruff check apps/api scripts
pytest --cov=axignal_api --cov-report=term-missing
python scripts/verify_persistent_research_spine.py
```

## Infrastructure verification

```bash
docker compose exec -T postgres psql -U axignal -d axignal -c \
  "SELECT extname FROM pg_extension WHERE extname IN ('pgcrypto', 'postgis', 'vector') ORDER BY extname;"
docker compose exec -T postgres psql -U axignal -d axignal -c \
  "SELECT schema_name FROM information_schema.schemata WHERE schema_name IN ('axignal_global', 'tenant_private', 'intent_intelligence') ORDER BY schema_name;"
docker compose exec -T valkey valkey-cli ping
```

Expected extensions:

```text
pgcrypto
postgis
vector
```

Expected schemas:

```text
axignal_global
intent_intelligence
tenant_private
```

Expected Valkey response:

```text
PONG
```

## Shutdown and reset

```bash
docker compose down

# destructive local reset
docker compose down --volumes --remove-orphans
```

## Authority boundaries

- The visible Investigation Shell still uses the synthetic PR #14 flow until persistent client integration passes.
- The persistent path stores Source Objects, Evidence Objects, Candidate Claims, dossiers, admission batches and canonical observed facts.
- Live source access is disabled by default.
- World Bank inflation is annual national context, not Moscow property evidence, causal proof or advice.
- Tenant-private records are protected with PostgreSQL RLS and FORCE RLS.
- Tenant-private evidence cannot support global Candidate Claims.
- Structured World Bank data is parsed deterministically and uses zero model calls.
- Local or external model output remains proposal-only and cannot auto-admit.
- The deterministic runtime may admit an exact observed fact only after source, rights, provenance and semantic gates pass.
- The Claim Ledger is append-only.
- Knowledge Tides are research-prioritisation signals, not market evidence.
- Production credentials or customer data MUST NOT be used locally or in CI.
