# AXIGNAL local development

Status: `EXECUTABLE SPINE v0.2 / RESEARCH RUN FIXTURE`
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

# Product API, including the bounded ResearchRun router
python -m uvicorn axignal_api.application:app --app-dir apps/api/src --reload --port 8000
```

Endpoints:

- product UI: `http://localhost:3000`
- landing: `http://localhost:3001`
- API docs: `http://localhost:8000/docs`
- API health: `http://localhost:8000/health`
- synthetic ResearchRun: `POST http://localhost:8000/v1/prototype/research-runs`

Example ResearchRun fixture:

```bash
curl -sS -X POST http://localhost:8000/v1/prototype/research-runs \
  -H 'content-type: application/json' \
  -d '{
    "question": "Investiga el contexto regulatorio y socioeconómico",
    "include_private_knowledge": false
  }'
```

Expected authority state:

```text
run.state = ADMISSION_QUEUED
candidate_claims[*].canonical_claim_id = null
```

## Quality gates

```bash
pnpm typecheck
pnpm build
pnpm exec playwright install chromium
pnpm test:e2e --project=chromium-desktop
ruff check apps/api
pytest --cov=axignal_api --cov-report=term-missing
```

## Infrastructure verification

```bash
docker compose exec -T postgres psql -U axignal -d axignal -c \
  "SELECT extname FROM pg_extension WHERE extname IN ('postgis', 'vector') ORDER BY extname;"
docker compose exec -T valkey valkey-cli ping
```

Expected database extensions:

```text
postgis
vector
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

## Prototype boundaries

- All opportunity, claim, evidence, private-memory and ResearchRun data is synthetic.
- The Browser source is a frozen local fixture; no live web request occurs.
- The hostile Browser instruction is a test fixture and cannot modify tools, budgets or authority.
- Tenant-private evidence requires explicit opt-in and never supports global Candidate Claims.
- The prototype does not provide personalised advice or execute transactions.
- Navigator and research workers cannot write canonical claims.
- Candidate Claims remain proposals with `canonical_claim_id = null`.
- Knowledge Tides are not market evidence.
- Production credentials or customer data MUST NOT be used locally or in CI.
