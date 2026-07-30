#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import io
import json
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "data/ontology/p02-rollback-plan.v0.1.json"


def run_git(*args: str, capture_bytes: bool = False) -> bytes | str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=not capture_bytes,
    )
    return result.stdout


def export_tree(revision: str, destination: Path) -> None:
    archive = run_git("archive", "--format=tar", revision, capture_bytes=True)
    assert isinstance(archive, bytes)
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as bundle:
        bundle.extractall(destination, filter="data")


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tree_manifest(root: Path) -> dict[str, str]:
    manifest: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            manifest[path.relative_to(root).as_posix()] = (
                "symlink:" + path.readlink().as_posix()
            )
        elif path.is_file():
            manifest[path.relative_to(root).as_posix()] = file_digest(path)
    return manifest


assert PLAN_PATH.is_file(), f"missing {PLAN_PATH.relative_to(ROOT)}"
plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
assert plan["task_id"] == "AX-GE2E-P02-T01"
baseline = plan["baseline_sha"]

subprocess.run(
    ["git", "merge-base", "--is-ancestor", baseline, "HEAD"],
    cwd=ROOT,
    check=True,
)

changed_output = run_git("diff", "--name-only", f"{baseline}..HEAD")
assert isinstance(changed_output, str)
changed_paths = {line for line in changed_output.splitlines() if line}
expected_changed = set(plan["expected_changed_paths"])
assert changed_paths == expected_changed, {
    "unexpected": sorted(changed_paths - expected_changed),
    "missing": sorted(expected_changed - changed_paths),
}

for path in plan["remove_paths"]:
    exists_at_baseline = subprocess.run(
        ["git", "cat-file", "-e", f"{baseline}:{path}"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0
    assert not exists_at_baseline, f"remove path existed at baseline: {path}"
    assert (ROOT / path).is_file(), f"current remove path missing: {path}"

for path in plan["restore_paths"]:
    subprocess.run(
        ["git", "cat-file", "-e", f"{baseline}:{path}"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    assert (ROOT / path).is_file(), f"current restore path missing: {path}"

for path in plan["preserved_authority_paths"]:
    baseline_blob = run_git("rev-parse", f"{baseline}:{path}")
    current_blob = run_git("rev-parse", f"HEAD:{path}")
    assert baseline_blob == current_blob, f"authority drift detected: {path}"

with tempfile.TemporaryDirectory(prefix="axignal-p02-rollback-") as temp_dir:
    temp_root = Path(temp_dir)
    baseline_tree = temp_root / "baseline"
    candidate_tree = temp_root / "candidate"
    baseline_tree.mkdir()
    candidate_tree.mkdir()

    export_tree(baseline, baseline_tree)
    export_tree("HEAD", candidate_tree)

    for relative in plan["remove_paths"]:
        target = candidate_tree / relative
        assert target.exists() or target.is_symlink(), f"rollback target absent: {relative}"
        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(target)
        else:
            target.unlink()

    for relative in plan["restore_paths"]:
        source = baseline_tree / relative
        target = candidate_tree / relative
        assert source.is_file(), f"baseline restore source absent: {relative}"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    baseline_manifest = tree_manifest(baseline_tree)
    rollback_manifest = tree_manifest(candidate_tree)
    assert rollback_manifest == baseline_manifest, {
        "extra_after_rollback": sorted(
            set(rollback_manifest) - set(baseline_manifest)
        ),
        "missing_after_rollback": sorted(
            set(baseline_manifest) - set(rollback_manifest)
        ),
        "content_drift": sorted(
            path
            for path in set(baseline_manifest) & set(rollback_manifest)
            if baseline_manifest[path] != rollback_manifest[path]
        ),
    }

    manifest_digest = hashlib.sha256(
        json.dumps(baseline_manifest, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

print(
    json.dumps(
        {
            "status": "PASS",
            "task_id": plan["task_id"],
            "baseline_sha": baseline,
            "changed_paths": len(changed_paths),
            "removed_draft_artifacts": len(plan["remove_paths"]),
            "restored_baseline_files": len(plan["restore_paths"]),
            "preserved_authority_files": len(plan["preserved_authority_paths"]),
            "residual_paths": 0,
            "rolled_back_tree_equals_baseline": True,
            "baseline_manifest_sha256": manifest_digest,
        },
        sort_keys=True,
    )
)
