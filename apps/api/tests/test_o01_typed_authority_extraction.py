from __future__ import annotations

import importlib.util
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import ModuleType

from axignal_api.o01_approval_renewal import AuthorityEnvelope

ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = ROOT / "scripts/extract_gate7_o01_typed_authority.py"
HEAD = "a" * 40
MANIFEST = f"sha256:{'b' * 64}"
NOW = datetime(2026, 8, 1, 12, 0, tzinfo=UTC)


def load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("o01_authority_extractor", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def decision(authority: str, *, head: str = HEAD) -> dict[str, object]:
    return {
        "authority": authority,
        "decision": "APPROVE",
        "scope": "Bounded private O01 evidence campaign",
        "manifest_digest": MANIFEST,
        "head_sha": head,
        "timestamp": NOW.isoformat().replace("+00:00", "Z"),
        "expiry": (NOW + timedelta(days=20)).isoformat().replace("+00:00", "Z"),
        "conditions": ["No public claims"],
        "signature": f"approved-authority:{authority.casefold()}",
    }


def comment(comment_id: int, payload: dict[str, object], login: str) -> dict[str, object]:
    return {
        "id": comment_id,
        "body": f"Typed decision:\n```json\n{json.dumps(payload)}\n```",
        "html_url": f"https://github.test/issues/1#issuecomment-{comment_id}",
        "created_at": NOW.isoformat(),
        "updated_at": NOW.isoformat(),
        "user": {"login": login},
    }


def write_comments(path: Path, values: list[dict[str, object]]) -> None:
    path.write_text(json.dumps(values), encoding="utf-8")


def test_complete_external_authority_envelope_is_materialised(tmp_path: Path) -> None:
    module = load_script()
    legal = tmp_path / "legal.json"
    privacy = tmp_path / "privacy.json"
    output = tmp_path / "authority.json"
    write_comments(legal, [comment(1, decision("LEGAL"), "legal-reviewer")])
    write_comments(
        privacy,
        [comment(2, decision("PRIVACY_DATA_RIGHTS"), "privacy-reviewer")],
    )

    result = module.extract(
        legal_comments_path=legal,
        privacy_comments_path=privacy,
        expected_head_sha=HEAD,
        expected_manifest_digest=MANIFEST,
        output_path=output,
    )

    assert result["status"] == "COMPLETE"
    assert result["output_written"] is True
    envelope = AuthorityEnvelope.model_validate_json(output.read_text())
    assert {item.authority for item in envelope.decisions} == {
        "LEGAL",
        "PRIVACY_DATA_RIGHTS",
    }
    assert result["sources"]["LEGAL"]["comment_author"] == "legal-reviewer"


def test_informal_and_wrong_head_comments_do_not_grant_authority(tmp_path: Path) -> None:
    module = load_script()
    legal = tmp_path / "legal.json"
    privacy = tmp_path / "privacy.json"
    output = tmp_path / "authority.json"
    write_comments(
        legal,
        [
            {"id": 1, "body": "Approved", "user": {"login": "someone"}},
            comment(2, decision("LEGAL", head="c" * 40), "legal-reviewer"),
        ],
    )
    write_comments(privacy, [])

    result = module.extract(
        legal_comments_path=legal,
        privacy_comments_path=privacy,
        expected_head_sha=HEAD,
        expected_manifest_digest=MANIFEST,
        output_path=output,
    )

    assert result["status"] == "MISSING"
    assert result["output_written"] is False
    assert not output.exists()


def test_latest_exact_bound_decision_supersedes_earlier_comment(tmp_path: Path) -> None:
    module = load_script()
    legal = tmp_path / "legal.json"
    privacy = tmp_path / "privacy.json"
    output = tmp_path / "authority.json"
    rejected = decision("LEGAL")
    rejected["decision"] = "REJECT"
    approved = decision("LEGAL")
    write_comments(
        legal,
        [
            comment(10, rejected, "legal-reviewer"),
            comment(11, approved, "legal-reviewer"),
        ],
    )
    write_comments(
        privacy,
        [comment(12, decision("PRIVACY_DATA_RIGHTS"), "privacy-reviewer")],
    )

    result = module.extract(
        legal_comments_path=legal,
        privacy_comments_path=privacy,
        expected_head_sha=HEAD,
        expected_manifest_digest=MANIFEST,
        output_path=output,
    )

    envelope = AuthorityEnvelope.model_validate_json(output.read_text())
    legal_decision = next(item for item in envelope.decisions if item.authority == "LEGAL")
    assert legal_decision.decision.value == "APPROVE"
    assert result["sources"]["LEGAL"]["issue_comment_id"] == 11
