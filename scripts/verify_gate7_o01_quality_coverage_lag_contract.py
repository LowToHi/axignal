from __future__ import annotations

import argparse
import hashlib
import json
import ssl
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from axignal_api.o01_quality_campaign import evaluate_thresholds, sha256_prefixed

EXPECTED_PLAN_SHA256 = "sha256:7d323a9a920f1fe96832b5f6e631b4da257c3ce995ef433705aff95c3ed1643b"
EXPECTED_EVALUATOR_HEAD = "740895ba1a5bd58bb286d7c3c48f2d59488192af"
EXPECTED_EVALUATOR_TREE = "b778f327592a82fc43d35a03b5f4601e00d12802"
EXPECTED_MANIFEST_REFERENCE = "sha256:e5de7d2e362ecb07c5b8200df1f14f6521d7e37328333313d86e2cd620e31871"

EXPECTED_QUALITY_METRICS = {
    "identifier_accuracy",
    "title_completeness",
    "buyer_accuracy",
    "deadline_accuracy",
    "amount_accuracy",
    "currency_accuracy",
    "CPV_accuracy",
    "NUTS_accuracy",
    "lot_completeness",
    "contact_channel_classification_accuracy",
    "duplicate_rate",
    "unparseable_rate",
    "missing_field_rate",
}
EXPECTED_LAG_METRICS = {
    "source_publication_lag",
    "source_availability_lag",
    "AXIGNAL_acquisition_lag",
    "normalisation_lag",
    "indexing_lag",
    "subscriber_notification_lag",
}
CONTACT_FIELDS = {
    "buyer-contact-point",
    "buyer-email",
    "buyer-tel",
    "buyer-internet-address",
    "buyer-profile",
    "submission-url-lot",
}


class ContractError(RuntimeError):
    """Raised when the frozen O01-C contract or evidence is unsafe."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def cert_fingerprint(path: Path) -> str:
    der = ssl.PEM_cert_to_DER_cert(path.read_text(encoding="utf-8"))
    return hashlib.sha256(der).hexdigest().upper()


def verify_plan(plan_path: Path) -> dict[str, Any]:
    plan_digest = sha256_prefixed(plan_path.read_bytes())
    require(plan_digest == EXPECTED_PLAN_SHA256, "Frozen O01-C plan digest drift")
    plan = load_json(plan_path)
    require(isinstance(plan, dict), "O01-C plan must be a JSON object")
    require(
        plan["schema_version"] == "axignal.o01-quality-coverage-lag-plan/v0.1",
        "Unexpected O01-C plan schema",
    )
    require(plan["task_id"] == "AX-GE2E-G7-O01-C", "O01-C task mismatch")
    require(plan["frozen_before_execution"] is True, "Sample was not frozen")
    authority = plan["authority"]
    require(
        authority["evaluator_head_sha"] == EXPECTED_EVALUATOR_HEAD,
        "O01-B evaluator head drift",
    )
    require(
        authority["evaluator_tree_sha"] == EXPECTED_EVALUATOR_TREE,
        "O01-B evaluator tree drift",
    )
    require(
        authority["target_head_sha"]
        == "b754b5641e5f17c5a084434aace4f939a4be0e84",
        "O01 campaign target head drift",
    )
    require(
        authority["manifest_reference"] == EXPECTED_MANIFEST_REFERENCE,
        "O01-B manifest drift",
    )
    expiry = datetime.fromisoformat(authority["effective_expiry"].replace("Z", "+00:00"))
    require(expiry.tzinfo is not None, "Authority expiry requires timezone")
    require(expiry > datetime.now(UTC), "O01-B authority is expired")

    source = plan["source"]
    parsed = urlsplit(source["endpoint"])
    require(parsed.scheme == "https", "TED endpoint must use HTTPS")
    require(parsed.hostname == "api.ted.europa.eu", "TED endpoint host drift")
    require(parsed.path == "/v3/notices/search", "TED endpoint path drift")
    require(source["allowed_hosts"] == ["api.ted.europa.eu"], "Host allowlist drift")
    require(source["authentication"] == "NONE", "Search API must not use credentials")
    require(source["source_state"] == "CANDIDATE", "TED was admitted prematurely")

    window = plan["measurement_window"]
    require(window["query_start"] == "20260701", "Measurement start drift")
    require(window["query_end"] == "20260731", "Measurement end drift")

    sampling = plan["sampling"]
    countries = sampling["countries"]
    require(len(countries) == 12 and len(set(countries)) == 12, "Country strata drift")
    require(set(sampling["languages"]) == {"de", "en", "es", "fr", "it", "pt"}, "Language set drift")
    require(sampling["sample_size"] == 180, "Sample size drift")
    require(
        sampling["sample_size"]
        == len(countries) * sampling["target_per_country"],
        "Sample allocation does not match strata",
    )
    require("{country}" in sampling["query_contract"], "Query contract lacks country placeholder")
    require("20260701" in sampling["query_contract"] and "20260731" in sampling["query_contract"], "Query window drift")
    require(sampling["pagination_mode"] == "PAGE_NUMBER", "Pagination mode drift")
    require(1 <= sampling["page_size"] <= 100, "Unsafe page size")
    require(sampling["pages_per_country"] == 2, "Page budget drift")
    planned_requests = len(countries) * sampling["pages_per_country"] * 2 + 1
    require(
        planned_requests <= sampling["maximum_network_requests"] <= 60,
        "Network request budget is invalid",
    )
    require(sampling["maximum_attempts_per_request"] == 2, "Retry policy drift")
    require(len(sampling["exclusion_rules"]) >= 7, "Exclusion rules incomplete")

    retained = set(plan["fields"]["retained_raw_projection"])
    ephemeral = set(plan["fields"]["ephemeral_contact_projection"])
    require(retained.isdisjoint(CONTACT_FIELDS), "Contact fields entered retained raw projection")
    require(ephemeral == CONTACT_FIELDS | {"publication-number"}, "Ephemeral contact projection drift")
    require(retained.isdisjoint(ephemeral - {"publication-number"}), "Retained and ephemeral fields overlap")
    require(set(plan["quality_metrics"]) == EXPECTED_QUALITY_METRICS, "Quality metric contract drift")
    require(set(plan["lag_metrics"]) == EXPECTED_LAG_METRICS, "Lag metric contract drift")

    retention = plan["retention"]
    cert_path = plan_path.parent.parent / "keys" / "o01-evidence-recipient-cert.pem"
    require(cert_path.is_file(), "Evidence recipient certificate is missing")
    require(
        cert_fingerprint(cert_path) == retention["recipient_certificate_sha256_fingerprint"],
        "Evidence recipient certificate fingerprint mismatch",
    )
    require(retention["plaintext_raw_uploaded"] is False, "Plaintext raw upload enabled")
    require(retention["contact_values_persisted"] is False, "Contact persistence enabled")

    non_authorisations = plan["non_authorisations"]
    require(non_authorisations["public_launch"] == "NO_GO", "Public launch advanced")
    require(
        all(value is False for key, value in non_authorisations.items() if key != "public_launch"),
        "A forbidden authority was enabled",
    )
    require(len(plan["stop_conditions"]) >= 12, "Stop-condition set incomplete")
    return {
        "status": "PASS",
        "output": "O01_QUALITY_COVERAGE_LAG_PLAN_FROZEN",
        "plan_sha256": plan_digest,
        "sample_frozen": True,
        "sample_size": sampling["sample_size"],
        "countries": countries,
        "languages": sampling["languages"],
        "maximum_network_requests": sampling["maximum_network_requests"],
        "target_head_sha": authority["target_head_sha"],
        "manifest_reference": authority["manifest_reference"],
    }


def verify_final(plan_path: Path, result_dir: Path) -> dict[str, Any]:
    plan = load_json(plan_path)
    sampling = load_json(result_dir / "sampling-manifest.v0.1.json")
    coverage = load_json(result_dir / "coverage-report.v0.1.json")
    quality = load_json(result_dir / "quality-report.v0.1.json")
    lag = load_json(result_dir / "lag-report.v0.1.json")
    preliminary = load_json(result_dir / "preliminary-result.v0.1.json")
    raw_retention = load_json(result_dir / "raw-retention.v0.1.json")

    plan_digest = sha256_prefixed(plan_path.read_bytes())
    sample_frozen = (
        plan["frozen_before_execution"] is True
        and sampling["frozen_before_execution"] is True
        and sampling["plan_sha256"] == plan_digest
    )
    raw_secure = (
        raw_retention["status"] == "SEALED"
        and raw_retention["format"] == "CMS_ENVELOPED_DATA"
        and raw_retention["plaintext_removed"] is True
        and raw_retention["plaintext_uploaded"] is False
        and raw_retention["cms_structure_verified"] is True
        and raw_retention["recipient_certificate_sha256_fingerprint"]
        == plan["retention"]["recipient_certificate_sha256_fingerprint"]
        and (result_dir / raw_retention["ciphertext_file"]).is_file()
    )
    quality_complete = (
        quality["schema_version"] == "axignal.o01-quality-report/v0.1"
        and set(quality["metrics"]) == EXPECTED_QUALITY_METRICS
    )
    lag_complete = (
        lag["schema_version"] == "axignal.o01-lag-report/v0.1"
        and set(lag["metrics"]) == EXPECTED_LAG_METRICS
        and bool(lag["confidence_limitations"])
    )
    limitations_disclosed = (
        coverage["schema_version"] == "axignal.o01-coverage-report/v0.1"
        and len(coverage["areas_not_covered"]) >= 6
    )
    fabricated = int(preliminary["fabricated_evidence"])
    require(preliminary["synthetic_evidence"] == 0, "Synthetic evidence entered campaign")
    require(preliminary["source_state"] == "CANDIDATE", "TED source state advanced")
    require(preliminary["public_claim_contribution"] is False, "Campaign enabled a public claim")

    threshold_result = evaluate_thresholds(
        plan=plan,
        quality=quality,
        coverage=coverage,
        lag=lag,
        raw_responses_retained_securely=raw_secure,
    )
    criteria = {
        "SAMPLE_FROZEN": sample_frozen,
        "RAW_RESPONSES_RETAINED_SECURELY": raw_secure,
        "QUALITY_REPORT_COMPLETE": quality_complete,
        "LAG_REPORT_COMPLETE": lag_complete,
        "COVERAGE_LIMITATIONS_DISCLOSED": limitations_disclosed,
        "FABRICATED_EVIDENCE": fabricated,
    }
    pass_result = (
        sample_frozen
        and raw_secure
        and quality_complete
        and lag_complete
        and limitations_disclosed
        and fabricated == 0
        and threshold_result["all_pass"]
    )
    return {
        "status": "PASS" if pass_result else "FAIL",
        "output": (
            "O01_QUALITY_COVERAGE_LAG_PASS"
            if pass_result
            else "O01_QUALITY_COVERAGE_LAG_FAIL"
        ),
        "criteria": criteria,
        "thresholds": threshold_result,
        "sample_count": quality["sample_count"],
        "plan_sha256": plan_digest,
        "raw_retention": raw_retention,
        "authority_boundary": {
            "source_state": "CANDIDATE",
            "product_admitted": False,
            "public_claims_authorised": False,
            "public_redistribution_authorised": False,
            "contact_marketing_authorised": False,
            "model_training_authorised": False,
            "bid_submission_authorised": False,
            "public_launch": "NO_GO",
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--result-dir", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = (
            verify_final(args.plan, args.result_dir)
            if args.result_dir
            else verify_plan(args.plan)
        )
    except (
        KeyError,
        OSError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        ContractError,
    ) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    if args.result_dir and result["status"] != "PASS":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
