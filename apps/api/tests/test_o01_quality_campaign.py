from __future__ import annotations

from datetime import UTC, datetime, timedelta

from axignal_api.o01_quality_campaign import (
    PageObservation,
    contact_classification_report,
    coverage_report,
    deterministic_sample,
    index_and_enqueue,
    lag_report,
    quality_report,
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
