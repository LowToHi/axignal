from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime, timedelta

from scripts.verify_gate7_o01_ted_source_admission import (
    CAMPAIGN_RESULT_PATH,
    DOSSIER_PATH,
    MANIFEST_PATH,
    evaluate_payloads,
    load_json,
)

NOW = datetime(2026, 8, 2, 13, 30, tzinfo=UTC)


def historical_payloads() -> tuple[dict, dict, dict]:
    """Reconstruct the immutable v0.1 pre-admission state for legacy evaluation.

    The repository dossier now truthfully represents the later v0.2 admission. These
    tests exercise the historical v0.1 evaluator against its original CANDIDATE/MISSING
    semantics rather than treating the superseded evaluator as current authority.
    """

    manifest = load_json(MANIFEST_PATH)
    dossier = deepcopy(load_json(DOSSIER_PATH))
    campaign = load_json(CAMPAIGN_RESULT_PATH)

    sources = dossier["sources"]
    matches = [
        source
        for bucket in ("active", "suspended", "candidate")
        for source in sources[bucket]
        if source["source_id"] == manifest["source_id"]
    ]
    assert len(matches) == 1
    source = deepcopy(matches[0])
    campaign_sha = manifest["inputs"]["campaign_result_sha256"].removeprefix(
        "sha256:"
    )
    campaign_reference = {
        "kind": "QUALITY_REPORT",
        "reference": (
            "data/acceptance/campaign-results/"
            "AX-LIB-O01-TED-QALAG-ML-CONTROLS-v0.1.json"
        ),
        "sha256": campaign_sha,
        "expires_at": campaign["evidence_expires_at"],
    }

    source.update(
        {
            "state": "CANDIDATE",
            "contributes_to_public_claim": False,
            "rights_expiry": None,
            "admission": {
                "legal": "MISSING",
                "technical": "PASS",
                "quality": "MISSING",
                "rights": "MISSING",
                "human_authority": "MISSING",
            },
            "evidence": [campaign_reference],
        }
    )
    sources["active"] = []
    sources["suspended"] = []
    sources["candidate"] = [source]

    dossier["canonical_state"] = "BLOCKED"
    dossier["claim_decision"] = "DENIED"
    dossier["quality"] = {
        "status": "MISSING",
        "completeness": None,
        "accuracy": None,
        "freshness": None,
        "duplicate_rate": None,
        "evidence": [campaign_reference],
    }
    dossier["lag"] = {
        "status": "MISSING",
        "p50_seconds": None,
        "p95_seconds": None,
        "max_seconds": None,
        "evidence": [campaign_reference],
    }
    for journey in dossier["languages"]:
        journey.update(
            {
                "ingestion": "MISSING",
                "normalisation": "MISSING",
                "search": "MISSING",
                "presentation": "MISSING",
                "evidence": [],
            }
        )
    dossier["kill_switch"] = {
        "implemented": False,
        "tested": False,
        "evidence": [],
    }
    dossier["rollback"] = {
        "implemented": False,
        "tested": False,
        "evidence": [],
    }
    return manifest, dossier, campaign


def test_historical_evidence_blocks_admission_without_rejecting_source() -> None:
    manifest, dossier, campaign = historical_payloads()
    result = evaluate_payloads(manifest, dossier, campaign, now=NOW)
    assert result["output"] == "O01_TED_SOURCE_ADMISSION_BLOCKED"
    assert result["decision"] == "BLOCKED"
    assert result["next_state"] == "CANDIDATE"
    assert result["product_admitted"] is False
    assert result["claim_contribution"] is False
    assert result["failure_disposition"]["source_rejected"] is False
    assert "campaign_output" in result["failed_checks"]
    assert "quality" in result["failed_checks"]


def test_historical_campaign_pass_alone_cannot_admit_source() -> None:
    manifest, dossier, campaign = historical_payloads()
    campaign = deepcopy(campaign)
    campaign["output"] = "O01_QUALITY_COVERAGE_LAG_PASS"
    campaign["measurement_outcome"].update(
        {
            "sample_count": 180,
            "countries_observed": 12,
            "quality_report_complete": True,
            "lag_report_complete": True,
            "multilingual_journeys_complete": True,
            "kill_switch_rehearsal_complete": True,
            "rollback_rehearsal_complete": True,
            "thresholds_evaluated": True,
        }
    )
    result = evaluate_payloads(manifest, dossier, campaign, now=NOW)
    assert result["decision"] == "BLOCKED"
    assert "legal" in result["failed_checks"]
    assert "rights" in result["failed_checks"]
    assert "human_authority" in result["failed_checks"]


def test_historical_expired_campaign_evidence_blocks_admission() -> None:
    manifest, dossier, campaign = historical_payloads()
    campaign = deepcopy(campaign)
    campaign["evidence_expires_at"] = (
        NOW - timedelta(seconds=1)
    ).isoformat().replace("+00:00", "Z")
    result = evaluate_payloads(manifest, dossier, campaign, now=NOW)
    assert result["decision"] == "BLOCKED"
    assert "campaign_evidence_current" in result["failed_checks"]


def test_historical_hypothetical_complete_evidence_requires_every_gate() -> None:
    manifest, dossier, campaign = historical_payloads()
    dossier = deepcopy(dossier)
    campaign = deepcopy(campaign)
    source = dossier["sources"]["candidate"][0]
    source["admission"] = {
        "legal": "PASS",
        "technical": "PASS",
        "quality": "PASS",
        "rights": "PASS",
        "human_authority": "PASS",
    }
    for journey in dossier["languages"]:
        journey.update(
            {
                "ingestion": "PASS",
                "normalisation": "PASS",
                "search": "PASS",
                "presentation": "PASS",
                "evidence": [
                    {
                        "kind": "LANGUAGE_JOURNEY",
                        "reference": f"test:{journey['language']}",
                        "sha256": "0" * 64,
                        "expires_at": "2026-08-20T00:00:00Z",
                    }
                ],
            }
        )
    dossier["kill_switch"] = {
        "implemented": True,
        "tested": True,
        "evidence": [],
    }
    dossier["rollback"] = {
        "implemented": True,
        "tested": True,
        "evidence": [],
    }
    campaign["output"] = "O01_QUALITY_COVERAGE_LAG_PASS"
    campaign["measurement_outcome"].update(
        {
            "sample_count": 180,
            "countries_observed": 12,
            "quality_report_complete": True,
            "lag_report_complete": True,
            "multilingual_journeys_complete": True,
            "kill_switch_rehearsal_complete": True,
            "rollback_rehearsal_complete": True,
            "thresholds_evaluated": True,
        }
    )
    result = evaluate_payloads(manifest, dossier, campaign, now=NOW)
    assert result["decision"] == "ADMITTED"
    assert result["next_state"] == "PRODUCT_ADMITTED"
    assert result["product_admitted"] is True
    assert result["all_required_dimensions_pass"] is True
