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


def _int_env(name: str, default: int) -> int:
    value = environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc


def _float_env(name: str, default: float) -> float:
    value = environ.get(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be numeric") from exc


@dataclass(frozen=True)
class Settings:
    database_url: str | None
    valkey_url: str | None
    proposal_database_url: str | None
    persistent_research_enabled: bool
    live_sources_enabled: bool
    ted_procurement_enabled: bool
    world_bank_fixture_path: Path | None
    ted_fixture_path: Path | None
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
    deepseek_proposal_enabled: bool = False
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"
    deepseek_api_key: str | None = None
    deepseek_max_output_tokens: int = 1_200
    deepseek_timeout_seconds: float = 45.0

    @classmethod
    def from_env(cls) -> "Settings":
        fixture = environ.get("AXIGNAL_WORLD_BANK_FIXTURE_PATH")
        ted_fixture = environ.get("AXIGNAL_TED_FIXTURE_PATH")
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
            ted_procurement_enabled=_bool_env("AXIGNAL_TED_PROCUREMENT_ENABLED"),
            world_bank_fixture_path=Path(fixture).resolve() if fixture else None,
            ted_fixture_path=Path(ted_fixture).resolve() if ted_fixture else None,
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
            deepseek_proposal_enabled=_bool_env(
                "AXIGNAL_DEEPSEEK_PROPOSAL_ENABLED"
            ),
            deepseek_base_url=environ.get(
                "AXIGNAL_DEEPSEEK_BASE_URL",
                "https://api.deepseek.com",
            ).rstrip("/"),
            deepseek_model=environ.get(
                "AXIGNAL_DEEPSEEK_MODEL",
                "deepseek-v4-flash",
            ),
            deepseek_api_key=environ.get("DEEPSEEK_API_KEY"),
            deepseek_max_output_tokens=_int_env(
                "AXIGNAL_DEEPSEEK_MAX_OUTPUT_TOKENS",
                1_200,
            ),
            deepseek_timeout_seconds=_float_env(
                "AXIGNAL_DEEPSEEK_TIMEOUT_SECONDS",
                45.0,
            ),
        )

    def require_persistent_research(self) -> None:
        if not self.persistent_research_enabled:
            raise RuntimeError("Persistent research is disabled")
        if not self.database_url:
            raise RuntimeError("AXIGNAL_DATABASE_URL is required")
        if not self.valkey_url:
            raise RuntimeError("AXIGNAL_VALKEY_URL is required")

    def require_ted_procurement(self) -> None:
        self.require_persistent_research()
        if not self.ted_procurement_enabled:
            raise RuntimeError("TED procurement runtime is disabled")
        if not self.live_sources_enabled and not self.ted_fixture_path:
            raise RuntimeError(
                "AXIGNAL_TED_FIXTURE_PATH is required when live sources are disabled"
            )

    def require_document_proposal_worker(self) -> None:
        if not self.persistent_research_enabled:
            raise RuntimeError("Persistent research is disabled")
        if not self.proposal_database_url:
            raise RuntimeError("AXIGNAL_PROPOSAL_DATABASE_URL is required")
        if not self.valkey_url:
            raise RuntimeError("AXIGNAL_VALKEY_URL is required")
        if not self.document_fixture_path:
            raise RuntimeError("AXIGNAL_DOCUMENT_FIXTURE_PATH is required")
        if self.deepseek_proposal_enabled and self.local_model_base_url:
            raise RuntimeError(
                "DeepSeek and the local proposal endpoint cannot be enabled together"
            )
        if self.deepseek_proposal_enabled:
            if not self.deepseek_api_key:
                raise RuntimeError("DEEPSEEK_API_KEY is required")
            if self.deepseek_model != "deepseek-v4-flash":
                raise RuntimeError(
                    "AXIGNAL_DEEPSEEK_MODEL must be deepseek-v4-flash"
                )
            return
        if not self.local_model_base_url and not self.document_proposal_fixture_path:
            raise RuntimeError(
                "AXIGNAL_DOCUMENT_PROPOSAL_FIXTURE_PATH is required without a model endpoint"
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
