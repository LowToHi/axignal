CREATE OR REPLACE FUNCTION tenant_private.start_prepared_identity_trial(
  p_user_id uuid,
  p_subject text,
  p_email text,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.organisation_entitlements
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.current_tenant_id();
  v_grant identity_private.trial_grants%ROWTYPE;
  v_entitlement tenant_private.organisation_entitlements%ROWTYPE;
BEGIN
  IF v_tenant_id IS NULL THEN RAISE EXCEPTION 'tenant_context_required'; END IF;

  SELECT * INTO v_grant
  FROM identity_private.trial_grants
  WHERE tenant_id = v_tenant_id
    AND requested_by_user_id = p_user_id
  FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'trial_grant_not_found'; END IF;

  SELECT * INTO v_entitlement
  FROM tenant_private.organisation_entitlements
  WHERE tenant_id = v_tenant_id AND entitlement_kind = 'TRIAL'
  ORDER BY created_at
  LIMIT 1;
  IF FOUND THEN RETURN v_entitlement; END IF;

  IF v_grant.state <> 'READY'
     OR v_grant.decision NOT IN ('ALLOW', 'ALLOW_RESTRICTED') THEN
    RAISE EXCEPTION 'trial_not_ready';
  END IF;

  SELECT * INTO v_entitlement
  FROM tenant_private.activate_controlled_trial(p_subject, p_now);

  PERFORM tenant_private.bootstrap_organisation_owner(
    p_subject, p_email, p_subject, p_now
  );

  UPDATE identity_private.trial_grants
  SET state = 'ACTIVE', started_at = p_now,
      expires_at = p_now + interval '7 days', updated_at = p_now
  WHERE trial_grant_id = v_grant.trial_grant_id;

  INSERT INTO identity_private.trial_usage_accounts (
    trial_grant_id, tenant_id, token_budget_total,
    cost_budget_microunits, max_concurrent_runs, updated_at
  ) VALUES (
    v_grant.trial_grant_id, v_tenant_id, v_grant.token_budget_ceiling,
    v_grant.cost_budget_microunits, v_grant.max_concurrent_runs, p_now
  );

  INSERT INTO identity_private.trial_abuse_events (
    trial_grant_id, user_id, tenant_id, event_type,
    decision, reason_codes, metadata, occurred_at
  ) VALUES (
    v_grant.trial_grant_id, p_user_id, v_tenant_id,
    'TRIAL_ACTIVATED_ON_FIRST_AI_REQUEST', v_grant.decision,
    v_grant.reason_codes,
    jsonb_build_object(
      'duration_days', 7,
      'token_budget_ceiling', v_grant.token_budget_ceiling,
      'cost_budget_microunits', v_grant.cost_budget_microunits
    ), p_now
  );

  RETURN v_entitlement;
END
$$;

CREATE OR REPLACE FUNCTION identity_private.reserve_trial_cost_from_tokens()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_entitlement tenant_private.organisation_entitlements%ROWTYPE;
  v_grant identity_private.trial_grants%ROWTYPE;
  v_account identity_private.trial_usage_accounts%ROWTYPE;
  v_cost bigint;
BEGIN
  SELECT * INTO v_entitlement
  FROM tenant_private.organisation_entitlements
  WHERE entitlement_id = NEW.entitlement_id;
  IF NOT FOUND OR v_entitlement.entitlement_kind <> 'TRIAL' THEN
    RETURN NEW;
  END IF;

  SELECT * INTO v_grant
  FROM identity_private.trial_grants
  WHERE tenant_id = NEW.tenant_id AND state = 'ACTIVE';
  IF NOT FOUND THEN RAISE EXCEPTION 'active_trial_grant_required'; END IF;

  SELECT * INTO v_account
  FROM identity_private.trial_usage_accounts
  WHERE trial_grant_id = v_grant.trial_grant_id
  FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'trial_usage_account_required'; END IF;

  v_cost := NEW.requested_tokens * v_grant.cost_microunits_per_token;
  IF v_account.token_budget_total
       - v_account.token_budget_reserved
       - v_account.token_budget_consumed < NEW.requested_tokens THEN
    RAISE EXCEPTION 'trial_risk_token_budget_exhausted';
  END IF;
  IF v_account.cost_budget_microunits
       - v_account.cost_reserved_microunits
       - v_account.cost_consumed_microunits < v_cost THEN
    RAISE EXCEPTION 'trial_cost_budget_exhausted';
  END IF;

  UPDATE identity_private.trial_usage_accounts
  SET token_budget_reserved = token_budget_reserved + NEW.requested_tokens,
      cost_reserved_microunits = cost_reserved_microunits + v_cost,
      updated_at = now()
  WHERE trial_grant_id = v_grant.trial_grant_id;

  INSERT INTO identity_private.trial_cost_reservations (
    trial_grant_id, tenant_id, token_reservation_id,
    requested_tokens, requested_cost_microunits, state, created_at
  ) VALUES (
    v_grant.trial_grant_id, NEW.tenant_id, NEW.reservation_id,
    NEW.requested_tokens, v_cost, 'RESERVED', now()
  );
  RETURN NEW;
END
$$;

DROP TRIGGER IF EXISTS trial_cost_reservation_on_token_reservation
  ON tenant_private.ai_token_reservations;
CREATE TRIGGER trial_cost_reservation_on_token_reservation
AFTER INSERT ON tenant_private.ai_token_reservations
FOR EACH ROW EXECUTE FUNCTION identity_private.reserve_trial_cost_from_tokens();

CREATE OR REPLACE FUNCTION identity_private.reconcile_trial_cost_from_tokens()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_cost_reservation identity_private.trial_cost_reservations%ROWTYPE;
  v_grant identity_private.trial_grants%ROWTYPE;
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
  IF NOT FOUND THEN RETURN NEW; END IF;

  SELECT * INTO v_grant
  FROM identity_private.trial_grants
  WHERE trial_grant_id = v_cost_reservation.trial_grant_id;

  v_actual_tokens := CASE
    WHEN NEW.state = 'RECONCILED' THEN coalesce(NEW.actual_tokens, 0)
    ELSE 0
  END;
  v_actual_cost := v_actual_tokens * v_grant.cost_microunits_per_token;

  UPDATE identity_private.trial_usage_accounts
  SET token_budget_reserved =
        token_budget_reserved - v_cost_reservation.requested_tokens,
      token_budget_consumed = token_budget_consumed + v_actual_tokens,
      cost_reserved_microunits =
        cost_reserved_microunits - v_cost_reservation.requested_cost_microunits,
      cost_consumed_microunits =
        cost_consumed_microunits + v_actual_cost,
      updated_at = now()
  WHERE trial_grant_id = v_cost_reservation.trial_grant_id;

  UPDATE identity_private.trial_cost_reservations
  SET actual_tokens = v_actual_tokens,
      actual_cost_microunits = v_actual_cost,
      state = NEW.state,
      reconciled_at = now()
  WHERE trial_cost_reservation_id =
    v_cost_reservation.trial_cost_reservation_id;
  RETURN NEW;
END
$$;

DROP TRIGGER IF EXISTS trial_cost_reconciliation_on_token_reservation
  ON tenant_private.ai_token_reservations;
CREATE TRIGGER trial_cost_reconciliation_on_token_reservation
AFTER UPDATE OF state, actual_tokens ON tenant_private.ai_token_reservations
FOR EACH ROW EXECUTE FUNCTION identity_private.reconcile_trial_cost_from_tokens();

CREATE OR REPLACE FUNCTION identity_private.govern_trial_research_concurrency()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_account identity_private.trial_usage_accounts%ROWTYPE;
  v_old_active boolean := false;
  v_new_active boolean := false;
BEGIN
  IF TG_OP = 'INSERT' THEN
    v_new_active := NEW.state IN (
      'QUEUED', 'RETRIEVING', 'PROPOSING', 'ADMISSION_PENDING'
    );
  ELSE
    v_old_active := OLD.state IN (
      'QUEUED', 'RETRIEVING', 'PROPOSING', 'ADMISSION_PENDING'
    );
    v_new_active := NEW.state IN (
      'QUEUED', 'RETRIEVING', 'PROPOSING', 'ADMISSION_PENDING'
    );
  END IF;

  SELECT * INTO v_account
  FROM identity_private.trial_usage_accounts
  WHERE tenant_id = NEW.tenant_id
  FOR UPDATE;
  IF NOT FOUND THEN RETURN NEW; END IF;

  IF NOT v_old_active AND v_new_active THEN
    IF v_account.active_runs >= v_account.max_concurrent_runs THEN
      RAISE EXCEPTION 'trial_concurrency_exhausted';
    END IF;
    UPDATE identity_private.trial_usage_accounts
    SET active_runs = active_runs + 1, updated_at = now()
    WHERE trial_grant_id = v_account.trial_grant_id;
  ELSIF v_old_active AND NOT v_new_active THEN
    UPDATE identity_private.trial_usage_accounts
    SET active_runs = greatest(active_runs - 1, 0), updated_at = now()
    WHERE trial_grant_id = v_account.trial_grant_id;
  END IF;
  RETURN NEW;
END
$$;

DROP TRIGGER IF EXISTS trial_research_concurrency_guard
  ON tenant_private.research_runs;
CREATE TRIGGER trial_research_concurrency_guard
BEFORE INSERT OR UPDATE OF state ON tenant_private.research_runs
FOR EACH ROW EXECUTE FUNCTION identity_private.govern_trial_research_concurrency();

REVOKE ALL ON ALL TABLES IN SCHEMA identity_private FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA identity_private FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.start_prepared_identity_trial(
  uuid, text, text, timestamptz
) FROM PUBLIC;

GRANT USAGE ON SCHEMA identity_private TO axignal_app;
GRANT EXECUTE ON FUNCTION identity_private.consume_rate_limit(
  text, text, integer, integer, timestamptz
) TO axignal_app;
GRANT EXECUTE ON FUNCTION identity_private.begin_email_challenge(
  text, text, text, text, text, text, text, text,
  boolean, timestamptz, timestamptz
) TO axignal_app;
GRANT EXECUTE ON FUNCTION identity_private.consume_signup_challenge(
  text, text, text, bigint, bigint, bigint, bigint, timestamptz
) TO axignal_app;
GRANT EXECUTE ON FUNCTION identity_private.resolve_bootstrap_ticket(
  text, text, timestamptz
) TO axignal_app;
GRANT EXECUTE ON FUNCTION identity_private.create_webauthn_challenge(
  text, text, text, uuid, uuid, text, text, timestamptz, timestamptz
) TO axignal_app;
GRANT EXECUTE ON FUNCTION identity_private.pending_webauthn_challenge(
  text, text, timestamptz
) TO axignal_app;
GRANT EXECUTE ON FUNCTION identity_private.credential_for_authentication(text)
  TO axignal_app;
GRANT EXECUTE ON FUNCTION identity_private.complete_passkey_registration(
  text, text, text, text, bigint, text[], text, boolean, text,
  text, text, text, text, text[], integer, integer, timestamptz
) TO axignal_app;
GRANT EXECUTE ON FUNCTION identity_private.complete_passkey_authentication(
  text, text, bigint, text, text, text, text, integer, integer, timestamptz
) TO axignal_app;
GRANT EXECUTE ON FUNCTION identity_private.resolve_identity_session(
  text, integer, timestamptz
) TO axignal_app;
GRANT EXECUTE ON FUNCTION identity_private.revoke_identity_session(
  text, text, timestamptz
) TO axignal_app;
GRANT EXECUTE ON FUNCTION identity_private.begin_recovery(
  text, text, text, timestamptz
) TO axignal_app;
GRANT EXECUTE ON FUNCTION identity_private.trial_status_for_tenant(uuid)
  TO axignal_app;
GRANT EXECUTE ON FUNCTION identity_private.approve_trial_step_up(
  uuid, uuid, text, text, text, bigint, bigint, timestamptz
) TO axignal_app;
GRANT EXECUTE ON FUNCTION tenant_private.start_prepared_identity_trial(
  uuid, text, text, timestamptz
) TO axignal_app;
