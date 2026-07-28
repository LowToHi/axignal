from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUDY_DIR = ROOT / "studies/f1/controlled-study-v1"
MANIFEST_PATH = STUDY_DIR / "manifest.json"
LOCK_PATH = STUDY_DIR / "manifest.sha256"
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data, usedforsecurity=False).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    manifest_bytes = MANIFEST_PATH.read_bytes()
    manifest = json.loads(manifest_bytes)
    lock_parts = LOCK_PATH.read_text(encoding="utf-8").strip().split()
    require(
        len(lock_parts) == 2 and lock_parts[1] == "manifest.json",
        "invalid manifest lock",
    )
    require(
        SHA256_RE.fullmatch(lock_parts[0]) is not None,
        "invalid manifest SHA-256",
    )
    require(
        hashlib.sha256(manifest_bytes).hexdigest() == lock_parts[0],
        "manifest lock mismatch",
    )

    require(
        manifest["study_id"] == "AXIGNAL-F1-CONTROLLED-001",
        "unexpected study id",
    )
    require(manifest["protocol_version"] == "1.0.0", "unexpected protocol version")
    require(manifest["status"] == "FROZEN_PRE_RECRUITMENT", "protocol is not frozen")
    require(
        manifest["baseline"]["commit_sha"]
        == "03471bd3764e8696b86380fd8a83f6356ac92f7a",
        "baseline moved",
    )
    require(
        manifest["experiment"]["conditions"] == ["AXIGNAL", "CONTROL"],
        "condition drift",
    )
    assignment = manifest["experiment"]["assignment"]
    require(assignment["rerandomisation"] is False, "rerandomisation enabled")
    require(
        manifest["analysis"]["primary_population"] == "INTENTION_TO_TREAT",
        "analysis population drift",
    )
    require(
        manifest["analysis"]["no_optional_stopping_on_performance"] is True,
        "optional stopping enabled",
    )
    require(
        manifest["stopping_rule"]["performance_based_early_stop"] is False,
        "performance stop enabled",
    )
    require(
        manifest["decision_rule"]["human_gate_required"] is True,
        "human decision gate removed",
    )

    tasks = manifest["tasks"]
    require(
        len(tasks) == 6 and len(set(tasks)) == 6,
        "task set must contain six unique tasks",
    )

    baseline = manifest["baseline"]
    source_keys = (
        "task_and_scoring_source",
        "answer_key_boundary",
        "crypto_boundary",
    )
    for key in source_keys:
        source = baseline[key]
        require(
            SHA1_RE.fullmatch(source["git_blob_sha1"]) is not None,
            f"invalid lock for {key}",
        )
        path = ROOT / source["path"]
        require(path.is_file(), f"missing locked source: {source['path']}")
        require(
            git_blob_sha1(path.read_bytes()) == source["git_blob_sha1"],
            f"source drift: {source['path']}",
        )

    task_path = ROOT / baseline["task_and_scoring_source"]["path"]
    task_sql = task_path.read_text(encoding="utf-8")
    for task_id in tasks:
        require(
            task_sql.count(f"'{task_id}'") == 1,
            f"task definition drift: {task_id}",
        )
    require(
        task_sql.count("'f1-qualified-user@0.1.0'") == 6,
        "experiment version drift",
    )
    assignment_locked = (
        "get_byte(digest(" in task_sql
        and "% 2 = 0 THEN 'AXIGNAL'" in task_sql
    )
    require(assignment_locked, "assignment algorithm drift")

    cohort = manifest["cohort"]
    require(cohort["minimum_distinct_participants"] >= 6, "participant minimum weakened")
    require(cohort["minimum_valid_sessions"] >= 12, "session minimum weakened")
    require(
        cohort["maximum_valid_sessions"] >= cohort["minimum_valid_sessions"],
        "invalid session cap",
    )
    require(cohort["minimum_sessions_per_condition"] >= 4, "condition minimum weakened")

    guardrails = manifest["guardrails"]
    require(
        all(value == 0 for value in guardrails.values()),
        "guardrail tolerance must remain zero",
    )

    print(
        json.dumps(
            {
                "study_id": manifest["study_id"],
                "protocol_version": manifest["protocol_version"],
                "manifest_sha256": lock_parts[0],
                "baseline_commit": baseline["commit_sha"],
                "locked_sources": len(source_keys),
                "frozen_tasks": len(tasks),
                "optional_stopping": False,
                "human_gate_required": True,
                "protocol_ready": True,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
