from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from axignal_api import admission_runtime as admission_module
from axignal_api import proposal_worker as proposal_module
from axignal_api import worker as research_module
from axignal_api.admission_queue import AdmissionReviewJob
from axignal_api.admission_types import (
    AdmissionIntegrityError,
    AdmissionPolicyError,
    AdmissionRunResult,
    AdmissionRuntimeError,
)
from axignal_api.document_proposals import DocumentPipelineError, DocumentSecurityError
from axignal_api.proposal_queue import DocumentProposalBudget, DocumentProposalJob
from axignal_api.proposal_repository import DOCUMENT_ID, PIPELINE_VERSION, SOURCE_ID
from axignal_api.queue import ResearchJob
from axignal_api.ted_runtime import PROFILE_ID


class FakeQueue:
    def __init__(self, *items: object | None) -> None:
        self.items = list(items)
        self.timeouts: list[int] = []

    def dequeue(self, *, timeout_seconds: int = 1):
        self.timeouts.append(timeout_seconds)
        return self.items.pop(0) if self.items else None


class ResearchRepositoryFake:
    def __init__(
        self,
        *,
        run: dict[str, object] | None,
        source: dict[str, object] | None,
    ) -> None:
        self.run = run
        self.source = source
        self.failures: list[dict[str, object]] = []
        self.transitions: list[str] = []
        self.world_bank_completion: dict[str, object] | None = None
        self.ted_completion: dict[str, object] | None = None

    def get_run_for_worker(self, **_: object):
        return self.run

    def get_source(self, _: str):
        return self.source

    def fail_run(self, **kwargs: object) -> None:
        self.failures.append(kwargs)

    def transition_run(self, *, state: str, **_: object) -> None:
        self.transitions.append(state)

    def complete_world_bank_run(self, **kwargs: object) -> None:
        self.world_bank_completion = kwargs

    def complete_ted_run(self, **kwargs: object) -> None:
        self.ted_completion = kwargs


class ProposalRepositoryFake:
    def __init__(
        self,
        *,
        run: dict[str, object] | None,
        source: dict[str, object] | None,
    ) -> None:
        self.run = run
        self.source = source
        self.failures: list[dict[str, object]] = []
        self.transitions: list[str] = []
        self.persisted: dict[str, object] | None = None

    def get_run_for_worker(self, **_: object):
        return self.run

    def get_source(self, _: str):
        return self.source

    def record_failure(self, **kwargs: object) -> None:
        self.failures.append(kwargs)

    def transition_run(self, *, state: str, **_: object) -> None:
        self.transitions.append(state)

    def persist_result(self, **kwargs: object) -> None:
        self.persisted = kwargs


class AdmissionRepositoryFake:
    def __init__(self, outcome: object) -> None:
        self.outcome = outcome
        self.decided: list[AdmissionReviewJob] = []
        self.failures: list[dict[str, object]] = []

    def decide(self, job: AdmissionReviewJob):
        self.decided.append(job)
        if isinstance(self.outcome, BaseException):
            raise self.outcome
        return self.outcome

    def record_failure(self, **kwargs: object) -> None:
        self.failures.append(kwargs)


def research_job(source_id: str) -> ResearchJob:
    return ResearchJob(
        tenant_id=uuid4(),
        research_run_id=uuid4(),
        source_id=source_id,
    )


def proposal_job(
    *,
    source_id: str = SOURCE_ID,
    document_id: str = DOCUMENT_ID,
    pipeline_version: str = PIPELINE_VERSION,
) -> DocumentProposalJob:
    return DocumentProposalJob(
        tenant_id=uuid4(),
        research_run_id=uuid4(),
        source_id=source_id,
        document_id=document_id,
        pipeline_version=pipeline_version,
        budget=DocumentProposalBudget(),
    )


def admission_job() -> AdmissionReviewJob:
    return AdmissionReviewJob(
        admission_handoff_id=uuid4(),
        research_run_id=uuid4(),
        tenant_id=uuid4(),
        expected_package_hash=f"sha256:{'a' * 64}",
    )


def admitted_world_bank_source() -> dict[str, object]:
    return {
        "admission_state": "ADMITTED",
        "kill_switch": False,
        "rights_status": "COMMERCIAL_REUSE_WITH_ATTRIBUTION",
        "commercial_use": True,
        "redistribution": True,
    }


def admitted_ted_source() -> dict[str, object]:
    return {
        "admission_state": "ADMITTED",
        "kill_switch": False,
        "rights_status": "COMMERCIAL_REUSE_WITH_ATTRIBUTION",
        "commercial_use": True,
        "redistribution": False,
        "config": {
            "product_profile": PROFILE_ID,
            "api_redistribution_allowed": False,
        },
    }


def admitted_document_source() -> dict[str, object]:
    return {
        "admission_state": "ADMITTED",
        "kill_switch": False,
        "rights_status": "COMMERCIAL_REUSE_WITH_ATTRIBUTION",
        "license_id": "CC-BY-4.0",
        "commercial_use": True,
        "redistribution": True,
    }


def test_research_worker_idle_and_dispatch_contract() -> None:
    job = research_job(research_module.WORLD_BANK_SOURCE_ID)
    queue = FakeQueue(None, job)
    repository = ResearchRepositoryFake(run=None, source=None)
    worker = research_module.ResearchWorker(
        repository=repository,  # type: ignore[arg-type]
        queue=queue,  # type: ignore[arg-type]
        world_bank_connector=SimpleNamespace(),  # type: ignore[arg-type]
    )

    assert worker.run_once(timeout_seconds=7) is False
    assert worker.run_once(timeout_seconds=3) is True
    assert queue.timeouts == [7, 3]
    assert repository.failures == []


def test_research_worker_ignores_completed_duplicate() -> None:
    repository = ResearchRepositoryFake(
        run={"state": "COMPLETED", "opportunity_id": "opp"},
        source=admitted_world_bank_source(),
    )
    worker = research_module.ResearchWorker(
        repository=repository,  # type: ignore[arg-type]
        queue=FakeQueue(),  # type: ignore[arg-type]
        world_bank_connector=SimpleNamespace(),  # type: ignore[arg-type]
    )

    worker.process(research_job(research_module.WORLD_BANK_SOURCE_ID))

    assert repository.transitions == []
    assert repository.failures == []


@pytest.mark.parametrize(
    ("source_id", "run", "source", "error_code"),
    [
        ("unknown-source", {"state": "QUEUED"}, None, "SOURCE_NOT_ROUTED"),
        (
            research_module.WORLD_BANK_SOURCE_ID,
            {"state": "QUEUED"},
            None,
            "SOURCE_NOT_REGISTERED",
        ),
        (
            research_module.WORLD_BANK_SOURCE_ID,
            {"state": "QUEUED"},
            {**admitted_world_bank_source(), "kill_switch": True},
            "SOURCE_NOT_ADMITTED",
        ),
    ],
)
def test_research_worker_rejects_unroutable_or_unadmitted_work(
    source_id: str,
    run: dict[str, object],
    source: dict[str, object] | None,
    error_code: str,
) -> None:
    repository = ResearchRepositoryFake(run=run, source=source)
    worker = research_module.ResearchWorker(
        repository=repository,  # type: ignore[arg-type]
        queue=FakeQueue(),  # type: ignore[arg-type]
        world_bank_connector=SimpleNamespace(),  # type: ignore[arg-type]
    )

    worker.process(research_job(source_id))

    assert repository.failures[-1]["error_code"] == error_code
    assert repository.transitions == []


def test_research_worker_completes_world_bank_state_machine(monkeypatch) -> None:
    observation = SimpleNamespace(period="2025", value=2.5, content_hash="sha256:obs")
    evidence = object()
    candidate = object()
    decision = object()
    repository = ResearchRepositoryFake(
        run={"state": "QUEUED", "opportunity_id": "opp-world-bank"},
        source=admitted_world_bank_source(),
    )
    connector = SimpleNamespace(fetch_latest_inflation=lambda: observation)
    monkeypatch.setattr(
        research_module,
        "build_world_bank_inflation_artifacts",
        lambda **_: (evidence, candidate),
    )
    monkeypatch.setattr(research_module, "evaluate_observed_fact", lambda **_: decision)
    worker = research_module.ResearchWorker(
        repository=repository,  # type: ignore[arg-type]
        queue=FakeQueue(),  # type: ignore[arg-type]
        world_bank_connector=connector,  # type: ignore[arg-type]
    )

    worker.process(research_job(research_module.WORLD_BANK_SOURCE_ID))

    assert repository.transitions == ["RETRIEVING", "PROPOSING", "ADMISSION_PENDING"]
    assert repository.world_bank_completion is not None
    assert repository.world_bank_completion["observation"] is observation
    assert repository.world_bank_completion["decision"] is decision
    assert repository.failures == []


def test_research_worker_completes_ted_state_machine(monkeypatch) -> None:
    page = object()
    evidence = (object(), object())
    candidates = (object(), object())
    repository = ResearchRepositoryFake(
        run={
            "state": "QUEUED",
            "job_kind": "TED_PROCUREMENT",
            "opportunity_id": "opp-ted",
        },
        source=admitted_ted_source(),
    )
    connector = SimpleNamespace(fetch_probe_page=lambda: page)
    monkeypatch.setattr(
        research_module,
        "build_ted_search_artifacts",
        lambda **_: (evidence, candidates),
    )
    monkeypatch.setattr(
        research_module,
        "evaluate_ted_observed_field",
        lambda **_: "ALLOW",
    )
    worker = research_module.ResearchWorker(
        repository=repository,  # type: ignore[arg-type]
        queue=FakeQueue(),  # type: ignore[arg-type]
        world_bank_connector=SimpleNamespace(),  # type: ignore[arg-type]
        ted_connector=connector,  # type: ignore[arg-type]
    )

    worker.process(research_job(research_module.TED_SOURCE_ID))

    assert repository.transitions == ["RETRIEVING", "PROPOSING", "ADMISSION_PENDING"]
    assert repository.ted_completion is not None
    assert repository.ted_completion["decisions"] == ("ALLOW", "ALLOW")
    assert repository.failures == []


def test_research_worker_fails_closed_on_connector_error() -> None:
    def fail() -> object:
        raise RuntimeError("connector unavailable")

    repository = ResearchRepositoryFake(
        run={"state": "QUEUED", "opportunity_id": "opp"},
        source=admitted_world_bank_source(),
    )
    worker = research_module.ResearchWorker(
        repository=repository,  # type: ignore[arg-type]
        queue=FakeQueue(),  # type: ignore[arg-type]
        world_bank_connector=SimpleNamespace(fetch_latest_inflation=fail),  # type: ignore[arg-type]
    )

    worker.process(research_job(research_module.WORLD_BANK_SOURCE_ID))

    assert repository.failures[-1]["error_code"] == "RUNTIMEERROR"
    assert repository.world_bank_completion is None


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ({"admission_state": "PENDING"}, "admission state"),
        ({"kill_switch": True}, "kill switch"),
        ({"rights_status": "UNKNOWN"}, "rights"),
        ({"commercial_use": False}, "commercial-use"),
        ({"redistribution": False}, "redistribution"),
    ],
)
def test_world_bank_source_policy_rejects_each_missing_authority(
    mutation: dict[str, object],
    expected: str,
) -> None:
    source = {**admitted_world_bank_source(), **mutation}
    reason = research_module.ResearchWorker._source_block_reason(
        source,
        source_id=research_module.WORLD_BANK_SOURCE_ID,
    )
    assert reason is not None
    assert expected.lower() in reason.lower()


def test_ted_source_policy_requires_bounded_non_redistributable_profile() -> None:
    valid = admitted_ted_source()
    assert (
        research_module.ResearchWorker._source_block_reason(
            valid,
            source_id=research_module.TED_SOURCE_ID,
        )
        is None
    )
    invalid_profile = {**valid, "config": {"api_redistribution_allowed": False}}
    assert "profile" in str(
        research_module.ResearchWorker._source_block_reason(
            invalid_profile,
            source_id=research_module.TED_SOURCE_ID,
        )
    ).lower()
    invalid_redistribution = {
        **valid,
        "config": {
            "product_profile": PROFILE_ID,
            "api_redistribution_allowed": True,
        },
    }
    assert "redistribution guard" in str(
        research_module.ResearchWorker._source_block_reason(
            invalid_redistribution,
            source_id=research_module.TED_SOURCE_ID,
        )
    ).lower()


def proposal_worker(
    repository: ProposalRepositoryFake,
    *,
    queue: FakeQueue | None = None,
    document_id: str = DOCUMENT_ID,
    pipeline: object | None = None,
) -> proposal_module.PersistentDocumentProposalWorker:
    return proposal_module.PersistentDocumentProposalWorker(
        repository=repository,  # type: ignore[arg-type]
        queue=queue or FakeQueue(),  # type: ignore[arg-type]
        document=SimpleNamespace(document_id=document_id),  # type: ignore[arg-type]
        pipeline=pipeline or SimpleNamespace(execute=lambda **_: {"result": "ok"}),  # type: ignore[arg-type]
    )


def test_proposal_worker_idle_and_missing_run_are_idempotent() -> None:
    job = proposal_job()
    repository = ProposalRepositoryFake(run=None, source=None)
    worker = proposal_worker(repository, queue=FakeQueue(None, job))

    assert worker.run_once(timeout_seconds=5) is False
    assert worker.run_once(timeout_seconds=2) is True
    assert repository.failures == []
    assert repository.transitions == []


@pytest.mark.parametrize(
    ("run", "job", "document_id", "source", "error_code"),
    [
        (
            {"state": "QUEUED", "job_kind": "OTHER"},
            proposal_job(),
            DOCUMENT_ID,
            admitted_document_source(),
            "JOB_KIND_MISMATCH",
        ),
        (
            {"state": "QUEUED", "job_kind": "DOCUMENT_PROPOSAL"},
            proposal_job(source_id="other"),
            DOCUMENT_ID,
            admitted_document_source(),
            "DOCUMENT_NOT_ROUTED",
        ),
        (
            {"state": "QUEUED", "job_kind": "DOCUMENT_PROPOSAL"},
            proposal_job(pipeline_version="different"),
            DOCUMENT_ID,
            admitted_document_source(),
            "PIPELINE_VERSION_MISMATCH",
        ),
        (
            {"state": "QUEUED", "job_kind": "DOCUMENT_PROPOSAL"},
            proposal_job(),
            "doc_other",
            admitted_document_source(),
            "DOCUMENT_FIXTURE_MISMATCH",
        ),
        (
            {"state": "QUEUED", "job_kind": "DOCUMENT_PROPOSAL"},
            proposal_job(),
            DOCUMENT_ID,
            None,
            "SOURCE_NOT_REGISTERED",
        ),
        (
            {"state": "QUEUED", "job_kind": "DOCUMENT_PROPOSAL"},
            proposal_job(),
            DOCUMENT_ID,
            {**admitted_document_source(), "kill_switch": True},
            "SOURCE_NOT_ADMITTED",
        ),
    ],
)
def test_proposal_worker_rejects_invalid_preconditions(
    run: dict[str, object],
    job: DocumentProposalJob,
    document_id: str,
    source: dict[str, object] | None,
    error_code: str,
) -> None:
    repository = ProposalRepositoryFake(run=run, source=source)

    proposal_worker(repository, document_id=document_id).process(job)

    assert repository.failures[-1]["error_code"] == error_code
    assert repository.persisted is None


def test_proposal_worker_ignores_completed_redelivery() -> None:
    repository = ProposalRepositoryFake(
        run={"state": "COMPLETED_PROVISIONAL", "job_kind": "DOCUMENT_PROPOSAL"},
        source=admitted_document_source(),
    )

    proposal_worker(repository).process(proposal_job())

    assert repository.failures == []
    assert repository.transitions == []


def test_proposal_worker_persists_only_after_full_state_sequence() -> None:
    result = {"proposal": "bounded"}
    repository = ProposalRepositoryFake(
        run={
            "state": "QUEUED",
            "job_kind": "DOCUMENT_PROPOSAL",
            "opportunity_id": "opp-doc",
            "question": "What is supported?",
        },
        source=admitted_document_source(),
    )
    pipeline = SimpleNamespace(execute=lambda **_: result)

    proposal_worker(repository, pipeline=pipeline).process(proposal_job())

    assert repository.transitions == [
        "RETRIEVING",
        "DOCUMENT_PARSING",
        "SECURITY_SCANNING",
        "PROPOSING",
        "EVIDENCE_BINDING",
        "HANDOFF_PENDING",
    ]
    assert repository.persisted is not None
    assert repository.persisted["result"] is result
    assert repository.failures == []


@pytest.mark.parametrize(
    ("failure", "code", "quarantined"),
    [
        (DocumentSecurityError("unsafe document"), "DOCUMENT_SECURITY_QUARANTINE", True),
        (DocumentPipelineError("model contract failed"), "DOCUMENTPIPELINEERROR", False),
        (RuntimeError("runtime failed"), "RUNTIMEERROR", False),
    ],
)
def test_proposal_worker_records_security_and_pipeline_failures(
    failure: BaseException,
    code: str,
    quarantined: bool,
) -> None:
    repository = ProposalRepositoryFake(
        run={
            "state": "QUEUED",
            "job_kind": "DOCUMENT_PROPOSAL",
            "opportunity_id": "opp-doc",
            "question": "Question",
        },
        source=admitted_document_source(),
    )

    def fail(**_: object) -> object:
        raise failure

    proposal_worker(repository, pipeline=SimpleNamespace(execute=fail)).process(proposal_job())

    assert repository.persisted is None
    assert repository.failures[-1]["error_code"] == code
    assert repository.failures[-1]["quarantined"] is quarantined


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ({"admission_state": "PENDING"}, "admission state"),
        ({"kill_switch": True}, "kill switch"),
        ({"rights_status": "UNKNOWN"}, "rights"),
        ({"license_id": "OTHER"}, "license"),
        ({"commercial_use": False}, "permissions"),
        ({"redistribution": False}, "permissions"),
    ],
)
def test_document_source_policy_rejects_each_missing_authority(
    mutation: dict[str, object],
    expected: str,
) -> None:
    reason = proposal_module.PersistentDocumentProposalWorker._source_block_reason(
        {**admitted_document_source(), **mutation}
    )
    assert reason is not None
    assert expected.lower() in reason.lower()


def test_admission_runtime_idle_and_success() -> None:
    job = admission_job()
    result = AdmissionRunResult(
        admission_batch_id=uuid4(),
        canonical_claim_ids=(uuid4(),),
        outcomes=("ADMITTED",),
        idempotent_replay=False,
    )
    repository = AdmissionRepositoryFake(result)
    runtime = admission_module.DeterministicAdmissionRuntime(
        repository=repository,  # type: ignore[arg-type]
        queue=FakeQueue(None, job),  # type: ignore[arg-type]
    )

    assert runtime.run_once(timeout_seconds=4) is False
    assert runtime.run_once(timeout_seconds=2) is True
    assert repository.decided == [job]
    assert repository.failures == []


@pytest.mark.parametrize(
    ("failure", "code", "quarantined"),
    [
        (
            AdmissionIntegrityError("hash mismatch"),
            "ADMISSION_INTEGRITY_QUARANTINE",
            True,
        ),
        (AdmissionPolicyError("policy denied"), "ADMISSIONPOLICYERROR", False),
        (AdmissionRuntimeError("store unavailable"), "ADMISSIONRUNTIMEERROR", False),
        (LookupError("missing evidence"), "LOOKUPERROR", False),
        (ValueError("invalid package"), "VALUEERROR", False),
    ],
)
def test_admission_runtime_fails_closed_with_integrity_quarantine(
    failure: BaseException,
    code: str,
    quarantined: bool,
) -> None:
    job = admission_job()
    repository = AdmissionRepositoryFake(failure)
    runtime = admission_module.DeterministicAdmissionRuntime(
        repository=repository,  # type: ignore[arg-type]
        queue=FakeQueue(),  # type: ignore[arg-type]
    )

    runtime.process(job)

    assert repository.failures[-1]["error_code"] == code
    assert repository.failures[-1]["quarantined"] is quarantined
    assert repository.failures[-1]["job"] == job
