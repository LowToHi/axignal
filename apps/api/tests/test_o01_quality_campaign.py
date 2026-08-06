from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from axignal_api.o01_quality_campaign import (
    PageObservation,
    contact_classification_report,
    coverage_report,
    deterministic_sample,
    index_and_enqueue,
    lag_report,
    quality_report,
)
from axignal_api.o01_quality_failure import (
    purge_ephemeral_directory,
    sanitise_ted_error_body,
)


def source_record(number: str, country: str = "ESP") -> dict[str, object]:
    return {
        "publication-number": number,
        "publication-date": "2026-07-15",
        "notice-identifier": [f"notice-{number}"],
        "notice-version": ["01"],
        "notice-type": ["cn-standard"],
        "form-type": ["competition"],
        "notice-title": {"eng": ["Public software services"]},
        "buyer-name": {"eng": ["Example public authority"]},
        "buyer-country": [country],
        "procedure-type": ["open"],
        "contract-nature": ["services"],
        "classification-cpv": ["48000000"],
        "place-of-performance-country-proc": [country],
        "place-of-performance-subdiv-proc": [f"{country[:2]}1"],
        "deadline": ["2026-09-01T12:00:00Z"],
        "estimated-value-proc": ["100000.00"],
        "estimated-value-cur-proc": ["EUR"],
        "identifier-lot": ["LOT-1"],
    }


def observation(country: str = "ESP") -> PageObservation:
    start = datetime.now(UTC) - timedelta(seconds=1)
    return PageObservation(
        country=country,
        page=1,
        query="frozen",
        retrieval_started_at=start,
        retrieval_completed_at=start + timedelta(milliseconds=250),
        response_date_header=None,
        total_notice_count=2,
        returned_count=2,
    )


def minimal_plan() -> dict[str, object]:
    return {
        "sampling": {
            "page_size": 100,
            "pages_per_country": 2,
            "maximum_network_requests": 60,
            "maximum_attempts_per_request": 2,
        },
        "source": {
            "declared_publication_frequency": "MONDAY_TO_FRIDAY",
            "official_limits": {
                "page_number_max_retrievable_notices": 15000,
                "max_notices_per_page": 250,
                "max_fields_per_page": 10000,
                "iteration_total_limit": None,
            },
        },
    }


def test_deterministic_sample_is_stable_and_stratified() -> None:
    candidates = {
        "ESP": [source_record("000001-2026"), source_record("000002-2026")],
        "FRA": [
            source_record("000003-2026", "FRA"),
            source_record("000004-2026", "FRA"),
        ],
    }
    first, available = deterministic_sample(
        candidates,
        seed="frozen-seed",
        target_per_country=1,
    )
    second, _ = deterministic_sample(
        candidates,
        seed="frozen-seed",
        target_per_country=1,
    )
    assert first == second
    assert available == {"ESP": 2, "FRA": 2}
    assert {country for country, _ in first} == {"ESP", "FRA"}


def test_real_field_projection_builds_complete_reports() -> None:
    page = observation()
    selected = [
        (source_record("000001-2026"), "ESP", page),
        (source_record("000002-2026"), "ESP", page),
    ]
    normalized, acquisition, notifications = index_and_enqueue(selected)
    contact = contact_classification_report(
        [
            {
                "publication-number": "000001-2026",
                "buyer-email": ["procurement@example.eu"],
                "buyer-internet-address": ["https://example.eu/procurement"],
            }
        ]
    )
    quality = quality_report(
        selected_source_records=[item[0] for item in selected],
        normalized_records=normalized,
        all_candidate_records=[item[0] for item in selected],
        contact_classification=contact,
    )
    coverage = coverage_report(
        normalized_records=normalized,
        page_observations=[page],
        available_by_country={"ESP": 2},
        plan=minimal_plan(),
        history_probe={"status": "OBSERVED"},
    )
    lag = lag_report(normalized, acquisition_by_notice=acquisition)

    assert quality["metrics"]["identifier_accuracy"]["value"] == 1.0
    assert quality["metrics"]["CPV_accuracy"]["value"] == 1.0
    assert contact["value"] == 1.0
    assert contact["raw_contact_values_persisted"] is False
    assert coverage["countries_and_jurisdictions_observed"]["buyer_country"] == {
        "ESP": 2
    }
    assert lag["metrics"]["AXIGNAL_acquisition_lag"]["sample_count"] == 2
    assert len(notifications) == 2
    assert all(item["external_delivery_authorised"] is False for item in notifications)


def test_missing_optional_source_metadata_is_disclosed_without_claims() -> None:
    page = observation()
    normalized, _, _ = index_and_enqueue(
        [(source_record("000001-2026"), "ESP", page)]
    )
    plan = minimal_plan()
    source = plan["source"]
    assert isinstance(source, dict)
    source.clear()

    report = coverage_report(
        normalized_records=normalized,
        page_observations=[page],
        available_by_country={"ESP": 1},
        plan=plan,
        history_probe={"status": "OBSERVED"},
    )

    assert (
        report["frequency"]["declared"]
        == "NOT_DECLARED_IN_FROZEN_EXECUTION_CONTRACT"
    )
    assert (
        report["search_limits"]["status"]
        == "NOT_EMBEDDED_IN_FROZEN_EXECUTION_CONTRACT"
    )
    assert report["search_limits"]["public_claim_authorised"] is False
    assert report["search_limits"]["campaign_enforced_limits"] == {
        "maximum_network_requests": 60,
        "maximum_attempts_per_request": 2,
        "page_size": 100,
        "pages_per_country": 2,
        "country_retrieval_cap": 200,
    }
    assert any(
        "no provider-frequency claim is made" in limitation
        for limitation in report["areas_not_covered"]
    )
    assert any(
        "only enforced campaign limits are disclosed" in limitation
        for limitation in report["areas_not_covered"]
    )


def test_duplicate_rate_uses_candidate_universe() -> None:
    page = observation()
    record = source_record("000001-2026")
    normalized, _, _ = index_and_enqueue([(record, "ESP", page)])
    contact = contact_classification_report([])
    report = quality_report(
        selected_source_records=[record],
        normalized_records=normalized,
        all_candidate_records=[record, record],
        contact_classification=contact,
    )
    assert report["metrics"]["duplicate_rate"]["value"] == 0.5
    assert report["metrics"]["contact_channel_classification_accuracy"]["value"] is None


def test_ted_error_diagnostic_is_bounded_and_allowlisted() -> None:
    raw = json.dumps(
        {
            "errors": [
                {
                    "errorCode": "QUERY_SYNTAX",
                    "message": "Unexpected comparison operator",
                    "location": {"line": 1, "column": 25},
                    "buyer-email": "must-not-survive@example.eu",
                    "secret": "must-not-survive",
                }
            ],
            "payload": {"buyer-email": "must-not-survive@example.eu"},
        }
    ).encode()
    diagnostic = sanitise_ted_error_body(raw)
    rendered = json.dumps(diagnostic, sort_keys=True)

    assert diagnostic["format"] == "JSON"
    assert diagnostic["raw_response_retained"] is False
    assert "QUERY_SYNTAX" in rendered
    assert "Unexpected comparison operator" in rendered
    assert "buyer-email" not in rendered
    assert "must-not-survive" not in rendered


def test_ephemeral_raw_directory_is_purged(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "response.json").write_text("sensitive", encoding="utf-8")

    assert purge_ephemeral_directory(raw_dir) is True
    assert not raw_dir.exists()
    assert purge_ephemeral_directory(raw_dir) is False
