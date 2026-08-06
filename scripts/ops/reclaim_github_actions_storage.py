#!/usr/bin/env python3
"""Contract-aware GitHub Actions storage reclamation for AXIGNAL.

The script can run from a VPS or a temporary GitHub-hosted runner. It inventories
Actions artifacts, derives protected evidence from the canonical contract and
ledger, preserves active product lines and open pull-request heads, then removes
only obsolete workflow runs until the requested byte target is reached.
"""

from __future__ import annotations

import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

API_VERSION = "2022-11-28"
CONTRACT_PATH = "docs/contracts/AX-GE2E-FINISH-003.md"
LEDGER_PATH = "docs/roadmap/AXIGNAL_E2E_FINISH_LEDGER.json"
RETRYABLE = {429, 500, 502, 503, 504}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class GitHubAPI:
    def __init__(self, repository: str, token: str) -> None:
        self.repository = repository
        self.root = f"https://api.github.com/repos/{repository}"
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "axignal-actions-storage-reclaimer/1.0",
        }

    def request(
        self,
        path_or_url: str,
        *,
        method: str = "GET",
        expected: set[int] | None = None,
        attempts: int = 6,
    ) -> tuple[int, dict[str, str], bytes]:
        expected = expected or {200}
        url = path_or_url if path_or_url.startswith("https://") else f"{self.root}{path_or_url}"
        last_error: Exception | None = None
        for attempt in range(1, attempts + 1):
            request = urllib.request.Request(url, headers=self.headers, method=method)
            try:
                with urllib.request.urlopen(request, timeout=90) as response:
                    status = int(response.status)
                    body = response.read()
                    headers = dict(response.headers.items())
                    if status not in expected:
                        raise RuntimeError(f"unexpected status={status} method={method} url={url}")
                    return status, headers, body
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")
                if exc.code in expected:
                    return int(exc.code), dict(exc.headers.items()), body.encode("utf-8")
                last_error = RuntimeError(
                    f"GitHub API status={exc.code} method={method} url={url}: {body[:500]}"
                )
                if exc.code not in RETRYABLE or attempt == attempts:
                    raise last_error from exc
            except (urllib.error.URLError, TimeoutError) as exc:
                last_error = exc
                if attempt == attempts:
                    raise
            time.sleep(min(2 ** (attempt - 1), 20))
        raise RuntimeError(f"request failed: {last_error}")

    def json(self, path_or_url: str) -> tuple[Any, dict[str, str]]:
        _, headers, body = self.request(path_or_url)
        return json.loads(body.decode("utf-8")), headers

    def content(self, path: str, ref: str = "main") -> str:
        quoted = urllib.parse.quote(path, safe="/")
        payload, _ = self.json(f"/contents/{quoted}?ref={urllib.parse.quote(ref, safe='')}")
        if payload.get("encoding") != "base64":
            raise RuntimeError(f"unsupported content encoding for {path}")
        return base64.b64decode(payload["content"]).decode("utf-8")


def collect_structured_authority(
    node: Any,
    artifact_ids: set[int],
    run_ids: set[int],
    shas: set[str],
    key_hint: str = "",
) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            collect_structured_authority(value, artifact_ids, run_ids, shas, str(key).lower())
        return
    if isinstance(node, list):
        for value in node:
            collect_structured_authority(value, artifact_ids, run_ids, shas, key_hint)
        return
    if isinstance(node, int):
        if "artifact" in key_hint:
            artifact_ids.add(node)
        elif "run" in key_hint:
            run_ids.add(node)
        return
    if isinstance(node, str):
        stripped = node.strip()
        if re.fullmatch(r"[0-9a-fA-F]{40}", stripped) and "sha" in key_hint:
            shas.add(stripped.lower())
        if stripped.isdigit():
            number = int(stripped)
            if "artifact" in key_hint:
                artifact_ids.add(number)
            elif "run" in key_hint:
                run_ids.add(number)


def collect_text_authority(
    text: str,
    artifact_ids: set[int],
    run_ids: set[int],
    shas: set[str],
) -> None:
    artifact_patterns = (
        r"(?i)artifact[_\s-]*id[^0-9]{0,24}([0-9]{8,})",
        r"(?i)artifact[^\n]{0,40}\b([0-9]{8,})\b",
    )
    run_patterns = (
        r"(?i)run[_\s-]*id[^0-9]{0,24}([0-9]{8,})",
        r"(?i)\brun\s+`?([0-9]{8,})`?",
    )
    for pattern in artifact_patterns:
        artifact_ids.update(int(match) for match in re.findall(pattern, text))
    for pattern in run_patterns:
        run_ids.update(int(match) for match in re.findall(pattern, text))
    shas.update(match.lower() for match in re.findall(r"\b[0-9a-fA-F]{40}\b", text))


def paginated(api: GitHubAPI, path: str, key: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    page = 1
    while True:
        separator = "&" if "?" in path else "?"
        payload, headers = api.json(f"{path}{separator}per_page=100&page={page}")
        batch = payload.get(key, []) if isinstance(payload, dict) else payload
        if not batch:
            break
        items.extend(batch)
        remaining = int(headers.get("X-RateLimit-Remaining", "5000"))
        if remaining < 700:
            raise RuntimeError(
                f"API budget too low while paginating {path}: remaining={remaining}"
            )
        if len(batch) < 100:
            break
        page += 1
    return items


def main() -> int:
    repository = os.environ.get("GITHUB_REPOSITORY") or os.environ.get("REPOSITORY")
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not repository or not token:
        raise SystemExit("GITHUB_REPOSITORY/REPOSITORY and GITHUB_TOKEN/GH_TOKEN are required")

    target_mib = int(os.environ.get("TARGET_FREE_MIB", "300"))
    target_bytes = target_mib * 1024 * 1024
    recent_hours = int(os.environ.get("PRESERVE_RECENT_HOURS", "24"))
    dry_run = parse_bool(os.environ.get("DRY_RUN"), default=True)
    report_path = Path(os.environ.get("REPORT_PATH", "/tmp/axignal-actions-storage-report.json"))
    current_run_id = int(os.environ.get("GITHUB_RUN_ID", "0") or "0")
    current_sha = os.environ.get("GITHUB_SHA", "").lower()

    api = GitHubAPI(repository, token)
    preserve_artifact_ids: set[int] = set()
    preserve_run_ids: set[int] = set()
    preserve_shas: set[str] = set()

    contract_text = api.content(CONTRACT_PATH, "main")
    ledger_text = api.content(LEDGER_PATH, "main")
    collect_text_authority(contract_text, preserve_artifact_ids, preserve_run_ids, preserve_shas)
    collect_text_authority(ledger_text, preserve_artifact_ids, preserve_run_ids, preserve_shas)
    try:
        collect_structured_authority(
            json.loads(ledger_text), preserve_artifact_ids, preserve_run_ids, preserve_shas
        )
    except json.JSONDecodeError:
        pass

    ref_payload, _ = api.json("/git/ref/heads/main")
    preserve_shas.add(str(ref_payload["object"]["sha"]).lower())
    if current_sha:
        preserve_shas.add(current_sha)
    if current_run_id:
        preserve_run_ids.add(current_run_id)

    open_pulls = paginated(api, "/pulls?state=open", "items")
    for pull in open_pulls:
        head_sha = str((pull.get("head") or {}).get("sha", "")).lower()
        if head_sha:
            preserve_shas.add(head_sha)

    for status in ("queued", "in_progress", "waiting", "requested", "pending"):
        payload, _ = api.json(f"/actions/runs?status={status}&per_page=100")
        for run in payload.get("workflow_runs", []):
            preserve_run_ids.add(int(run["id"]))
            head_sha = str(run.get("head_sha", "")).lower()
            if head_sha:
                preserve_shas.add(head_sha)

    artifacts = paginated(api, "/actions/artifacts", "artifacts")
    before_bytes = sum(int(item.get("size_in_bytes", 0)) for item in artifacts)
    cutoff = utc_now() - timedelta(hours=recent_hours)

    run_bytes: dict[int, int] = defaultdict(int)
    run_created: dict[int, datetime] = {}
    run_sha: dict[int, str] = {}
    run_artifact_ids: dict[int, list[int]] = defaultdict(list)
    protected_by_artifact: set[int] = set()

    for artifact in artifacts:
        workflow_run = artifact.get("workflow_run") or {}
        raw_run_id = workflow_run.get("id")
        if not raw_run_id:
            continue
        run_id = int(raw_run_id)
        artifact_id = int(artifact["id"])
        run_bytes[run_id] += int(artifact.get("size_in_bytes", 0))
        run_artifact_ids[run_id].append(artifact_id)
        run_sha[run_id] = str(workflow_run.get("head_sha", "")).lower()
        created = datetime.fromisoformat(str(artifact["created_at"]).replace("Z", "+00:00"))
        previous = run_created.get(run_id)
        if previous is None or created > previous:
            run_created[run_id] = created
        if artifact_id in preserve_artifact_ids:
            protected_by_artifact.add(run_id)

    candidates: list[tuple[int, int]] = []
    protected_runs: set[int] = set()
    for run_id, size in run_bytes.items():
        if (
            run_id in preserve_run_ids
            or run_id in protected_by_artifact
            or run_sha.get(run_id, "") in preserve_shas
            or run_created[run_id] >= cutoff
        ):
            protected_runs.add(run_id)
            continue
        candidates.append((run_id, size))
    candidates.sort(key=lambda item: (item[1], -item[0]), reverse=True)

    potential_bytes = 0
    planned_runs: list[dict[str, Any]] = []
    for run_id, size in candidates:
        if potential_bytes >= target_bytes:
            break
        potential_bytes += size
        planned_runs.append(
            {
                "run_id": run_id,
                "bytes": size,
                "mib": round(size / 1024 / 1024, 3),
                "head_sha": run_sha.get(run_id, ""),
                "artifact_count": len(run_artifact_ids[run_id]),
                "latest_artifact_at": run_created[run_id].isoformat(),
            }
        )

    deleted_runs: list[int] = []
    verified_404_runs: list[int] = []
    freed_bytes = 0
    failures: list[str] = []

    if not dry_run:
        for candidate in planned_runs:
            run_id = int(candidate["run_id"])
            size = int(candidate["bytes"])
            try:
                api.request(f"/actions/runs/{run_id}", method="DELETE", expected={204, 404})
                status, _, _ = api.request(
                    f"/actions/runs/{run_id}", method="GET", expected={404}
                )
                if status != 404:
                    raise RuntimeError(f"post-delete verification failed for run {run_id}")
                deleted_runs.append(run_id)
                verified_404_runs.append(run_id)
                freed_bytes += size
            except Exception as exc:  # retain complete audit trail and stop safely
                failures.append(str(exc))
                break

    summary = {
        "schema": "axignal.actions-storage-reclamation.v3",
        "repository": repository,
        "timestamp": utc_now().isoformat(),
        "dry_run": dry_run,
        "target_mib": target_mib,
        "target_bytes": target_bytes,
        "artifact_count_before": len(artifacts),
        "artifact_bytes_before": before_bytes,
        "artifact_mib_before": round(before_bytes / 1024 / 1024, 2),
        "protected_artifact_ids": sorted(preserve_artifact_ids),
        "protected_run_count": len(protected_runs),
        "protected_sha_count": len(preserve_shas),
        "eligible_run_count": len(candidates),
        "planned_run_count": len(planned_runs),
        "planned_free_bytes": potential_bytes,
        "planned_free_mib": round(potential_bytes / 1024 / 1024, 2),
        "planned_runs": planned_runs,
        "deleted_runs": deleted_runs,
        "verified_404_runs": verified_404_runs,
        "freed_bytes": freed_bytes,
        "freed_mib": round(freed_bytes / 1024 / 1024, 2),
        "estimated_bytes_after": before_bytes - freed_bytes,
        "estimated_mib_after": round((before_bytes - freed_bytes) / 1024 / 1024, 2),
        "target_reached": potential_bytes >= target_bytes if dry_run else freed_bytes >= target_bytes,
        "failures": failures,
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))

    if failures:
        return 3
    if not summary["target_reached"]:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
