# ruff: noqa: E501
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

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "data/acceptance/campaigns/AX-LIB-O01-quality-coverage-lag-execution-contract.v0.2.json"
PLAN_SHA = "sha256:cae7894ca905ae7b0d0085699d6b9e75d08e684b70d58f6398594dad46fc5c97"
CONTRACT_SHA = "sha256:f86672f2925343fccc61ebe0cb1085a470bbb54d062f1f936eed9347854ff3a3"
EVALUATOR = ("488cedd13ff7771324fdeaa4717bd17f2d6294b7", "bb23c60e8b647951681754bbc77d37930a542636")
TARGET = ("63b210b12988b26be04abed3701f8d97ffccebad", "2d02c1d616516a14168b6c378d2d3352d2750da2")
MANIFEST = "sha256:e608b2d464c005aab5efff6f2e9689b7cd29c78941a1f45336eab91b87d58de6"
AUTHORITY_ARTIFACT = (8835414821, "sha256:20fa305b6647ff30c2d410d20107ecd1632fa94a5897ec273fb3a437c3b30802")
LANGUAGES = {"de", "en", "es", "fr", "it", "pt"}
QUALITY = {"identifier_accuracy", "title_completeness", "buyer_accuracy", "deadline_accuracy", "amount_accuracy", "currency_accuracy", "CPV_accuracy", "NUTS_accuracy", "lot_completeness", "contact_channel_classification_accuracy", "duplicate_rate", "unparseable_rate", "missing_field_rate"}
LAG = {"source_publication_lag", "source_availability_lag", "AXIGNAL_acquisition_lag", "normalisation_lag", "indexing_lag", "subscriber_notification_lag"}
CONTACTS = {"buyer-contact-point", "buyer-email", "buyer-tel", "buyer-internet-address", "buyer-profile", "submission-url-lot"}
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
    require(sha256_prefixed(path.read_bytes()) == PLAN_SHA, "Plan digest drift")
    require(sha256_prefixed(CONTRACT.read_bytes()) == CONTRACT_SHA, "Contract digest drift")
    plan, contract = load(path), load(CONTRACT)
    comparable = dict(plan)
    authority = comparable.pop("authority")
    comparable["schema_version"] = contract["schema_version"]
    require(comparable == contract, "Plan differs from approved execution contract")
    require((authority["evaluator_head_sha"], authority["evaluator_tree_sha"]) == EVALUATOR, "Evaluator drift")
    require((authority["target_head_sha"], authority["target_tree_sha"]) == TARGET, "Target drift")
    require(authority["manifest_reference"] == MANIFEST, "Manifest drift")
    require((authority["authority_artifact_id"], authority["authority_artifact_digest"]) == AUTHORITY_ARTIFACT, "Authority artifact drift")
    expiry = datetime.fromisoformat(authority["effective_expiry"].replace("Z", "+00:00"))
    require(expiry.tzinfo is not None and expiry > datetime.now(UTC), "Authority expired")
    source, sample = plan["source"], plan["sampling"]
    endpoint = urlsplit(source["endpoint"])
    require((endpoint.scheme, endpoint.hostname, endpoint.path) == ("https", "api.ted.europa.eu", "/v3/notices/search"), "Endpoint drift")
    require(source["allowed_hosts"] == ["api.ted.europa.eu"] and source["authentication"] == "NONE", "Source boundary drift")
    require(source["source_state"] == "CANDIDATE", "TED admitted prematurely")
    require(sample["query_contract"] == QUERY, "Approved query drift")
    require(len(sample["countries"]) == 12 and len(set(sample["countries"])) == 12, "Country strata drift")
    require(set(sample["languages"]) == LANGUAGES, "Language set drift")
    require((sample["sample_size"], sample["target_per_country"], sample["page_size"], sample["pages_per_country"]) == (180, 15, 100, 2), "Sampling drift")
    require((sample["maximum_network_requests"], sample["maximum_attempts_per_request"]) == (60, 2), "Network budget drift")
    retained = set(plan["fields"]["retained_raw_projection"])
    ephemeral = set(plan["fields"]["ephemeral_contact_projection"])
    require(retained.isdisjoint(CONTACTS) and ephemeral == CONTACTS | {"publication-number"}, "Contact projection drift")
    require(set(plan["quality_metrics"]) == QUALITY and set(plan["lag_metrics"]) == LAG, "Metric contract drift")
    cert = path.parent.parent / "keys" / "o01-evidence-recipient-cert.pem"
    require(certificate_fingerprint(cert) == plan["retention"]["recipient_certificate_sha256_fingerprint"], "Certificate drift")
    require(plan["retention"]["plaintext_raw_uploaded"] is False and plan["retention"]["contact_values_persisted"] is False, "Retention boundary drift")
    boundary = plan["non_authorisations"]
    require(boundary["public_launch"] == "NO_GO" and all(v is False for k, v in boundary.items() if k != "public_launch"), "Authority expanded")
    return {"status": "PASS", "output": "O01_QUALITY_COVERAGE_LAG_V0_2_PLAN_FROZEN", "plan_sha256": PLAN_SHA, "execution_contract_sha256": CONTRACT_SHA, "sample_size": 180, "countries": sample["countries"], "languages": sample["languages"], "maximum_network_requests": 60, "target_head_sha": TARGET[0], "manifest_reference": MANIFEST, "authority_artifact_id": AUTHORITY_ARTIFACT[0]}


def verify_final(path: Path, result_dir: Path) -> dict[str, Any]:
    plan = load(path)
    sampling, coverage = load(result_dir / "sampling-manifest.v0.1.json"), load(result_dir / "coverage-report.v0.1.json")
    quality, lag = load(result_dir / "quality-report.v0.1.json"), load(result_dir / "lag-report.v0.1.json")
    preliminary, raw = load(result_dir / "preliminary-result.v0.1.json"), load(result_dir / "raw-retention.v0.1.json")
    controls, multilingual = load(result_dir / "operational-controls.v0.1.json"), load(result_dir / "multilingual-journeys.v0.1.json")
    sample_frozen = plan["frozen_before_execution"] is True and sampling["frozen_before_execution"] is True and sampling["plan_sha256"] == PLAN_SHA
    raw_secure = raw["status"] == "SEALED" and raw["format"] == "CMS_ENVELOPED_DATA" and raw["plaintext_removed"] is True and raw["plaintext_uploaded"] is False and raw["cms_structure_verified"] is True and raw["recipient_certificate_sha256_fingerprint"] == plan["retention"]["recipient_certificate_sha256_fingerprint"] and (result_dir / raw["ciphertext_file"]).is_file()
    quality_complete = quality["schema_version"] == "axignal.o01-quality-report/v0.1" and set(quality["metrics"]) == QUALITY
    lag_complete = lag["schema_version"] == "axignal.o01-lag-report/v0.1" and set(lag["metrics"]) == LAG and bool(lag["confidence_limitations"])
    limitations = coverage["schema_version"] == "axignal.o01-coverage-report/v0.1" and len(coverage["areas_not_covered"]) >= 6
    controls_complete = controls["status"] == "PASS" and controls["output"] == "O01_OPERATIONAL_CONTROLS_PASS" and controls["kill_switch"]["pass"] is True and controls["kill_switch"]["requests_after_activation"] == 0 and controls["rollback"]["pass"] is True and controls["rollback"]["exact_restore"] is True and controls["authority_boundary_unchanged"] is True
    multilingual_complete = multilingual["status"] == "PASS" and multilingual["output"] == "O01_MULTILINGUAL_JOURNEYS_PASS" and multilingual["all_languages_complete"] is True and set(multilingual["journeys"]) == LANGUAGES and all(all(j[stage] == "PASS" for stage in ("ingestion", "normalisation", "search", "presentation")) for j in multilingual["journeys"].values()) and multilingual["raw_text_persisted"] is False
    require(preliminary["synthetic_evidence"] == 0 and preliminary["fabricated_evidence"] == 0, "Invented evidence entered campaign")
    require(preliminary["source_state"] == "CANDIDATE" and preliminary["public_claim_contribution"] is False, "Authority boundary advanced")
    require(controls["fabricated_evidence"] == 0 and multilingual["fabricated_evidence"] == 0, "Control evidence fabricated")
    thresholds = evaluate_thresholds(plan=plan, quality=quality, coverage=coverage, lag=lag, raw_responses_retained_securely=raw_secure)
    criteria = {"SAMPLE_FROZEN": sample_frozen, "RAW_RESPONSES_RETAINED_SECURELY": raw_secure, "QUALITY_REPORT_COMPLETE": quality_complete, "LAG_REPORT_COMPLETE": lag_complete, "COVERAGE_LIMITATIONS_DISCLOSED": limitations, "MULTILINGUAL_JOURNEYS_COMPLETE": multilingual_complete, "KILL_SWITCH_TESTED": controls_complete and controls["kill_switch"]["pass"], "ROLLBACK_TESTED": controls_complete and controls["rollback"]["pass"], "FABRICATED_EVIDENCE": 0}
    passed = all(v is True or v == 0 for v in criteria.values()) and controls_complete and thresholds["all_pass"]
    return {"status": "PASS" if passed else "FAIL", "output": "O01_QUALITY_COVERAGE_LAG_PASS" if passed else "O01_QUALITY_COVERAGE_LAG_FAIL", "criteria": criteria, "thresholds": thresholds, "sample_count": quality["sample_count"], "plan_sha256": PLAN_SHA, "controls": controls, "multilingual": multilingual, "raw_retention": raw, "authority_boundary": {"source_state": "CANDIDATE", "product_admitted": False, "public_claims_authorised": False, "public_redistribution_authorised": False, "contact_marketing_authorised": False, "model_training_authorised": False, "bid_submission_authorised": False, "public_launch": "NO_GO"}}


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
