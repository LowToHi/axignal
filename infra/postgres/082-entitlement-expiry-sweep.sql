-- Persist an expired trial's READ_ONLY transition in its own transaction.
-- Callers execute this function before attempting a reservation so a later
-- fail-closed authorization error cannot roll back the lifecycle transition.

CREATE OR REPLACE FUNCTION tenant_private.expire_due_trial(
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.current_tenant_id();
  v_entitlement_id uuid;
BEGIN
  IF v_tenant_id IS NULL THEN
    RAISE EXCEPTION 'tenant_context_required';
  END IF;
  IF p_actor_subject IS NULL OR btrim(p_actor_subject) = '' THEN
    RAISE EXCEPTION 'actor_subject_required';
  END IF;

  UPDATE tenant_private.organisation_entitlements
  SET state = 'READ_ONLY', updated_at = p_now
  WHERE tenant_id = v_tenant_id
    AND entitlement_kind = 'TRIAL'
    AND state = 'ACTIVE'
    AND expires_at <= p_now
  RETURNING entitlement_id INTO v_entitlement_id;

  IF v_entitlement_id IS NULL THEN
    RETURN false;
  END IF;

  INSERT INTO tenant_private.entitlement_events (
    tenant_id,
    entitlement_id,
    event_type,
    actor_subject,
    payload,
    occurred_at
  ) VALUES (
    v_tenant_id,
    v_entitlement_id,
    'TRIAL_EXPIRED',
    p_actor_subject,
    jsonb_build_object('transition', 'READ_ONLY', 'trigger', 'PRE_AUTHORIZATION_SWEEP'),
    p_now
  );
  RETURN true;
END
$$;

REVOKE ALL ON FUNCTION tenant_private.expire_due_trial(text, timestamptz)
  FROM PUBLIC;
GRANT EXECUTE ON FUNCTION tenant_private.expire_due_trial(text, timestamptz)
  TO axignal_app;
