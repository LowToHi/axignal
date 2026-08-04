-- Close cost reservations created while a trial grant was active even when the
-- grant expires or is suspended before token reconciliation completes.
-- New reservations remain guarded by identity_private.reserve_trial_cost_from_tokens().

CREATE OR REPLACE FUNCTION identity_private.reconcile_trial_cost_from_tokens()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_grant identity_private.trial_grants%ROWTYPE;
  v_reserved_cost bigint;
  v_actual_cost bigint;
BEGIN
  IF OLD.state <> 'RESERVED' OR NEW.state NOT IN ('RECONCILED', 'RELEASED') THEN
    RETURN NEW;
  END IF;

  SELECT * INTO v_grant
  FROM identity_private.trial_grants
  WHERE tenant_id = NEW.tenant_id
  FOR UPDATE;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'trial_grant_required_for_settlement';
  END IF;

  v_reserved_cost := OLD.requested_tokens * v_grant.cost_microunits_per_token;
  v_actual_cost := COALESCE(NEW.actual_tokens, 0) * v_grant.cost_microunits_per_token;

  UPDATE identity_private.trial_usage_accounts
  SET cost_reserved_microunits = cost_reserved_microunits - v_reserved_cost,
      cost_consumed_microunits = cost_consumed_microunits + v_actual_cost,
      updated_at = COALESCE(NEW.reconciled_at, pg_catalog.now())
  WHERE tenant_id = NEW.tenant_id
    AND trial_grant_id = v_grant.trial_grant_id;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'trial_usage_account_required_for_settlement';
  END IF;

  RETURN NEW;
END
$$;

REVOKE ALL ON FUNCTION identity_private.reconcile_trial_cost_from_tokens()
  FROM PUBLIC;
