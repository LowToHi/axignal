from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


AUDIT = load(
    "audit_actions_storage",
    ROOT / "scripts" / "ops" / "audit_actions_storage.py",
)
MIGRATE = load(
    "migrate_actions_retention",
    ROOT / "scripts" / "ops" / "migrate_actions_artifact_retention.py",
)

POLICY = {
    "schema": "axignal.actions-storage-policy.v1",
    "classification": {
        "contractual_name_fragments": ["attestation", "evidence-bundle"],
        "diagnostic_name_fragments": ["diagnostic", "playwright", "trace"],
    },
    "retention_days": {
        "ephemeral": 1,
        "diagnostic": 2,
        "contractual": 30,
    },
    "workflow_limits": {
        "maximum_upload_steps_per_workflow": 8,
        "maximum_artifacts_per_run": 12,
    },
    "inventory": {
        "preserve_recent_hours": 24,
        "top_families": 50,
    },
    "canonical_authorities": [],
    "explicit_protected_artifact_ids": [],
    "explicit_protected_run_ids": [],
}


class StoragePolicyToolsTest(unittest.TestCase):
    def make_workflow(self, root: Path, body: str) -> Path:
        path = root / ".github" / "workflows" / "fixture.yml"
        path.parent.mkdir(parents=True)
        path.write_text(body, encoding="utf-8")
        return path

    def test_migrator_inserts_diagnostic_retention(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = self.make_workflow(
                root,
                """name: Fixture
on: workflow_dispatch
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Upload diagnostics
        uses: actions/upload-artifact@v4
        with:
          name: playwright-diagnostics-${{ github.sha }}
          path: reports/
""",
            )
            transformed, changes = MIGRATE.transform(path, POLICY, root)
            self.assertIn("retention-days: 2", transformed)
            self.assertEqual(changes[0].action, "insert")
            self.assertEqual(changes[0].classification, "diagnostic")

    def test_migrator_reduces_ephemeral_retention(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = self.make_workflow(
                root,
                """name: Fixture
on: workflow_dispatch
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/upload-artifact@v4
        with:
          name: temporary-output
          path: out/
          retention-days: 90
""",
            )
            transformed, changes = MIGRATE.transform(path, POLICY, root)
            self.assertIn("retention-days: 1", transformed)
            self.assertNotIn("retention-days: 90", transformed)
            self.assertEqual(changes[0].action, "replace")

    def test_migrator_rejects_dynamic_retention(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = self.make_workflow(
                root,
                """name: Fixture
on: workflow_dispatch
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/upload-artifact@v4
        with:
          name: temporary-output
          path: out/
          retention-days: ${{ inputs.retention }}
""",
            )
            transformed, changes = MIGRATE.transform(path, POLICY, root)
            self.assertIn("${{ inputs.retention }}", transformed)
            self.assertEqual(changes[0].action, "dynamic-rejected")

    def test_auditor_detects_compact_upload_step(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = self.make_workflow(
                root,
                """name: Fixture
on:
  pull_request:
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/upload-artifact@v4
        with:
          name: trace-output
          path: trace.zip
""",
            )
            result = AUDIT.scan_workflow(path, POLICY, root)
            self.assertEqual(len(result.uploads), 1)
            self.assertEqual(result.uploads[0].classification, "diagnostic")
            self.assertEqual(result.uploads[0].issue, "missing-retention-days")
            self.assertTrue(result.pull_request)

    def test_family_normalization_removes_sha(self) -> None:
        family = AUDIT.normalize_family(
            "diagnostic-7c551728c7d750ee35b3607a3939df493f697592"
        )
        self.assertEqual(family, "diagnostic-{sha}")


if __name__ == "__main__":
    unittest.main()
