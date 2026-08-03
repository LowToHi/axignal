from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

QUERY_RE = re.compile(
    r"^publication-date >= (?P<lower>\d{8}) "
    r"AND publication-date <= (?P<upper>\d{8})$"
)
FORBIDDEN_FILE_SUFFIXES = {
    ".gz",
    ".xls",
    ".xlsx",
    ".xml",
    ".zip",
}
SECRET_PATTERN = re.compile(
    rb"sk_(?:live|test)_|rk_(?:live|test)_|whsec_|"
    rb"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY|"
    rb'"(?:buyer-email|buyer-tel|organisation-tel-buyer|buyer-contact-point)"\s*:'
)


class VerificationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"Expected JSON object: {path}")
    return value


def sha256_prefixed(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def verify_query(query: str) -> None:
    require("SORT" not in query.upper(), f"Forbidden SORT clause: {query}")
    match = QUERY_RE.fullmatch(query)
    require(match is not None, f"Query is not a closed canonical interval: {query}")
    lower = datetime.strptime(match.group("lower"), "%Y%m%d").date()
    upper = datetime.strptime(match.group("upper"), "%Y%m%d").date()
    require(lower <= upper, f"Inverted query interval: {query}")


def verify_plan(plan: dict[str, Any]) -> None:
    require(
        plan["schema_version"]
        == "axignal.o01-history-frequency-lag-verification-repair-plan/v0.1",
        "Unexpected verification-repair plan schema",
    )
    require(plan["task_id"] == "AX-GE2E-G7-O01-E-VERIFY-REPAIR", "Task drift")
    require(plan["library_id"] == "AX-LIB-O01", "Library drift")
    source = plan["source_campaign"]
    require(source["workflow_run_id"] == 30771690223, "Source run drift")
    require(source["measurement_job_id"] == 91559905777, "Source job drift")
    require(
        source["request_head_sha"]
        == "134fae19b78693164a797f8938ee2451656a70e4",
        "Source head drift",
    )
    require(source["artifact_id"] == 8840746749, "Source artifact drift")
    require(
        source["artifact_digest"]
        == "sha256:9d94a78484928a79a2a23e0d78dab52a74f68526708a6807234f3a4477ed75c5",
        "Source artifact digest drift",
    )
    require(source["measurement_step"] == "SUCCESS", "Measurement did not pass")
    require(source["verification_step"] == "FAIL", "Repair source is not failed verification")
    require(
        source["verification_error"] == "Calendar edition count drift",
        "Unexpected source verification failure",
    )
    require(source["state_transition_applied"] is False, "Failed verifier changed state")

    root = plan["root_cause"]
    require(root["classification"] == "VERIFIER_OVERCONSTRAINT", "Root cause drift")
    require(root["thresholds_changed"] is False, "Thresholds changed")
    require(root["measurement_changed"] is False, "Measurement changed")
    require(root["network_replay_authorised"] is False, "TED replay authorised")

    repair = plan["repair_execution"]
    require(repair["ted_network_requests_authorised"] == 0, "TED network authorised")
    require(repair["source_artifact_downloads_authorised"] == 1, "Artifact download drift")
    require(repair["verification_only"] is True, "Repair is not verification-only")

    boundary = plan["non_authorisations"]
    for key in (
        "measurement_mutation",
        "threshold_relaxation",
        "calendar_count_normalisation",
        "source_scope_change",
        "public_claim_contribution",
        "gate7_closed",
    ):
        require(boundary[key] is False, f"Forbidden repair authority enabled: {key}")
    require(boundary["public_launch"] == "NO_GO", "Repair enabled launch")


def verify_artifact_metadata(
    plan: dict[str, Any],
    metadata: dict[str, Any],
) -> None:
    source = plan["source_campaign"]
    require(metadata["id"] == source["artifact_id"], "Artifact metadata id drift")
    require(metadata["name"] == source["artifact_name"], "Artifact metadata name drift")
    require(metadata["digest"] == source["artifact_digest"], "Artifact metadata digest drift")
    require(metadata["size_in_bytes"] == source["artifact_size_bytes"], "Artifact size drift")
    require(metadata["expired"] is False, "Source artifact expired")
    require(
        metadata["workflow_run"]["id"] == source["workflow_run_id"],
        "Artifact run drift",
    )
    require(
        metadata["workflow_run"]["head_sha"] == source["request_head_sha"],
        "Artifact head drift",
    )


def verify_member_identity(plan: dict[str, Any], evidence_dir: Path) -> None:
    expected = plan["required_members_sha256"]
    actual_files = {
        path.name: path
        for path in evidence_dir.iterdir()
        if path.is_file()
    }
    require(set(actual_files) == set(expected), "Retained evidence member set drift")
    for name, expected_digest in expected.items():
        path = actual_files[name]
        require(path.suffix.casefold() not in FORBIDDEN_FILE_SUFFIXES, f"Forbidden file: {name}")
        require(sha256_prefixed(path) == expected_digest, f"Member digest drift: {name}")
        require(SECRET_PATTERN.search(path.read_bytes()) is None, f"Sensitive value in {name}")


def verify_provenance(plan: dict[str, Any], evidence_dir: Path) -> None:
    lines = {}
    for raw_line in (evidence_dir / "preflight-provenance.txt").read_text(
        encoding="utf-8"
    ).splitlines():
        key, value = raw_line.split("=", 1)
        lines[key] = value
    source = plan["source_campaign"]
    require(lines["head_sha"] == source["request_head_sha"], "Provenance head drift")
    require(lines["tree_sha"] == source["request_tree_sha"], "Provenance tree drift")
    require(lines["parent_sha"] == source["controller_parent_sha"], "Parent SHA drift")
    require(
        lines["parent_tree_sha"] == source["controller_parent_tree_sha"],
        "Parent tree drift",
    )
    require(lines["stage"] == "PRE_NETWORK_PREFLIGHT_PASS", "Preflight did not pass")
    require(lines["network_requests_emitted"] == "0", "Network occurred before preflight")


def verify_retained_authorities(evidence_dir: Path) -> None:
    expected = {
        "admission-artifact-metadata.json": (
            8838855002,
            "sha256:870261e24767ab170b191ee4a5e8fca27b9c406aec7113237cc41220eb80f74a",
        ),
        "calendar-probe-artifact-metadata.json": (
            8839697337,
            "sha256:5b77b1a6975443ad9f9cb2af4668821aa508a2b2d72749ff4aa546aae25016f8",
        ),
        "history-diagnostic-artifact-metadata.json": (
            8839903336,
            "sha256:f6a7524549b8f48fdc4858a06641b5fbd94de0a61f1e1f812a8c3021b3897a1a",
        ),
        "retry-trigger-artifact-metadata.json": (
            8840624551,
            "sha256:b585a8c11bc5d23075a86696dca7153a376aa49c4e22e2b7677c834d9b9500ce",
        ),
    }
    for name, (artifact_id, artifact_digest) in expected.items():
        metadata = load_json(evidence_dir / name)
        require(metadata["id"] == artifact_id, f"Authority id drift: {name}")
        require(metadata["digest"] == artifact_digest, f"Authority digest drift: {name}")
        require(metadata["expired"] is False, f"Authority expired: {name}")


def verify_calendars(
    plan: dict[str, Any],
    evidence_dir: Path,
) -> dict[int, dict[str, Any]]:
    document = load_json(evidence_dir / "release-calendar-observations.v0.1.json")
    require(document["status"] == "PASS", "Release-calendar observation failed")
    require(document["parser"] == "xlrd==2.0.2", "Calendar parser drift")
    require(document["parser_lock"] == "requirements/o01-xls.lock", "Parser lock drift")
    require(document["release_calendar_bodies_persisted"] is False, "XLS body retained")
    require(document["fabricated_evidence"] == 0, "Calendar evidence fabricated")
    calendars = {item["year"]: item for item in document["calendars"]}
    require(set(calendars) == {2025, 2026}, "Calendar year set drift")

    expected_years = plan["expected_measurement"]["calendar_years"]
    for year, calendar in calendars.items():
        expected = expected_years[str(year)]
        require(calendar["format"] == "XLS_OLE2_BIFF8", f"Format drift: {year}")
        require(calendar["magic_hex"] == "d0cf11e0a1b11ae1", f"OLE2 drift: {year}")
        require(calendar["body_persisted"] is False, f"Calendar body retained: {year}")
        require(calendar["release_count"] == expected["release_count"], f"Count drift: {year}")
        require(calendar["first_issue"] == expected["first_issue"] == 1, f"First issue drift: {year}")
        require(calendar["last_issue"] == expected["last_issue"], f"Last issue drift: {year}")
        require(
            calendar["last_issue"] == calendar["release_count"],
            f"Issue sequence is not contiguous from 1: {year}",
        )
        require(calendar["first_release"] == expected["first_release"], f"First date drift: {year}")
        require(calendar["last_release"] == expected["last_release"], f"Last date drift: {year}")
        require(calendar["metadata"]["http_status"] == 200, f"Calendar HTTP drift: {year}")
        require(calendar["metadata"]["response_bytes"] > 0, f"Empty calendar: {year}")
    return calendars


def verify_official_sources(plan: dict[str, Any], evidence_dir: Path) -> None:
    ledger = load_json(evidence_dir / "official-source-attempt-ledger.v0.1.json")
    observations = load_json(evidence_dir / "official-source-observations.v0.1.json")
    expected = plan["expected_measurement"]
    require(ledger["status"] == "PASS", "Official-source ledger failed")
    require(ledger["source_count"] == expected["official_source_count"], "Source count drift")
    require(ledger["attempt_count"] == expected["official_source_attempt_count"], "Attempt count drift")
    require(ledger["response_bodies_persisted"] is False, "Official bodies retained")
    require(len(ledger["sources"]) == 5, "Incomplete official-source ledger")
    for source in ledger["sources"]:
        require(source["status"] == "PASS", f"Official source failed: {source['url']}")
        require(source["response_body_persisted"] is False, "Official source body retained")
        require(len(source["attempts"]) == 1, f"Unexpected retry count: {source['url']}")
        attempt = source["attempts"][0]
        require(attempt["http_status"] == 200, f"Official source not 200: {source['url']}")
        require(attempt["accepted"] is True, f"Official source rejected: {source['url']}")
        require(attempt["response_body_persisted"] is False, "Attempt body retained")

    require(observations["status"] == "PASS", "Official observations failed")
    require(observations["response_bodies_persisted"] is False, "Observation bodies retained")
    require(len(observations["documents"]) == 5, "Official observation count drift")
    for document in observations["documents"]:
        require(document["status"] == "PASS", f"Document failed: {document['url']}")
        require(document["anchors_present"] == document["anchors_expected"], "Anchor drift")
        require(document["body_persisted"] is False, "Document body retained")
        require(document["metadata"]["http_status"] == 200, "Document HTTP drift")
        require(document["metadata"]["response_body_persisted"] is False, "Body retained")


def verify_measurements(plan: dict[str, Any], evidence_dir: Path) -> dict[str, Any]:
    final = load_json(evidence_dir / "final-result.v0.1.json")
    console = load_json(evidence_dir / "campaign-console.json")
    history = load_json(evidence_dir / "history-depth-report.v0.1.json")
    frequency = load_json(evidence_dir / "update-frequency-report.v0.1.json")
    lag = load_json(evidence_dir / "publication-lag-report.v0.1.json")
    expected = plan["expected_measurement"]

    require(console == final, "Campaign console and final result differ")
    require(final["schema_version"] == "axignal.o01-history-frequency-lag-result/v0.7", "Result schema drift")
    require(final["status"] == "PASS", "Measurement result failed")
    require(final["output"] == "O01_HISTORY_FREQUENCY_LAG_PASS", "Measurement output drift")
    require(final["observed_at"] == expected["observed_at"], "Observation timestamp drift")
    require(final["evidence_expires_at"] == expected["evidence_expires_at"], "Expiry drift")
    require(datetime.now(UTC) < parse_iso(final["evidence_expires_at"]), "Evidence expired")
    require(final["network_requests_used"] == expected["network_requests_used"], "Request count drift")
    require(final["network_requests_maximum"] == expected["network_requests_maximum"], "Budget drift")
    require(final["network_requests_used"] <= final["network_requests_maximum"], "Budget exceeded")
    require(final["fabricated_evidence"] == 0, "Fabricated evidence present")
    require(final["synthetic_evidence"] == 0, "Synthetic evidence present")
    require(final["official_source_response_bodies_persisted"] is False, "Official bodies retained")
    require(final["release_calendar_bodies_persisted"] is False, "Calendar bodies retained")
    require(all(final["checks"].values()), "A frozen measurement check failed")

    require(final["history"] == history, "History report/result mismatch")
    require(final["frequency"] == frequency, "Frequency report/result mismatch")
    require(final["lag"] == lag, "Lag report/result mismatch")

    expected_history = expected["history"]
    for key, value in expected_history.items():
        require(history[key] == value, f"History drift: {key}")
    require(history["status"] == "PASS", "History report failed")
    require(history["query_contract"] == "CANONICAL_CLOSED_INTERVAL_WITHOUT_SORT", "History query contract drift")
    require(history["full_internal_archive_claimed"] is False, "Internal archive claimed")
    require(history["exhaustive_notice_ingestion_performed"] is False, "Exhaustive ingest claimed")
    for observation in history["binary_search_observations"]:
        verify_query(observation["query"])
        require(observation["request"]["http_status"] == 200, "History request failed")

    expected_frequency = expected["frequency"]
    for key in (
        "reference_year",
        "reference_year_editions",
        "reference_year_weekend_editions",
        "search_presence_ratio",
        "package_presence_ratio",
    ):
        require(frequency[key] == expected_frequency[key], f"Frequency drift: {key}")
    require(
        frequency["reference_year_editions"]
        >= expected_frequency["reference_year_editions_minimum"],
        "Reference-year edition threshold failed",
    )
    require(len(frequency["recent_release_sample"]) == 20, "Search sample count drift")
    require(len(frequency["daily_package_sample"]) == 10, "Package sample count drift")
    for observation in frequency["recent_release_sample"]:
        verify_query(observation["query"])
        require(observation["notice_count"] > 0, "Scheduled edition missing")
        require(observation["request"]["http_status"] == 200, "Search sample failed")
    for package in frequency["daily_package_sample"]:
        require(package["available"] is True, "Daily package unavailable")
        require(package["metadata"]["http_status"] == 200, "Package probe failed")
        require(package["metadata"]["response_bytes"] == 0, "Package body retained")

    expected_lag = expected["lag"]
    require(
        lag["search_request_duration_seconds"]["p95"]
        == expected_lag["search_request_p95_seconds"],
        "Search request p95 drift",
    )
    require(
        lag["publication_to_axignal_upper_bound_seconds"]["p95"]
        == expected_lag["publication_to_axignal_p95_seconds"],
        "Publication lag p95 drift",
    )
    require(
        lag["publication_to_axignal_upper_bound_seconds"]["p95"]
        <= expected_lag["publication_to_axignal_p95_threshold_seconds"],
        "Publication lag threshold failed",
    )
    require(lag["direct_first_seen_timestamp_claimed"] is False, "Exact first-seen claimed")

    transition = plan["success_transition"]
    decision = final["decision"]
    require(decision["o01_metrics_closed"] is transition["o01_metrics_closed"], "Metrics closure drift")
    require(decision["recommended_canonical_state"] == transition["o01_canonical_state"], "State drift")
    require(decision["recommended_claim_decision"] == transition["o01_claim_decision"], "Claim decision drift")
    require(decision["claim_contribution"] is False, "Claim contribution enabled")
    require(decision["gate7_closed"] is False, "Gate 7 closed by O01-E")
    require(decision["public_launch"] == "NO_GO", "Launch enabled")
    return final


def verify(
    plan_path: Path,
    artifact_metadata_path: Path,
    evidence_dir: Path,
) -> dict[str, Any]:
    plan = load_json(plan_path)
    metadata = load_json(artifact_metadata_path)
    verify_plan(plan)
    verify_artifact_metadata(plan, metadata)
    verify_member_identity(plan, evidence_dir)
    verify_provenance(plan, evidence_dir)
    verify_retained_authorities(evidence_dir)
    calendars = verify_calendars(plan, evidence_dir)
    verify_official_sources(plan, evidence_dir)
    final = verify_measurements(plan, evidence_dir)

    return {
        "schema_version": "axignal.o01-history-frequency-lag-verification-repair-result/v0.1",
        "status": "PASS",
        "output": "O01_HISTORY_FREQUENCY_LAG_RETAINED_EVIDENCE_PASS",
        "source_workflow_run_id": plan["source_campaign"]["workflow_run_id"],
        "source_measurement_job_id": plan["source_campaign"]["measurement_job_id"],
        "source_request_head_sha": plan["source_campaign"]["request_head_sha"],
        "source_artifact_id": plan["source_campaign"]["artifact_id"],
        "source_artifact_digest": plan["source_campaign"]["artifact_digest"],
        "source_member_count": len(plan["required_members_sha256"]),
        "source_members_exact": True,
        "measurement_status": final["status"],
        "measurement_output": final["output"],
        "measurement_network_requests": final["network_requests_used"],
        "repair_ted_network_requests": 0,
        "calendar_counts": {
            str(year): calendar["release_count"]
            for year, calendar in sorted(calendars.items())
        },
        "history_boundary": final["history"]["earliest_available_date"],
        "history_day_before_total": final["history"]["day_before_earliest_total"],
        "search_presence_ratio": final["frequency"]["search_presence_ratio"],
        "package_presence_ratio": final["frequency"]["package_presence_ratio"],
        "publication_to_axignal_p95_seconds": final["lag"][
            "publication_to_axignal_upper_bound_seconds"
        ]["p95"],
        "o01_metrics_closed": True,
        "recommended_canonical_state": "ACCEPTED",
        "recommended_claim_decision": "DENIED",
        "claim_contribution": False,
        "gate7_closed": False,
        "public_launch": "NO_GO",
        "evidence_expires_at": final["evidence_expires_at"],
        "verified_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--artifact-metadata", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = verify(
            args.plan.resolve(),
            args.artifact_metadata.resolve(),
            args.evidence_dir.resolve(),
        )
    except (
        KeyError,
        OSError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        VerificationError,
    ) as exc:
        result = {
            "schema_version": "axignal.o01-history-frequency-lag-verification-repair-result/v0.1",
            "status": "FAIL",
            "output": "O01_HISTORY_FREQUENCY_LAG_RETAINED_EVIDENCE_FAIL",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "repair_ted_network_requests": 0,
            "claim_contribution": False,
            "gate7_closed": False,
            "public_launch": "NO_GO",
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(result, sort_keys=True))
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
