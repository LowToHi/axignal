-- Settle the economic trial ledger from the immutable cost reservation that
-- was created while admission was authorised. A later expiry, suspension or
-- paid lifecycle transition must not strand reserved budget, and a non-trial
-- token reservation must remain outside this trigger.
--
-- New trial reservations remain fail-closed under
-- identity_private.reserve_trial_cost_from_tokens().

CREATE OR REPLACE FUNCTION identity_private.reconcile_trial_cost_from_tokens()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_cost_reservation identity_private.trial_cost_reservations%ROWTYPE;
  v_actual_tokens bigint;
  v_actual_cost bigint;
BEGIN
  IF OLD.state <> 'RESERVED' OR NEW.state NOT IN ('RECONCILED', 'RELEASED') THEN
    RETURN NEW;
  END IF;

  SELECT * INTO v_cost_reservation
  FROM identity_private.trial_cost_reservations
  WHERE token_reservation_id = NEW.reservation_id
    AND state = 'RESERVED'
  FOR UPDATE;

  -- Paid and other non-trial reservations do not have a P25 cost reservation.
  IF NOT FOUND THEN
    RETURN NEW;
  END IF;

  v_actual_tokens := CASE
    WHEN NEW.state = 'RECONCILED' THEN COALESCE(NEW.actual_tokens, 0)
    ELSE 0
  END;
  v_actual_cost := (
    v_cost_reservation.requested_cost_microunits * v_actual_tokens
  ) / v_cost_reservation.requested_tokens;

  UPDATE identity_private.trial_usage_accounts
  SET token_budget_reserved =
        token_budget_reserved - v_cost_reservation.requested_tokens,
      token_budget_consumed = token_budget_consumed + v_actual_tokens,
      cost_reserved_microunits =
        cost_reserved_microunits - v_cost_reservation.requested_cost_microunits,
      cost_consumed_microunits = cost_consumed_microunits + v_actual_cost,
      updated_at = COALESCE(NEW.reconciled_at, pg_catalog.now())
  WHERE trial_grant_id = v_cost_reservation.trial_grant_id;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'trial_usage_account_required_for_settlement';
  END IF;

  UPDATE identity_private.trial_cost_reservations
  SET actual_tokens = v_actual_tokens,
      actual_cost_microunits = v_actual_cost,
      state = NEW.state,
      reconciled_at = COALESCE(NEW.reconciled_at, pg_catalog.now())
  WHERE trial_cost_reservation_id =
    v_cost_reservation.trial_cost_reservation_id;

  RETURN NEW;
END
$$;

REVOKE ALL ON FUNCTION identity_private.reconcile_trial_cost_from_tokens()
  FROM PUBLIC;
