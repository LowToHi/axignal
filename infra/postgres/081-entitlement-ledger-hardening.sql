-- AX-F9-T15 entitlement ledger authority hardening.
-- The application role may read tenant-scoped state and invoke typed functions,
-- but it may not mutate entitlement, reservation or event tables directly.

ALTER FUNCTION tenant_private.activate_controlled_trial(text, timestamptz)
  SECURITY DEFINER;
ALTER FUNCTION tenant_private.activate_controlled_trial(text, timestamptz)
  SET search_path TO pg_catalog;

ALTER FUNCTION tenant_private.reserve_ai_tokens(text, text, bigint, text, timestamptz)
  SECURITY DEFINER;
ALTER FUNCTION tenant_private.reserve_ai_tokens(text, text, bigint, text, timestamptz)
  SET search_path TO pg_catalog;

ALTER FUNCTION tenant_private.reconcile_ai_tokens(uuid, bigint, text, timestamptz)
  SECURITY DEFINER;
ALTER FUNCTION tenant_private.reconcile_ai_tokens(uuid, bigint, text, timestamptz)
  SET search_path TO pg_catalog;

ALTER FUNCTION tenant_private.release_ai_token_reservation(uuid, text, timestamptz)
  SECURITY DEFINER;
ALTER FUNCTION tenant_private.release_ai_token_reservation(uuid, text, timestamptz)
  SET search_path TO pg_catalog;

ALTER FUNCTION tenant_private.expire_current_trial(text, timestamptz)
  SECURITY DEFINER;
ALTER FUNCTION tenant_private.expire_current_trial(text, timestamptz)
  SET search_path TO pg_catalog;

REVOKE ALL ON FUNCTION tenant_private.activate_controlled_trial(text, timestamptz)
  FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.reserve_ai_tokens(text, text, bigint, text, timestamptz)
  FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.reconcile_ai_tokens(uuid, bigint, text, timestamptz)
  FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.release_ai_token_reservation(uuid, text, timestamptz)
  FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.expire_current_trial(text, timestamptz)
  FROM PUBLIC;

GRANT EXECUTE ON FUNCTION tenant_private.activate_controlled_trial(text, timestamptz)
  TO axignal_app;
GRANT EXECUTE ON FUNCTION tenant_private.reserve_ai_tokens(text, text, bigint, text, timestamptz)
  TO axignal_app;
GRANT EXECUTE ON FUNCTION tenant_private.reconcile_ai_tokens(uuid, bigint, text, timestamptz)
  TO axignal_app;
GRANT EXECUTE ON FUNCTION tenant_private.release_ai_token_reservation(uuid, text, timestamptz)
  TO axignal_app;
GRANT EXECUTE ON FUNCTION tenant_private.expire_current_trial(text, timestamptz)
  TO axignal_app;

REVOKE INSERT, UPDATE, DELETE, TRUNCATE
  ON tenant_private.organisation_entitlements
  FROM axignal_app;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE
  ON tenant_private.ai_token_reservations
  FROM axignal_app;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE
  ON tenant_private.entitlement_events
  FROM axignal_app;

-- Re-materialise the reservation function so an operation id is checked again
-- after the entitlement row lock. Concurrent retries of the same operation are
-- therefore idempotent rather than surfacing a unique-index race.
CREATE OR REPLACE FUNCTION tenant_private.reserve_ai_tokens(
  p_operation_id text,
  p_capability text,
  p_requested_tokens bigint,
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.ai_token_reservations
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.current_tenant_id();
  v_entitlement tenant_private.organisation_entitlements%ROWTYPE;
  v_existing tenant_private.ai_token_reservations%ROWTYPE;
  v_reservation tenant_private.ai_token_reservations%ROWTYPE;
BEGIN
  IF v_tenant_id IS NULL THEN RAISE EXCEPTION 'tenant_context_required'; END IF;
  IF p_requested_tokens <= 0 THEN RAISE EXCEPTION 'requested_tokens_must_be_positive'; END IF;

  SELECT * INTO v_existing
  FROM tenant_private.ai_token_reservations
  WHERE tenant_id = v_tenant_id AND operation_id = p_operation_id;
  IF FOUND THEN
    IF v_existing.capability <> p_capability
       OR v_existing.requested_tokens <> p_requested_tokens THEN
      RAISE EXCEPTION 'operation_id_conflict';
    END IF;
    RETURN v_existing;
  END IF;

  SELECT * INTO v_entitlement
  FROM tenant_private.organisation_entitlements
  WHERE tenant_id = v_tenant_id AND state = 'ACTIVE'
  FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'active_entitlement_required'; END IF;

  -- A concurrent request may have inserted the same operation while this
  -- transaction waited for the entitlement lock. Re-check under the lock.
  SELECT * INTO v_existing
  FROM tenant_private.ai_token_reservations
  WHERE tenant_id = v_tenant_id AND operation_id = p_operation_id;
  IF FOUND THEN
    IF v_existing.capability <> p_capability
       OR v_existing.requested_tokens <> p_requested_tokens THEN
      RAISE EXCEPTION 'operation_id_conflict';
    END IF;
    RETURN v_existing;
  END IF;

  IF v_entitlement.entitlement_kind = 'TRIAL' AND v_entitlement.expires_at <= p_now THEN
    RAISE EXCEPTION 'trial_expired';
  END IF;

  IF v_entitlement.entitlement_kind = 'TRIAL'
     AND v_entitlement.token_budget_total - v_entitlement.token_budget_consumed
         - v_entitlement.token_budget_reserved < p_requested_tokens THEN
    RAISE EXCEPTION 'trial_token_budget_exhausted';
  END IF;

  INSERT INTO tenant_private.ai_token_reservations (
    tenant_id, entitlement_id, operation_id, capability, requested_tokens,
    state, reserved_at, expires_at
  ) VALUES (
    v_tenant_id, v_entitlement.entitlement_id, p_operation_id, p_capability,
    p_requested_tokens, 'RESERVED', p_now, p_now + interval '5 minutes'
  ) RETURNING * INTO v_reservation;

  UPDATE tenant_private.organisation_entitlements
  SET token_budget_reserved = token_budget_reserved + p_requested_tokens,
      updated_at = p_now
  WHERE entitlement_id = v_entitlement.entitlement_id;

  INSERT INTO tenant_private.entitlement_events (
    tenant_id, entitlement_id, reservation_id, event_type, actor_subject, payload, occurred_at
  ) VALUES (
    v_tenant_id, v_entitlement.entitlement_id, v_reservation.reservation_id,
    'TOKENS_RESERVED', p_actor_subject,
    jsonb_build_object('operation_id', p_operation_id, 'capability', p_capability,
                       'requested_tokens', p_requested_tokens), p_now
  );
  RETURN v_reservation;
END
$$;

REVOKE ALL ON FUNCTION tenant_private.reserve_ai_tokens(text, text, bigint, text, timestamptz)
  FROM PUBLIC;
GRANT EXECUTE ON FUNCTION tenant_private.reserve_ai_tokens(text, text, bigint, text, timestamptz)
  TO axignal_app;
