from __future__ import annotations

import argparse
import time

import psycopg
from redis import Redis

from axignal_api.object_store import LocalFilesystemObjectStore
from axignal_api.scheduler import (
    SchedulerOutboxPublisher,
    SchedulerRepository,
    SchedulerWorker,
    ValkeySchedulerQueue,
    default_handlers,
)
from axignal_api.settings import Settings
from axignal_api.telemetry import build_tracer_provider, tracer_for


def healthcheck(settings: Settings) -> int:
    settings.require_scheduler()
    settings.require_object_store()
    assert settings.scheduler_database_url is not None
    assert settings.valkey_url is not None
    with psycopg.connect(settings.scheduler_database_url) as connection:
        connection.execute("SELECT 1")
    Redis.from_url(settings.valkey_url).ping()
    if settings.object_store_backend == "local":
        store = LocalFilesystemObjectStore(settings.object_store_root)
        probe = store.put(
            namespace="health",
            content=b"axignal-scheduler-health",
            content_type="text/plain",
        )
        store.verify_hash(probe.key)
    return 0


def run_forever(settings: Settings) -> int:
    settings.require_scheduler()
    settings.require_object_store()
    assert settings.scheduler_database_url is not None
    assert settings.valkey_url is not None
    provider = build_tracer_provider(service_name=settings.otel_service_name)
    tracer = tracer_for(provider, "axignal.scheduler.service")
    repository = SchedulerRepository(settings.scheduler_database_url)
    queue = ValkeySchedulerQueue(
        settings.valkey_url,
        queue_key=settings.scheduler_queue_key,
    )
    publisher = SchedulerOutboxPublisher(repository, queue, tracer=tracer)
    worker = SchedulerWorker(
        repository=repository,
        queue=queue,
        worker_id="scheduler-service",
        tracer=tracer,
        handlers=default_handlers(repository),
    )
    while True:
        repository.recover_expired_leases()
        published = publisher.publish_pending()
        worked = worker.run_once(timeout_seconds=1)
        if not published and not worked:
            time.sleep(1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--healthcheck", action="store_true")
    args = parser.parse_args()
    settings = Settings.from_env()
    if args.healthcheck:
        return healthcheck(settings)
    return run_forever(settings)


if __name__ == "__main__":
    raise SystemExit(main())
