from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .o01_quality_common import (
    O01QualityCampaignError,
    PageObservation,
    deterministic_sample,
    publication_number,
    sha256_prefixed,
)
from .o01_quality_contacts import contact_classification_report
from .o01_quality_coverage_lag import coverage_report, lag_report
from .o01_quality_http import (
    NetworkBudget,
    ensure_authority,
    extract_notices,
    extract_total,
    load_json,
    post_json,
    request_payload,
    write_json,
)
from .o01_quality_pipeline import index_and_enqueue
from .o01_quality_reports import quality_report


def run_campaign(
    *,
    plan_path: Path,
    authority_envelope_path: Path,
    raw_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    plan = load_json(plan_path)
    authority_envelope = load_json(authority_envelope_path)
    if not isinstance(plan, dict) or not isinstance(authority_envelope, dict):
        raise O01QualityCampaignError("Plan and authority envelope must be objects")
    ensure_authority(plan, authority_envelope)
    plan_digest = sha256_prefixed(plan_path.read_bytes())
    endpoint = str(plan["source"]["endpoint"])
    allowed_hosts = frozenset(str(item) for item in plan["source"]["allowed_hosts"])
    sampling = plan["sampling"]
    budget = NetworkBudget(int(sampling["maximum_network_requests"]))
    raw_dir.mkdir(parents=True, exist_ok=False)
    os.chmod(raw_dir, 0o700)
    output_dir.mkdir(parents=True, exist_ok=True)

    candidates_by_country: dict[str, list[dict[str, Any]]] = {
        country: [] for country in sampling["countries"]
    }
    record_page: dict[tuple[str, str], PageObservation] = {}
    page_observations: list[PageObservation] = []
    network_ledger: list[dict[str, Any]] = []
    retained_fields = [
        str(item) for item in plan["fields"]["retained_raw_projection"]
    ]

    for country in sampling["countries"]:
        query = str(sampling["query_contract"]).format(country=country)
        for page in range(1, int(sampling["pages_per_country"]) + 1):
            payload = request_payload(
                query=query,
                fields=retained_fields,
                page=page,
                plan=plan,
            )
            response, raw_body, metadata, started_at, completed_at = post_json(
                endpoint=endpoint,
                payload=payload,
                allowed_hosts=allowed_hosts,
                timeout_seconds=float(sampling["request_timeout_seconds"]),
                max_response_bytes=int(sampling["maximum_response_bytes"]),
                maximum_attempts=int(sampling["maximum_attempts_per_request"]),
                minimum_delay_seconds=float(sampling["minimum_delay_seconds"]),
                budget=budget,
            )
            notices = extract_notices(response)
            raw_path = raw_dir / f"retained-{country}-page-{page}.json"
            raw_path.write_bytes(raw_body)
            os.chmod(raw_path, 0o600)
            observation = PageObservation(
                country=country,
                page=page,
                query=query,
                retrieval_started_at=started_at,
                retrieval_completed_at=completed_at,
                response_date_header=metadata["date"],
                total_notice_count=extract_total(response),
                returned_count=len(notices),
            )
            page_observations.append(observation)
            candidates_by_country[country].extend(notices)
            for record in notices:
                notice_id = publication_number(record)
                if notice_id:
                    record_page[(country, notice_id)] = observation
            network_ledger.append(
                {
                    "purpose": "RETAINED_ALLOWLISTED_FIELD_PROJECTION",
                    "country": country,
                    "page": page,
                    "query": query,
                    "fields": retained_fields,
                    "returned_count": len(notices),
                    "total_notice_count": observation.total_notice_count,
                    "retrieval_started_at": started_at.isoformat().replace(
                        "+00:00", "Z"
                    ),
                    "retrieval_completed_at": completed_at.isoformat().replace(
                        "+00:00", "Z"
                    ),
                    **metadata,
                }
            )

    selected, available_by_country = deterministic_sample(
        candidates_by_country,
        seed=str(sampling["deterministic_seed"]),
        target_per_country=int(sampling["target_per_country"]),
    )
    selected_ids = {
        (country, publication_number(record) or "") for country, record in selected
    }

    contact_records: list[dict[str, Any]] = []
    contact_fields = [
        str(item) for item in plan["fields"]["ephemeral_contact_projection"]
    ]
    for country in sampling["countries"]:
        query = str(sampling["query_contract"]).format(country=country)
        for page in range(1, int(sampling["pages_per_country"]) + 1):
            payload = request_payload(
                query=query,
                fields=contact_fields,
                page=page,
                plan=plan,
            )
            response, _raw_body, metadata, started_at, completed_at = post_json(
                endpoint=endpoint,
                payload=payload,
                allowed_hosts=allowed_hosts,
                timeout_seconds=float(sampling["request_timeout_seconds"]),
                max_response_bytes=int(sampling["maximum_response_bytes"]),
                maximum_attempts=int(sampling["maximum_attempts_per_request"]),
                minimum_delay_seconds=float(sampling["minimum_delay_seconds"]),
                budget=budget,
            )
            notices = extract_notices(response)
            for record in notices:
                notice_id = publication_number(record)
                if notice_id and (country, notice_id) in selected_ids:
                    contact_records.append(record)
            network_ledger.append(
                {
                    "purpose": "EUHEMERAL_CONTACT_CLASSIFICATION_NO_PERSISTENCE",
                    "country": country,
                    "page": page,
                    "query": query,
                    "field_names": contact_fields,
                    "returned_count": len(notices),
                    "retained_contact_values": False,
                    "retrieval_started_at": started_at.isoformat().replace(
                        "+00:00", "Z"
                    ),
                    "retrieval_completed_at": completed_at.isoformat().replace(
                        "+00:00", "Z"
                    ),
                    "http_status": metadata["http_status"],
                    "response_bytes": metadata["response_bytes"],
                    "response_body_sha256": metadata["response_body_sha256"],
                }
            )

    contact_report = contact_classification_report(contact_records)
    contact_records.clear()

    history_query = "publication-date >= 19900101 SORT BY publication-date ASC"
    history_payload = request_payload(
        query=history_query,
        fields=["publication-number", "publication-date"],
        page=1,
        plan=plan,
    )
    history_probe: dict[str, Any]
    try:
        response, raw_body, metadata, started_at, completed_at = post_json(
            endpoint=endpoint,
            payload=history_payload,
            allowed_hosts=allowed_hosts,
            timeout_seconds=float(sampling["request_timeout_seconds"]),
            max_response_bytes=int(sampling["maximum_response_bytes"]),
            maximum_attempts=int(sampling["maximum_attempts_per_request"]),
            minimum_delay_seconds=float(sampling["minimum_delay_seconds"]),
            budget=budget,
        )
        notices = extract_notices(response)
        history_path = raw_dir / "retained-history-probe.json"
        history_path.write_bytes(raw_body)
        os.chmod(history_path, 0o600)
        first = notices[0] if notices else {}
        history_probe = {
            "status": "OBSERVED",
            "query": history_query,
            "scope": plan["source"]["scope"],
            "earliest_observed_publication_number": publication_number(first),
            "earliest_observed_publication_date": first.get("publication-date"),
            "total_notice_count": extract_total(response),
            "retrieved_at": completed_at.isoformat().replace("+00:00", "Z"),
            "limitation": (
                "Bounded Search API observation under the frozen scope; not proof "
                "of exhaustive archive history."
            ),
        }
        network_ledger.append(
            {
                "purpose": "BOUNDED_HISTORY_PROBE",
                "query": history_query,
                "fields": ["publication-number", "publication-date"],
                "retrieval_started_at": started_at.isoformat().replace(
                    "+00:00", "Z"
                ),
                "retrieval_completed_at": completed_at.isoformat().replace(
                    "+00:00", "Z"
                ),
                **metadata,
            }
        )
    except O01QualityCampaignError as exc:
        history_probe = {
            "status": "UNAVAILABLE",
            "query": history_query,
            "scope": plan["source"]["scope"],
            "error_class": type(exc).__name__,
            "limitation": (
                "History probe failed closed; no historical coverage claim is made."
            ),
        }

    selected_with_pages: list[tuple[dict[str, Any], str, PageObservation]] = []
    for country, record in selected:
        notice_id = publication_number(record)
        if not notice_id:
            continue
        observation = record_page.get((country, notice_id))
        if observation is None:
            continue
        selected_with_pages.append((record, country, observation))

    normalized_records, acquisition_by_notice, notification_ledger = (
        index_and_enqueue(selected_with_pages)
    )
    selected_source_records = [
        record for record, _country, _page in selected_with_pages
    ]
    all_candidate_records = [
        record
        for country in sorted(candidates_by_country)
        for record in candidates_by_country[country]
    ]

    quality = quality_report(
        selected_source_records=selected_source_records,
        normalized_records=normalized_records,
        all_candidate_records=all_candidate_records,
        contact_classification=contact_report,
    )
    coverage = coverage_report(
        normalized_records=normalized_records,
        page_observations=page_observations,
        available_by_country=available_by_country,
        plan=plan,
        history_probe=history_probe,
    )
    lag = lag_report(
        normalized_records,
        acquisition_by_notice=acquisition_by_notice,
    )

    sampling_manifest = {
        "schema_version": "axignal.o01-frozen-sampling-manifest/v0.1",
        "plan_sha256": plan_digest,
        "frozen_before_execution": bool(plan["frozen_before_execution"]),
        "measurement_window": plan["measurement_window"],
        "sampling_method": sampling["sampling_method"],
        "query_contract": sampling["query_contract"],
        "languages": sampling["languages"],
        "countries": sampling["countries"],
        "notice_types": sampling["notice_types"],
        "sample_size_target": sampling["sample_size"],
        "sample_size_observed": len(normalized_records),
        "pagination_rules": sampling["pagination_rules"],
        "exclusion_rules": sampling["exclusion_rules"],
        "deterministic_seed": sampling["deterministic_seed"],
        "available_by_country": available_by_country,
        "selected_publication_numbers": [
            item.publication_number for item in normalized_records
        ],
    }

    write_json(output_dir / "sampling-manifest.v0.1.json", sampling_manifest)
    write_json(output_dir / "coverage-report.v0.1.json", coverage)
    write_json(output_dir / "quality-report.v0.1.json", quality)
    write_json(output_dir / "lag-report.v0.1.json", lag)
    write_json(
        output_dir / "network-ledger.v0.1.json",
        {
            "network_requests_used": budget.used,
            "network_requests_maximum": budget.maximum,
            "entries": network_ledger,
        },
    )
    with (output_dir / "sanitised-sample-inventory.v0.1.jsonl").open(
        "w", encoding="utf-8"
    ) as handle:
        for record in normalized_records:
            handle.write(
                json.dumps(asdict(record), ensure_ascii=False, sort_keys=True) + "\n"
            )
    with (output_dir / "notification-ledger.v0.1.jsonl").open(
        "w", encoding="utf-8"
    ) as handle:
        for item in notification_ledger:
            handle.write(json.dumps(item, sort_keys=True) + "\n")

    preliminary = {
        "status": "MEASURED_PENDING_RAW_SEAL",
        "plan_sha256": plan_digest,
        "sample_frozen": sampling_manifest["frozen_before_execution"],
        "sample_count": len(normalized_records),
        "quality_report_complete": True,
        "lag_report_complete": True,
        "coverage_limitations_disclosed": bool(coverage["areas_not_covered"]),
        "raw_responses_retained_securely": False,
        "fabricated_evidence": 0,
        "synthetic_evidence": 0,
        "source_state": "CANDIDATE",
        "public_claim_contribution": False,
        "network_requests_used": budget.used,
    }
    write_json(output_dir / "preliminary-result.v0.1.json", preliminary)
    return preliminary
