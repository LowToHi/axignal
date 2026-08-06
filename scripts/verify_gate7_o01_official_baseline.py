from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CONTRACT_PATH = Path(
    "data/acceptance/approvals/"
    "AX-LIB-O01-official-online-baseline-contract.v0.1.json"
)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return value


def main() -> int:
    contract = load_json(CONTRACT_PATH)
    assert contract["task_id"] == "AX-GE2E-G7-O01-A"
    assert contract["gate_id"] == "PUBLIC-LAUNCH-GATE-7"
    assert contract["library_id"] == "AX-LIB-O01"
    assert contract["output"] == "O01_OFFICIAL_BASELINE_PASS"

    schedule = contract["schedule"]
    assert schedule["cadence"] == "DAILY"
    assert schedule["cron_utc"] == "41 6 * * *"

    network = contract["network_policy"]
    assert network["allowed_schemes"] == ["https"]
    assert network["allowed_ports"] == [443]
    assert set(network["allowed_hosts"]) == {
        "ted.europa.eu",
        "docs.ted.europa.eu",
        "eur-lex.europa.eu",
    }
    assert network["max_redirects"] <= 3
    assert network["max_response_bytes"] <= 5 * 1024 * 1024
    assert network["timeout_seconds"] <= 20
    assert network["require_all_resolved_addresses_global"] is True
    assert network["pin_connection_to_validated_address"] is True
    assert network["allow_url_credentials"] is False
    assert network["allow_proxy_environment"] is False

    documents = contract["official_documents"]
    assert len(documents) == 3
    assert {item["document_id"] for item in documents} == {
        "ted-legal-notice",
        "ted-search-api-3.0",
        "commission-decision-2011-833-eu",
    }
    for document in documents:
        assert document["url"].startswith("https://")
        assert document["publisher"]
        assert len(document["critical_anchors"]) >= 3
        assert set(document["content_types"]).issubset(
            {"text/html", "application/xhtml+xml"}
        )

    retention = contract["retention"]
    assert retention == {
        "artifact_retention_days": 30,
        "artifact_safety_margin_days": 3,
        "evidence_freshness_days": 30,
    }

    invariants = contract["baseline_invariants"]
    assert invariants == {
        "automatic_human_approval": False,
        "automatic_human_signature": False,
        "campaign_authority": False,
        "evidence_expiry": "VALID",
        "first_observation_change_class": "BASELINE_ESTABLISHED",
        "official_online_baseline": "PRESENT",
        "official_terms_available": True,
        "permissions_generated": False,
        "public_launch": "NO_GO",
        "source_admission": False,
    }

    result = {
        "status": "PASS",
        "output": "O01_OFFICIAL_BASELINE_CONTRACT_PASS",
        "task_id": contract["task_id"],
        "documents": len(documents),
        "official_hosts": len(network["allowed_hosts"]),
        "automatic_human_signature": False,
        "automatic_human_approval": False,
        "campaign_authority": False,
        "public_launch": "NO_GO",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
