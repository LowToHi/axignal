from __future__ import annotations

from collections import Counter
from datetime import UTC, date, datetime
from typing import Any

from .o01_quality_common import NormalizedNotice, PageObservation
from .o01_quality_reports import metric_summary


def coverage_report(
    *,
    normalized_records: list[NormalizedNotice],
    page_observations: list[PageObservation],
    available_by_country: dict[str, int],
    plan: dict[str, Any],
    history_probe: dict[str, Any],
) -> dict[str, Any]:
    buyer_countries = Counter(
        code for record in normalized_records for code in record.buyer_countries
    )
    performance_countries = Counter(
        code for record in normalized_records for code in record.performance_countries
    )
    cpv_prefixes = Counter(
        code[:2]
        for record in normalized_records
        for code in record.cpv_codes
        if len(code) >= 2
    )
    procedure_types = Counter(
        value for record in normalized_records for value in record.procedure_types
    )
    notice_types = Counter(
        value for record in normalized_records for value in record.notice_type
    )
    form_types = Counter(
        value for record in normalized_records for value in record.form_type
    )
    contract_natures = Counter(
        value for record in normalized_records for value in record.contract_natures
    )
    publication_dates = sorted(
        record.publication_date
        for record in normalized_records
        if record.publication_date
    )
    unique_dates = sorted(set(publication_dates))
    observed_gaps: list[int] = []
    for previous, current in zip(unique_dates, unique_dates[1:], strict=False):
        observed_gaps.append(
            (date.fromisoformat(current) - date.fromisoformat(previous)).days
        )

    page_size = int(plan["sampling"]["page_size"])
    page_cap = int(plan["sampling"]["pages_per_country"]) * page_size
    truncation = []
    for observation in page_observations:
        if observation.page != 1 or observation.total_notice_count is None:
            continue
        if observation.total_notice_count > page_cap:
            truncation.append(
                {
                    "country": observation.country,
                    "matching_notices": observation.total_notice_count,
                    "retrieval_cap": page_cap,
                    "risk": "HIGH",
                }
            )

    return {
        "schema_version": "axignal.o01-coverage-report/v0.1",
        "sample_count": len(normalized_records),
        "countries_and_jurisdictions_observed": {
            "buyer_country": dict(sorted(buyer_countries.items())),
            "place_of_performance_country": dict(
                sorted(performance_countries.items())
            ),
            "sampling_strata_available": dict(sorted(available_by_country.items())),
        },
        "sectors_and_cpv_prefixes": dict(sorted(cpv_prefixes.items())),
        "procedure_types": dict(sorted(procedure_types.items())),
        "notice_types": dict(sorted(notice_types.items())),
        "form_types": dict(sorted(form_types.items())),
        "contract_natures": dict(sorted(contract_natures.items())),
        "lots": {
            "records_with_lot_identifiers": sum(
                bool(item.lot_identifiers) for item in normalized_records
            ),
            "lot_identifier_count": sum(
                len(item.lot_identifiers) for item in normalized_records
            ),
        },
        "history_available": {
            "sample_earliest_publication_date": (
                publication_dates[0] if publication_dates else None
            ),
            "sample_latest_publication_date": (
                publication_dates[-1] if publication_dates else None
            ),
            "archive_probe": history_probe,
        },
        "frequency": {
            "declared": plan["source"]["declared_publication_frequency"],
            "observed_unique_publication_dates": len(unique_dates),
            "observed_dates": unique_dates,
            "maximum_observed_calendar_gap_days": (
                max(observed_gaps) if observed_gaps else None
            ),
        },
        "search_limits": plan["source"]["official_limits"],
        "pagination_limits": {
            "frozen_page_size": page_size,
            "frozen_pages_per_country": plan["sampling"]["pages_per_country"],
            "frozen_country_retrieval_cap": page_cap,
        },
        "truncation_risk": {
            "strata_at_risk": truncation,
            "risk_present": bool(truncation),
        },
        "areas_not_covered": [
            "Countries outside the twelve frozen buyer-country strata.",
            (
                "Notices outside 2026-07-01 through 2026-07-31 and notices "
                "outside TED ACTIVE scope."
            ),
            "National and sub-threshold procurement portals not published through TED.",
            (
                "Attachments, source-native full text, third-party works and full "
                "XML/HTML payloads."
            ),
            (
                "Natural-person buyers, personal contact endpoints and contact "
                "values in retained evidence."
            ),
            (
                "Exhaustive archive history; the history probe is a bounded API "
                "observation only."
            ),
            (
                "Source factual correctness beyond transformation fidelity of "
                "projected TED fields."
            ),
        ],
    }


def lag_report(
    normalized_records: list[NormalizedNotice],
    *,
    acquisition_by_notice: dict[str, float],
) -> dict[str, Any]:
    source_publication: list[float] = []
    source_availability_upper_bound: list[float] = []
    acquisition: list[float] = []
    normalisation: list[float] = []
    indexing: list[float] = []
    notification: list[float] = []

    for record in normalized_records:
        retrieved_started = datetime.fromisoformat(
            record.retrieval_started_at.replace("Z", "+00:00")
        )
        retrieved_completed = datetime.fromisoformat(
            record.retrieval_completed_at.replace("Z", "+00:00")
        )
        normalised_at = datetime.fromisoformat(
            record.normalised_at.replace("Z", "+00:00")
        )
        indexed_at = datetime.fromisoformat(
            record.indexed_at.replace("Z", "+00:00")
        )
        notified_at = datetime.fromisoformat(
            record.notification_enqueued_at.replace("Z", "+00:00")
        )
        if record.publication_date:
            published = datetime.combine(
                date.fromisoformat(record.publication_date),
                datetime.min.time(),
                tzinfo=UTC,
            )
            lag = max(0.0, (retrieved_started - published).total_seconds())
            source_publication.append(lag)
            source_availability_upper_bound.append(lag)
        acquisition.append(
            acquisition_by_notice.get(
                record.publication_number,
                max(
                    0.0,
                    (retrieved_completed - retrieved_started).total_seconds(),
                ),
            )
        )
        normalisation.append(
            max(0.0, (normalised_at - retrieved_completed).total_seconds())
        )
        indexing.append(max(0.0, (indexed_at - normalised_at).total_seconds()))
        notification.append(max(0.0, (notified_at - indexed_at).total_seconds()))

    return {
        "schema_version": "axignal.o01-lag-report/v0.1",
        "metrics": {
            "source_publication_lag": metric_summary(
                source_publication, unit="seconds"
            ),
            "source_availability_lag": metric_summary(
                source_availability_upper_bound,
                unit="seconds_upper_bound",
            ),
            "AXIGNAL_acquisition_lag": metric_summary(
                acquisition, unit="seconds"
            ),
            "normalisation_lag": metric_summary(
                normalisation, unit="seconds"
            ),
            "indexing_lag": metric_summary(indexing, unit="seconds"),
            "subscriber_notification_lag": metric_summary(
                notification, unit="seconds"
            ),
        },
        "confidence_limitations": [
            (
                "TED publication-date is date-granular, so source_publication_lag "
                "uses 00:00 UTC as a conservative reference."
            ),
            (
                "Historical one-shot acquisition cannot observe the exact first "
                "API-availability instant; source_availability_lag is an upper "
                "bound ending at first campaign observation."
            ),
            (
                "AXIGNAL acquisition measures the bounded Search API HTTP request, "
                "not recurring production polling cadence."
            ),
            (
                "Subscriber notification lag measures creation of the private "
                "internal notification ledger, not external email, webhook or "
                "message delivery."
            ),
            (
                "Percentiles describe this frozen stratified sample and are not "
                "population-wide confidence intervals."
            ),
        ],
    }
