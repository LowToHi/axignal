from __future__ import annotations

from collections import deque
from collections.abc import Iterator
from contextlib import contextmanager
from types import SimpleNamespace
from typing import Any
from uuid import UUID, uuid4

import pytest

from axignal_api.admission_repository import AdmissionRepository
from axignal_api.proposal_repository import DocumentProposalRepository
from axignal_api.ted_repository import TEDResearchRepository

TENANT = UUID("00000000-0000-4000-8000-000000000201")
RUN = UUID("00000000-0000-4000-8000-000000000202")
ENTITY = UUID("00000000-0000-4000-8000-000000000203")


class Cursor:
    def __init__(
        self,
        *,
        one: list[dict[str, Any] | None] | None = None,
        many: list[list[dict[str, Any]]] | None = None,
        rowcount: int = 1,
    ) -> None:
        self.one = deque(one or [])
        self.many = deque(many or [])
        self.rowcount = rowcount
        self.executions: list[tuple[object, object | None]] = []

    def execute(self, statement: object, params: object | None = None) -> None:
        self.executions.append((statement, params))

    def fetchone(self) -> dict[str, Any] | None:
        return self.one.popleft() if self.one else None

    def fetchall(self) -> list[dict[str, Any]]:
        return self.many.popleft() if self.many else []


class Plan:
    def __init__(self, *cursors: Cursor) -> None:
        self.cursors = deque(cursors)
        self.contexts: list[tuple[tuple[object, ...], dict[str, object]]] = []

    @contextmanager
    def __call__(self, *args: object, **kwargs: object) -> Iterator[Cursor]:
        self.contexts.append((args, dict(kwargs)))
        if not self.cursors:
            raise AssertionError("unexpected repository cursor")
        yield self.cursors.popleft()


def attach(repository: object, *cursors: Cursor) -> Plan:
    plan = Plan(*cursors)
    setattr(repository, "_cursor", plan)
    return plan


def test_proposal_repository_simple_wrappers_and_role_separation() -> None:
    repository = DocumentProposalRepository(
        app_dsn="postgresql://app", proposal_dsn="postgresql://proposal"
    )
    create_cursor = Cursor()
    plan = attach(repository, create_cursor)
    run_id = repository.create_run(
        tenant_id=TENANT,
        context_id="ctx",
        opportunity_id="opp",
        question="Question",
    )
    assert isinstance(run_id, UUID)
    assert len(create_cursor.executions) == 2
    assert plan.contexts == [(("axignal_app", TENANT), {})]

    event_id = uuid4()
    aggregate_id = uuid4()
    attach(
        repository,
        Cursor(
            many=[[
                {
                    "proposal_outbox_event_id": event_id,
                    "aggregate_id": aggregate_id,
                    "event_type": "research.document_proposal.requested",
                    "payload": {"schema_version": 1},
                    "attempts": 0,
                }
            ]]
        ),
    )
    events = repository.pending_proposal_outbox(limit=3)
    assert len(events) == 1
    assert events[0].event_id == event_id
    assert events[0].aggregate_id == aggregate_id

    for invoke in [
        lambda: repository.mark_proposal_outbox_published(event_id),
        lambda: repository.mark_proposal_outbox_failed(event_id, "x" * 600),
    ]:
        cursor = Cursor()
        attach(repository, cursor)
        invoke()
        assert len(cursor.executions) == 1

    attach(repository, Cursor(one=[{"source_id": "source"}]))
    assert repository.get_source("source") == {"source_id": "source"}
    attach(repository, Cursor(one=[{"research_run_id": RUN}]))
    assert repository.get_run_for_worker(tenant_id=TENANT, run_id=RUN) == {
        "research_run_id": RUN
    }
    attach(repository, Cursor(rowcount=1))
    repository.transition_run(tenant_id=TENANT, run_id=RUN, state="PROPOSING")
    attach(repository, Cursor(rowcount=0))
    with pytest.raises(LookupError):
        repository.transition_run(tenant_id=TENANT, run_id=RUN, state="PROPOSING")


def test_proposal_persist_result_idempotent_and_orchestrated(monkeypatch) -> None:
    repository = DocumentProposalRepository(proposal_dsn="postgresql://proposal")
    attach(repository, Cursor(one=[{"state": "COMPLETED_PROVISIONAL"}]))
    assert repository.persist_result(
        tenant_id=TENANT,
        run_id=RUN,
        source={},
        result=SimpleNamespace(),
    ) == {"idempotent_replay": True}

    evidence = SimpleNamespace(evidence_key="ev-1")
    candidate = SimpleNamespace(
        candidate_claim_id="candidate-1",
        evidence_keys=["ev-1"],
    )
    result = SimpleNamespace(
        evidence=(evidence,),
        candidate_claims=(candidate,),
        fragments=(),
        actual_usage={"model_calls": 1},
        admission_results=(),
        document=SimpleNamespace(model_dump=lambda **_: {"document_id": "doc"}),
        dossier=SimpleNamespace(
            title="Dossier",
            summary="Summary",
            attribution={},
            sections=(),
            model_dump=lambda **_: {"title": "Dossier"},
        ),
        pipeline_version="pipeline@1",
    )
    source = {
        "source_id": "source",
        "rights_status": "COMMERCIAL_REUSE_WITH_ATTRIBUTION",
        "license_id": "CC-BY-4.0",
        "admission_state": "ADMITTED",
        "kill_switch": False,
    }
    monkeypatch.setattr(repository, "_source_object", lambda *_: uuid4())
    monkeypatch.setattr(repository, "_fragments", lambda *_: None)
    monkeypatch.setattr(repository, "_evidence", lambda *_: uuid4())
    monkeypatch.setattr(repository, "_candidate", lambda *_: uuid4())
    monkeypatch.setattr(repository, "_package", lambda *_: {"package": True})
    monkeypatch.setattr(repository, "_handoff", lambda *_: uuid4())
    monkeypatch.setattr(repository, "_dossier", lambda *_: uuid4())
    cursor = Cursor(one=[{"state": "HANDOFF_PENDING"}])
    attach(repository, cursor)
    persisted = repository.persist_result(
        tenant_id=TENANT,
        run_id=RUN,
        source=source,
        result=result,
    )
    assert persisted["idempotent_replay"] is False
    assert len(persisted["evidence_ids"]) == 1
    assert len(persisted["candidate_claim_ids"]) == 1
    assert any("research.run.proposed" in str(statement) for statement, _ in cursor.executions)

    attach(repository, Cursor(one=[None]))
    with pytest.raises(LookupError):
        repository.persist_result(
            tenant_id=TENANT,
            run_id=RUN,
            source=source,
            result=result,
        )


def test_proposal_failure_and_idempotent_helper_paths() -> None:
    repository = DocumentProposalRepository(proposal_dsn="postgresql://proposal")
    job = SimpleNamespace(tenant_id=TENANT, research_run_id=RUN)
    cursor = Cursor()
    attach(repository, cursor)
    repository.record_failure(
        job=job,
        error_code="FAILED",
        error_detail="detail",
        quarantined=False,
    )
    assert len(cursor.executions) == 2

    source = {
        "source_id": "source",
        "attribution_text": "Attribution",
        "license_id": "CC-BY-4.0",
        "rights_status": "COMMERCIAL_REUSE_WITH_ATTRIBUTION",
        "terms_url": "https://example.test/terms",
        "dataset_url": "https://example.test/data",
    }
    document = SimpleNamespace(
        document_id="doc",
        source_url="https://example.test/doc",
        retrieved_at="2026-08-01T00:00:00Z",
        content_type="application/pdf",
        content_hash="sha256:doc",
        title="Title",
        published_at="2026-01-01T00:00:00Z",
    )
    result = SimpleNamespace(document=document)
    insert_id = uuid4()
    cursor = Cursor(one=[{"source_object_id": insert_id}])
    assert repository._source_object(cursor, source, result) == insert_id
    existing_id = uuid4()
    cursor = Cursor(one=[None, {"source_object_id": existing_id}])
    assert repository._source_object(cursor, source, result) == existing_id

    candidate = SimpleNamespace(
        fingerprint="sha256:candidate",
        opportunity_id="opp",
        subject_id="subject",
        predicate="predicate",
        object_value={"value": 1},
        statement="Statement",
        kind="FACT",
        producer_id="model",
        method_version="method",
        relationship="SUPPORTING",
        model_version="model",
        prompt_version="prompt",
        extraction_confidence=0.9,
        assumptions=[],
        unknowns=[],
    )
    evidence_id = uuid4()
    candidate_id = uuid4()
    cursor = Cursor(one=[{"candidate_claim_id": candidate_id}])
    assert repository._candidate(cursor, candidate, [evidence_id]) == candidate_id
    cursor = Cursor(one=[None, {"candidate_claim_id": candidate_id}])
    assert repository._candidate(cursor, candidate, [evidence_id]) == candidate_id

    handoff_id = uuid4()
    cursor = Cursor(one=[{"admission_handoff_id": handoff_id}])
    assert repository._handoff(
        cursor, TENANT, RUN, [candidate_id], {"package": True}, "sha256:package"
    ) == handoff_id
    cursor = Cursor(one=[None, {"admission_handoff_id": handoff_id}])
    assert repository._handoff(
        cursor, TENANT, RUN, [candidate_id], {"package": True}, "sha256:package"
    ) == handoff_id


def test_ted_repository_create_validation_idempotency_and_orchestration(monkeypatch) -> None:
    repository = TEDResearchRepository("postgresql://ted")
    cursor = Cursor()
    attach(repository, cursor)
    run_id = repository.create_ted_run(
        tenant_id=TENANT,
        context_id="ctx",
        opportunity_id="opp",
        question="Question",
    )
    assert isinstance(run_id, UUID)
    assert len(cursor.executions) == 2

    with pytest.raises(ValueError, match="no evidence"):
        repository.complete_ted_run(
            tenant_id=TENANT,
            run_id=RUN,
            source={},
            page=SimpleNamespace(),
            evidence=(),
            candidates=(),
            decisions=(),
        )
    with pytest.raises(ValueError, match="cardinality"):
        repository.complete_ted_run(
            tenant_id=TENANT,
            run_id=RUN,
            source={},
            page=SimpleNamespace(),
            evidence=(SimpleNamespace(),),
            candidates=(),
            decisions=(),
        )

    item = SimpleNamespace()
    attach(
        repository,
        Cursor(one=[{"state": "COMPLETED", "job_kind": "TED_PROCUREMENT"}]),
    )
    assert repository.complete_ted_run(
        tenant_id=TENANT,
        run_id=RUN,
        source={},
        page=SimpleNamespace(),
        evidence=(item,),
        candidates=(item,),
        decisions=(item,),
    ) == {"idempotent_replay": True}

    attach(repository, Cursor(one=[None]))
    with pytest.raises(LookupError):
        repository.complete_ted_run(
            tenant_id=TENANT,
            run_id=RUN,
            source={},
            page=SimpleNamespace(),
            evidence=(item,),
            candidates=(item,),
            decisions=(item,),
        )
    attach(repository, Cursor(one=[{"state": "QUEUED", "job_kind": "OTHER"}]))
    with pytest.raises(ValueError, match="not a TED"):
        repository.complete_ted_run(
            tenant_id=TENANT,
            run_id=RUN,
            source={},
            page=SimpleNamespace(),
            evidence=(item,),
            candidates=(item,),
            decisions=(item,),
        )

    evidence_item = SimpleNamespace(evidence_key="ev")
    candidate = SimpleNamespace(candidate_claim_id="candidate")
    decision = SimpleNamespace(
        policy_version="policy@1",
        admitted=False,
        reasons=("DENIED",),
        as_json=lambda: {"outcome": "REJECT"},
    )
    page = SimpleNamespace(
        retrieved_at="2026-08-01T00:00:00Z",
        request_url="https://ted.test",
        retrieval_mode="FROZEN_FIXTURE",
        notices=(SimpleNamespace(),),
        content_hash="sha256:page",
    )
    monkeypatch.setattr(repository, "_upsert_ted_source_object", lambda **_: uuid4())
    monkeypatch.setattr(repository, "_upsert_ted_evidence", lambda **_: uuid4())
    monkeypatch.setattr(repository, "_upsert_ted_candidate", lambda **_: uuid4())
    monkeypatch.setattr(repository, "_dossier_sections", lambda **_: [])
    monkeypatch.setattr("axignal_api.ted_repository.sanitised_projection", lambda _: {})
    monkeypatch.setattr("axignal_api.ted_repository.canonical_hash", lambda _: "sha256:p")
    cursor = Cursor(one=[{"state": "QUEUED", "job_kind": "TED_PROCUREMENT"}])
    attach(repository, cursor)
    completed = repository.complete_ted_run(
        tenant_id=TENANT,
        run_id=RUN,
        source={"source_id": "ted"},
        page=page,
        evidence=(evidence_item,),
        candidates=(candidate,),
        decisions=(decision,),
    )
    assert completed["idempotent_replay"] is False
    assert completed["canonical_claim_ids"] == []
    assert len(cursor.executions) >= 7


def test_ted_upsert_and_dossier_helper_paths() -> None:
    repository = TEDResearchRepository("postgresql://ted")
    source = {
        "source_id": "ted-search-api",
        "rights_status": "COMMERCIAL_REUSE_WITH_ATTRIBUTION",
        "license_id": "TED-TERMS",
        "attribution_text": "TED",
        "terms_url": "https://ted.test/terms",
        "dataset_url": "https://ted.test",
    }
    page = SimpleNamespace(
        retrieval_key="key",
        request_url="https://ted.test",
        retrieved_at="2026-08-01T00:00:00Z",
        http_status=200,
        content_type="application/json",
        content_hash="sha256:page",
        raw_payload={"results": []},
        retrieval_mode="FROZEN_FIXTURE",
    )
    inserted = uuid4()
    cursor = Cursor(one=[{"source_object_id": inserted}])
    assert repository._upsert_ted_source_object(
        cursor=cursor, source=source, page=page
    ) == inserted
    cursor = Cursor(one=[None, None])
    with pytest.raises(RuntimeError, match="source object upsert"):
        repository._upsert_ted_source_object(cursor=cursor, source=source, page=page)

    candidate_ids = (uuid4(), uuid4())
    evidence_ids = [uuid4(), uuid4()]
    candidates = (
        SimpleNamespace(
            candidate_claim_id="a",
            statement="A",
            evidence_key="ev-a",
            relationship="SUPPORTING",
        ),
        SimpleNamespace(
            candidate_claim_id="b",
            statement="B",
            evidence_key="ev-b",
            relationship="ADVERSE",
        ),
    )
    sections = repository._dossier_sections(
        candidates=candidates,
        candidate_ids=list(candidate_ids),
        evidence_ids=evidence_ids,
        canonical_by_candidate={candidate_ids[0]: uuid4()},
    )
    assert len(sections) == 2
    assert sections[0]["status"] == "ADMITTED"
    assert sections[1]["status"] == "PROVISIONAL"


def test_repository_cursor_credentials_fail_closed() -> None:
    proposal = DocumentProposalRepository()
    with pytest.raises(RuntimeError, match="axignal_app"):
        with proposal._cursor("axignal_app"):
            pass
    with pytest.raises(RuntimeError, match="axignal_proposal_worker"):
        with proposal._cursor("axignal_proposal_worker"):
            pass

    admission = AdmissionRepository()
    with pytest.raises(RuntimeError, match="axignal_app"):
        with admission._cursor("axignal_app"):
            pass
    with pytest.raises(RuntimeError, match="axignal_admission_runtime"):
        with admission._cursor("axignal_admission_runtime"):
            pass
