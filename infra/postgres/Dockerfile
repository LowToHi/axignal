FROM postgis/postgis:17-3.5

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-17-pgvector \
    && rm -rf /var/lib/apt/lists/*

COPY init.sql /docker-entrypoint-initdb.d/010-axignal-extensions.sql
COPY 020-research-spine.sql /docker-entrypoint-initdb.d/020-axignal-research-spine.sql
COPY 025-research-runtime-grants.sql /docker-entrypoint-initdb.d/025-axignal-research-runtime-grants.sql
COPY 030-proposal-worker-boundary.sql /docker-entrypoint-initdb.d/030-axignal-proposal-worker.sql
COPY 035-deterministic-admission-runtime.sql /docker-entrypoint-initdb.d/035-axignal-admission-runtime.sql
