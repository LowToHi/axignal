from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from axignal_api import admission_runtime as admission_module
from axignal_api import proposal_publisher as publisher_module
from axignal_api import proposal_worker as proposal_module
from axignal_api import retention_worker as retention_module
from axignal_api import scheduler_service as scheduler_module
from axignal_api import worker as research_module
from axignal_api.runtime_invariants import (
    RuntimeConfigurationInvariantError,
    require_runtime_value,
)


def setting(**overrides: object) -> SimpleNamespace:
    defaults: dict[str, object] = {
        "database_url": "postgresql://app",
        "proposal_database_url": "postgresql://proposal",
        "admission_database_url": "postgresql://admission",
        "scheduler_database_url": "postgresql://scheduler",
        "valkey_url": "redis://valkey/0",
        "queue_key": "research",
        "proposal_queue_key": "proposal",
        "admission_queue_key": "admission",
        "scheduler_queue_key": "scheduler",
        "live_sources_enabled": False,
        "world_bank_fixture_path": Path("world-bank.json"),
        "ted_live_sources_enabled": False,
        "ted_fixture_path": Path("ted.json"),
        "document_fixture_path": Path("document.json"),
        "document_proposal_fixture_path": Path("proposal.json"),
        "deepseek_proposal_enabled": False,
        "deepseek_api_key": None,
        "deepseek_base_url": "https://api.deepseek.test",
        "deepseek_model": "deepseek-v4-flash",
        "deepseek_max_output_tokens": 2048,
        "deepseek_timeout_seconds": 30.0,
        "local_model_base_url": None,
        "local_model_name": None,
        "local_model_api_key": None,
        "object_store_backend": "memory",
        "object_store_root": Path("objects"),
        "otel_service_name": "axignal-test",
        "purge_lease_seconds": 30,
        "require_persistent_research": lambda: None,
        "require_document_proposal_worker": lambda: None,
        "require_admission_runtime": lambda: None,
        "require_scheduler": lambda: None,
        "require_object_store": lambda: None,
        "require_purge_worker": lambda: None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_runtime_value_is_not_an_optimisable_assertion() -> None:
    marker = object()
    assert require_runtime_value(marker, name="MARKER") is marker
    assert require_runtime_value("configured", name="TEXT") == "configured"

    with pytest.raises(RuntimeConfigurationInvariantError, match="MISSING"):
        require_runtime_value(None, name="MISSING")
    with pytest.raises(RuntimeConfigurationInvariantError, match="EMPTY"):
        require_runtime_value("", name="EMPTY")


def test_retention_worker_idle_and_purge(monkeypatch) -> None:
    now = retention_module.datetime(2026, 8, 1, tzinfo=retention_module.UTC)
    claim_id = uuid4()
    repositories: list[object] = []

    class Repository:
        def __init__(self, dsn: str) -> None:
            assert dsn == "postgresql://retention"
            self.claim_result: dict[str, object] | None = None
            repositories.append(self)

        def queue_due(self, *, now):
            assert now == globals_now
            return 2

        def claim(self, *, worker_id: str, lease_seconds: int, now):
            assert worker_id == "retention-test-host-4242"
            assert lease_seconds == 45
            assert now == globals_now
            return self.claim_result

        def purge(self, *, deletion_id, worker_id: str, now):
            assert deletion_id == claim_id
            assert worker_id == "retention-test-host-4242"
            assert now == globals_now
            return {
                "deletion_id": claim_id,
                "verification_digest": "sha256:tombstone",
            }

    globals_now = now
    monkeypatch.setattr(
        retention_module.RetentionSettings,
        "from_env",
        lambda: setting(
            database_url="postgresql://retention",
            purge_lease_seconds=45,
        ),
    )
    monkeypatch.setattr(retention_module, "RetentionRepository", Repository)
    monkeypatch.setattr(retention_module.socket, "gethostname", lambda: "test-host")
    monkeypatch.setattr(retention_module.os, "getpid", lambda: 4242)

    idle = retention_module.run_once(now=now)
    assert idle == {
        "schema": "axignal.retention-worker-run.v0.1",
        "status": "IDLE",
        "queued": 2,
        "purged": 0,
    }

    repository = repositories[-1]
    repository.claim_result = {"deletion_id": claim_id}  # type: ignore[attr-defined]
    purged = retention_module.run_once(now=now)
    assert purged["status"] == "PURGED"
    assert purged["deletion_id"] == str(claim_id)
    assert purged["verification_digest"] == "sha256:tombstone"


def test_retention_worker_main_emits_machine_readable_result(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        retention_module,
        "run_once",
        lambda: {"status": "IDLE", "queued": 0, "purged": 0},
    )

    assert retention_module.main() == 0
    assert json.loads(capsys.readouterr().out) == {
        "status": "IDLE",
        "queued": 0,
        "purged": 0,
    }


def test_retention_worker_rejects_missing_validated_database(monkeypatch) -> None:
    monkeypatch.setattr(
        retention_module.RetentionSettings,
        "from_env",
        lambda: setting(database_url=None),
    )
    with pytest.raises(RuntimeConfigurationInvariantError):
        retention_module.run_once()


def test_research_build_runtime_wires_independent_components(monkeypatch) -> None:
    constructed: dict[str, object] = {}

    class Repository:
        def __init__(self, dsn: str) -> None:
            constructed["repository"] = dsn

    class Queue:
        def __init__(self, url: str, *, queue_key: str) -> None:
            constructed["queue"] = (url, queue_key)

    class WorldBank:
        def __init__(self, *, live_enabled: bool, fixture_path: Path) -> None:
            constructed["world_bank"] = (live_enabled, fixture_path)

    class Ted:
        def __init__(self, *, live_enabled: bool, fixture_path: Path) -> None:
            constructed["ted"] = (live_enabled, fixture_path)

    class Publisher:
        def __init__(self, repository, queue) -> None:
            self.repository = repository
            self.queue = queue

    monkeypatch.setattr(research_module, "TEDResearchRepository", Repository)
    monkeypatch.setattr(research_module, "ValkeyResearchQueue", Queue)
    monkeypatch.setattr(research_module, "WorldBankConnector", WorldBank)
    monkeypatch.setattr(research_module, "TEDSearchConnector", Ted)
    monkeypatch.setattr(research_module, "OutboxPublisher", Publisher)

    publisher, worker = research_module.build_runtime(setting())  # type: ignore[arg-type]

    assert isinstance(publisher, Publisher)
    assert isinstance(worker, research_module.ResearchWorker)
    assert constructed == {
        "repository": "postgresql://app",
        "queue": ("redis://valkey/0", "research"),
        "world_bank": (False, Path("world-bank.json")),
        "ted": (False, Path("ted.json")),
    }


def test_research_main_once_publishes_before_and_after_work(monkeypatch) -> None:
    calls: list[object] = []
    publisher = SimpleNamespace(
        publish_pending=lambda *, limit: calls.append(("publish", limit)) or 0
    )
    worker = SimpleNamespace(
        run_once=lambda *, timeout_seconds: calls.append(("work", timeout_seconds)) or False
    )
    monkeypatch.setattr(sys, "argv", ["research-worker", "--once"])
    monkeypatch.setattr(research_module.Settings, "from_env", lambda: setting())
    monkeypatch.setattr(research_module, "build_runtime", lambda _: (publisher, worker))

    assert research_module.main() == 0
    assert calls == [("publish", 20), ("work", 1), ("publish", 20)]


def test_proposal_publisher_build_and_once(monkeypatch) -> None:
    constructed: dict[str, object] = {}

    class Repository:
        def __init__(self, *, app_dsn: str) -> None:
            constructed["repository"] = app_dsn

    class Queue:
        def __init__(self, url: str, *, queue_key: str) -> None:
            constructed["queue"] = (url, queue_key)

    class Publisher:
        def __init__(self, repository, queue) -> None:
            self.repository = repository
            self.queue = queue
            self.calls: list[int] = []

        def publish_pending(self, *, limit: int) -> int:
            self.calls.append(limit)
            return 3

    monkeypatch.setattr(publisher_module, "DocumentProposalRepository", Repository)
    monkeypatch.setattr(publisher_module, "ValkeyDocumentProposalQueue", Queue)
    monkeypatch.setattr(publisher_module, "ProposalOutboxPublisher", Publisher)
    publisher = publisher_module.build_publisher(setting())  # type: ignore[arg-type]
    assert isinstance(publisher, Publisher)
    assert constructed == {
        "repository": "postgresql://app",
        "queue": ("redis://valkey/0", "proposal"),
    }

    monkeypatch.setattr(sys, "argv", ["proposal-publisher", "--once"])
    monkeypatch.setattr(publisher_module.Settings, "from_env", lambda: setting())
    monkeypatch.setattr(publisher_module, "build_publisher", lambda _: publisher)
    assert publisher_module.main() == 0
    assert publisher.calls == [20]


def test_admission_build_runtime_and_once(monkeypatch) -> None:
    constructed: dict[str, object] = {}

    class Repository:
        def __init__(self, *, admission_dsn: str) -> None:
            constructed["repository"] = admission_dsn

    class Queue:
        def __init__(self, url: str, *, queue_key: str) -> None:
            constructed["queue"] = (url, queue_key)

        def dequeue(self, *, timeout_seconds: int):
            constructed["timeout"] = timeout_seconds
            return None

    monkeypatch.setattr(admission_module, "AdmissionRepository", Repository)
    monkeypatch.setattr(admission_module, "ValkeyAdmissionQueue", Queue)
    runtime = admission_module.build_runtime(setting())  # type: ignore[arg-type]
    assert constructed == {
        "repository": "postgresql://admission",
        "queue": ("redis://valkey/0", "admission"),
    }

    monkeypatch.setattr(sys, "argv", ["admission-runtime", "--once"])
    monkeypatch.setattr(admission_module.Settings, "from_env", lambda: setting())
    monkeypatch.setattr(admission_module, "build_runtime", lambda _: runtime)
    assert admission_module.main() == 0
    assert constructed["timeout"] == 1


def patch_proposal_runtime_constructors(monkeypatch, constructed: dict[str, object]) -> None:
    class Repository:
        def __init__(self, *, proposal_dsn: str) -> None:
            constructed["repository"] = proposal_dsn

    class Queue:
        def __init__(self, url: str, *, queue_key: str) -> None:
            constructed["queue"] = (url, queue_key)

    class DocumentModel:
        @classmethod
        def model_validate(cls, payload: dict[str, object]):
            constructed["document_payload"] = payload
            return SimpleNamespace(document_id="doc_fixture")

    class ProposalModel:
        @classmethod
        def model_validate(cls, payload: dict[str, object]):
            constructed["proposal_payload"] = payload
            return payload

    class Pipeline:
        def __init__(self, *, model_gateway) -> None:
            constructed["gateway"] = model_gateway

    monkeypatch.setattr(proposal_module, "DocumentProposalRepository", Repository)
    monkeypatch.setattr(proposal_module, "ValkeyDocumentProposalQueue", Queue)
    monkeypatch.setattr(proposal_module, "InstitutionalDocument", DocumentModel)
    monkeypatch.setattr(proposal_module, "ProposalBatch", ProposalModel)
    monkeypatch.setattr(proposal_module, "LocalDocumentProposalPipeline", Pipeline)
    monkeypatch.setattr(
        proposal_module,
        "_load_json",
        lambda path: {"fixture": str(path)},
    )


def test_proposal_build_runtime_supports_frozen_local_and_deepseek(monkeypatch) -> None:
    constructed: dict[str, object] = {}
    patch_proposal_runtime_constructors(monkeypatch, constructed)

    class Frozen:
        def __init__(self, proposal) -> None:
            self.kind = "frozen"
            self.proposal = proposal

    class Local:
        def __init__(self, **kwargs: object) -> None:
            self.kind = "local"
            self.kwargs = kwargs

    class DeepSeek:
        def __init__(self, **kwargs: object) -> None:
            self.kind = "deepseek"
            self.kwargs = kwargs

    monkeypatch.setattr(proposal_module, "FrozenProposalAdapter", Frozen)
    monkeypatch.setattr(proposal_module, "OpenAICompatibleLocalModelAdapter", Local)
    monkeypatch.setattr(proposal_module, "DeepSeekV4FlashProposalAdapter", DeepSeek)

    frozen = proposal_module.build_runtime(setting())  # type: ignore[arg-type]
    assert isinstance(constructed["gateway"], Frozen)
    assert isinstance(frozen, proposal_module.PersistentDocumentProposalWorker)

    proposal_module.build_runtime(  # type: ignore[arg-type]
        setting(
            local_model_base_url="http://local-model",
            local_model_name="bounded-model",
            local_model_api_key=None,
        )
    )
    local = constructed["gateway"]
    assert isinstance(local, Local)
    assert local.kwargs["api_key"] == "local-only"

    proposal_module.build_runtime(  # type: ignore[arg-type]
        setting(
            deepseek_proposal_enabled=True,
            deepseek_api_key="test-key",
        )
    )
    deepseek = constructed["gateway"]
    assert isinstance(deepseek, DeepSeek)
    assert deepseek.kwargs["api_key"] == "test-key"


def test_proposal_build_runtime_fails_closed_for_missing_model_configuration(
    monkeypatch,
) -> None:
    patch_proposal_runtime_constructors(monkeypatch, {})

    with pytest.raises(RuntimeError, match="AXIGNAL_LOCAL_MODEL_NAME"):
        proposal_module.build_runtime(  # type: ignore[arg-type]
            setting(local_model_base_url="http://local-model", local_model_name=None)
        )

    with pytest.raises(RuntimeConfigurationInvariantError, match="DEEPSEEK_API_KEY"):
        proposal_module.build_runtime(  # type: ignore[arg-type]
            setting(deepseek_proposal_enabled=True, deepseek_api_key=None)
        )

    with pytest.raises(
        RuntimeConfigurationInvariantError,
        match="DOCUMENT_PROPOSAL_FIXTURE_PATH",
    ):
        proposal_module.build_runtime(  # type: ignore[arg-type]
            setting(document_proposal_fixture_path=None)
        )


def test_load_json_rejects_non_object_fixture(tmp_path: Path) -> None:
    valid = tmp_path / "valid.json"
    valid.write_text('{"key": "value"}', encoding="utf-8")
    assert proposal_module._load_json(valid) == {"key": "value"}

    invalid = tmp_path / "invalid.json"
    invalid.write_text("[]", encoding="utf-8")
    with pytest.raises(RuntimeError, match="must contain a JSON object"):
        proposal_module._load_json(invalid)


def test_proposal_main_once_processes_at_most_one_job(monkeypatch) -> None:
    calls: list[int] = []
    worker = SimpleNamespace(
        run_once=lambda *, timeout_seconds: calls.append(timeout_seconds) or False
    )
    monkeypatch.setattr(sys, "argv", ["proposal-worker", "--once"])
    monkeypatch.setattr(proposal_module.Settings, "from_env", lambda: setting())
    monkeypatch.setattr(proposal_module, "build_runtime", lambda _: worker)

    assert proposal_module.main() == 0
    assert calls == [1]


def test_scheduler_healthcheck_verifies_database_valkey_and_local_store(
    monkeypatch,
    tmp_path: Path,
) -> None:
    events: list[object] = []

    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def execute(self, query: str) -> None:
            events.append(("sql", query))

    class RedisClient:
        def ping(self) -> bool:
            events.append("redis")
            return True

    monkeypatch.setattr(
        scheduler_module.psycopg,
        "connect",
        lambda dsn: events.append(("connect", dsn)) or Connection(),
    )
    monkeypatch.setattr(
        scheduler_module.Redis,
        "from_url",
        lambda url: events.append(("valkey", url)) or RedisClient(),
    )

    result = scheduler_module.healthcheck(
        setting(
            object_store_backend="local",
            object_store_root=tmp_path,
        )  # type: ignore[arg-type]
    )

    assert result == 0
    assert ("connect", "postgresql://scheduler") in events
    assert ("sql", "SELECT 1") in events
    assert ("valkey", "redis://valkey/0") in events
    assert "redis" in events
    assert any(path.is_file() for path in tmp_path.rglob("*"))


def test_scheduler_run_loop_recovers_publishes_works_and_backs_off(monkeypatch) -> None:
    calls: list[object] = []

    class Repository:
        def __init__(self, dsn: str) -> None:
            calls.append(("repository", dsn))

        def recover_expired_leases(self) -> int:
            calls.append("recover")
            return 0

    class Queue:
        def __init__(self, url: str, *, queue_key: str) -> None:
            calls.append(("queue", url, queue_key))

    class Publisher:
        def __init__(self, repository, queue, *, tracer) -> None:
            calls.append("publisher")

        def publish_pending(self) -> int:
            calls.append("publish")
            return 0

    class Worker:
        def __init__(self, **_: object) -> None:
            calls.append("worker")

        def run_once(self, *, timeout_seconds: int) -> bool:
            calls.append(("work", timeout_seconds))
            return False

    monkeypatch.setattr(scheduler_module, "SchedulerRepository", Repository)
    monkeypatch.setattr(scheduler_module, "ValkeySchedulerQueue", Queue)
    monkeypatch.setattr(scheduler_module, "SchedulerOutboxPublisher", Publisher)
    monkeypatch.setattr(scheduler_module, "SchedulerWorker", Worker)
    monkeypatch.setattr(scheduler_module, "default_handlers", lambda repository: {"h": repository})
    monkeypatch.setattr(scheduler_module, "build_tracer_provider", lambda **_: object())
    monkeypatch.setattr(scheduler_module, "tracer_for", lambda *_: object())

    def stop_after_backoff(seconds: float) -> None:
        calls.append(("sleep", seconds))
        raise StopIteration

    monkeypatch.setattr(scheduler_module.time, "sleep", stop_after_backoff)

    with pytest.raises(StopIteration):
        scheduler_module.run_forever(setting())  # type: ignore[arg-type]

    assert calls[-4:] == ["recover", "publish", ("work", 1), ("sleep", 1)]


def test_scheduler_main_routes_healthcheck(monkeypatch) -> None:
    runtime_settings = setting()
    monkeypatch.setattr(sys, "argv", ["scheduler", "--healthcheck"])
    monkeypatch.setattr(scheduler_module.Settings, "from_env", lambda: runtime_settings)
    monkeypatch.setattr(
        scheduler_module,
        "healthcheck",
        lambda value: int(value is runtime_settings) - 1,
    )

    assert scheduler_module.main() == 0
