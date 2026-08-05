from pathlib import Path


def test_c4_upgrade_hardening_removes_old_signature_and_clamps_delete_time() -> None:
    migration = Path("infra/postgres/142-c4-axent-upgrade-hardening.sql").read_text()
    assert "DROP FUNCTION IF EXISTS tenant_private.append_axent_message_idempotent" in migration
    assert "greatest(p_delete_after, p_now)" in migration
    assert "request_axent_conversation_deletion_for_identity" in migration
    assert "TO axignal_app" in migration
