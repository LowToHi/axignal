from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = ROOT / ".github/workflows"
REQUIRED_WORKFLOW_NAMES = (
    "G6 Supply Chain Reproducibility",
    "G6 Inactive Next Preview Guard",
    "P21-T02 Seat Governance E2E",
    "P25-T01 Identity Passwordless and Trial Abuse E2E",
    "P26-T01 Organic Discovery and Founder Admin E2E",
    "Full PostgreSQL Migration Matrix",
    "E2E Technical Audit",
    "Pilot Deployment Candidate",
    "Executable Spine",
    "Contract Validation",
    "V1.5 Canonical Contract Validation",
    "Human Review Acceptance",
    "G5 Web Security Boundaries",
    "Frontend Unit Contracts",
    "F1 Controlled Study Protocol",
    "F1 Qualified-User Validation",
    "F2 Runtime Closure",
    "Landing Globe",
    "P17 Cross-Library Intelligence Validation",
    "P18 Intent Intelligence and Knowledge Tides Validation",
    "P19 Scenarios Calibration and Outcomes Validation",
    "P20 Enterprise API Private Data Validation",
    "P23-T02 Message Copy Validation E2E",
    "P23-T03 B2G Landing Copy E2E",
)
EXACT_SHA_EXPRESSION_PARTS = (
    "github.event_name == 'pull_request'",
    "github.event.pull_request.head.sha",
    "github.sha",
)
TREE_ATTESTATION_PATTERN = re.compile(
    r"git\s+rev-parse\s+['\"]?HEAD\^\{tree\}['\"]?"
)


@dataclass(frozen=True)
class WorkflowFinding:
    workflow_name: str
    path: str
    finding: str
    detail: str


def workflow_name(text: str, path: Path) -> str:
    match = re.search(r"(?m)^name:\s*[\"']?([^\n\"']+)[\"']?\s*$", text)
    if match is None:
        raise RuntimeError(f"Workflow has no top-level name: {path}")
    return match.group(1).strip()


def workflow_files() -> dict[str, tuple[Path, str]]:
    discovered: dict[str, tuple[Path, str]] = {}
    for path in sorted((*WORKFLOW_DIR.glob("*.yml"), *WORKFLOW_DIR.glob("*.yaml"))):
        text = path.read_text(encoding="utf-8")
        name = workflow_name(text, path)
        if name in discovered:
            raise RuntimeError(f"Duplicate workflow name: {name}")
        discovered[name] = (path, text)
    return discovered


def step_blocks(text: str, action: str) -> list[str]:
    lines = text.splitlines()
    blocks: list[str] = []
    for index, line in enumerate(lines):
        if action not in line:
            continue
        indent = len(line) - len(line.lstrip())
        block = [line]
        for candidate in lines[index + 1 :]:
            candidate_indent = len(candidate) - len(candidate.lstrip())
            stripped = candidate.lstrip()
            if stripped.startswith("- ") and candidate_indent <= indent:
                break
            if candidate_indent < indent and stripped:
                break
            block.append(candidate)
        blocks.append("\n".join(block))
    return blocks


def inspect_workflow(name: str, path: Path, text: str) -> list[WorkflowFinding]:
    findings: list[WorkflowFinding] = []
    relative = path.relative_to(ROOT).as_posix()

    for part in EXACT_SHA_EXPRESSION_PARTS:
        if part not in text:
            findings.append(
                WorkflowFinding(
                    name,
                    relative,
                    "EXACT_SHA_RESOLUTION_MISSING",
                    f"Missing expression component: {part}",
                )
            )

    checkout_blocks = step_blocks(text, "uses: actions/checkout@")
    if not checkout_blocks:
        findings.append(
            WorkflowFinding(
                name,
                relative,
                "CHECKOUT_MISSING",
                "No actions/checkout step found",
            )
        )
    for index, block in enumerate(checkout_blocks, start=1):
        if "ref: ${{ env.AXIGNAL_EXACT_SHA }}" not in block:
            findings.append(
                WorkflowFinding(
                    name,
                    relative,
                    "CHECKOUT_REF_NOT_EXACT",
                    f"Checkout step {index} does not pin env.AXIGNAL_EXACT_SHA",
                )
            )
        if "persist-credentials: false" not in block:
            findings.append(
                WorkflowFinding(
                    name,
                    relative,
                    "CHECKOUT_CREDENTIALS_NOT_DISABLED",
                    f"Checkout step {index} does not disable persisted credentials",
                )
            )

    if "git rev-parse HEAD" not in text or "AXIGNAL_EXACT_SHA" not in text:
        findings.append(
            WorkflowFinding(
                name,
                relative,
                "HEAD_ASSERTION_MISSING",
                "Workflow does not assert checked-out HEAD against the exact SHA",
            )
        )
    if TREE_ATTESTATION_PATTERN.search(text) is None:
        findings.append(
            WorkflowFinding(
                name,
                relative,
                "TREE_ATTESTATION_MISSING",
                "Workflow does not capture the exact Git tree",
            )
        )

    upload_blocks = step_blocks(text, "uses: actions/upload-artifact@")
    if not upload_blocks:
        findings.append(
            WorkflowFinding(
                name,
                relative,
                "ARTIFACT_UPLOAD_MISSING",
                "Release-critical workflow retains no artifact",
            )
        )
    for index, block in enumerate(upload_blocks, start=1):
        if "${{ env.AXIGNAL_EXACT_SHA }}" not in block:
            findings.append(
                WorkflowFinding(
                    name,
                    relative,
                    "ARTIFACT_NAME_NOT_EXACT_SHA_BOUND",
                    f"Artifact upload {index} is not named with the exact SHA",
                )
            )

    for line in text.splitlines():
        if (
            "AXIGNAL_BUILD_SHA" in line
            or "--build-arg AXIGNAL_BUILD_SHA" in line
        ) and "GITHUB_SHA" in line:
            findings.append(
                WorkflowFinding(
                    name,
                    relative,
                    "BUILD_SHA_USES_EVENT_SHA",
                    line.strip(),
                )
            )

    if "AXIGNAL_BUILD_SHA" in text and "AXIGNAL_EXACT_SHA" not in text:
        findings.append(
            WorkflowFinding(
                name,
                relative,
                "BUILD_SHA_NOT_EXACT_HEAD_BOUND",
                "Build SHA is configured without the exact-head variable",
            )
        )

    return findings


def main() -> int:
    discovered = workflow_files()
    missing = sorted(set(REQUIRED_WORKFLOW_NAMES) - set(discovered))
    unexpected_required_duplicates = len(REQUIRED_WORKFLOW_NAMES) != len(
        set(REQUIRED_WORKFLOW_NAMES)
    )
    findings: list[WorkflowFinding] = []

    for name in REQUIRED_WORKFLOW_NAMES:
        item = discovered.get(name)
        if item is None:
            continue
        path, text = item
        findings.extend(inspect_workflow(name, path, text))

    payload = {
        "schema_version": "axignal.release-exact-head-provenance-inventory/v0.1",
        "status": "PASS" if not findings and not missing else "FAIL",
        "required_workflows": len(REQUIRED_WORKFLOW_NAMES),
        "discovered_required_workflows": len(REQUIRED_WORKFLOW_NAMES) - len(missing),
        "missing_workflows": missing,
        "required_name_duplicates": unexpected_required_duplicates,
        "finding_count": len(findings),
        "findings": [asdict(finding) for finding in findings],
        "public_launch_authorised": False,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
