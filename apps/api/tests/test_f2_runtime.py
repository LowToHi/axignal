from __future__ import annotations

from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pytest
from opentelemetry import trace

from axignal_api.object_store import (
    InMemoryObjectStore,
    LocalFilesystemObjectStore,
    ObjectIntegrityError,
    ObjectNotFoundError,
    S3CompatibleObjectStore,
)
from axignal_api.scheduler import ScheduledJob, default_handlers
from axignal_api.telemetry import (
    attach_trace_envelope,
    build_in_memory_telemetry,
    inject_trace_envelope,
    sanitize_attributes,
    span_export_is_redacted,
    start_span,
    tracer_for,
)


class FakeS3:
    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], dict] = {}

    def put_object(self, **kwargs):
        key = (kwargs["Bucket"], kwargs["Key"])
        if kwargs.get("IfNoneMatch") == "*" and key in self.objects:
            raise RuntimeError("precondition failed")
        self.objects[key] = {
            "Body": bytes(kwargs["Body"]),
            "Metadata": dict(kwargs["Metadata"]),
            "ContentType": kwargs["ContentType"],
        }

    def get_object(self, **kwargs):
        try:
            item = self.objects[(kwargs["Bucket"], kwargs["Key"])]
        except KeyError as exc:
            raise RuntimeError("not found") from exc
        return {"Body": BytesIO(item["Body"])}

    def head_object(self, **kwargs):
        try:
            item = self.objects[(kwargs["Bucket"], kwargs["Key"])]
        except KeyError as exc:
            raise RuntimeError("not found") from exc
        return {
            "ContentLength": len(item["Body"]),
            "ContentType": item["ContentType"],
            "Metadata": item["Metadata"],
        }

    def delete_object(self, **kwargs):
        self.objects.pop((kwargs["Bucket"], kwargs["Key"]), None)


class FakeRepository:
    def recover_expired_leases(self) -> int:
        return 2


def scheduled_job(kind: str, payload: dict) -> ScheduledJob:
    return ScheduledJob(
        scheduled_job_id=uuid4(),
        tenant_id=None,
        job_kind=kind,
        idempotency_key="idempotency-123",
        payload=payload,
        trace_context={},
        state="LEASED",
        attempt_count=1,
        max_attempts=3,
    )


def test_memory_object_store_roundtrip() -> None:
    store = InMemoryObjectStore()
    metadata = store.put(
        namespace="tenant/111/source",
        content=b"immutable evidence",
        content_type="application/octet-stream",
    )
    assert metadata.key.endswith(metadata.sha256)
    assert store.get(metadata.key) == b"immutable evidence"
    assert store.verify_hash(metadata.key) == metadata
    assert store.delete_if_unreferenced(metadata.key, reference_count=1) is False
    assert store.delete_if_unreferenced(metadata.key, reference_count=0) is True
    with pytest.raises(ObjectNotFoundError):
        store.get(metadata.key)


def test_local_store_rejects_hash_mismatch_and_tamper(tmp_path: Path) -> None:
    store = LocalFilesystemObjectStore(tmp_path)
    with pytest.raises(ObjectIntegrityError):
        store.put(
            namespace="tenant/111",
            content=b"content",
            content_type="text/plain",
            expected_sha256="0" * 64,
        )
    metadata = store.put(
        namespace="tenant/111",
        content=b"original",
        content_type="text/plain",
    )
    store._data_path(metadata.key).write_bytes(b"tampered")
    with pytest.raises(ObjectIntegrityError):
        store.get(metadata.key)


def test_s3_adapter_uses_injected_client() -> None:
    store = S3CompatibleObjectStore(client=FakeS3(), bucket="axignal", prefix="dev")
    metadata = store.put(
        namespace="tenant/111",
        content=b"s3-compatible",
        content_type="text/plain",
    )
    assert store.get(metadata.key) == b"s3-compatible"
    assert store.verify_hash(metadata.key).sha256 == metadata.sha256
    assert store.delete_if_unreferenced(metadata.key, reference_count=0) is True


def test_sensitive_attributes_are_redacted() -> None:
    assert sanitize_attributes(
        {
            "authorization": "Bearer dangerous",
            "api_key": "sk-secretvalue",
            "research_run_id": "run-1",
        }
    ) == {
        "authorization": "[REDACTED]",
        "api_key": "[REDACTED]",
        "research_run_id": "run-1",
    }


def test_trace_context_propagates_between_layers() -> None:
    provider, exporter = build_in_memory_telemetry()
    producer = tracer_for(provider, "producer")
    consumer = tracer_for(provider, "consumer")
    with start_span(producer, "schedule", attributes={"password": "not-exported"}):
        envelope = inject_trace_envelope().as_dict()
    with attach_trace_envelope(envelope):
        with start_span(consumer, "execute", attributes={"scheduled_job_id": "job-1"}):
            assert trace.get_current_span().get_span_context().is_valid
    spans = list(exporter.get_finished_spans())
    assert len(spans) == 2
    assert spans[0].context.trace_id == spans[1].context.trace_id
    assert span_export_is_redacted(spans)


def test_default_scheduler_handlers_are_bounded() -> None:
    handlers = default_handlers(FakeRepository())  # type: ignore[arg-type]
    assert handlers["VERIFY_RUNTIME_HEALTH"](
        scheduled_job("VERIFY_RUNTIME_HEALTH", {"components": ["valkey", "postgres"]})
    ) == {"state": "HEALTHY", "checked": ["postgres", "valkey"]}
    assert handlers["RECOVER_EXPIRED_SCHEDULER_LEASES"](
        scheduled_job("RECOVER_EXPIRED_SCHEDULER_LEASES", {})
    ) == {"recovered": 2}
    assert handlers["RETRY_STALE_OUTBOX"](
        scheduled_job("RETRY_STALE_OUTBOX", {})
    )["state"] == "FAIL_CLOSED"
