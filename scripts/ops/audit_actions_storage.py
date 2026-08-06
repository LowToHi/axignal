#!/usr/bin/env python3
"""Audit AXIGNAL GitHub Actions storage without deleting anything.

The audit has two independent layers:
1. Static workflow policy: upload-artifact retention, cache usage, runner labels.
2. Remote artifact inventory: counts/bytes by class and normalized name family,
   with canonical evidence derived from the contractual authorities.

The script is standard-library only and fail-closed. It never mutates GitHub.
"""

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
HEX_SHA_RE = re.compile(r"\b[0-9a-fA-F]{40}\b")
ARTIFACT_ID_RE = re.compile(r"(?i)artifact(?:[_\s-]*id)?[^0-9]{0,24}([0-9]{8,})")
RUN_ID_RE = re.compile(r"(?i)(?:workflow[_\s-]*)?run(?:[_\s-]*id)?[^0-9]{0,24}([0-9]{8,})")
UPLOAD_USES_RE = re.compile(r"^\s*uses:\s*actions/upload-artifact@", re.I)
CACHE_USES_RE = re.compile(r"^\s*uses:\s*actions/cache@", re.I)
RUNS_ON_RE = re.compile(r"^\s*runs-on:\s*(.+?)\s*$", re.I)
RETENTION_RE = re.compile(r"^\s*retention-days:\s*(.+?)\s*$", re.I)
NAME_RE = re.compile(r"^\s*name:\s*(.+?)\s*$", re.I)
STEP_RE = re.compile(r"^(\s*)-\s+(?:name|uses):")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def mib(value: int) -> float:
    return round(value / 1024 / 1024, 3)


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"required policy not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON policy {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit(f"policy root must be an object: {path}")
    return payload


def unquote_yaml_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def classify_name(name: str, policy: dict[str, Any]) -> str:
    lowered = name.lower()
    classification = policy["classification"]
    if any(fragment in lowered for fragment in classification["contractual_name_fragments"]):
        return "contractual"
    if any(fragment in lowered for fragment in classification["diagnostic_name_fragments"]):
        return "diagnostic"
    return "ephemeral"


def normalize_family(name: str) -> str:
    value = name.lower().strip()
    value = re.sub(r"[0-9a-f]{64}", "{digest}", value)
    value = re.sub(r"[0-9a-f]{40}", "{sha}", value)
    value = re.sub(r"\b20\d{2}[01]\d[0-3]\d[t_-]?[0-2]\d[0-5]\d[0-5]\d(?:z)?\b", "{timestamp}", value)
    value = re.sub(r"(?<![a-z])\d{8,}(?![a-z])", "{id}", value)
    value = re.sub(r"[-_]{2,}", "-", value)
    return value[:240]


@dataclass
class UploadStep:
    workflow: str
    line: int
    artifact_name: str
    classification: str
    retention_raw: str | None
    retention_days: int | None
    issue: str | None


@dataclass
class WorkflowAudit:
    path: str
    upload_steps: list[UploadStep]
    cache_steps: int
    runners: list[str]
    has_pull_request: bool
    has_pull_request_target: bool
    has_push: bool
    has_schedule: bool
    has_workflow_dispatch: bool


def step_block(lines: list[str], index: int) -> tuple[int, int]:
    start = index
    while start > 0:
        match = STEP_RE.match(lines[start])
        if match:
            break
        start -= 1
    start_match = STEP_RE.match(lines[start])
    base_indent = len(start_match.group(1)) if start_match else 0
    end = index + 1
    while end < len(lines):
        match = STEP_RE.match(lines[end])
        if match and len(match.group(1)) <= base_indent:
            break
        end += 1
    return start, end


def scan_workflow(path: Path, policy: dict[str, Any], repo_root: Path) -> WorkflowAudit:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    uploads: list[UploadStep] = []
    cache_steps = sum(1 for line in lines if CACHE_USES_RE.match(line))
    runners = [unquote_yaml_scalar(match.group(1)) for line in lines if (match := RUNS_ON_RE.match(line))]

    for index, line in enumerate(lines):
        if not UPLOAD_USES_RE.match(line):
            continue
        start, end = step_block(lines, index)
        block = lines[start:end]
        artifact_name = "<dynamic-or-missing>"
        retention_raw: str | None = None
        for candidate in block:
            name_match = NAME_RE.match(candidate)
            if name_match and candidate.lstrip().startswith("name:"):
                value = unquote_yaml_scalar(name_match.group(1))
                if value and not value.lower().startswith(("upload ", "publish ", "archive ")):
                    artifact_name = value
            retention_match = RETENTION_RE.match(candidate)
            if retention_match:
                retention_raw = unquote_yaml_scalar(retention_match.group(1))

        classification = classify_name(artifact_name, policy)
        expected = int(policy["retention_days"][classification])
        retention_days: int | None = None
        issue: str | None = None
        if retention_raw is None:
            issue = "missing-retention-days"
        elif "${{" in retention_raw:
            issue = "dynamic-retention-days"
        else:
            try:
                retention_days = int(retention_raw)
            except ValueError:
                issue = "invalid-retention-days"
            else:
                if retention_days > expected:
                    issue = f"retention-exceeds-{classification}-maximum-{expected}"
                elif retention_days < 1:
                    issue = "retention-below-one-day"

        uploads.append(
            UploadStep(
                workflow=str(path.relative_to(repo_root)),
                line=index + 1,
                artifact_name=artifact_name,
                classification=classification,
                retention_raw=retention_raw,
                retention_days=retention_days,
                issue=issue,
            )
        )

    lowered = text.lower()
    return WorkflowAudit(
        path=str(path.relative_to(repo_root)),
        upload_steps=uploads,
        cache_steps=cache_steps,
        runners=sorted(set(runners)),
        has_pull_request=bool(re.search(r"(?m)^\s*pull_request\s*:", lowered)),
        has_pull_request_target=bool(re.search(r"(?m)^\s*pull_request_target\s*:", lowered)),
        has_push=bool(re.search(r"(?m)^\s*push\s*:", lowered)),
        has_schedule=bool(re.search(r"(?m)^\s*schedule\s*:", lowered)),
        has_workflow_dispatch=bool(re.search(r"(?m)^\s*workflow_dispatch\s*:", lowered)),
    )


class GitHubAPI:
    def __init__(self, repository: str, token: str | None, minimum_remaining: int) -> None:
        self.repository = repository
        self.root = f"https://api.github.com/repos/{repository}"
        self.minimum_remaining = minimum_remaining
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "axignal-actions-storage-audit/1.0",
        }
        if token:
            clean_token = token.strip()
            if any(ord(char) < 33 or ord(char) == 127 for char in clean_token):
                raise SystemExit("token contains whitespace or control characters")
            self.headers["Authorization"] = f"Bearer {clean_token}"

    def request(self, path_or_url: str, attempts: int = 6) -> tuple[Any, dict[str, str]]:
        url = path_or_url if path_or_url.startswith("https://") else f"{self.root}{path_or_url}"
        last_error: Exception | None = None
        for attempt in range(1, attempts + 1):
            request = urllib.request.Request(url, headers=self.headers, method="GET")
            try:
                with urllib.request.urlopen(request, timeout=90) as response:
                    body = response.read().decode("utf-8")
                    headers = dict(response.headers.items())
                    remaining = int(headers.get("X-RateLimit-Remaining", "5000"))
                    if remaining < self.minimum_remaining:
                        raise RuntimeError(
                            f"GitHub API budget below safety floor: remaining={remaining} "
                            f"floor={self.minimum_remaining}"
                        )
                    return json.loads(body), headers
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")
                last_error = RuntimeError(f"GitHub API GET {url} failed: {exc.code} {body[:500]}")
                if exc.code not in RETRYABLE or attempt == attempts:
                    raise last_error from exc
            except (urllib.error.URLError, TimeoutError) as exc:
                last_error = exc
                if attempt == attempts:
                    raise
            time.sleep(min(2 ** (attempt - 1), 20))
        raise RuntimeError(f"GitHub request failed: {last_error}")

    def paginated(self, path: str, key: str, max_pages: int = 0) -> Iterable[dict[str, Any]]:
        page = 1
        while True:
            if max_pages and page > max_pages:
                return
            separator = "&" if "?" in path else "?"
            payload, _ = self.request(f"{path}{separator}per_page=100&page={page}")
            batch = payload.get(key, []) if isinstance(payload, dict) else payload
            if not batch:
                return
            yield from batch
            if len(batch) < 100:
                return
            page += 1


def collect_authority_text(text: str, artifacts: set[int], runs: set[int], shas: set[str]) -> None:
    artifacts.update(int(value) for value in ARTIFACT_ID_RE.findall(text))
    runs.update(int(value) for value in RUN_ID_RE.findall(text))
    shas.update(value.lower() for value in HEX_SHA_RE.findall(text))


def collect_authorities(repo_root: Path, policy: dict[str, Any]) -> tuple[set[int], set[int], set[str]]:
    artifacts = {int(value) for value in policy.get("explicit_protected_artifact_ids", [])}
    runs = {int(value) for value in policy.get("explicit_protected_run_ids", [])}
    shas: set[str] = set()
    for relative in policy.get("canonical_authorities", []):
        path = repo_root / relative
        if not path.is_file():
            raise SystemExit(f"canonical authority missing: {relative}")
        collect_authority_text(path.read_text(encoding="utf-8"), artifacts, runs, shas)
    return artifacts, runs, shas


def inventory_artifacts(
    api: GitHubAPI,
    policy: dict[str, Any],
    protected_artifacts: set[int],
    protected_runs: set[int],
    protected_shas: set[str],
    max_pages: int,
) -> dict[str, Any]:
    ref, _ = api.request("/git/ref/heads/main")
    protected_shas.add(str(ref["object"]["sha"]).lower())

    for pull in api.paginated("/pulls?state=open", "items", max_pages=10):
        head_sha = str((pull.get("head") or {}).get("sha", "")).lower()
        if head_sha:
            protected_shas.add(head_sha)

    recent_cutoff = utc_now() - timedelta(hours=int(policy["inventory"]["preserve_recent_hours"]))
    class_stats: dict[str, Counter[str]] = defaultdict(Counter)
    family_stats: dict[str, Counter[str]] = defaultdict(Counter)
    run_stats: dict[int, Counter[str]] = defaultdict(Counter)
    total_count = 0
    total_bytes = 0
    candidate_count = 0
    candidate_bytes = 0
    protected_count = 0
    protected_bytes = 0
    newest: datetime | None = None
    oldest: datetime | None = None

    for artifact in api.paginated("/actions/artifacts", "artifacts", max_pages=max_pages):
        total_count += 1
        size = int(artifact.get("size_in_bytes") or 0)
        total_bytes += size
        created = parse_utc(str(artifact["created_at"]))
        newest = created if newest is None or created > newest else newest
        oldest = created if oldest is None or created < oldest else oldest
        name = str(artifact.get("name") or "")
        artifact_class = classify_name(name, policy)
        family = normalize_family(name)
        workflow_run = artifact.get("workflow_run") or {}
        run_id = int(workflow_run.get("id") or 0)
        head_sha = str(workflow_run.get("head_sha") or "").lower()

        class_stats[artifact_class]["count"] += 1
        class_stats[artifact_class]["bytes"] += size
        family_stats[family]["count"] += 1
        family_stats[family]["bytes"] += size
        run_stats[run_id]["count"] += 1
        run_stats[run_id]["bytes"] += size

        is_protected = (
            int(artifact["id"]) in protected_artifacts
            or run_id in protected_runs
            or head_sha in protected_shas
            or artifact_class == "contractual"
            or created >= recent_cutoff
        )
        if is_protected:
            protected_count += 1
            protected_bytes += size
        else:
            candidate_count += 1
            candidate_bytes += size

    top_n = int(policy["inventory"].get("top_families", 50))
    top_families = sorted(
        (
            {
                "family": family,
                "count": stats["count"],
                "bytes": stats["bytes"],
                "mib": mib(stats["bytes"]),
            }
            for family, stats in family_stats.items()
        ),
        key=lambda item: (item["bytes"], item["count"]),
        reverse=True,
    )[:top_n]
    maximum_artifacts_per_run = int(policy["workflow_limits"]["maximum_artifacts_per_run"])
    excessive_runs = sorted(
        (
            {
                "run_id": run_id,
                "artifact_count": stats["count"],
                "bytes": stats["bytes"],
                "mib": mib(stats["bytes"]),
            }
            for run_id, stats in run_stats.items()
            if run_id and stats["count"] > maximum_artifacts_per_run
        ),
        key=lambda item: (item["artifact_count"], item["bytes"]),
        reverse=True,
    )[:100]

    return {
        "complete": max_pages == 0,
        "max_pages": max_pages,
        "total_count": total_count,
        "total_bytes": total_bytes,
        "total_mib": mib(total_bytes),
        "candidate_count": candidate_count,
        "candidate_bytes": candidate_bytes,
        "candidate_mib": mib(candidate_bytes),
        "protected_count": protected_count,
        "protected_bytes": protected_bytes,
        "protected_mib": mib(protected_bytes),
        "oldest_created_at": oldest.isoformat() if oldest else None,
        "newest_created_at": newest.isoformat() if newest else None,
        "by_class": {
            name: {
                "count": stats["count"],
                "bytes": stats["bytes"],
                "mib": mib(stats["bytes"]),
            }
            for name, stats in sorted(class_stats.items())
        },
        "top_families": top_families,
        "runs_exceeding_artifact_limit": excessive_runs,
        "protected_artifact_ids": sorted(protected_artifacts),
        "protected_run_ids": sorted(protected_runs),
        "protected_sha_count": len(protected_shas),
    }


def markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# AXIGNAL Actions storage audit",
        "",
        f"- Timestamp: `{report['timestamp']}`",
        f"- Repository: `{report['repository']}`",
        f"- Policy: `{report['policy_schema']}`",
        f"- Destructive cleanup: `{report['destructive_cleanup_enabled']}`",
        "",
        "## Static workflow audit",
        "",
        f"- Workflows scanned: **{report['static']['workflow_count']}**",
        f"- Upload steps: **{report['static']['upload_step_count']}**",
        f"- Upload violations: **{report['static']['violation_count']}**",
        f"- Cache steps: **{report['static']['cache_step_count']}**",
        f"- Public PR workflows using self-hosted labels: **{len(report['static']['unsafe_self_hosted_pr_workflows'])}**",
    ]
    if report["static"]["violations"]:
        lines.extend(["", "### Retention violations", ""])
        for item in report["static"]["violations"][:200]:
            lines.append(
                f"- `{item['workflow']}:{item['line']}` — `{item['issue']}` — "
                f"artifact `{item['artifact_name']}`"
            )
    inventory = report.get("inventory")
    if inventory:
        lines.extend(
            [
                "",
                "## Remote artifact inventory",
                "",
                f"- Complete: **{inventory['complete']}**",
                f"- Artifacts: **{inventory['total_count']}**",
                f"- Stored: **{inventory['total_mib']} MiB**",
                f"- Protected: **{inventory['protected_mib']} MiB**",
                f"- Non-protected candidate pool: **{inventory['candidate_mib']} MiB**",
                "",
                "### Largest normalized families",
                "",
            ]
        )
        for item in inventory["top_families"]:
            lines.append(
                f"- `{item['family']}` — {item['count']} artifacts — {item['mib']} MiB"
            )
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--policy", default="config/actions-storage-policy.json")
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", "LowToHi/axignal"))
    parser.add_argument("--inventory-artifacts", action="store_true")
    parser.add_argument("--max-pages", type=int, default=0, help="0 scans all artifact pages")
    parser.add_argument("--report-json", default="reports/actions-storage-audit.json")
    parser.add_argument("--report-md", default="reports/actions-storage-audit.md")
    parser.add_argument("--check", action="store_true", help="exit non-zero on policy violations")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    repo_root = Path(args.repo_root).resolve()
    policy_path = repo_root / args.policy
    policy = read_json(policy_path)

    workflow_paths = sorted((repo_root / ".github" / "workflows").glob("*.y*ml"))
    audits = [scan_workflow(path, policy, repo_root) for path in workflow_paths]
    uploads = [asdict(step) for audit in audits for step in audit.upload_steps]
    violations = [step for step in uploads if step["issue"]]
    maximum_uploads = int(policy["workflow_limits"]["maximum_upload_steps_per_workflow"])
    excessive_upload_workflows = [
        {"workflow": audit.path, "upload_steps": len(audit.upload_steps)}
        for audit in audits
        if len(audit.upload_steps) > maximum_uploads
    ]
    unsafe_self_hosted = [
        audit.path
        for audit in audits
        if (audit.has_pull_request or audit.has_pull_request_target)
        and any("self-hosted" in runner.lower() for runner in audit.runners)
    ]

    protected_artifacts, protected_runs, protected_shas = collect_authorities(repo_root, policy)
    report: dict[str, Any] = {
        "schema": "axignal.actions-storage-audit.v1",
        "timestamp": utc_now().isoformat(),
        "repository": args.repository,
        "policy_schema": policy.get("schema"),
        "destructive_cleanup_enabled": bool(policy.get("destructive_cleanup_enabled")),
        "static": {
            "workflow_count": len(audits),
            "upload_step_count": len(uploads),
            "cache_step_count": sum(audit.cache_steps for audit in audits),
            "violation_count": len(violations),
            "violations": violations,
            "workflows_exceeding_upload_limit": excessive_upload_workflows,
            "unsafe_self_hosted_pr_workflows": unsafe_self_hosted,
            "workflows": [
                {
                    **asdict(audit),
                    "upload_steps": [asdict(step) for step in audit.upload_steps],
                }
                for audit in audits
            ],
        },
    }

    if args.inventory_artifacts:
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        api = GitHubAPI(
            args.repository,
            token,
            int(policy["inventory"].get("minimum_api_remaining", 250)),
        )
        report["inventory"] = inventory_artifacts(
            api,
            policy,
            protected_artifacts,
            protected_runs,
            protected_shas,
            args.max_pages,
        )

    json_path = repo_root / args.report_json
    md_path = repo_root / args.report_md
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(markdown_report(report), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))

    if args.check and (
        violations
        or excessive_upload_workflows
        or unsafe_self_hosted
        or bool(policy.get("destructive_cleanup_enabled"))
    ):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
