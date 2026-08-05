from pathlib import Path

SCRIPT = Path("apps/api/src/axignal_api/c4_axent_e2e.py")


def test_c4_e2e_composes_existing_research_and_axent_authorities() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert "tenant_private.research_runs" in source
    assert "/v1/research-runs/" in source
    assert "axignal.axent-research-context.v1" in source
    assert "/v1/subscriber-workspace/axent/conversations" in source
    assert "build_identity_assertion" in source


def test_c4_e2e_proves_persistence_isolation_and_retention() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert "AXENT ciphertext contains plaintext content" in source
    assert "same-tenant identity" in source
    assert "OTHER_TENANT_ID" in source
    assert "place_axent_legal_hold" in source
    assert "release_axent_legal_hold" in source
    assert "purge_due_axent_conversations" in source
    assert "VERIFY_AFTER_RESTART" in source


def test_c4_e2e_markers_are_phase_bounded() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert "AX_C4_RESEARCH_AXENT_PREPARE_PASS" in source
    assert "AX_C4_RESEARCH_AXENT_RUNTIME_PASS" in source
    assert "AX_C4_RESEARCH_AXENT_E2E_PASS" not in source
