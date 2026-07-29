from __future__ import annotations

import json
from pathlib import Path

from axignal_api.connectors.ted import FIXED_FIELDS, SOURCE_ID, TEDSearchConnector
from axignal_api.ted_runtime import (
    PROFILE_ID,
    build_ted_search_artifacts,
    evaluate_ted_observed_field,
    sanitised_projection,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "data" / "sources" / "ted-search-api-v3.v0.1.json"
PROFILE_PATH = (
    ROOT
    / "data"
    / "universes"
    / "eu-public-procurement"
    / "ted-product-admission-profile.v0.1.json"
)
RIGHTS_PATH = ROOT / "docs" / "sources" / "ted-product-admission-v0.1.md"
SECURITY_PATH = ROOT / "docs" / "security" / "AX-F8-T14-ted-runtime-security-review.md"
TASK_PATH = ROOT / "docs" / "roadmap" / "tasks" / "AX-F8-T14.json"
F9_TASK_PATH = ROOT / "docs" / "roadmap" / "tasks" / "AX-F9-T15.json"
MIGRATION_PATH = ROOT / "infra" / "postgres" / "070-ted-product-runtime.sql"
PILOT_PATH = ROOT / "infra" / "pilot" / "compose.yaml"
API_PATH = ROOT / "apps" / "api" / "src" / "axignal_api" / "persistent_ted_research.py"
WORKER_PATH = ROOT / "apps" / "api" / "src" / "axignal_api" / "worker.py"
REPOSITORY_PATH = ROOT / "apps" / "api" / "src" / "axignal_api" / "ted_repository.py"
WEB_ROUTE_PATH = ROOT / "apps" / "web" / "app" / "api" / "research" / "runs" / "route.ts"
FIXTURE_PATH = ROOT / "apps" / "api" / "tests" / "fixtures" / "ted_search_probe.json"


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path.relative_to(ROOT)} must contain an object")
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def admitted_source_for_runtime(source: dict, profile: dict) -> dict:
    return {
        "source_id": source["source_id"],
        "admission_state": "ADMITTED",
        "kill_switch": source["kill_switch_enabled"],
        "rights_status": "COMMERCIAL_REUSE_WITH_ATTRIBUTION",
        "commercial_use": source["rights"]["customer_display"] == "PERMITTED",
        "redistribution": False,
        "license_id": "TED-LEGAL-NOTICE-REUSE",
        "config": {
            "product_profile": profile["profile_id"],
            "api_redistribution_allowed": False,
        },
    }


def validate_source_and_profile() -> tuple[dict, dict]:
    source = load_json(SOURCE_PATH)
    profile = load_json(PROFILE_PATH)
    require(source["source_id"] == SOURCE_ID, "TED source identifier drifted")
    require(source["status"] == "PRODUCT_ADMITTED", "TED source is not product admitted")
    require(source["kill_switch_enabled"] is False, "TED source kill switch remains enabled")
    require(source["contains_personal_data"] is True, "TED personal-data risk was hidden")
    rights = source["rights"]
    for operation in (
        "collection",
        "transient_processing",
        "persistent_storage",
        "derived_calculations",
        "internal_display",
        "customer_display",
        "export",
    ):
        require(rights[operation] == "PERMITTED", f"TED {operation} is not admitted")
    require(rights["api_redistribution"] == "PROHIBITED", "API redistribution was enabled")
    require(rights["model_training"] == "PROHIBITED", "model training was enabled")
    require(rights["attribution_required"] is True, "TED attribution requirement is absent")

    require(
        profile["status"] == "PRODUCT_ADMITTED_BOUNDED_PROFILE",
        "TED product profile status drifted",
    )
    require(profile["source_id"] == SOURCE_ID, "TED profile points to another source")
    require(profile["profile_id"] == PROFILE_ID, "TED profile identifier drifted")
    require(profile["runtime_default"] == "DISABLED", "TED runtime default was enabled")
    require(
        profile["activation_state"] == "PRIVATE_PILOT_ENABLED",
        "TED private-pilot activation is absent",
    )
    require(
        profile["activation_scope"] == "AUTHENTICATED_VERIFIED_ORGANISATIONS",
        "TED activation scope is too broad",
    )
    require(
        profile["live_source_flag"] == "AXIGNAL_TED_LIVE_SOURCES_ENABLED",
        "TED live-source flag drifted",
    )
    require(
        tuple(profile["field_allowlist"]) == FIXED_FIELDS,
        "TED field allowlist differs from connector contract",
    )
    require(profile["query_contract"]["limit"] == 3, "TED notice budget drifted")
    require(
        profile["authority"]["generative_model_calls"] == 0,
        "TED admitted profile permits model calls",
    )
    require(
        profile["rights_boundary"]["api_redistribution"] == "PROHIBITED",
        "TED API redistribution guard drifted",
    )
    return source, profile


def validate_deterministic_artifacts(source: dict, profile: dict) -> dict[str, int]:
    page = TEDSearchConnector(
        live_enabled=False,
        fixture_path=FIXTURE_PATH,
    ).fetch_probe_page()
    projection = sanitised_projection(page)
    encoded = json.dumps(projection, sort_keys=True)
    require("links" not in encoded, "unrequested TED links survived sanitisation")
    require("xml" not in encoded, "unrequested TED XML link survived sanitisation")

    evidence, candidates = build_ted_search_artifacts(
        page=page,
        opportunity_id="opp_eu_procurement_verification",
    )
    require(len(evidence) == 7, "unexpected TED evidence count")
    require(len(candidates) == 7, "unexpected TED candidate count")
    runtime_source = admitted_source_for_runtime(source, profile)
    decisions = tuple(
        evaluate_ted_observed_field(
            source=runtime_source,
            evidence=evidence_item,
            candidate=candidate,
        )
        for evidence_item, candidate in zip(evidence, candidates, strict=True)
    )
    require(all(item.admitted for item in decisions), "exact TED observed fields were blocked")
    require(
        all(item.epistemic_class == "OBSERVED_FACT" for item in decisions),
        "TED epistemic class drifted",
    )
    return {
        "notice_count": len(page.notices),
        "evidence_count": len(evidence),
        "candidate_count": len(candidates),
        "admitted_count": sum(item.admitted for item in decisions),
    }


def validate_wiring() -> None:
    migration = MIGRATION_PATH.read_text(encoding="utf-8")
    api = API_PATH.read_text(encoding="utf-8")
    worker = WORKER_PATH.read_text(encoding="utf-8")
    repository = REPOSITORY_PATH.read_text(encoding="utf-8")
    web_route = WEB_ROUTE_PATH.read_text(encoding="utf-8")
    pilot = PILOT_PATH.read_text(encoding="utf-8")
    rights = RIGHTS_PATH.read_text(encoding="utf-8")
    security = SECURITY_PATH.read_text(encoding="utf-8")
    task = load_json(TASK_PATH)
    f9_task = load_json(F9_TASK_PATH)

    require("'TED_PROCUREMENT'" in migration, "TED job kind is absent from migration")
    require("'ADMITTED'" in migration, "TED source is not admitted in PostgreSQL")
    require("api_redistribution_allowed', false" in migration, "SQL redistribution guard missing")
    require("/research-runs/ted-procurement" in api, "TED API route is absent")
    require("settings.require_ted_procurement()" in api, "TED API flag gate is absent")
    require('ConfigDict(extra="forbid")' in api, "TED request does not reject extra fields")
    require("build_ted_search_artifacts" in worker, "TED worker route is absent")
    require("complete_ted_run" in worker, "TED completion path is absent")
    require("ted_live_sources_enabled" in worker, "TED live activation is not source-specific")
    require("sanitised_projection(page)" in repository, "TED projection sanitisation is absent")
    require('model_calls": 0' in repository, "TED zero-model usage evidence is absent")
    require("TED_PROCUREMENT" in web_route, "Navigator TED route is absent")
    require("AXIGNAL_TED_PROCUREMENT_UI_ENABLED" in web_route, "TED UI flag is absent")
    require('AXIGNAL_TED_PROCUREMENT_ENABLED: "true"' in pilot, "pilot API/worker flag is absent")
    require('AXIGNAL_TED_LIVE_SOURCES_ENABLED: "true"' in pilot, "pilot live TED flag is absent")
    require('AXIGNAL_TED_PROCUREMENT_UI_ENABLED: "true"' in pilot, "pilot TED UI is absent")
    require('AXIGNAL_LIVE_SOURCES_ENABLED: "false"' in pilot, "pilot enabled all live sources")
    require("PRODUCT_ADMITTED" in rights, "TED rights record does not state admission")
    require("PASS / PRIVATE-PILOT PRODUCT RUNTIME" in security, "security decision is absent")
    require(task["state"] == "ACCEPTED", "AX-F8-T14 is not accepted")
    require(task["rollback"]["tested"] is True, "TED rollback is not declared tested")
    user_research = next(
        item for item in task["acceptance_evidence"] if item["evidence_type"] == "USER_RESEARCH"
    )
    require(user_research["required"] is False, "F9 commercial research still blocks F8")
    require(user_research["status"] == "NOT_APPLICABLE", "F8 fabricates user research")
    require(f9_task["state"] != "ACCEPTED", "F9 commercial validation was silently accepted")


def main() -> None:
    source, profile = validate_source_and_profile()
    summary = validate_deterministic_artifacts(source, profile)
    validate_wiring()
    print(
        json.dumps(
            {
                "status": "PASS",
                "task": "AX-F8-T14",
                "task_state": "ACCEPTED",
                "source_id": SOURCE_ID,
                "profile_id": PROFILE_ID,
                "runtime_default": "DISABLED",
                "activation_state": "PRIVATE_PILOT_ENABLED",
                "activation_scope": "AUTHENTICATED_VERIFIED_ORGANISATIONS",
                "public_general_availability": False,
                "tenant_resolution": "SERVER_AUTHENTICATED_IDENTITY",
                "model_calls": 0,
                "api_redistribution": False,
                **summary,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
