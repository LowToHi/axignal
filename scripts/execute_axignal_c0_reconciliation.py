#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WP1_HEAD = "cb851be6bb5ff1d5feb8f61c0deb171dbbc38428"
WP2_HEAD = "4d03c88fb747b6b9a6531def146fc2b4003f1b1e"
MERGE_BASE = "a49330dfa01af9328b459c4bf6818477c78da775"

ATOMIC_PATHS = (
    ".github/workflows/landing-foundation.yml",
    "apps/landing",
    "tests/landing",
    "docs/landing",
    "docs/adr/ADR-014-b2g-landing-international-runtime.md",
    "docs/tasks/active/2026-07-29_landing-b2g-international.md",
    "docs/tasks/active/2026-07-29_landing-b2g-international.task.json",
    "docs/tasks/active/2026-08-04_ax-ge2e-closure-next-001.evidence.json",
    "docs/tasks/completed/2026-07-28_axignal-gsap-ui-ux-skill.md",
    "scripts/capture_globe_review.mjs",
    "scripts/prepare_landing_assets.py",
    "scripts/verify_landing_foundation.py",
    "scripts/verify_landing_implementation.py",
    "skills/axignal-cinematic-webgl-scroll",
    "skills/axignal-gsap-ui-ux",
)

SHARED_PATHS = (
    "docs/roadmap/02-task-catalogue.md",
    "docs/roadmap/04-dynamic-skill-map.md",
    "skills/registry.yaml",
)

TASK_SECTION = """## Legacy implementation task additions

| Task | Purpose | Governing scope | Required skills |
|---|---|---|---|
| `AX-F2-T18` | Rebuild the public landing for the B2G procurement wedge with six-locale parity, evidence-state truth and controlled B2G trial intake | 01–06, 08, 12–13, 16, 18, 20–21, 23, 28, ADR-013, ADR-014 | frontend-architect, axignal-gsap-ui-ux, axignal-cinematic-webgl-scroll, globe-engineer, multilingual-localiser, analytics-engineer, accessibility-auditor, performance-engineer, test-engineer |

This row preserves the immutable F2 implementation authority without representing it as a v1.5-native P25–P27 task or as canonical acceptance.
"""

SKILL_MAP_ROWS = (
    "| `axignal-gsap-ui-ux` | GSAP, motion, animation or cinematic interaction | "
    "semantic choreography, implementation, reduced-motion fallback and validation evidence |",
    "| `axignal-cinematic-webgl-scroll` | Globe texture, Canvas, GPU, LOD or sharpness work | "
    "capability tiers, regional blending, rights, fallback and measurable R3F quality gates |",
)

REGISTRY_BLOCK = """  - skill_id: axignal-gsap-ui-ux
    version: 0.1.0
    state: CONTRACTED
    category: experience
    phases: [F1, F2, F4, F5, F6, F8, F9, F12]
    contracts: [GOAL_LOCK, \"05\", \"08\", \"12\", \"13\", \"16\", \"18\", \"20\", \"21\"]
    triggers: [ui, ux, gsap, greensock, motion, animation, interaction, scroll, transition, morph, svg, prototype, cinematic]
    purpose: Design, implement and audit ambitious AXIGNAL motion systems with GSAP while preserving semantic truth, accessibility, performance and user control.

  - skill_id: axignal-cinematic-webgl-scroll
    version: 0.1.0
    state: CONTRACTED
    category: experience
    phases: [F1, F2, F5, F8]
    contracts: [GOAL_LOCK, \"03\", \"05\", \"08\", \"12\", \"13\", \"18\", \"20\", \"21\"]
    triggers: [webgl, globe, texture, ktx2, dpr, drawing-buffer, anisotropy, gpu, lod, sharpness, r3f]
    purpose: Enforce texture, Canvas, regional LOD, rights, fallback and R3F performance gates without duplicating GSAP choreography.

"""


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.strip()


def changed_paths(start: str, end: str) -> set[str]:
    output = git("diff", "--name-only", f"{start}..{end}")
    return {line for line in output.splitlines() if line}


def tree_paths(commit: str, path: str) -> set[str]:
    output = git("ls-tree", "-r", "--name-only", commit, "--", path)
    return {line for line in output.splitlines() if line}


def restore_wp1_authority(controller_head: str) -> list[str]:
    wp2_only: set[str] = set()
    directory_paths = {
        "apps/landing",
        "tests/landing",
        "docs/landing",
        "skills/axignal-cinematic-webgl-scroll",
        "skills/axignal-gsap-ui-ux",
    }
    for path in ATOMIC_PATHS:
        if path in directory_paths:
            wp2_only.update(tree_paths(controller_head, path) - tree_paths(WP1_HEAD, path))

    git("restore", f"--source={WP1_HEAD}", "--staged", "--worktree", "--", *ATOMIC_PATHS)
    for path in sorted(wp2_only):
        git("restore", f"--source={controller_head}", "--staged", "--worktree", "--", path)
    return sorted(wp2_only)


def insert_after(path: Path, anchor: str, additions: tuple[str, ...]) -> None:
    content = path.read_text(encoding="utf-8")
    missing = [item for item in additions if item not in content]
    if not missing:
        return
    assert anchor in content, f"anchor missing in {path}: {anchor}"
    replacement = anchor + "\n" + "\n".join(missing)
    updated = content.replace(anchor, replacement, 1)
    assert updated.count(missing[0]) == 1
    path.write_text(updated, encoding="utf-8")


def insert_before(path: Path, anchor: str, addition: str) -> None:
    content = path.read_text(encoding="utf-8")
    if addition in content:
        return
    assert anchor in content, f"anchor missing in {path}: {anchor}"
    updated = content.replace(anchor, addition.rstrip() + "\n\n" + anchor, 1)
    assert updated.count(addition.splitlines()[0]) == 1
    path.write_text(updated, encoding="utf-8")


def reconcile_shared_files() -> None:
    task_catalogue = ROOT / "docs/roadmap/02-task-catalogue.md"
    task_content = task_catalogue.read_text(encoding="utf-8")
    if "`AX-F2-T18`" not in task_content:
        insert_before(task_catalogue, "## Closure rule", TASK_SECTION)
    task_content = task_catalogue.read_text(encoding="utf-8")
    assert task_content.count("`AX-F2-T18`") == 1
    assert task_content.index("## Legacy implementation task additions") < task_content.index(
        "## Closure rule"
    )

    skill_map = ROOT / "docs/roadmap/04-dynamic-skill-map.md"
    skill_content = skill_map.read_text(encoding="utf-8")
    if "`axignal-gsap-ui-ux`" not in skill_content:
        anchor = next(
            line
            for line in skill_content.splitlines()
            if line.startswith("| `visualisation-designer` |")
        )
        insert_after(skill_map, anchor, SKILL_MAP_ROWS)
    skill_content = skill_map.read_text(encoding="utf-8")
    assert skill_content.count("`axignal-gsap-ui-ux`") == 1
    assert skill_content.count("`axignal-cinematic-webgl-scroll`") == 1

    registry = ROOT / "skills/registry.yaml"
    registry_content = registry.read_text(encoding="utf-8")
    if registry_content.startswith("version: 0.3.1\n"):
        registry_content = registry_content.replace("version: 0.3.1\n", "version: 0.4.0\n", 1)
    assert registry_content.startswith("version: 0.4.0\n")
    if "skill_id: axignal-gsap-ui-ux" not in registry_content:
        anchor = "  - skill_id: globe-engineer\n"
        assert anchor in registry_content
        registry_content = registry_content.replace(anchor, REGISTRY_BLOCK + anchor, 1)
    assert registry_content.count("skill_id: axignal-gsap-ui-ux") == 1
    assert registry_content.count("skill_id: axignal-cinematic-webgl-scroll") == 1
    registry.write_text(registry_content, encoding="utf-8")

    git("add", *SHARED_PATHS)


def classify(path: str) -> str:
    if path in SHARED_PATHS:
        return "MERGED_EXPLICITLY"
    for selected in ATOMIC_PATHS:
        if path == selected or path.startswith(selected.rstrip("/") + "/"):
            return "WP1_CANONICAL_AUTHORITY"
    return "WP2_PRESERVED"


def write_ledger(
    controller_head: str,
    wp1_tree: str,
    wp2_tree: str,
    wp2_only: list[str],
    output: Path,
) -> None:
    wp1_changed = changed_paths(MERGE_BASE, WP1_HEAD)
    wp2_changed = changed_paths(MERGE_BASE, WP2_HEAD)
    overlap = sorted(wp1_changed & wp2_changed)
    resolutions = [{"path": path, "resolution": classify(path)} for path in overlap]
    selected = [
        path
        for path in sorted(wp1_changed)
        if classify(path) in {"WP1_CANONICAL_AUTHORITY", "MERGED_EXPLICITLY"}
    ]
    ledger = {
        "schema": "axignal.c0.canonical-reconciliation.v1",
        "contract_id": "AX-GE2E-CLOSURE-EXECUTION-002",
        "work_package": "C0_CANONICAL_RECONCILIATION",
        "controller_head": controller_head,
        "inputs": {
            "wp1": {"head": WP1_HEAD, "tree": wp1_tree, "role": "LANDING_AUTHORITY"},
            "wp2": {"head": WP2_HEAD, "tree": wp2_tree, "role": "FUNCTIONAL_BASE"},
            "merge_base": MERGE_BASE,
        },
        "policy": {
            "default": "WP2_PRESERVED",
            "landing_scopes": "WP1_CANONICAL_AUTHORITY",
            "shared_files": "MERGED_EXPLICITLY",
            "wp2_only_files_under_imported_directories": "WP2_PRESERVED",
            "source_prs_merged": False,
            "public_launch_authorized": False,
        },
        "atomic_paths": list(ATOMIC_PATHS),
        "shared_paths": list(SHARED_PATHS),
        "wp1_selected_changed_paths": selected,
        "wp2_only_paths_preserved": wp2_only,
        "overlap_count": len(overlap),
        "overlap_resolutions": resolutions,
        "state": "TREE_RECONCILED_AWAITING_EXACT_HEAD_MATRIX",
        "output_marker": "AX_C0_RECONCILIATION_TREE_PASS",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    git("add", str(output.relative_to(ROOT)))


def verify_tree() -> None:
    assert (ROOT / "apps/landing/lib/canonical-commercial-contract.ts").is_file()
    assert (ROOT / "docs/tasks/active/2026-08-04_axignal-e2e-blocker-ownership.v1.json").is_file()
    assert (ROOT / "scripts/verify_axignal_e2e_blocker_ownership.py").is_file()
    registry = (ROOT / "skills/registry.yaml").read_text(encoding="utf-8")
    assert registry.startswith("version: 0.4.0\n")
    assert registry.count("skill_id: axignal-gsap-ui-ux") == 1
    assert registry.count("skill_id: axignal-cinematic-webgl-scroll") == 1
    assert not git("ls-files", "-u")
    git("diff", "--check")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--controller-head", required=True)
    parser.add_argument(
        "--ledger",
        default="docs/tasks/active/2026-08-04_axignal-c0-canonical-reconciliation.v1.json",
    )
    args = parser.parse_args()

    controller_head = args.controller_head
    assert git("rev-parse", "HEAD") == controller_head
    wp1_tree = git("rev-parse", f"{WP1_HEAD}^{{tree}}")
    wp2_tree = git("rev-parse", f"{WP2_HEAD}^{{tree}}")
    assert len(wp1_tree) == 40 and git("cat-file", "-t", wp1_tree) == "tree"
    assert len(wp2_tree) == 40 and git("cat-file", "-t", wp2_tree) == "tree"
    assert git("merge-base", WP1_HEAD, WP2_HEAD) == MERGE_BASE
    git("merge-base", "--is-ancestor", WP2_HEAD, controller_head)

    git("merge", "-s", "ours", "--no-commit", "--no-ff", WP1_HEAD)
    wp2_only = restore_wp1_authority(controller_head)
    reconcile_shared_files()
    ledger_path = ROOT / args.ledger
    write_ledger(controller_head, wp1_tree, wp2_tree, wp2_only, ledger_path)
    verify_tree()

    print(
        json.dumps(
            {
                "status": "PASS",
                "marker": "AX_C0_RECONCILIATION_TREE_PASS",
                "controller_head": controller_head,
                "wp1_head": WP1_HEAD,
                "wp1_tree": wp1_tree,
                "wp2_head": WP2_HEAD,
                "wp2_tree": wp2_tree,
                "wp2_only_preserved": len(wp2_only),
                "ledger": str(ledger_path.relative_to(ROOT)),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
