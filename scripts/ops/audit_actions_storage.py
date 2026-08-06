#!/usr/bin/env python3
"""Fail-closed, read-only audit of AXIGNAL Actions workflows and artifacts."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

API_VERSION = "2022-11-28"
RETRYABLE = {429, 500, 502, 503, 504}
SHA_RE = re.compile(r"\b[0-9a-fA-F]{40}\b")
ARTIFACT_ID_RE = re.compile(r"(?i)artifact(?:[_\s-]*id)?[^0-9]{0,24}([0-9]{8,})")
RUN_ID_RE = re.compile(r"(?i)(?:workflow[_\s-]*)?run(?:[_\s-]*id)?[^0-9]{0,24}([0-9]{8,})")
UPLOAD_RE = re.compile(r"^\s*-?\s*uses:\s*actions/upload-artifact@", re.I)
CACHE_RE = re.compile(r"^\s*-?\s*uses:\s*actions/cache@", re.I)
RUNNER_RE = re.compile(r"^\s*runs-on:\s*(.+?)\s*$", re.I)
RETENTION_RE = re.compile(r"^\s*retention-days:\s*(.+?)\s*$", re.I)
NAME_RE = re.compile(r"^\s*name:\s*(.+?)\s*$", re.I)
STEP_RE = re.compile(r"^(\s*)-\s+(?:name|uses):")


def now() -> datetime:
    return datetime.now(timezone.utc)


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def mib(value: int) -> float:
    return round(value / 1024 / 1024, 3)


def scalar(value: str) -> str:
    value = value.strip()
    if len(value) > 1 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def load_policy(path: Path) -> dict[str, Any]:
    policy = json.loads(path.read_text(encoding="utf-8"))
    if policy.get("schema") != "axignal.actions-storage-policy.v1":
        raise SystemExit(f"unexpected policy schema: {policy.get('schema')}")
    if policy.get("destructive_cleanup_enabled") is not False:
        raise SystemExit("destructive cleanup must remain disabled")
    return policy


def classify(name: str, policy: dict[str, Any]) -> str:
    lowered = name.lower()
    rules = policy["classification"]
    if any(part in lowered for part in rules["contractual_name_fragments"]):
        return "contractual"
    if any(part in lowered for part in rules["diagnostic_name_fragments"]):
        return "diagnostic"
    return "ephemeral"


def family(name: str) -> str:
    value = name.lower().strip()
    value = re.sub(r"[0-9a-f]{64}", "{digest}", value)
    value = re.sub(r"[0-9a-f]{40}", "{sha}", value)
    value = re.sub(r"\b20\d{2}[01]\d[0-3]\d[t_-]?[0-2]\d[0-5]\d[0-5]\d(?:z)?\b", "{timestamp}", value)
    value = re.sub(r"(?<![a-z])\d{8,}(?![a-z])", "{id}", value)
    return re.sub(r"[-_]{2,}", "-", value)[:240]


@dataclass
class Upload:
    workflow: str
    line: int
    artifact_name: str
    classification: str
    retention_raw: str | None
    retention_days: int | None
    issue: str | None


@dataclass
class Workflow:
    path: str
    uploads: list[Upload]
    cache_steps: int
    runners: list[str]
    pull_request: bool
    pull_request_target: bool
    push: bool
    schedule: bool
    workflow_dispatch: bool


def bounds(lines: list[str], index: int) -> tuple[int, int]:
    start = index
    while start > 0 and not STEP_RE.match(lines[start]):
        start -= 1
    match = STEP_RE.match(lines[start])
    indent = len(match.group(1)) if match else 0
    end = index + 1
    while end < len(lines):
        candidate = STEP_RE.match(lines[end])
        if candidate and len(candidate.group(1)) <= indent:
            break
        end += 1
    return start, end


def scan(path: Path, root: Path, policy: dict[str, Any]) -> Workflow:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    uploads: list[Upload] = []
    for index, line in enumerate(lines):
        if not UPLOAD_RE.match(line):
            continue
        start, end = bounds(lines, index)
        name = "<dynamic-or-missing>"
        retention: str | None = None
        for candidate in lines[start:end]:
            if match := NAME_RE.match(candidate):
                name = scalar(match.group(1))
            if match := RETENTION_RE.match(candidate):
                retention = scalar(match.group(1))
        kind = classify(name, policy)
        maximum = int(policy["retention_days"][kind])
        days: int | None = None
        issue: str | None = None
        if retention is None:
            issue = "missing-retention-days"
        elif "${{" in retention:
            issue = "dynamic-retention-days"
        else:
            try:
                days = int(retention)
            except ValueError:
                issue = "invalid-retention-days"
            else:
                if days < 1:
                    issue = "retention-below-one-day"
                elif days > maximum:
                    issue = f"retention-exceeds-{kind}-maximum-{maximum}"
        uploads.append(Upload(str(path.relative_to(root)), index + 1, name, kind, retention, days, issue))
    lowered = text.lower()
    runners = sorted({scalar(m.group(1)) for line in lines if (m := RUNNER_RE.match(line))})
    return Workflow(
        str(path.relative_to(root)), uploads, sum(bool(CACHE_RE.match(line)) for line in lines), runners,
        bool(re.search(r"(?m)^\s*pull_request\s*:", lowered)),
        bool(re.search(r"(?m)^\s*pull_request_target\s*:", lowered)),
        bool(re.search(r"(?m)^\s*push\s*:", lowered)),
        bool(re.search(r"(?m)^\s*schedule\s*:", lowered)),
        bool(re.search(r"(?m)^\s*workflow_dispatch\s*:", lowered)),
    )


class API:
    def __init__(self, repository: str, token: str | None, floor: int) -> None:
        self.root = f"https://api.github.com/repos/{repository}"
        self.floor = floor
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "axignal-actions-storage-audit/1.1",
        }
        if token:
            clean = token.strip()
            if any(ord(char) < 33 or ord(char) == 127 for char in clean):
                raise SystemExit("token contains whitespace/control characters")
            self.headers["Authorization"] = f"Bearer {clean}"

    def get(self, path: str, attempts: int = 6) -> Any:
        url = path if path.startswith("https://") else self.root + path
        for attempt in range(1, attempts + 1):
            request = urllib.request.Request(url, headers=self.headers)
            try:
                with urllib.request.urlopen(request, timeout=90) as response:
                    remaining = int(response.headers.get("X-RateLimit-Remaining", "5000"))
                    if remaining < self.floor:
                        raise RuntimeError(f"API budget below floor: {remaining} < {self.floor}")
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")
                if exc.code not in RETRYABLE or attempt == attempts:
                    raise RuntimeError(f"GitHub API GET {url}: {exc.code} {body[:500]}") from exc
            except (urllib.error.URLError, TimeoutError):
                if attempt == attempts:
                    raise
            time.sleep(min(2 ** (attempt - 1), 20))
        raise RuntimeError(f"GitHub API GET failed: {url}")

    def pages(self, path: str, key: str, max_pages: int = 0) -> Iterable[dict[str, Any]]:
        page = 1
        while not max_pages or page <= max_pages:
            join = "&" if "?" in path else "?"
            payload = self.get(f"{path}{join}per_page=100&page={page}")
            batch = payload.get(key, []) if isinstance(payload, dict) else payload
            if not batch:
                return
            yield from batch
            if len(batch) < 100:
                return
            page += 1


def authorities(root: Path, policy: dict[str, Any]) -> tuple[set[int], set[int], set[str]]:
    artifacts = {int(v) for v in policy.get("explicit_protected_artifact_ids", [])}
    runs = {int(v) for v in policy.get("explicit_protected_run_ids", [])}
    shas: set[str] = set()
    for relative in policy.get("canonical_authorities", []):
        path = root / relative
        if not path.is_file():
            raise SystemExit(f"canonical authority missing: {relative}")
        text = path.read_text(encoding="utf-8")
        artifacts.update(int(v) for v in ARTIFACT_ID_RE.findall(text))
        runs.update(int(v) for v in RUN_ID_RE.findall(text))
        shas.update(v.lower() for v in SHA_RE.findall(text))
    return artifacts, runs, shas


def inventory(api: API, policy: dict[str, Any], protected: tuple[set[int], set[int], set[str]], max_pages: int) -> dict[str, Any]:
    protected_artifacts, protected_runs, protected_shas = protected
    protected_shas.add(str(api.get("/git/ref/heads/main")["object"]["sha"]).lower())
    for pull in api.pages("/pulls?state=open", "items", 10):
        sha = str((pull.get("head") or {}).get("sha", "")).lower()
        if sha:
            protected_shas.add(sha)
    cutoff = now() - timedelta(hours=int(policy["inventory"]["preserve_recent_hours"]))
    classes: dict[str, Counter[str]] = defaultdict(Counter)
    families: dict[str, Counter[str]] = defaultdict(Counter)
    runs: dict[int, Counter[str]] = defaultdict(Counter)
    total_count = total_bytes = protected_count = protected_bytes = 0
    oldest: datetime | None = None
    newest: datetime | None = None
    for artifact in api.pages("/actions/artifacts", "artifacts", max_pages):
        total_count += 1
        size = int(artifact.get("size_in_bytes") or 0)
        total_bytes += size
        created = parse_time(str(artifact["created_at"]))
        oldest = created if oldest is None or created < oldest else oldest
        newest = created if newest is None or created > newest else newest
        name = str(artifact.get("name") or "")
        kind = classify(name, policy)
        run = artifact.get("workflow_run") or {}
        run_id = int(run.get("id") or 0)
        sha = str(run.get("head_sha") or "").lower()
        classes[kind].update(count=1, bytes=size)
        families[family(name)].update(count=1, bytes=size)
        runs[run_id].update(count=1, bytes=size)
        if int(artifact["id"]) in protected_artifacts or run_id in protected_runs or sha in protected_shas or kind == "contractual" or created >= cutoff:
            protected_count += 1
            protected_bytes += size
    top = sorted(
        ({"family": key, "count": value["count"], "bytes": value["bytes"], "mib": mib(value["bytes"])} for key, value in families.items()),
        key=lambda item: (item["bytes"], item["count"]), reverse=True,
    )[: int(policy["inventory"].get("top_families", 50))]
    limit = int(policy["workflow_limits"]["maximum_artifacts_per_run"])
    excessive = sorted(
        ({"run_id": key, "artifact_count": value["count"], "bytes": value["bytes"], "mib": mib(value["bytes"])} for key, value in runs.items() if key and value["count"] > limit),
        key=lambda item: (item["artifact_count"], item["bytes"]), reverse=True,
    )[:100]
    candidate_bytes = total_bytes - protected_bytes
    return {
        "complete": max_pages == 0, "max_pages": max_pages,
        "total_count": total_count, "total_bytes": total_bytes, "total_mib": mib(total_bytes),
        "protected_count": protected_count, "protected_bytes": protected_bytes, "protected_mib": mib(protected_bytes),
        "candidate_count": total_count - protected_count, "candidate_bytes": candidate_bytes, "candidate_mib": mib(candidate_bytes),
        "oldest_created_at": oldest.isoformat() if oldest else None,
        "newest_created_at": newest.isoformat() if newest else None,
        "by_class": {key: {"count": value["count"], "bytes": value["bytes"], "mib": mib(value["bytes"])} for key, value in sorted(classes.items())},
        "top_families": top, "runs_exceeding_artifact_limit": excessive,
        "protected_artifact_ids": sorted(protected_artifacts), "protected_run_ids": sorted(protected_runs),
        "protected_sha_count": len(protected_shas),
    }


def scan_workflow(path: Path, policy: dict[str, Any], repo_root: Path) -> Workflow:
    return scan(path, repo_root, policy)


def normalize_family(name: str) -> str:
    return family(name)


def markdown(report: dict[str, Any]) -> str:
    static = report["static"]
    lines = [
        "# AXIGNAL Actions storage audit", "",
        f"- Timestamp: `{report['timestamp']}`", f"- Repository: `{report['repository']}`",
        f"- Destructive cleanup: `{report['destructive_cleanup_enabled']}`", "",
        "## Static workflow audit", "",
        f"- Workflows scanned: **{static['workflow_count']}**",
        f"- Upload steps: **{static['upload_step_count']}**",
        f"- Upload violations: **{static['violation_count']}**",
        f"- Cache steps: **{static['cache_step_count']}**",
        f"- Unsafe self-hosted PR workflows: **{len(static['unsafe_self_hosted_pr_workflows'])}**",
    ]
    for item in static["violations"][:200]:
        lines.append(f"- `{item['workflow']}:{item['line']}` — `{item['issue']}` — `{item['artifact_name']}`")
    if remote := report.get("inventory"):
        lines += ["", "## Remote artifact inventory", "", f"- Complete: **{remote['complete']}**", f"- Artifacts: **{remote['total_count']}**", f"- Stored: **{remote['total_mib']} MiB**", f"- Protected: **{remote['protected_mib']} MiB**", f"- Candidate pool: **{remote['candidate_mib']} MiB**", "", "### Largest normalized families", ""]
        lines += [f"- `{item['family']}` — {item['count']} artifacts — {item['mib']} MiB" for item in remote["top_families"]]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--policy", default="config/actions-storage-policy.json")
    parser.add_argument("--repository", default=os.getenv("GITHUB_REPOSITORY", "LowToHi/axignal"))
    parser.add_argument("--inventory-artifacts", action="store_true")
    parser.add_argument("--max-pages", type=int, default=0)
    parser.add_argument("--report-json", default="reports/actions-storage-audit.json")
    parser.add_argument("--report-md", default="reports/actions-storage-audit.md")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    policy = load_policy(root / args.policy)
    workflows = [scan(path, root, policy) for path in sorted((root / ".github/workflows").glob("*.y*ml"))]
    uploads = [asdict(upload) for workflow in workflows for upload in workflow.uploads]
    violations = [upload for upload in uploads if upload["issue"]]
    max_uploads = int(policy["workflow_limits"]["maximum_upload_steps_per_workflow"])
    excessive = [{"workflow": workflow.path, "upload_steps": len(workflow.uploads)} for workflow in workflows if len(workflow.uploads) > max_uploads]
    unsafe = [workflow.path for workflow in workflows if (workflow.pull_request or workflow.pull_request_target) and any("self-hosted" in runner.lower() for runner in workflow.runners)]
    report: dict[str, Any] = {
        "schema": "axignal.actions-storage-audit.v1", "timestamp": now().isoformat(),
        "repository": args.repository, "policy_schema": policy["schema"],
        "destructive_cleanup_enabled": policy["destructive_cleanup_enabled"],
        "static": {
            "workflow_count": len(workflows), "upload_step_count": len(uploads),
            "cache_step_count": sum(workflow.cache_steps for workflow in workflows),
            "violation_count": len(violations), "violations": violations,
            "workflows_exceeding_upload_limit": excessive,
            "unsafe_self_hosted_pr_workflows": unsafe,
            "workflows": [asdict(workflow) for workflow in workflows],
        },
    }
    if args.inventory_artifacts:
        api = API(args.repository, os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN"), int(policy["inventory"].get("minimum_api_remaining", 250)))
        report["inventory"] = inventory(api, policy, authorities(root, policy), args.max_pages)
    json_path, md_path = root / args.report_json, root / args.report_md
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(markdown(report), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.check and policy.get("mode") == "enforce" and (violations or excessive or unsafe):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
