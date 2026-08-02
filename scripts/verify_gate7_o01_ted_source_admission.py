from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = (
    ROOT
    / "data/acceptance/source-admission/"
    "AX-LIB-O01-TED-source-admission-gate.v0.1.json"
)
DOSSIER_PATH = ROOT / "data/acceptance/library-coverage/AX-LIB-O01.json"
CAMPAIGN_RESULT_PATH = (
    ROOT
    / "data/acceptance/campaign-results/"
    "AX-LIB-O01-TED-QALAG-ML-CONTROLS-v0.1.json"
)
SCHEMA_PATH = ROOT / "schemas/o01-ted-source-admission-gate.schema.json"
EXPECTED_MANIFEST_SHA256 = (
    "8ec359f868803730eced3db5a60bd42d4d6f24068bd2822aa9d59943f542d0ea"
)
EXPECTED_DOSSIER_SHA256 = (
    "cbbc12b17bf73b877456e491952f95f851038bbdb3d0c66ca104305c3d9de4ab"
)
EXPECTED_CAMPAIGN_SHA256 = (
    "039042d6e0c66a6dd4af65a9417f890d9edb4afc751a3d873bf54597fff805ab"
)


class AdmissionContractError(RuntimeError):
    """Raised when source-admission evidence violates its contract."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AdmissionContractError(f"Required file is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise AdmissionContractError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise AdmissionContractError(f"Expected JSON object in {path}")
    return value


def sha256_hex(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_time(value: str | datetime) -> datetime:
    parsed = (
        value
        if isinstance(value, datetime)
        else datetime.fromisoformat(value.replace("Z", "+00:00"))
    )
    if parsed.tzinfo is None:
        raise AdmissionContractError("Timestamps must include a timezone")
    return parsed.astimezone(UTC)


def evidence_current(expires_at: str, now: datetime) -> bool:
    return parse_time(expires_at) > now


def find_source(dossier: dict[str, Any], source_id: str) -> dict[str, Any]:
    matches = [
        source
        for bucket in ("active", "suspended", "candidate")
        for source in dossier["sources"][bucket]
        if source["source_id"] == source_id
    ]
    if len(matches) != 1:
        raise AdmissionContractError(
            f"Expected exactly one source {source_id}; found {len(matches)}"
        )
    return matches[0]


def language_journeys_pass(
    dossier: dict[str, Any], required_languages: list[str], now: datetime
) -> bool:
    journeys = dossier["languages"]
    if {item["language"] for item in journeys} != set(required_languages):
        return False
    for item in journeys:
        if any(
            item[stage] != "PASS"
            for stage in ("ingestion", "normalisation", "search", "presentation")
        ):
            return False
        if not item["evidence"]:
            return False
        if not all(
            evidence_current(reference["expires_at"], now)
            for reference in item["evidence"]
        ):
            return False
    return True


def campaign_reference_present(
    dossier: dict[str, Any], expected_sha256: str
) -> bool:
    references = [
        reference
        for source in dossier["sources"]["candidate"]
        for reference in source["evidence"]
    ]
    references.extend(dossier["quality"]["evidence"])
    references.extend(dossier["lag"]["evidence"])
    return any(
        reference["reference"]
        == "data/acceptance/campaign-results/"
        "AX-LIB-O01-TED-QALAG-ML-CONTROLS-v0.1.json"
        and reference["sha256"] == expected_sha256
        for reference in references
    )


def evaluate_payloads(
    manifest: dict[str, Any],
    dossier: dict[str, Any],
    campaign: dict[str, Any],
    *,
    now: datetime,
) -> dict[str, Any]:
    current = parse_time(now)
    required = manifest["required_admission_dimensions"]
    source = find_source(dossier, manifest["source_id"])
    admission = source["admission"]
    measurement = campaign["measurement_outcome"]
    privacy = campaign["privacy_and_retention"]
    boundary = campaign["authority_boundary"]
    integrated = campaign_reference_present(
        dossier,
        manifest["inputs"]["campaign_result_sha256"].removeprefix("sha256:"),
    )

    checks: dict[str, dict[str, Any]] = {
        "source_is_candidate": {
            "required": "CANDIDATE",
            "observed": source["state"],
            "pass": source["state"] == "CANDIDATE",
        },
        "legal": {
            "required": required["legal"],
            "observed": admission["legal"],
            "pass": admission["legal"] == required["legal"],
        },
        "technical": {
            "required": required["technical"],
            "observed": admission["technical"],
            "pass": admission["technical"] == required["technical"],
        },
        "quality": {
            "required": required["quality"],
            "observed": admission["quality"],
            "pass": admission["quality"] == required["quality"],
        },
        "rights": {
            "required": required["rights"],
            "observed": admission["rights"],
            "pass": admission["rights"] == required["rights"],
        },
        "human_authority": {
            "required": required["human_authority"],
            "observed": admission["human_authority"],
            "pass": admission["human_authority"]
            == required["human_authority"],
        },
        "campaign_output": {
            "required": required["campaign_output"],
            "observed": campaign["output"],
            "pass": campaign["output"] == required["campaign_output"],
        },
        "minimum_sample_count": {
            "required": required["minimum_sample_count"],
            "observed": measurement["sample_count"],
            "pass": measurement["sample_count"]
            >= required["minimum_sample_count"],
        },
        "minimum_countries_observed": {
            "required": required["minimum_countries_observed"],
            "observed": measurement["countries_observed"],
            "pass": measurement["countries_observed"]
            >= required["minimum_countries_observed"],
        },
        "quality_report_complete": {
            "required": True,
            "observed": measurement["quality_report_complete"],
            "pass": measurement["quality_report_complete"] is True,
        },
        "lag_report_complete": {
            "required": True,
            "observed": measurement["lag_report_complete"],
            "pass": measurement["lag_report_complete"] is True,
        },
        "multilingual_journeys": {
            "required": required["required_languages"],
            "observed": [item["language"] for item in dossier["languages"]],
            "pass": language_journeys_pass(
                dossier, required["required_languages"], current
            ),
        },
        "kill_switch": {
            "required": True,
            "observed": dossier["kill_switch"],
            "pass": dossier["kill_switch"]["implemented"] is True
            and dossier["kill_switch"]["tested"] is True,
        },
        "rollback": {
            "required": True,
            "observed": dossier["rollback"],
            "pass": dossier["rollback"]["implemented"] is True
            and dossier["rollback"]["tested"] is True,
        },
        "fabricated_evidence": {
            "required_max": required["fabricated_evidence_max"],
            "observed": measurement["fabricated_evidence"],
            "pass": measurement["fabricated_evidence"]
            <= required["fabricated_evidence_max"],
        },
        "raw_plaintext_uploaded": {
            "required": required["raw_plaintext_uploaded"],
            "observed": privacy["raw_plaintext_uploaded"],
            "pass": privacy["raw_plaintext_uploaded"]
            is required["raw_plaintext_uploaded"],
        },
        "public_claim_contribution": {
            "required": required["public_claim_contribution_before_admission"],
            "observed": source["contributes_to_public_claim"],
            "pass": source["contributes_to_public_claim"]
            is required["public_claim_contribution_before_admission"],
        },
        "campaign_reference_integrated": {
            "required": True,
            "observed": integrated,
            "pass": integrated,
        },
        "campaign_evidence_current": {
            "required": True,
            "observed": campaign["evidence_expires_at"],
            "pass": evidence_current(campaign["evidence_expires_at"], current),
        },
        "permanent_boundary": {
            "required": "NO_EXPANSION",
            "observed": boundary,
            "pass": boundary
            == {
                "bid_submission_authorised": False,
                "contact_marketing_authorised": False,
                "external_notification_delivery_authorised": False,
                "model_training_authorised": False,
                "public_claims_authorised": False,
                "public_launch": "NO_GO",
                "public_redistribution_authorised": False,
                "ted_product_admitted": False,
            },
        },
    }

    all_pass = all(item["pass"] for item in checks.values())
    decision = "ADMITTED" if all_pass else "BLOCKED"
    next_state = "PRODUCT_ADMITTED" if all_pass else "CANDIDATE"
    failed_checks = sorted(
        name for name, item in checks.items() if not item["pass"]
    )
    result = {
        "schema_version": "axignal.o01-ted-source-admission-result/v0.1",
        "status": "PASS",
        "output": (
            "O01_TED_SOURCE_ADMITTED"
            if all_pass
            else "O01_TED_SOURCE_ADMISSION_BLOCKED"
        ),
        "gate_id": manifest["gate_id"],
        "library_id": manifest["library_id"],
        "source_id": manifest["source_id"],
        "evaluated_at": current.isoformat().replace("+00:00", "Z"),
        "decision": decision,
        "previous_state": source["state"],
        "next_state": next_state,
        "product_admitted": all_pass,
        "claim_contribution": all_pass,
        "all_required_dimensions_pass": all_pass,
        "checks": checks,
        "failed_checks": failed_checks,
        "reasons": (
            ["All source-admission dimensions are current and PASS"]
            if all_pass
            else [f"Admission blocked by {name}" for name in failed_checks]
        ),
        "failure_disposition": {
            "campaign_failure_class": campaign["admission_effect"][
                "failure_class"
            ],
            "source_rejected": campaign["admission_effect"]["source_rejected"],
            "retriable_only_under_new_versioned_contract": campaign[
                "admission_effect"
            ]["retriable_only_under_new_versioned_contract"],
        },
        "authority_boundary": deepcopy(boundary),
    }
    expected = manifest["expected_current_decision"]
    if not all_pass:
        if result["decision"] != expected["decision"]:
            raise AdmissionContractError("Blocked decision diverges from manifest")
        if result["output"] != expected["output"]:
            raise AdmissionContractError("Blocked output diverges from manifest")
        if result["next_state"] != expected["source_state"]:
            raise AdmissionContractError("Blocked state diverges from manifest")
        if result["product_admitted"] is not expected["product_admitted"]:
            raise AdmissionContractError("Product admission diverges from manifest")
    return result


def verify_contract() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    actual = {
        "manifest": sha256_hex(MANIFEST_PATH),
        "dossier": sha256_hex(DOSSIER_PATH),
        "campaign": sha256_hex(CAMPAIGN_RESULT_PATH),
    }
    expected = {
        "manifest": EXPECTED_MANIFEST_SHA256,
        "dossier": EXPECTED_DOSSIER_SHA256,
        "campaign": EXPECTED_CAMPAIGN_SHA256,
    }
    if actual != expected:
        raise AdmissionContractError(
            f"Immutable input digest mismatch: expected={expected} actual={actual}"
        )
    manifest = load_json(MANIFEST_PATH)
    dossier = load_json(DOSSIER_PATH)
    campaign = load_json(CAMPAIGN_RESULT_PATH)
    schema = load_json(SCHEMA_PATH)
    errors = sorted(
        Draft202012Validator(
            schema, format_checker=FormatChecker()
        ).iter_errors(manifest),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        rendered = "; ".join(error.message for error in errors[:10])
        raise AdmissionContractError(
            f"Admission manifest schema failed: {rendered}"
        )
    inputs = manifest["inputs"]
    if inputs["gate7_dossier_sha256"] != f"sha256:{actual['dossier']}":
        raise AdmissionContractError("Manifest dossier digest mismatch")
    if inputs["campaign_result_sha256"] != f"sha256:{actual['campaign']}":
        raise AdmissionContractError("Manifest campaign digest mismatch")
    if dossier["library_id"] != manifest["library_id"]:
        raise AdmissionContractError("Library identity mismatch")
    if campaign["source_id"] != manifest["source_id"]:
        raise AdmissionContractError("Source identity mismatch")
    return manifest, dossier, campaign


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--now", default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--require-admitted", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    manifest, dossier, campaign = verify_contract()
    now = parse_time(args.now) if args.now else datetime.now(UTC)
    result = evaluate_payloads(manifest, dossier, campaign, now=now)
    if args.output_dir is not None:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = args.output_dir / "source-admission-result.v0.1.json"
        output_path.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(result, sort_keys=True))
    if args.require_admitted and result["decision"] != "ADMITTED":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
