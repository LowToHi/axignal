from __future__ import annotations

import argparse
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "studies/f1/controlled-study-v1/manifest.json"
PARTICIPANT_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
BOOLEAN_METRICS = (
    "task_completed",
    "critical_error",
    "authority_layer_correct",
    "evidence_traceability",
    "unknowns_identified",
)


def wilson(
    successes: int,
    total: int,
    z: float = 1.959963984540054,
) -> list[float]:
    if total == 0:
        return [0.0, 0.0]
    p = successes / total
    denominator = 1 + (z * z / total)
    centre = (p + z * z / (2 * total)) / denominator
    variance = (p * (1 - p) + z * z / (4 * total)) / total
    radius = z * math.sqrt(variance) / denominator
    return [max(0.0, centre - radius), min(1.0, centre + radius)]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def eligible_sessions(
    dataset: dict[str, Any],
    manifest: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    allowed_profiles = set(manifest["cohort"]["qualified_profiles"])
    tasks = set(manifest["tasks"])
    retained: dict[tuple[str, str], dict[str, Any]] = {}
    exclusions: list[dict[str, Any]] = []
    sessions = sorted(
        dataset.get("sessions", []),
        key=lambda item: item.get("started_at", ""),
    )

    for session in sessions:
        participant_hash = session.get("participant_id_hash", "")
        require(
            PARTICIPANT_RE.fullmatch(participant_hash) is not None,
            "direct or invalid participant identifier",
        )
        require(session.get("condition") in {"AXIGNAL", "CONTROL"}, "invalid condition")
        require(session.get("task_id") in tasks, "task outside frozen set")
        require(
            session.get("protocol_version") == manifest["protocol_version"],
            "protocol version mismatch",
        )
        require(session.get("study_id") == manifest["study_id"], "study id mismatch")
        if session.get("participant_profile") not in allowed_profiles:
            exclusions.append(
                {
                    "session_id": session.get("session_id"),
                    "code": "UNQUALIFIED_PROFILE",
                }
            )
            continue
        if session.get("technical_pre_response_failure") is True:
            exclusions.append(
                {
                    "session_id": session.get("session_id"),
                    "code": "TECHNICAL_PRE_RESPONSE_FAILURE",
                }
            )
            continue
        key = (participant_hash, session["task_id"])
        if key in retained:
            exclusions.append(
                {
                    "session_id": session.get("session_id"),
                    "code": "DUPLICATE_PARTICIPANT_TASK",
                }
            )
            continue
        retained[key] = session
    return list(retained.values()), exclusions


def condition_metrics(sessions: list[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {"sessions": len(sessions)}
    result["distinct_participants"] = len(
        {item["participant_id_hash"] for item in sessions}
    )
    confidences: list[float] = []
    for metric in BOOLEAN_METRICS:
        successes = 0
        for item in sessions:
            outcome = item.get("outcome") or {}
            successes += int(bool(outcome.get(metric, False)))
            confidence = outcome.get("confidence")
            if metric == "task_completed" and isinstance(confidence, (int, float)):
                confidences.append(float(confidence))
        rate = successes / len(sessions) if sessions else 0.0
        result[metric] = {
            "successes": successes,
            "rate": rate,
            "wilson_95": wilson(successes, len(sessions)),
        }
    result["mean_confidence"] = (
        sum(confidences) / len(confidences) if confidences else None
    )
    return result


def evaluate(dataset: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    require(
        dataset.get("study_id") == manifest["study_id"],
        "dataset study id mismatch",
    )
    require(
        dataset.get("protocol_version") == manifest["protocol_version"],
        "dataset protocol mismatch",
    )
    incidents = dataset.get("incidents")
    require(isinstance(incidents, dict), "explicit incident counts are required")
    require(
        set(incidents) == set(manifest["guardrails"]),
        "incident keys do not match frozen guardrails",
    )
    require(
        all(isinstance(value, int) and value >= 0 for value in incidents.values()),
        "incident counts must be non-negative integers",
    )

    sessions, exclusions = eligible_sessions(dataset, manifest)
    by_condition: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for session in sessions:
        by_condition[session["condition"]].append(session)
    metrics = {
        condition: condition_metrics(by_condition[condition])
        for condition in ("AXIGNAL", "CONTROL")
    }

    cohort = manifest["cohort"]
    distinct_participants = len(
        {item["participant_id_hash"] for item in sessions}
    )
    condition_minimum_met = all(
        metrics[condition]["sessions"] >= cohort["minimum_sessions_per_condition"]
        for condition in metrics
    )
    sample_ready = (
        len(sessions) >= cohort["minimum_valid_sessions"]
        and distinct_participants >= cohort["minimum_distinct_participants"]
        and condition_minimum_met
    )

    guardrails_pass = all(
        incidents[key] <= maximum
        for key, maximum in manifest["guardrails"].items()
    )
    ax = metrics["AXIGNAL"]
    control = metrics["CONTROL"]
    absolute = manifest["thresholds"]["axignal_absolute"]
    absolute_checks = {
        "task_completion_rate": (
            ax["task_completed"]["rate"] >= absolute["task_completion_rate_min"]
        ),
        "critical_error_rate": (
            ax["critical_error"]["rate"] <= absolute["critical_error_rate_max"]
        ),
        "authority_layer_comprehension": (
            ax["authority_layer_correct"]["rate"]
            >= absolute["authority_layer_comprehension_min"]
        ),
        "evidence_traceability_rate": (
            ax["evidence_traceability"]["rate"]
            >= absolute["evidence_traceability_rate_min"]
        ),
        "unknowns_identification_rate": (
            ax["unknowns_identified"]["rate"]
            >= absolute["unknowns_identification_rate_min"]
        ),
    }

    differences = {
        "task_completion_rate": (
            ax["task_completed"]["rate"] - control["task_completed"]["rate"]
        ),
        "critical_error_rate": (
            ax["critical_error"]["rate"] - control["critical_error"]["rate"]
        ),
        "authority_layer_comprehension": (
            ax["authority_layer_correct"]["rate"]
            - control["authority_layer_correct"]["rate"]
        ),
        "evidence_traceability_rate": (
            ax["evidence_traceability"]["rate"]
            - control["evidence_traceability"]["rate"]
        ),
        "unknowns_identification_rate": (
            ax["unknowns_identified"]["rate"]
            - control["unknowns_identified"]["rate"]
        ),
    }
    margins = manifest["thresholds"]["comparative_non_inferiority"]
    comparative_checks = {
        "task_completion_rate": (
            differences["task_completion_rate"]
            >= margins["task_completion_rate_difference_min"]
        ),
        "critical_error_rate": (
            differences["critical_error_rate"]
            <= margins["critical_error_rate_difference_max"]
        ),
        "authority_layer_comprehension": (
            differences["authority_layer_comprehension"]
            >= margins["authority_layer_comprehension_difference_min"]
        ),
        "evidence_traceability_rate": (
            differences["evidence_traceability_rate"]
            >= margins["evidence_traceability_rate_difference_min"]
        ),
    }

    if not sample_ready:
        recommendation = "NOT_READY"
    elif not guardrails_pass or not all(absolute_checks.values()):
        recommendation = "FAIL_CANDIDATE"
    elif all(comparative_checks.values()):
        recommendation = "PASS_CANDIDATE"
    else:
        recommendation = "INCONCLUSIVE"

    return {
        "study_id": manifest["study_id"],
        "protocol_version": manifest["protocol_version"],
        "population": manifest["analysis"]["primary_population"],
        "eligible_sessions": len(sessions),
        "distinct_participants": distinct_participants,
        "exclusions": exclusions,
        "incidents": incidents,
        "condition_metrics": metrics,
        "differences_axignal_minus_control": differences,
        "sample_ready": sample_ready,
        "guardrails_pass": guardrails_pass,
        "absolute_checks": absolute_checks,
        "comparative_checks": comparative_checks,
        "recommendation": recommendation,
        "human_gate_required": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--expect",
        choices=("NOT_READY", "FAIL_CANDIDATE", "PASS_CANDIDATE", "INCONCLUSIVE"),
    )
    args = parser.parse_args()

    result = evaluate(load_json(args.input), load_json(MANIFEST_PATH))
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    if args.expect and result["recommendation"] != args.expect:
        raise SystemExit(f"expected {args.expect}, got {result['recommendation']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
