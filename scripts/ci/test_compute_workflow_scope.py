#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/ci/compute_workflow_scope.py"
MANIFEST = ROOT / ".github/ci/workflow-scope.json"


class ScopeTests(unittest.TestCase):
    def run_scope(
        self,
        group: str,
        changed: list[str],
        *,
        labels: list[str] | None = None,
    ) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            changed_path = tmp_path / "changed.txt"
            changed_path.write_text("\n".join(changed) + "\n", encoding="utf-8")
            output_path = tmp_path / "output.txt"
            env = os.environ.copy()
            env["GITHUB_OUTPUT"] = str(output_path)
            subprocess.run(
                [
                    "python",
                    str(SCRIPT),
                    "--manifest",
                    str(MANIFEST),
                    "--group",
                    group,
                    "--changed-files",
                    str(changed_path),
                    "--labels-json",
                    json.dumps(labels or []),
                ],
                check=True,
                cwd=tmp_path,
                env=env,
                capture_output=True,
                text=True,
            )
            return json.loads(
                (tmp_path / f"ci-scope-{group}.json").read_text(encoding="utf-8")
            )

    def test_document_only_keeps_runtime_heavy_suites_off(self) -> None:
        decision = self.run_scope("runtime", ["docs/tasks/active/example.md"])
        self.assertFalse(decision["full_matrix"])
        self.assertFalse(any(decision["selected"].values()))

    def test_contract_validation_is_always_selected(self) -> None:
        decision = self.run_scope("core", ["README.md"])
        self.assertTrue(decision["selected"]["contract_validation"])
        self.assertFalse(decision["selected"]["e2e_technical_audit"])

    def test_frontend_delta_selects_frontend_and_viewports(self) -> None:
        decision = self.run_scope("core", ["apps/web/src/example.tsx"])
        self.assertTrue(decision["selected"]["frontend_unit_tests"])
        self.assertTrue(decision["selected"]["subscriber_viewport_matrix"])

    def test_architecture_change_forces_entire_group(self) -> None:
        decision = self.run_scope("domain", [".github/ci/workflow-scope.json"])
        self.assertTrue(decision["full_matrix"])
        self.assertTrue(all(decision["selected"].values()))

    def test_full_matrix_label_forces_entire_group(self) -> None:
        decision = self.run_scope(
            "runtime", ["README.md"], labels=["ci:full-matrix"]
        )
        self.assertTrue(decision["full_matrix"])
        self.assertTrue(all(decision["selected"].values()))


if __name__ == "__main__":
    unittest.main()
