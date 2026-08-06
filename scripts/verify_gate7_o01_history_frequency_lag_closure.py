from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CLOSURE = ROOT / (
    "data/acceptance/campaigns/"
    "AX-LIB-O01-history-frequency-lag-closure.v0.1.json"
)
CAMPAIGN_DIR = ROOT / "data/acceptance/campaigns"


class ClosureError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ClosureError(message)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"Expected JSON object: {path}")
    return value


def parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def verify_no_active_requests() -> list[str]:
    patterns = (
        "AX-LIB-O01-history-frequency-lag-execution-request*.json",
        "AX-LIB-O01-history-frequency-lag-verification-repair-request*.json",
    )
    active = sorted(
        str(path.relative_to(ROOT))
        for pattern in patterns
        for path in CAMPAIGN_DIR.glob(pattern)
        if path.is_file()
    )
    require(not active, f"Active one-shot request files remain: {active}")
    return active


def verify_closure(closure: dict[str, Any]) -> dict[str, Any]:
    require(
        closure["schema_version"]
        == "axignal.o01-history-frequency-lag-closure/v0.1",
        "Unexpected closure schema",
    )
    require(closure["task_id"] == "AX-GE2E-G7-O01-E", "Task drift")
    require(closure["library_id"] == "AX-LIB-O01", "Library drift")
    require(closure["source_id"] == "src_ted_search_api_v3", "Source drift")
    require(closure["status"] == "PASS", "Closure status is not PASS")
    require(
        closure["output"] == "O01_HISTORY_FREQUENCY_LAG_CLOSED",
        "Closure output drift",
    )
    require(closure["phase_closed"] is True, "O01-E is not closed")
    require(
        datetime.now(UTC) < parse_iso(closure["evidence_expires_at"]),
        "O01-E evidence is expired",
    )
    require(
        closure["revalidation_required_at_or_before"]
        == closure["evidence_expires_at"],
        "Revalidation boundary drift",
    )

    admission = closure["source_admission"]
    require(admission["artifact_id"] == 8838855002, "Admission artifact drift")
    require(
        admission["artifact_digest"]
        == "sha256:870261e24767ab170b191ee4a5e8fca27b9c406aec7113237cc41220eb80f74a",
        "Admission digest drift",
    )
    require(admission["source_state"] == "PRODUCT_ADMITTED", "Source not admitted")

    measurement = closure["measurement"]
    require(measurement["workflow_run_id"] == 30771690223, "Measurement run drift")
    require(measurement["job_id"] == 91559905777, "Measurement job drift")
    require(
        measurement["request_head_sha"]
        == "134fae19b78693164a797f8938ee2451656a70e4",
        "Measurement head drift",
    )
    require(measurement["artifact_id"] == 8840746749, "Measurement artifact drift")
    require(
        measurement["artifact_digest"]
        == "sha256:9d94a78484928a79a2a23e0d78dab52a74f68526708a6807234f3a4477ed75c5",
        "Measurement digest drift",
    )
    require(measurement["measurement_step"] == "SUCCESS", "Measurement step failed")
    require(measurement["status"] == "PASS", "Measurement status failed")
    require(
        measurement["output"] == "O01_HISTORY_FREQUENCY_LAG_PASS",
        "Measurement output drift",
    )
    require(measurement["network_requests_used"] == 52, "Measurement request drift")
    require(measurement["network_requests_maximum"] == 60, "Measurement budget drift")
    require(
        measurement["network_requests_used"]
        <= measurement["network_requests_maximum"],
        "Measurement exceeded request budget",
    )
    require(measurement["fabricated_evidence"] == 0, "Fabricated evidence present")
    require(measurement["synthetic_evidence"] == 0, "Synthetic evidence present")

    repair = closure["verification_repair"]
    require(repair["workflow_run_id"] == 30772939221, "Repair run drift")
    require(repair["job_id"] == 91563202076, "Repair job drift")
    require(
        repair["request_head_sha"]
        == "ed84e5ecaad9b89b3f60d8ae1f1a304127582839",
        "Repair head drift",
    )
    require(repair["artifact_id"] == 8841114156, "Repair artifact drift")
    require(
        repair["artifact_digest"]
        == "sha256:8167cbbef67798e4d92a9cdf273b8f6f0a2be3116dc32a420756353b63053128",
        "Repair digest drift",
    )
    require(repair["status"] == "PASS", "Repair status failed")
    require(
        repair["output"]
        == "O01_HISTORY_FREQUENCY_LAG_RETAINED_EVIDENCE_PASS",
        "Repair output drift",
    )
    require(repair["source_member_count"] == 15, "Source member count drift")
    require(repair["source_members_exact"] is True, "Source members are not exact")
    require(repair["repair_ted_network_requests"] == 0, "Repair replayed TED")
    require(repair["source_files_mutated"] is False, "Repair mutated source files")
    require(
        repair["published_lag_key"] == "direct_first-seen_timestamp_claimed",
        "Published lag key drift",
    )
    require(
        repair["internal_verifier_alias"]
        == "direct_first_seen_timestamp_claimed",
        "Verifier alias drift",
    )

    calendars = closure["calendar_evidence"]
    require(set(calendars) == {"2025", "2026"}, "Calendar year set drift")
    expected_calendars = {
        "2025": (252, "2025-01-02", "2025-12-31"),
        "2026": (254, "2026-01-02", "2026-12-31"),
    }
    for year, (count, first_release, last_release) in expected_calendars.items():
        calendar = calendars[year]
        require(calendar["release_count"] == count, f"Calendar count drift: {year}")
        require(calendar["first_issue"] == 1, f"Calendar first issue drift: {year}")
        require(calendar["last_issue"] == count, f"Calendar last issue drift: {year}")
        require(calendar["first_release"] == first_release, f"First release drift: {year}")
        require(calendar["last_release"] == last_release, f"Last release drift: {year}")
        require(
            calendar["issue_sequence_contiguous_from_one"] is True,
            f"Calendar issue sequence is not contiguous: {year}",
        )

    history = closure["historical_depth"]
    require(history["status"] == "PASS", "Historical depth failed")
    require(history["declared_public_years"] == 10, "Declared depth drift")
    require(history["declared_boundary_date"] == "2016-08-02", "Boundary drift")
    require(history["earliest_available_date"] == "2016-08-02", "Earliest date drift")
    require(history["day_before_earliest_total"] == 0, "Pre-boundary data present")
    require(history["boundary_slack_days"] == 0, "Boundary slack drift")
    require(history["latest_available_date"] == "2026-07-31", "Latest date drift")
    require(history["public_depth_days"] == 3651, "Public depth days drift")
    require(history["full_internal_archive_claimed"] is False, "Archive claimed")
    require(
        history["exhaustive_notice_ingestion_performed"] is False,
        "Exhaustive ingestion claimed",
    )

    frequency = closure["update_frequency"]
    require(frequency["status"] == "PASS", "Frequency evidence failed")
    require(frequency["reference_year"] == 2025, "Reference year drift")
    require(frequency["reference_year_editions"] == 252, "Edition count drift")
    require(
        frequency["reference_year_editions"]
        >= frequency["reference_year_editions_minimum"],
        "Edition threshold failed",
    )
    require(frequency["reference_year_weekend_editions"] == 0, "Weekend drift")
    require(frequency["recent_release_sample_count"] == 20, "Search sample drift")
    require(frequency["search_presence_ratio"] == 1.0, "Search presence drift")
    require(frequency["daily_package_sample_count"] == 10, "Package sample drift")
    require(frequency["package_presence_ratio"] == 1.0, "Package presence drift")

    lag = closure["publication_lag"]
    require(lag["status"] == "PASS", "Publication lag failed")
    require(
        lag["metric_semantics"]
        == "CONSERVATIVE_UPPER_BOUND_NOT_EXACT_FIRST_SEEN",
        "Lag semantics drift",
    )
    require(
        lag["publication_to_axignal_p95_seconds"]
        == 32400.367884099996,
        "Lag p95 drift",
    )
    require(
        lag["publication_to_axignal_p95_seconds"]
        <= lag["publication_to_axignal_p95_threshold_seconds"],
        "Lag threshold failed",
    )
    require(lag["exact_first_seen_timestamp_claimed"] is False, "Exact lag claimed")

    privacy = closure["privacy_and_retention"]
    require(all(value is False for value in privacy.values()), "Retention boundary failed")

    decision = closure["decision"]
    require(decision["o01_metrics_closed"] is True, "Metrics not closed")
    require(decision["o01_canonical_state"] == "ACCEPTED", "O01 state drift")
    require(decision["o01_claim_decision"] == "DENIED", "Claim decision drift")
    require(decision["source_state"] == "PRODUCT_ADMITTED", "Source state drift")
    require(
        decision["source_contributes_to_public_claim"] is False,
        "Source contributes to public claim",
    )
    require(decision["gate7_decision"] == "IN_PROGRESS", "Gate 7 decision drift")
    require(decision["public_launch"] == "NO_GO", "Launch enabled")

    integrity = closure["integrity"]
    require(integrity["thresholds_relaxed"] is False, "Thresholds relaxed")
    require(integrity["measurement_mutated"] is False, "Measurement mutated")
    require(integrity["source_files_mutated"] is False, "Source files mutated")
    require(integrity["network_replay_for_repair"] is False, "Repair replayed network")
    require(
        integrity["failed_attempts_applied_state_transition"] is False,
        "Failed attempts changed state",
    )
    require(integrity["one_shot_requests_retired"] is True, "Requests not retired")

    boundary = closure["permanent_boundaries"]
    for key, value in boundary.items():
        if key == "public_launch":
            require(value == "NO_GO", "Permanent boundary enabled launch")
        else:
            require(value is False, f"Permanent boundary enabled: {key}")

    verify_no_active_requests()
    return {
        "schema_version": "axignal.o01-history-frequency-lag-closure-result/v0.1",
        "status": "PASS",
        "output": "O01_HISTORY_FREQUENCY_LAG_CLOSURE_PASS",
        "task_id": closure["task_id"],
        "library_id": closure["library_id"],
        "source_id": closure["source_id"],
        "phase_closed": True,
        "measurement_artifact_id": measurement["artifact_id"],
        "measurement_artifact_digest": measurement["artifact_digest"],
        "repair_artifact_id": repair["artifact_id"],
        "repair_artifact_digest": repair["artifact_digest"],
        "historical_boundary": history["earliest_available_date"],
        "search_presence_ratio": frequency["search_presence_ratio"],
        "package_presence_ratio": frequency["package_presence_ratio"],
        "publication_to_axignal_p95_seconds": lag[
            "publication_to_axignal_p95_seconds"
        ],
        "o01_canonical_state": decision["o01_canonical_state"],
        "o01_claim_decision": decision["o01_claim_decision"],
        "source_state": decision["source_state"],
        "claim_contribution": False,
        "gate7_decision": "IN_PROGRESS",
        "public_launch": "NO_GO",
        "evidence_expires_at": closure["evidence_expires_at"],
        "active_request_files": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--closure", type=Path, default=DEFAULT_CLOSURE)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        closure = load_json(args.closure.resolve())
        result = verify_closure(closure)
    except (
        KeyError,
        OSError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        ClosureError,
    ) as exc:
        result = {
            "schema_version": "axignal.o01-history-frequency-lag-closure-result/v0.1",
            "status": "FAIL",
            "output": "O01_HISTORY_FREQUENCY_LAG_CLOSURE_FAIL",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "claim_contribution": False,
            "gate7_decision": "IN_PROGRESS",
            "public_launch": "NO_GO",
        }
        encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(encoded, encoding="utf-8")
        print(encoded, end="")
        return 1

    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
