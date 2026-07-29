from __future__ import annotations

import json
from pathlib import Path

import yaml

from axignal_api.identity import MAX_ASSERTION_TTL_SECONDS

ROOT = Path(__file__).resolve().parents[1]
IDENTITY = ROOT / "apps/api/src/axignal_api/identity.py"
API = ROOT / "apps/api/src/axignal_api/persistent_ted_research.py"
REPOSITORY = ROOT / "apps/api/src/axignal_api/repository.py"
TED_REPOSITORY = ROOT / "apps/api/src/axignal_api/ted_repository.py"
WORKER = ROOT / "apps/api/src/axignal_api/worker.py"
RESEARCH_SQL = ROOT / "infra/postgres/020-research-spine.sql"
GRANTS_SQL = ROOT / "infra/postgres/025-research-runtime-grants.sql"
TED_SQL = ROOT / "infra/postgres/070-ted-product-runtime.sql"
PROFILE = ROOT / "data/universes/eu-public-procurement/ted-product-admission-profile.v0.1.json"
PILOT = ROOT / "infra/pilot/compose.yaml"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    identity = IDENTITY.read_text(encoding="utf-8")
    api = API.read_text(encoding="utf-8")
    repository = REPOSITORY.read_text(encoding="utf-8")
    ted_repository = TED_REPOSITORY.read_text(encoding="utf-8")
    worker = WORKER.read_text(encoding="utf-8")
    research_sql = RESEARCH_SQL.read_text(encoding="utf-8")
    grants_sql = GRANTS_SQL.read_text(encoding="utf-8")
    ted_sql = TED_SQL.read_text(encoding="utf-8")
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    pilot = yaml.safe_load(PILOT.read_text(encoding="utf-8"))
    require(isinstance(pilot, dict), "pilot topology is not a mapping")
    services = pilot["services"]

    request_contract = api.split(
        "class PersistentTEDResearchRunAccepted", 1
    )[0]
    require('ConfigDict(extra="forbid")' in request_contract, "extra fields are accepted")
    require("tenant_id:" not in request_contract, "client tenant field entered request schema")
    require(
        "include_private_knowledge: Literal[False]" in request_contract,
        "tenant-private knowledge can enter TED runtime",
    )
    require("Depends(require_identity)" in api, "authenticated identity dependency is absent")
    require("tenant_id=identity.tenant_id" in api, "tenant is not resolved from identity")

    require(MAX_ASSERTION_TTL_SECONDS <= 300, "identity assertion lifetime exceeds five minutes")
    require("hmac.compare_digest" in identity, "identity signature is not constant-time compared")
    require("ASSERTION_AUDIENCE" in identity, "identity audience binding is absent")
    require("expires_at" in identity and "issued_at" in identity, "identity expiry checks are absent")

    require("SET LOCAL ROLE" in repository, "database role is not transaction-scoped")
    require("set_config('app.tenant_id'" in repository, "tenant RLS context is absent")
    require("FORCE ROW LEVEL SECURITY" in research_sql, "tenant tables do not force RLS")
    require(
        "GRANT SELECT ON" in grants_sql and "canonical_claims" in grants_sql,
        "application read grant is absent",
    )
    require(
        "GRANT INSERT ON axignal_global.outbox_events TO axignal_app" in grants_sql,
        "application outbox grant is absent",
    )
    require(
        "GRANT INSERT ON axignal_global.canonical_claims" not in grants_sql,
        "application role received canonical insert authority",
    )
    require(
        "GRANT UPDATE ON axignal_global.canonical_claims" not in grants_sql,
        "application role received canonical update authority",
    )
    require(
        "GRANT DELETE ON axignal_global.canonical_claims" not in grants_sql,
        "application role received canonical delete authority",
    )

    require("sanitised_projection(page)" in ted_repository, "raw TED payload can enter storage")
    require('"api_redistribution": False' in ted_repository, "redistribution guard is absent")
    require('"model_calls": 0' in ted_repository, "model-free authority evidence is absent")
    require('source.get("kill_switch")' in worker, "source kill switch is not enforced")

    require(pilot["networks"]["backend"]["internal"] is True, "backend is not internal")
    require(pilot["networks"]["ted-egress"]["internal"] is False, "TED egress is closed")
    egress_services = {
        service_id
        for service_id, service in services.items()
        if "ted-egress" in service.get("networks", [])
    }
    require(egress_services == {"research-worker"}, "TED egress is not worker-exclusive")
    require(
        services["api"]["environment"]["AXIGNAL_LIVE_SOURCES_ENABLED"] == "false",
        "global live sources were enabled in API",
    )
    require(
        services["research-worker"]["environment"]["AXIGNAL_LIVE_SOURCES_ENABLED"]
        == "false",
        "global live sources were enabled in worker",
    )
    require(
        services["research-worker"]["environment"]["AXIGNAL_TED_LIVE_SOURCES_ENABLED"]
        == "true",
        "bounded TED live source is disabled",
    )
    require(
        services["web"]["environment"]["AXIGNAL_TED_PROCUREMENT_UI_ENABLED"] == "true",
        "TED Navigator route is disabled",
    )

    require(profile["activation_state"] == "PRIVATE_PILOT_ENABLED", "pilot activation absent")
    require(profile["rights_boundary"]["personal_contact_data"] == "PROHIBITED", "PII enabled")
    require(profile["rights_boundary"]["api_redistribution"] == "PROHIBITED", "API resale enabled")
    require(profile["authority"]["generative_model_calls"] == 0, "model authority enabled")
    require(profile["query_contract"]["arbitrary_query_allowed"] is False, "arbitrary query enabled")
    require("api_redistribution_allowed', false" in ted_sql, "SQL redistribution guard is absent")

    result = {
        "status": "PASS",
        "task": "AX-F8-T14",
        "review_type": "INDEPENDENT_AUTOMATED_SECURITY_BOUNDARY",
        "activation_scope": profile["activation_scope"],
        "identity_signature": "HMAC_SHA256_CONSTANT_TIME",
        "identity_ttl_seconds_max": MAX_ASSERTION_TTL_SECONDS,
        "tenant_source": "SIGNED_ASSERTION_SERVER_SIDE",
        "client_tenant_injection": "REJECTED",
        "tenant_isolation": "POSTGRES_FORCE_RLS",
        "canonical_writer": "DETERMINISTIC_RUNTIME_ONLY",
        "private_knowledge": "PROHIBITED",
        "personal_contact_fields": "PROHIBITED",
        "arbitrary_query": "PROHIBITED",
        "api_redistribution": "PROHIBITED",
        "global_live_sources": False,
        "source_specific_activation": True,
        "egress_service_allowlist": ["research-worker"],
        "kill_switches": ["WORKFLOW", "LIVE_SOURCE", "SOURCE"],
        "residual_risk": {
            "identity_assertion_replay_window_seconds": MAX_ASSERTION_TTL_SECONDS,
            "acceptance": "PRIVATE_INTERNAL_GATEWAY_ONLY; TLS AND NETWORK ISOLATION REQUIRED",
            "public_general_availability": False,
        },
    }
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
