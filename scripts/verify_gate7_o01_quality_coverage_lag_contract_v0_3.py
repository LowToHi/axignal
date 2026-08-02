# ruff: noqa: E501
from __future__ import annotations

import argparse
import hashlib
import json
import ssl
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from axignal_api.o01_quality_campaign import evaluate_thresholds, sha256_prefixed
from materialize_gate7_o01_quality_coverage_lag_plan_v0_3 import materialize_plan

LANGUAGES = {"de", "en", "es", "fr", "it", "pt"}
QUALITY = {"identifier_accuracy", "title_completeness", "buyer_accuracy", "deadline_accuracy", "amount_accuracy", "currency_accuracy", "CPV_accuracy", "NUTS_accuracy", "lot_completeness", "contact_channel_classification_accuracy", "duplicate_rate", "unparseable_rate", "missing_field_rate"}
LAG = {"source_publication_lag", "source_availability_lag", "AXIGNAL_acquisition_lag", "normalisation_lag", "indexing_lag", "subscriber_notification_lag"}
CONTACTS = {"buyer-contact-point", "buyer-email", "organisation-tel-buyer", "buyer-internet-address", "buyer-profile", "submission-url-lot"}
QUERY = "buyer-country IN ({country}) AND publication-date >= 20260701 AND publication-date <= 20260731 SORT BY publication-number"


class ContractError(RuntimeError):
    pass


def require(value: bool, message: str) -> None:
    if not value:
        raise ContractError(message)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"Expected JSON object: {path}")
    return value


def certificate_fingerprint(path: Path) -> str:
    der = ssl.PEM_cert_to_DER_cert(path.read_text(encoding="utf-8"))
    return hashlib.sha256(der).hexdigest().upper()


def verify_plan(path: Path) -> dict[str, Any]:
    actual = load(path)
    expected, manifest = materialize_plan()
    require(actual == expected, "Materialized v0.3 plan drift")
    authority = actual["authority"]
    require(authority["required_output"] == "O01_CAMPAIGN_AUTHORISED", "Authority output drift")
    require(set(authority["required_authorities"]) == {"LEGAL", "PRIVACY_DATA_RIGHTS"}, "Authority set drift")
    require(authority["target_head_sha"] == manifest["target"]["head_sha"], "Target head drift")
    require(authority["target_tree_sha"] == manifest["target"]["git_tree_sha"], "Target tree drift")
    require(authority["effective_expiry"] == manifest["decision_contract"]["decision_max_expires_at"], "Expiry boundary drift")

    source, sample = actual["source"], actual["sampling"]
    endpoint = urlsplit(source["endpoint"])
    require((endpoint.scheme, endpoint.hostname, endpoint.path) == ("https", "api.ted.europa.eu", "/v3/notices/search"), "Endpoint drift")
    require(source["allowed_hosts"] == ["api.ted.europa.eu"] and source["authentication"] == "NONE", "Source boundary drift")
    require(source["source_state"] == "CANDIDATE", "TED admitted prematurely")
    require(sample["query_contract"] == QUERY, "Approved query drift")
    require(len(sample["countries"]) == 12 and len(set(sample["countries"])) == 12, "Country strata drift")
    require(set(sample["languages"]) == LANGUAGES, "Language set drift")
    require((sample["sample_size"], sample["target_per_country"], sample["page_size"], sample["pages_per_country"]) == (180, 15, 100, 2), "Sampling drift")
    require((sample["maximum_network_requests"], sample["maximum_attempts_per_request"]) == (60, 2), "Network budget drift")
    retained = set(actual["fields"]["retained_raw_projection"])
    ephemeral = set(actual["fields"]["ephemeral_contact_projection"])
    require(retained.isdisjoint(CONTACTS), "Contact value entered retained projection")
    require(ephemeral == CONTACTS | {"publication-number"}, "Canonical contact projection drift")
    require("buyer-tel" not in ephemeral, "Unsupported buyer-tel remains present")
    require(set(actual["quality_metrics"]) == QUALITY and set(actual["lag_metrics"]) == LAG, "Metric contract drift")
    cert = path.parents[2] / "data/acceptance/keys/o01-evidence-recipient-cert.pem"
    require(certificate_fingerprint(cert) == actual["retention"]["recipient_certificate_sha256_fingerprint"], "Certificate drift")
    require(actual["retention"]["plaintext_raw_uploaded"] is False and actual["retention"]["contact_values_persisted"] is False, "Retention boundary drift")
    boundary = actual["non_authorisations"]
    require(boundary["public_launch"] == "NO_GO" and all(v is False for k, v in boundary.items() if k != "public_launch"), "Authority expanded")
    return {
        "status": "PASS",
        "output": "O01_QUALITY_COVERAGE_LAG_V0_3_PLAN_FROZEN",
        "plan_sha256": sha256_prefixed(path.read_bytes()),
        "campaign_id": actual["campaign_id"],
        "sample_size": sample["sample_size"],
        "countries": sample["countries"],
        "languages": sample["languages"],
        "maximum_network_requests": sample["maximum_network_requests"],
        "target_head_sha": authority["target_head_sha"],
        "manifest_reference": authority["manifest_reference"],
        "canonical_telephone_field": "organisation-tel-buyer",
    }


def verify_final(path: Path, result_dir: Path) -> dict[str, Any]:
    plan = load(path)
    verify_plan(path)
    plan_sha = sha256_prefixed(path.read_bytes())
    sampling = load(result_dir / "sampling-manifest.v0.1.json")
    coverage = load(result_dir / "coverage-report.v0.1.json")
    quality = load(result_dir / "quality-report.v0.1.json")
    lag = load(result_dir / "lag-report.v0.1.json")
    preliminary = load(result_dir / "preliminary-result.v0.1.json")
    raw = load(result_dir / "raw-retention.v0.1.json")
    controls = load(result_dir / "operational-controls.v0.1.json")
    multilingual = load(result_dir / "multilingual-journeys.v0.1.json")
    authority = load(result_dir / "current-authority/result.v0.1.json")
    network = load(result_dir / "network-ledger.v0.1.json")

    sample_frozen = plan["frozen_before_execution"] is True and sampling["frozen_before_execution"] is True and sampling["plan_sha256"] == plan_sha
    raw_secure = raw["status"] == "SEALED" and raw["format"] == "CMS_ENVELOPED_DATA" and raw["plaintext_removed"] is True and raw["plaintext_uploaded"] is False and raw["cms_structure_verified"] is True and raw["recipient_certificate_sha256_fingerprint"] == plan["retention"]["recipient_certificate_sha256_fingerprint"] and (result_dir / raw["ciphertext_file"]).is_file()
    quality_complete = quality["schema_version"] == "axignal.o01-quality-report/v0.1" and set(quality["metrics"]) == QUALITY
    lag_complete = lag["schema_version"] == "axignal.o01-lag-report/v0.1" and set(lag["metrics"]) == LAG and bool(lag["confidence_limitations"])
    limitations = coverage["schema_version"] == "axignal.o01-coverage-report/v0.1" and len(coverage["areas_not_covered"]) >= 6
    controls_complete = controls["status"] == "PASS" and controls["output"] == "O01_OPERATIONAL_CONTROLS_PASS" and controls["kill_switch"]["pass"] is True and controls["kill_switch"]["requests_after_activation"] == 0 and controls["rollback"]["pass"] is True and controls["rollback"]["exact_restore"] is True and controls["authority_boundary_unchanged"] is True
    multilingual_complete = multilingual["status"] == "PASS" and multilingual["output"] == "O01_MULTILINGUAL_JOURNEYS_PASS" and multilingual["all_languages_complete"] is True and set(multilingual["journeys"]) == LANGUAGES and all(all(j[stage] == "PASS" for stage in ("ingestion", "normalisation", "search", "presentation")) for j in multilingual["journeys"].values()) and multilingual["raw_text_persisted"] is False
    authority_current = authority["execution_authorised"] is True and authority["output"] == "O01_CAMPAIGN_AUTHORISED" and authority["head_match"] is True and authority["manifest_match"] is True and authority["signatures_human"] is True and authority["expiry_within_evidence"] is True

    require(authority_current, "Human authority was not current at execution")
    require(network["network_requests_used"] <= network["network_requests_maximum"] <= 60, "Network budget exceeded")
    require(preliminary["synthetic_evidence"] == 0 and preliminary["fabricated_evidence"] == 0, "Invented evidence entered campaign")
    require(preliminary["source_state"] == "CANDIDATE" and preliminary["public_claim_contribution"] is False, "Authority boundary advanced")
    require(controls["fabricated_evidence"] == 0 and multilingual["fabricated_evidence"] == 0, "Control evidence fabricated")

    thresholds = evaluate_thresholds(plan=plan, quality=quality, coverage=coverage, lag=lag, raw_responses_retained_securely=raw_secure)
    criteria = {
        "HUMAN_AUTHORITY_CURRENT": authority_current,
        "SAMPLE_FROZEN": sample_frozen,
        "RAW_RESPONSES_RETAINED_SECURELY": raw_secure,
        "QUALITY_REPORT_COMPLETE": quality_complete,
        "LAG_REPORT_COMPLETE": lag_complete,
        "COVERAGE_LIMITATIONS_DISCLOSED": limitations,
        "MULTILINGUAL_JOURNEYS_COMPLETE": multilingual_complete,
        "KILL_SWITCH_TESTED": controls_complete and controls["kill_switch"]["pass"],
        "ROLLBACK_TESTED": controls_complete and controls["rollback"]["pass"],
        "FABRICATED_EVIDENCE": 0,
    }
    passed = all(v is True or v == 0 for v in criteria.values()) and controls_complete and thresholds["all_pass"]
    return {
        "status": "PASS" if passed else "FAIL",
        "output": "O01_QUALITY_COVERAGE_LAG_PASS" if passed else "O01_QUALITY_COVERAGE_LAG_FAIL",
        "criteria": criteria,
        "thresholds": thresholds,
        "sample_count": quality["sample_count"],
        "plan_sha256": plan_sha,
        "controls": controls,
        "multilingual": multilingual,
        "raw_retention": raw,
        "authority": authority,
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--result-dir", type=Path)
    args = parser.parse_args()
    try:
        result = verify_final(args.plan, args.result_dir) if args.result_dir else verify_plan(args.plan)
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError, ContractError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 2 if args.result_dir and result["status"] != "PASS" else 0


if __name__ == "__main__":
    raise SystemExit(main())
