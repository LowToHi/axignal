-- C4 upgrade hardening for databases that observed the first AXENT adapter.
-- Removes the superseded non-identity signature and makes immediate deletion
-- deterministic across the API-to-database clock boundary.

DROP FUNCTION IF EXISTS tenant_private.append_axent_message_idempotent(
  uuid, text, text, text, text, text, timestamptz
);

CREATE OR REPLACE FUNCTION tenant_private.request_axent_conversation_deletion_for_identity(
  p_conversation_id uuid,
  p_identity_subject text,
  p_delete_after timestamptz,
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.axent_conversations
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.c3_require_tenant();
BEGIN
  PERFORM 1
  FROM tenant_private.axent_conversations
  WHERE tenant_id = v_tenant_id
    AND conversation_id = p_conversation_id
    AND identity_subject = p_identity_subject;
  IF NOT FOUND THEN RAISE EXCEPTION 'axent_conversation_not_found'; END IF;
  RETURN tenant_private.request_axent_conversation_deletion(
    p_conversation_id,
    greatest(p_delete_after, p_now),
    p_actor_subject,
    p_now
  );
END
$$;

REVOKE ALL ON FUNCTION tenant_private.request_axent_conversation_deletion_for_identity(
  uuid, text, timestamptz, text, timestamptz
) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION tenant_private.request_axent_conversation_deletion_for_identity(
  uuid, text, timestamptz, text, timestamptz
) TO axignal_app;
