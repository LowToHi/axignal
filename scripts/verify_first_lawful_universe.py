from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
UNIVERSE = ROOT / "data/universes"
PROCUREMENT = UNIVERSE / "eu-public-procurement"
DOCS = ROOT / "docs"
SCORECARD_PATH = UNIVERSE / "first-lawful-universe-scorecard.v0.1.json"
ONTOLOGY_PATH = PROCUREMENT / "ontology.v0.1.json"
POLICY_PATH = PROCUREMENT / "claim-policy.v0.1.json"
PROFILE_PATH = PROCUREMENT / "ted-product-admission-profile.v0.1.json"
SOURCE_RECORD_PATH = ROOT / "data/sources/ted-search-api-v3.v0.1.json"
TASK_SCHEMA_PATH = ROOT / "schemas/task.schema.json"
SOURCE_SCHEMA_PATH = ROOT / "schemas/source.schema.json"
TASK_STATES = {
    "AX-F8-T01.json": "ACCEPTED",
    "AX-F8-T02.json": "ACCEPTED",
    "AX-F8-T03.json": "ACCEPTED",
    "AX-F8-T04.json": "IN_PROGRESS",
    "AX-F8-T05.json": "EVIDENCE_READY",
    "AX-F8-T06.json": "EVIDENCE_READY",
    "AX-F8-T14.json": "ACCEPTED",
}
TASK_PATHS = [DOCS / "roadmap/tasks" / name for name in TASK_STATES]
RESEARCH_PATH = DOCS / "research/first-lawful-universe-selection-v0.1.md"
ADR_PATH = DOCS / "adr/ADR-012-european-public-procurement-first-universe.md"
SOURCE_DOC_PATH = DOCS / "sources/ted-search-api-v3.md"
PRODUCT_ADMISSION_PATH = DOCS / "sources/ted-product-admission-v0.1.md"
SECURITY_REVIEW_PATH = DOCS / "security/AX-F8-T14-ted-runtime-security-review.md"
HYPOTHESIS_PATH = DOCS / "contracts/11-hypothesis-register.md"
ADR_INDEX_PATH = DOCS / "adr/README.md"
EXECUTION_STATE_PATH = DOCS / "roadmap/06-current-execution-state.md"
ACTIVE_CATALOGUE_PATH = DOCS / "roadmap/02-task-catalogue.md"


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path.relative_to(ROOT)} must contain an object")
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def weighted_total(criteria: list[dict], scores: dict[str, int]) -> Decimal:
    weights = {item["id"]: Decimal(str(item["weight"])) for item in criteria}
    return sum(weights[key] * Decimal(value) / Decimal(5) for key, value in scores.items())


def validate_scorecard() -> dict:
    scorecard = load_json(SCORECARD_PATH)
    require(scorecard["schema"] == "axignal.universe-selection.v1", "wrong schema")
    require(scorecard["goal_id"] == "AXIGNAL-GOAL-001", "wrong Goal ID")
    require(
        scorecard["status"] == "WEDGE_SELECTED_IMPLEMENTATION_NOT_ADMITTED",
        "historical selection decision was rewritten",
    )
    criteria = scorecard["criteria"]
    ids = [item["id"] for item in criteria]
    require(len(ids) == len(set(ids)), "duplicate score criterion")
    require(sum(item["weight"] for item in criteria) == 100, "invalid weights")

    gate = scorecard["selection_gate"]
    candidates = scorecard["candidates"]
    require(len(candidates) >= 5, "candidate set is too narrow")
    require(
        len({item["universe_id"] for item in candidates}) == len(candidates),
        "duplicate universe",
    )
    selected: list[dict] = []
    eligible: list[dict] = []
    for candidate in candidates:
        scores = candidate["scores"]
        require(set(scores) == set(ids), "score dimensions drifted")
        require(
            all(isinstance(value, int) and 0 <= value <= 5 for value in scores.values()),
            "invalid score",
        )
        declared = Decimal(str(candidate["weighted_total"]))
        require(
            weighted_total(criteria, scores) == declared,
            f"weighted total mismatch: {candidate['universe_id']}",
        )
        passed = declared >= Decimal(str(gate["minimum_total"]))
        passed = passed and all(
            scores[key] >= minimum for key, minimum in gate["minimum_scores"].items()
        )
        require(passed is candidate["knockout_pass"], "knockout mismatch")
        if passed:
            eligible.append(candidate)
        if candidate["decision"] == "SELECTED":
            selected.append(candidate)
        for item in candidate["official_evidence"]:
            parsed = urlparse(item["url"])
            require(parsed.scheme == "https", "official evidence is not HTTPS")
            require(
                parsed.hostname is not None
                and (
                    parsed.hostname.endswith("europa.eu")
                    or parsed.hostname.endswith("sec.gov")
                ),
                "non-official evidence domain",
            )
            require(item["checked_at"] == "2026-07-29", "evidence date drifted")

    require(len(selected) == 1, "exactly one universe must be selected")
    require(eligible, "no candidate passes the gate")
    winner = selected[0]
    require(winner["universe_id"] == "eu_public_procurement", "wrong universe")
    require(
        winner["weighted_total"] == max(item["weighted_total"] for item in eligible),
        "selected universe is not the highest-scoring eligible candidate",
    )
    historical = scorecard["selected_universe"]
    require(
        historical["admission_state"] == "NOT_PRODUCT_ADMITTED",
        "historical selection was rewritten",
    )
    require(historical["runtime_default"] == "DISABLED", "history enabled runtime")
    return {
        "candidate_count": len(candidates),
        "eligible_count": len(eligible),
        "selected_universe": winner["universe_id"],
        "selected_score": winner["weighted_total"],
    }


def validate_ontology() -> dict:
    ontology = load_json(ONTOLOGY_PATH)
    require(
        ontology["status"] == "IMPLEMENTATION_PROFILE_NOT_UNIVERSE_ADMISSION",
        "ontology overstates authority",
    )
    require(ontology["source_standard"]["name"] == "EU eForms", "wrong standard")
    transport = ontology["transport_contract"]
    require(
        "JSON search envelope" in transport["search_api"]["response_representation"],
        "JSON role missing",
    )
    require(
        transport["canonical_notice"]["representation"].startswith("XML"),
        "XML role missing",
    )
    blocks = ontology["notice_blocks"]
    require(len(blocks) == 6, "notice blocks drifted")
    require(all(item["authority"] == "OBSERVED" for item in blocks), "authority drifted")
    require(len(ontology["entity_types"]) >= 18, "entity model is too shallow")
    require(ontology["privacy_policy"]["personal_data_present"] is True, "privacy hidden")
    return {
        "ontology_blocks": len(blocks),
        "ontology_entities": len(ontology["entity_types"]),
    }


def validate_source_and_profile() -> dict:
    source_schema = load_json(SOURCE_SCHEMA_PATH)
    source = load_json(SOURCE_RECORD_PATH)
    errors = sorted(
        Draft202012Validator(
            source_schema,
            format_checker=FormatChecker(),
        ).iter_errors(source),
        key=lambda error: list(error.path),
    )
    require(not errors, f"TED source schema failure: {errors}")
    require(source["status"] == "PRODUCT_ADMITTED", "source is not admitted")
    require(source["kill_switch_enabled"] is False, "source is disabled")
    require(source["contains_personal_data"] is True, "privacy risk hidden")
    rights = source["rights"]
    require(rights["customer_display"] == "PERMITTED", "display not admitted")
    require(rights["export"] == "PERMITTED", "export not admitted")
    require(rights["api_redistribution"] == "PROHIBITED", "API resale enabled")
    require(rights["model_training"] == "PROHIBITED", "model training enabled")
    require(rights["attribution_required"] is True, "attribution absent")

    profile = load_json(PROFILE_PATH)
    require(
        profile["status"] == "PRODUCT_ADMITTED_BOUNDED_PROFILE",
        "profile is not admitted",
    )
    require(profile["source_id"] == source["source_id"], "profile source mismatch")
    require(profile["runtime_default"] == "DISABLED", "runtime default enabled")
    require(
        profile["activation_state"] == "PRIVATE_PILOT_ENABLED",
        "private-pilot runtime is not active",
    )
    require(
        profile["query_contract"]["arbitrary_query_allowed"] is False,
        "arbitrary query enabled",
    )
    require(profile["authority"]["generative_model_calls"] == 0, "model enabled")
    require(
        profile["rights_boundary"]["personal_contact_data"] == "PROHIBITED",
        "personal data enabled",
    )
    return {
        "ted_source_state": source["status"],
        "ted_profile": profile["profile_id"],
        "ted_activation": profile["activation_state"],
    }


def validate_claim_policy() -> dict:
    policy = load_json(POLICY_PATH)
    require(
        policy["status"] == "DISABLED_PENDING_PRODUCT_ADMISSION_AND_XML_PARSER",
        "full procurement policy was activated",
    )
    authority = policy["producer_authority"]
    require(authority["admission_runtime"] == "SOLE_CANONICAL_WRITER", "writer drifted")
    require(authority["local_model"] == "PROPOSAL_ONLY", "model authority drifted")
    require(
        policy["personal_fields"]["canonical_admission"] == "PROHIBITED",
        "personal admission enabled",
    )
    prohibited = set(policy["prohibited_profiles"])
    require("supplier_probability_of_winning" in prohibited, "win guard missing")
    require("expected_contract_profitability" in prohibited, "margin guard missing")
    require("bid_submission_or_representation" in prohibited, "bid guard missing")
    return {
        "observed_policy_profiles": len(policy["observed_claim_profiles"]),
        "calculated_policy_profiles": len(policy["calculated_claim_profiles"]),
    }


def validate_tasks() -> None:
    schema = load_json(TASK_SCHEMA_PATH)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    for path in TASK_PATHS:
        task = load_json(path)
        errors = sorted(validator.iter_errors(task), key=lambda error: list(error.path))
        require(not errors, f"task schema failure in {path.name}: {errors}")
        require(task["phase"] == "F8", f"wrong phase in {path.name}")
        require(task["state"] == TASK_STATES[path.name], f"wrong state in {path.name}")
        checks = task["goal_lock_checks"]
        require(
            [item["check_id"] for item in checks] == list(range(1, 11)),
            "Goal Lock checks drifted",
        )
        require(all(item["answer"] == "YES" for item in checks), "Goal Lock blocker")
        require(task["rollback"]["tested"] is True, "rollback is not tested")
        if task["state"] == "ACCEPTED":
            required = [item for item in task["acceptance_evidence"] if item["required"]]
            require(
                all(item["status"] == "PASS" for item in required),
                f"accepted task has an unpassed gate: {path.name}",
            )


def validate_normative_links() -> None:
    research = RESEARCH_PATH.read_text(encoding="utf-8")
    adr = ADR_PATH.read_text(encoding="utf-8")
    source_doc = SOURCE_DOC_PATH.read_text(encoding="utf-8")
    admission = PRODUCT_ADMISSION_PATH.read_text(encoding="utf-8")
    security = SECURITY_REVIEW_PATH.read_text(encoding="utf-8")
    hypothesis = HYPOTHESIS_PATH.read_text(encoding="utf-8")
    adr_index = ADR_INDEX_PATH.read_text(encoding="utf-8")
    execution = EXECUTION_STATE_PATH.read_text(encoding="utf-8")
    active_catalogue = ACTIVE_CATALOGUE_PATH.read_text(encoding="utf-8")

    require("European Public Procurement Intelligence" in research, "selection missing")
    require("WEDGE SELECTED / IMPLEMENTATION NOT ADMITTED" in research, "history missing")
    require("Status: `ACCEPTED / IMPLEMENTATION NOT ADMITTED`" in adr, "ADR missing")
    require("ADR-012" in adr_index, "ADR index missing")
    h006 = hypothesis.split("## 8. H-006", 1)[1].split("## 9.", 1)[0]
    require("State: `TEST_DESIGNED`" in h006, "H-006 drifted")

    # F0–F12 is now implementation history under Contract 30. The accepted F8
    # evidence is validated from its immutable typed tasks above, while the active
    # execution state must truthfully expose P00 and the bounded TED capability.
    require(
        "Legacy F0–F12 implementation history" in execution,
        "legacy programme history is not preserved",
    )
    require("bounded admitted TED Search profile" in execution, "bounded TED evidence missing")
    require("AX-GE2E-P00-T01" in execution, "active P00 task missing")
    require('"public_launch_authorised": false' in execution, "launch boundary missing")
    require("AX-GE2E-P08-T01" in active_catalogue, "active Procurement phase missing")

    require("Search API envelope — JSON" in source_doc, "JSON contract missing")
    require("Canonical notice — XML" in source_doc, "XML contract missing")
    require("PRODUCT_ADMITTED" in admission, "source admission missing")
    require("runtime remains disabled" in admission.casefold(), "default hidden")
    require("PASS / PRIVATE-PILOT PRODUCT RUNTIME" in security, "security missing")


def main() -> None:
    summary = validate_scorecard()
    summary.update(validate_ontology())
    summary.update(validate_source_and_profile())
    summary.update(validate_claim_policy())
    validate_tasks()
    validate_normative_links()
    print(json.dumps({"status": "PASS", **summary}, sort_keys=True))


if __name__ == "__main__":
    main()
