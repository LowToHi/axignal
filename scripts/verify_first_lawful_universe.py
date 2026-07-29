from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCORECARD_PATH = ROOT / "data/universes/first-lawful-universe-scorecard.v0.1.json"
ONTOLOGY_PATH = ROOT / "data/universes/eu-public-procurement/ontology.v0.1.json"
POLICY_PATH = ROOT / "data/universes/eu-public-procurement/claim-policy.v0.1.json"
SOURCE_RECORD_PATH = ROOT / "data/sources/ted-search-api-v3.v0.1.json"
TASK_SCHEMA_PATH = ROOT / "schemas/task.schema.json"
SOURCE_SCHEMA_PATH = ROOT / "schemas/source.schema.json"
TASK_STATES = {
    "AX-F8-T01.json": "ACCEPTED",
    "AX-F8-T02.json": "ACCEPTED",
    "AX-F8-T03.json": "ACCEPTED",
    "AX-F8-T04.json": "IN_PROGRESS",
    "AX-F8-T05.json": "IN_PROGRESS",
    "AX-F8-T06.json": "EVIDENCE_READY",
}
TASK_PATHS = [ROOT / "docs/roadmap/tasks" / name for name in TASK_STATES]
RESEARCH_PATH = ROOT / "docs/research/first-lawful-universe-selection-v0.1.md"
ADR_PATH = ROOT / "docs/adr/ADR-012-european-public-procurement-first-universe.md"
SOURCE_DOC_PATH = ROOT / "docs/sources/ted-search-api-v3.md"
HYPOTHESIS_PATH = ROOT / "docs/contracts/11-hypothesis-register.md"
ADR_INDEX_PATH = ROOT / "docs/adr/README.md"
EXECUTION_STATE_PATH = ROOT / "docs/roadmap/06-current-execution-state.md"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def weighted_total(criteria: list[dict], scores: dict[str, int]) -> Decimal:
    weights = {criterion["id"]: Decimal(str(criterion["weight"])) for criterion in criteria}
    return sum(weights[key] * Decimal(score) / Decimal(5) for key, score in scores.items())


def validate_scorecard() -> dict:
    scorecard = load_json(SCORECARD_PATH)
    require(scorecard["schema"] == "axignal.universe-selection.v1", "unexpected schema")
    require(scorecard["goal_id"] == "AXIGNAL-GOAL-001", "wrong Goal ID")
    require(
        scorecard["status"] == "WEDGE_SELECTED_IMPLEMENTATION_NOT_ADMITTED",
        "selection must remain explicitly non-admitted",
    )

    criteria = scorecard["criteria"]
    criterion_ids = [criterion["id"] for criterion in criteria]
    require(len(criterion_ids) == len(set(criterion_ids)), "duplicate score criterion")
    require(sum(criterion["weight"] for criterion in criteria) == 100, "weights must sum to 100")

    gate = scorecard["selection_gate"]
    candidates = scorecard["candidates"]
    require(len(candidates) >= 5, "candidate set is too narrow")
    require(
        len({candidate["universe_id"] for candidate in candidates}) == len(candidates),
        "duplicate universe",
    )

    selected = []
    eligible = []
    for candidate in candidates:
        scores = candidate["scores"]
        require(
            set(scores) == set(criterion_ids),
            f"score dimensions drifted for {candidate['universe_id']}",
        )
        for criterion_id, score in scores.items():
            require(isinstance(score, int) and 0 <= score <= 5, f"invalid {criterion_id}")

        computed = weighted_total(criteria, scores)
        declared = Decimal(str(candidate["weighted_total"]))
        require(computed == declared, f"weighted total mismatch: {candidate['universe_id']}")

        knockout_pass = declared >= Decimal(str(gate["minimum_total"]))
        for criterion_id, minimum in gate["minimum_scores"].items():
            knockout_pass = knockout_pass and scores[criterion_id] >= minimum
        require(
            knockout_pass is candidate["knockout_pass"],
            f"knockout mismatch: {candidate['universe_id']}",
        )

        if candidate["knockout_pass"]:
            eligible.append(candidate)
        if candidate["decision"] == "SELECTED":
            selected.append(candidate)

        evidence = candidate["official_evidence"]
        if candidate["knockout_pass"] or candidate["decision"] == "SELECTED":
            require(evidence, f"eligible candidate lacks evidence: {candidate['universe_id']}")
        for item in evidence:
            parsed = urlparse(item["url"])
            require(parsed.scheme == "https", "official evidence must use HTTPS")
            require(
                parsed.hostname is not None
                and (
                    parsed.hostname.endswith("europa.eu")
                    or parsed.hostname.endswith("sec.gov")
                ),
                f"non-official evidence domain: {parsed.hostname}",
            )
            require(item["checked_at"] == "2026-07-29", "evidence date drifted")

    require(len(selected) == 1, "exactly one universe must be selected")
    require(eligible, "no candidate passes the gate")
    winner = selected[0]
    require(
        winner["weighted_total"] == max(candidate["weighted_total"] for candidate in eligible),
        "selected universe is not the highest-scoring eligible candidate",
    )
    require(winner["universe_id"] == "eu_public_procurement", "unexpected selected universe")

    selected_contract = scorecard["selected_universe"]
    require(selected_contract["universe_id"] == winner["universe_id"], "pointer mismatch")
    require(selected_contract["admission_state"] == "NOT_PRODUCT_ADMITTED", "admission escalated")
    require(
        selected_contract["public_marketing_state"] == "PROHIBITED_UNTIL_UNIVERSE_GATE",
        "public marketing enabled before universe gate",
    )
    require(selected_contract["runtime_default"] == "DISABLED", "runtime must be disabled")
    require(
        scorecard["next_authorised_tasks"]
        == ["AX-F8-T03", "AX-F8-T04", "AX-F8-T05", "AX-F8-T06"],
        "next authorised task set drifted",
    )
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
        "ontology status overstates admission",
    )
    require(ontology["source_standard"]["name"] == "EU eForms", "wrong source standard")
    transport = ontology["transport_contract"]
    require("JSON search envelope" in transport["search_api"]["response_representation"], "JSON role missing")
    require(transport["canonical_notice"]["representation"].startswith("XML"), "XML evidence role missing")
    require(
        transport["sdk_field_repository"]["representation"] == "JSON metadata repository",
        "SDK JSON role missing",
    )

    expected_blocks = {
        "notice_identity_metadata",
        "buyer",
        "procurement_object",
        "economics_financing",
        "participation_and_access",
        "result_award",
    }
    blocks = ontology["notice_blocks"]
    require({block["block_id"] for block in blocks} == expected_blocks, "notice blocks drifted")
    require(all(block["optionality"] for block in blocks), "block optionality is missing")
    require(all(block["authority"] == "OBSERVED" for block in blocks), "authority drifted")
    require(len(ontology["entity_types"]) >= 18, "procurement entity model is too shallow")
    require("probability of winning" in ontology["prohibited_claims"], "win-probability guard missing")
    require(
        "canonical opportunity claim derived from natural-person contact data"
        in ontology["prohibited_claims"],
        "personal-data claim guard missing",
    )
    require(ontology["privacy_policy"]["personal_data_present"] is True, "privacy risk hidden")
    return {"ontology_blocks": len(blocks), "ontology_entities": len(ontology["entity_types"])}


def validate_source_record() -> None:
    schema = load_json(SOURCE_SCHEMA_PATH)
    source = load_json(SOURCE_RECORD_PATH)
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(source),
        key=lambda error: list(error.path),
    )
    require(not errors, f"TED source schema failure: {errors}")
    require(source["status"] == "TECHNICAL_PROBE", "TED source state escalated")
    require(source["kill_switch_enabled"] is True, "TED kill switch disabled")
    require(source["contains_personal_data"] is True, "TED personal-data risk hidden")
    require(source["rights"]["model_training"] == "UNKNOWN", "model training was assumed")
    for dimension in ("customer_display", "export", "api_redistribution"):
        require(source["rights"][dimension] == "CONDITIONAL", f"{dimension} over-admitted")


def validate_claim_policy() -> dict:
    policy = load_json(POLICY_PATH)
    require(
        policy["status"] == "DISABLED_PENDING_PRODUCT_ADMISSION_AND_XML_PARSER",
        "procurement policy activated prematurely",
    )
    require(policy["producer_authority"]["admission_runtime"] == "SOLE_CANONICAL_WRITER", "authority drifted")
    require(policy["producer_authority"]["local_model"] == "PROPOSAL_ONLY", "local model authority escalated")
    require(policy["personal_fields"]["canonical_admission"] == "PROHIBITED", "personal admission enabled")
    require(policy["missing_data_policy"]["zero_imputation"] == "PROHIBITED", "zero imputation enabled")
    prohibited = set(policy["prohibited_profiles"])
    require("supplier_probability_of_winning" in prohibited, "win-probability guard missing")
    require("expected_contract_profitability" in prohibited, "profitability guard missing")
    require("bid_submission_or_representation" in prohibited, "bid-execution guard missing")
    require(
        "official TED source state PRODUCT_ADMITTED" in policy["evidence_requirements"],
        "source admission prerequisite missing",
    )
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
        require(task["state"] == TASK_STATES[path.name], f"unexpected state in {path.name}")
        checks = task["goal_lock_checks"]
        require(
            [check["check_id"] for check in checks] == list(range(1, 11)),
            "Goal Lock checks drifted",
        )
        require(all(check["answer"] == "YES" for check in checks), "Goal Lock blocker")
        require(task["rollback"]["tested"] is True, "rollback declaration is not tested")


def validate_normative_links() -> None:
    research = RESEARCH_PATH.read_text(encoding="utf-8")
    adr = ADR_PATH.read_text(encoding="utf-8")
    source_doc = SOURCE_DOC_PATH.read_text(encoding="utf-8")
    hypothesis = HYPOTHESIS_PATH.read_text(encoding="utf-8")
    adr_index = ADR_INDEX_PATH.read_text(encoding="utf-8")
    execution_state = EXECUTION_STATE_PATH.read_text(encoding="utf-8")

    require("European Public Procurement Intelligence" in research, "research decision missing")
    require("WEDGE SELECTED / IMPLEMENTATION NOT ADMITTED" in research, "boundary missing")
    require("Status: `ACCEPTED / IMPLEMENTATION NOT ADMITTED`" in adr, "ADR boundary missing")
    require("ADR-012" in adr_index, "ADR index not updated")
    h006 = hypothesis.split("## 8. H-006", 1)[1].split("## 9.", 1)[0]
    require("State: `TEST_DESIGNED`" in h006, "H-006 state not updated")
    require("European Public Procurement Intelligence" in h006, "selected wedge missing")
    require(
        "F8 — First lawful opportunity universe | `IN_PROGRESS`" in execution_state,
        "F8 state not activated",
    )
    require("NOT_PRODUCT_ADMITTED" in execution_state, "non-admission boundary missing")
    require("Search API envelope — JSON" in source_doc, "JSON search-envelope contract missing")
    require("Canonical notice — XML" in source_doc, "XML canonical-evidence contract missing")


def main() -> None:
    summary = validate_scorecard()
    summary.update(validate_ontology())
    validate_source_record()
    summary.update(validate_claim_policy())
    validate_tasks()
    validate_normative_links()
    print(json.dumps({"status": "PASS", **summary}, sort_keys=True))


if __name__ == "__main__":
    main()
