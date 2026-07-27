# AXIGNAL local development

Status: `EXECUTABLE SPINE v0.1`
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

# Product API
python -m uvicorn axignal_api.main:app --app-dir apps/api/src --reload --port 8000
```

Endpoints:

- product UI: `http://localhost:3000`
- landing: `http://localhost:3001`
- API docs: `http://localhost:8000/docs`
- API health: `http://localhost:8000/health`

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

- All opportunity and claim data in the executable spine is synthetic.
- The prototype does not provide personalised advice or execute transactions.
- Navigator cannot write canonical claims.
- Knowledge Tides are not market evidence.
- Production credentials or customer data MUST NOT be used locally or in CI.
