from dataclasses import dataclass
from os import environ
from pathlib import Path


def _bool_env(name: str, default: bool = False) -> bool:
    value = environ.get(name)
    if value is None:
        return default
    return value.strip().casefold() in {"1", "true", "yes", "on"}


def _csv_env(name: str) -> tuple[str, ...]:
    value = environ.get(name, "")
    return tuple(item.strip() for item in value.split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    database_url: str | None
    valkey_url: str | None
    proposal_database_url: str | None
    persistent_research_enabled: bool
    live_sources_enabled: bool
    world_bank_fixture_path: Path | None
    queue_key: str
    proposal_queue_key: str
    document_fixture_path: Path | None
    document_proposal_fixture_path: Path | None
    local_model_base_url: str | None
    local_model_name: str | None
    local_model_api_key: str | None
    identity_assertion_secret: str | None
    admission_database_url: str | None = None
    admission_queue_key: str = "axignal:admission:queue:v1"
    human_review_database_url: str | None = None
    human_reviewer_subjects: tuple[str, ...] = ()
    scheduler_database_url: str | None = None
    scheduler_queue_key: str = "axignal:scheduler:queue:v1"
    scheduler_enabled: bool = False
    object_store_backend: str = "local"
    object_store_root: Path = Path(".axignal/objects")
    otel_enabled: bool = False
    otel_service_name: str = "axignal-local"
    otel_exporter_otlp_endpoint: str | None = None
    validation_database_url: str | None = None
    validation_participant_salt: str | None = None
    validation_enabled: bool = False

    @classmethod
    def from_env(cls) -> "Settings":
        fixture = environ.get("AXIGNAL_WORLD_BANK_FIXTURE_PATH")
        document_fixture = environ.get("AXIGNAL_DOCUMENT_FIXTURE_PATH")
        proposal_fixture = environ.get("AXIGNAL_DOCUMENT_PROPOSAL_FIXTURE_PATH")
        object_store_root = environ.get("AXIGNAL_OBJECT_STORE_ROOT", ".axignal/objects")
        return cls(
            database_url=environ.get("AXIGNAL_DATABASE_URL"),
            valkey_url=environ.get("AXIGNAL_VALKEY_URL"),
            proposal_database_url=environ.get("AXIGNAL_PROPOSAL_DATABASE_URL"),
            admission_database_url=environ.get("AXIGNAL_ADMISSION_DATABASE_URL"),
            human_review_database_url=environ.get(
                "AXIGNAL_HUMAN_REVIEW_DATABASE_URL"
            ),
            human_reviewer_subjects=_csv_env("AXIGNAL_HUMAN_REVIEWER_SUBJECTS"),
            scheduler_database_url=environ.get("AXIGNAL_SCHEDULER_DATABASE_URL"),
            scheduler_queue_key=environ.get(
                "AXIGNAL_SCHEDULER_QUEUE_KEY",
                "axignal:scheduler:queue:v1",
            ),
            scheduler_enabled=_bool_env("AXIGNAL_SCHEDULER_ENABLED"),
            object_store_backend=environ.get(
                "AXIGNAL_OBJECT_STORE_BACKEND",
                "local",
            ).strip().casefold(),
            object_store_root=Path(object_store_root).resolve(),
            otel_enabled=_bool_env("AXIGNAL_OTEL_ENABLED"),
            otel_service_name=environ.get("OTEL_SERVICE_NAME", "axignal-local"),
            otel_exporter_otlp_endpoint=environ.get(
                "OTEL_EXPORTER_OTLP_ENDPOINT"
            ),
            validation_database_url=environ.get("AXIGNAL_VALIDATION_DATABASE_URL"),
            validation_participant_salt=environ.get(
                "AXIGNAL_VALIDATION_PARTICIPANT_SALT"
            ),
            validation_enabled=_bool_env("AXIGNAL_VALIDATION_ENABLED"),
            persistent_research_enabled=_bool_env(
                "AXIGNAL_PERSISTENT_RESEARCH_ENABLED"
            ),
            live_sources_enabled=_bool_env("AXIGNAL_LIVE_SOURCES_ENABLED"),
            world_bank_fixture_path=Path(fixture).resolve() if fixture else None,
            queue_key=environ.get(
                "AXIGNAL_RESEARCH_QUEUE_KEY",
                "axignal:research:queue:v1",
            ),
            proposal_queue_key=environ.get(
                "AXIGNAL_PROPOSAL_QUEUE_KEY",
                "axignal:proposal:queue:v1",
            ),
            admission_queue_key=environ.get(
                "AXIGNAL_ADMISSION_QUEUE_KEY",
                "axignal:admission:queue:v1",
            ),
            document_fixture_path=(
                Path(document_fixture).resolve() if document_fixture else None
            ),
            document_proposal_fixture_path=(
                Path(proposal_fixture).resolve() if proposal_fixture else None
            ),
            local_model_base_url=environ.get("AXIGNAL_LOCAL_MODEL_BASE_URL"),
            local_model_name=environ.get("AXIGNAL_LOCAL_MODEL_NAME"),
            local_model_api_key=environ.get("AXIGNAL_LOCAL_MODEL_API_KEY"),
            identity_assertion_secret=environ.get(
                "AXIGNAL_IDENTITY_ASSERTION_SECRET"
            ),
        )

    def require_persistent_research(self) -> None:
        if not self.persistent_research_enabled:
            raise RuntimeError("Persistent research is disabled")
        if not self.database_url:
            raise RuntimeError("AXIGNAL_DATABASE_URL is required")
        if not self.valkey_url:
            raise RuntimeError("AXIGNAL_VALKEY_URL is required")

    def require_document_proposal_worker(self) -> None:
        if not self.persistent_research_enabled:
            raise RuntimeError("Persistent research is disabled")
        if not self.proposal_database_url:
            raise RuntimeError("AXIGNAL_PROPOSAL_DATABASE_URL is required")
        if not self.valkey_url:
            raise RuntimeError("AXIGNAL_VALKEY_URL is required")
        if not self.document_fixture_path:
            raise RuntimeError("AXIGNAL_DOCUMENT_FIXTURE_PATH is required")
        if not self.local_model_base_url and not self.document_proposal_fixture_path:
            raise RuntimeError(
                "AXIGNAL_DOCUMENT_PROPOSAL_FIXTURE_PATH is required without a local endpoint"
            )

    def require_admission_runtime(self) -> None:
        if not self.persistent_research_enabled:
            raise RuntimeError("Persistent research is disabled")
        if not self.admission_database_url:
            raise RuntimeError("AXIGNAL_ADMISSION_DATABASE_URL is required")
        if not self.valkey_url:
            raise RuntimeError("AXIGNAL_VALKEY_URL is required")

    def require_human_review(self) -> None:
        if not self.persistent_research_enabled:
            raise RuntimeError("Persistent research is disabled")
        if not self.human_review_database_url:
            raise RuntimeError("AXIGNAL_HUMAN_REVIEW_DATABASE_URL is required")
        if not self.human_reviewer_subjects:
            raise RuntimeError("AXIGNAL_HUMAN_REVIEWER_SUBJECTS is required")

    def require_scheduler(self) -> None:
        if not self.scheduler_enabled:
            raise RuntimeError("Scheduler is disabled")
        if not self.scheduler_database_url:
            raise RuntimeError("AXIGNAL_SCHEDULER_DATABASE_URL is required")
        if not self.valkey_url:
            raise RuntimeError("AXIGNAL_VALKEY_URL is required")

    def require_object_store(self) -> None:
        if self.object_store_backend not in {"memory", "local", "s3"}:
            raise RuntimeError("AXIGNAL_OBJECT_STORE_BACKEND is unsupported")
        if self.object_store_backend == "local":
            self.object_store_root.mkdir(parents=True, exist_ok=True)

    def require_validation(self) -> None:
        if not self.validation_enabled:
            raise RuntimeError("Qualified-user validation is disabled")
        if not self.validation_database_url:
            raise RuntimeError("AXIGNAL_VALIDATION_DATABASE_URL is required")
        if not self.validation_participant_salt:
            raise RuntimeError("AXIGNAL_VALIDATION_PARTICIPANT_SALT is required")
        if len(self.validation_participant_salt.encode("utf-8")) < 32:
            raise RuntimeError(
                "AXIGNAL_VALIDATION_PARTICIPANT_SALT must be at least 32 bytes"
            )

    def require_identity_assertions(self) -> None:
        if not self.identity_assertion_secret:
            raise RuntimeError("AXIGNAL_IDENTITY_ASSERTION_SECRET is required")
        if len(self.identity_assertion_secret.encode("utf-8")) < 32:
            raise RuntimeError(
                "AXIGNAL_IDENTITY_ASSERTION_SECRET must be at least 32 bytes"
            )
