FROM postgis/postgis:17-3.5

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-17-pgvector \
    && rm -rf /var/lib/apt/lists/*

COPY init.sql /docker-entrypoint-initdb.d/010-axignal-extensions.sql
COPY 020-research-spine.sql /docker-entrypoint-initdb.d/020-axignal-research-spine.sql
