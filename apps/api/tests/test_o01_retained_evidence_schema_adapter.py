from __future__ import annotations

import json
from pathlib import Path

import pytest

import verify_gate7_o01_retained_evidence_v8 as implementation
from verify_gate7_o01_retained_evidence_v8 import VerificationError
from verify_gate7_o01_retained_evidence_v10 import (
    INTERNAL_ALIAS,
    PUBLISHED_KEY,
    schema_aware_load_json,
)


def test_published_lag_key_is_adapted_in_memory(tmp_path: Path) -> None:
    path = tmp_path / "publication-lag-report.v0.1.json"
    original = {
        "status": "PASS",
        PUBLISHED_KEY: False,
    }
    path.write_text(json.dumps(original), encoding="utf-8")
    loaded = schema_aware_load_json(path)
    assert loaded[PUBLISHED_KEY] is False
    assert loaded[INTERNAL_ALIAS] is False
    assert json.loads(path.read_text(encoding="utf-8")) == original


@pytest.mark.parametrize(
    "name",
    ["final-result.v0.1.json", "campaign-console.json"],
)
def test_result_documents_are_adapted_without_file_mutation(
    tmp_path: Path,
    name: str,
) -> None:
    path = tmp_path / name
    original = {
        "status": "PASS",
        "lag": {PUBLISHED_KEY: False},
    }
    path.write_text(json.dumps(original), encoding="utf-8")
    loaded = schema_aware_load_json(path)
    assert loaded["lag"][INTERNAL_ALIAS] is False
    assert json.loads(path.read_text(encoding="utf-8")) == original


def test_console_and_final_result_normalise_identically(tmp_path: Path) -> None:
    original = {
        "status": "PASS",
        "lag": {PUBLISHED_KEY: False},
    }
    final_path = tmp_path / "final-result.v0.1.json"
    console_path = tmp_path / "campaign-console.json"
    final_path.write_text(json.dumps(original), encoding="utf-8")
    console_path.write_text(json.dumps(original), encoding="utf-8")
    assert schema_aware_load_json(final_path) == schema_aware_load_json(console_path)
    assert json.loads(final_path.read_text(encoding="utf-8")) == original
    assert json.loads(console_path.read_text(encoding="utf-8")) == original


def test_loader_remains_non_recursive_while_adapter_is_installed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "publication-lag-report.v0.1.json"
    original = {
        "status": "PASS",
        PUBLISHED_KEY: False,
    }
    path.write_text(json.dumps(original), encoding="utf-8")
    monkeypatch.setattr(implementation, "load_json", schema_aware_load_json)
    loaded = schema_aware_load_json(path)
    assert loaded[INTERNAL_ALIAS] is False
    assert json.loads(path.read_text(encoding="utf-8")) == original


def test_missing_published_key_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "publication-lag-report.v0.1.json"
    path.write_text(json.dumps({"status": "PASS"}), encoding="utf-8")
    with pytest.raises(VerificationError, match="Published lag key is missing"):
        schema_aware_load_json(path)


def test_enabled_exact_first_seen_claim_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "publication-lag-report.v0.1.json"
    path.write_text(json.dumps({PUBLISHED_KEY: True}), encoding="utf-8")
    with pytest.raises(VerificationError, match="claim enabled"):
        schema_aware_load_json(path)
