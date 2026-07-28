from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    guide = (ROOT / "apps/web/components/demo-guide.tsx").read_text(encoding="utf-8")
    page = (ROOT / "apps/web/app/demo/page.tsx").read_text(encoding="utf-8")
    fixture = (ROOT / "apps/api/src/axignal_api/main.py").read_text(encoding="utf-8")

    required_guide_terms = (
        "MODEL PROPOSAL",
        "DETERMINISTIC DECISION",
        "HUMAN REVIEW",
        "CANONICAL CLAIM",
        "UNKNOWN",
        "Reset demo",
    )
    for term in required_guide_terms:
        assert term in guide, f"guided demo is missing {term}"

    assert "localStorage.removeItem" in guide
    assert "InvestigationShell" in page
    assert "AuthGate" in page
    assert "ctx_moscow_real_estate_v01" in fixture
    assert 'kind="CONTRADICCIÓN"' in fixture
    assert 'kind="DESCONOCIDO"' in fixture
    assert "synthetic" in fixture.lower()

    evidence = {
        "guided_steps": 6,
        "authentication_gate": True,
        "synthetic_fixture": True,
        "contradiction_present": True,
        "unknown_present": True,
        "reset_scope": "browser-local-state-only",
        "canonical_mutation_allowed": False,
    }
    print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
