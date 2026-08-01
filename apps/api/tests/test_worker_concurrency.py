from __future__ import annotations

from contextlib import contextmanager
from typing import Any, cast
from uuid import UUID

from axignal_api.concurrent_repository import ConcurrentTEDResearchRepository
from axignal_api.queue import OutboxPublisher, ResearchJob
from axignal_api.worker import ResearchWorker

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
RUN_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
EVENT_ID = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")


class RecordingCursor:
    def __init__(self, *, rows: list[dict[str, Any]] | None = None) -> None:
        self.rows = rows or []
        self.statements: list[str] = []
        self.parameters: list[tuple[Any, ...] | None] = []
        self.rowcount = 1

    def execute(self, statement: str, parameters: tuple[Any, ...] | None = None) -> None:
        self.statements.append(" ".join(statement.split()))
        self.parameters.append(parameters)

    def fetchone(self) -> dict[str, Any] | None:
        return self.rows[0] if self.rows else None

    def fetchall(self) -> list[dict[str, Any]]:
        return list(self.rows)


class RepositoryHarness(ConcurrentTEDResearchRepository):
    def __init__(self, cursor: RecordingCursor) -> None:
        self.cursor = cursor

    @contextmanager
    def _cursor(self, *, role: str, tenant_id: UUID | None = None):  # type: ignore[override]
        del role, tenant_id
        yield self.cursor


class RecordingQueue:
    def __init__(self) -> None:
        self.jobs: list[ResearchJob] = []
        self.events: list[Any] = []

    def enqueue(self, job: ResearchJob) -> None:
        self.jobs.append(job)

    def publish_event(self, event: Any) -> None:
        self.events.append(event)


class DelegatingRepository:
    def __init__(self) -> None:
        self.calls: list[tuple[Any, int]] = []

    def publish_pending_to_queue(self, *, queue: Any, limit: int) -> int:
        self.calls.append((queue, limit))
        return 7


class DuplicateRepository:
    def __init__(self) -> None:
        self.claims = 0

    def claim_run_for_worker(self, *, tenant_id: UUID, run_id: UUID) -> None:
        assert tenant_id == TENANT_ID
        assert run_id == RUN_ID
        self.claims += 1
        return None

    def get_run_for_worker(self, *, tenant_id: UUID, run_id: UUID) -> dict[str, object]:
        assert tenant_id == TENANT_ID
        assert run_id == RUN_ID
        return {"state": "QUEUED", "opportunity_id": "opp_test"}

    def get_source(self, source_id: str) -> dict[str, object]:
        assert source_id == "world-bank-wdi"
        return {
            "admission_state": "ADMITTED",
            "kill_switch": False,
            "rights_status": "COMMERCIAL_REUSE_WITH_ATTRIBUTION",
            "commercial_use": True,
            "redistribution": True,
        }


class ForbiddenConnector:
    def fetch_latest_inflation(self) -> None:
        raise AssertionError("duplicate delivery must not reach source retrieval")


def test_run_claim_is_compare_and_set_from_queued() -> None:
    cursor = RecordingCursor(rows=[{"research_run_id": RUN_ID, "state": "RETRIEVING"}])
    repository = RepositoryHarness(cursor)

    claimed = repository.claim_run_for_worker(tenant_id=TENANT_ID, run_id=RUN_ID)

    assert claimed == {"research_run_id": RUN_ID, "state": "RETRIEVING"}
    assert "WHERE research_run_id = %s AND state = 'QUEUED'" in cursor.statements[0]
    assert "RETURNING *" in cursor.statements[0]


def test_outbox_publication_locks_rows_before_enqueue() -> None:
    cursor = RecordingCursor(
        rows=[
            {
                "outbox_event_id": EVENT_ID,
                "aggregate_id": RUN_ID,
                "event_type": "research.run.requested",
                "payload": {
                    "schema_version": 1,
                    "tenant_id": str(TENANT_ID),
                    "research_run_id": str(RUN_ID),
                    "source_id": "world-bank-wdi",
                },
                "attempts": 0,
            }
        ]
    )
    repository = RepositoryHarness(cursor)
    queue = RecordingQueue()

    published = repository.publish_pending_to_queue(queue=queue, limit=20)

    assert published == 1
    assert len(queue.jobs) == 1
    assert queue.jobs[0].research_run_id == RUN_ID
    assert "FOR UPDATE SKIP LOCKED" in cursor.statements[0]
    assert any("SET status = 'PUBLISHED'" in statement for statement in cursor.statements)


def test_outbox_publisher_uses_atomic_repository_boundary() -> None:
    repository = DelegatingRepository()
    queue = RecordingQueue()
    publisher = OutboxPublisher(
        cast(Any, repository),
        cast(Any, queue),
    )

    assert publisher.publish_pending(limit=13) == 7
    assert repository.calls == [(queue, 13)]


def test_duplicate_delivery_is_ignored_before_source_retrieval() -> None:
    repository = DuplicateRepository()
    worker = ResearchWorker(
        repository=cast(Any, repository),
        queue=cast(Any, object()),
        world_bank_connector=cast(Any, ForbiddenConnector()),
    )

    worker.process(
        ResearchJob(
            tenant_id=TENANT_ID,
            research_run_id=RUN_ID,
            source_id="world-bank-wdi",
        )
    )

    assert repository.claims == 1
