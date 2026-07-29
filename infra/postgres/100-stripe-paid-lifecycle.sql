-- AX-F9-T15 explicit paid selection and Stripe sandbox lifecycle.
-- No trial transition invokes Stripe. Paid access can only be activated by a
-- verified provider event processed through the isolated billing role.

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'axignal_billing_worker') THEN
    CREATE ROLE axignal_billing_worker NOLOGIN;
  END IF;
END
$$;

GRANT axignal_billing_worker TO axignal;
GRANT USAGE ON SCHEMA axignal_global, tenant_private TO axignal_billing_worker;

CREATE TABLE IF NOT EXISTS tenant_private.billing_plan_selections (
  selection_id uuid PRIMARY KEY DEFAULT public.gen_random_uuid(),
  tenant_id uuid NOT NULL,
  operation_id text NOT NULL CHECK (length(operation_id) BETWEEN 8 AND 200),
  provider text NOT NULL DEFAULT 'STRIPE' CHECK (provider = 'STRIPE'),
  provider_account_id text NOT NULL,
  plan_code text NOT NULL CHECK (plan_code IN ('PROFESSIONAL_MONTHLY', 'TEAM_MONTHLY')),
  pending_plan_code text CHECK (pending_plan_code IN ('PROFESSIONAL_MONTHLY', 'TEAM_MONTHLY')),
  state text NOT NULL CHECK (state IN (
    'SELECTED', 'CHECKOUT_CREATED', 'CHECKOUT_COMPLETED', 'ACTIVE',
    'UPGRADE_PENDING', 'CANCEL_PENDING', 'CANCEL_AT_PERIOD_END',
    'SUSPENDED', 'CANCELLED', 'FAILED', 'ROLLED_BACK'
  )),
  stripe_checkout_session_id text UNIQUE,
  stripe_customer_id text,
  stripe_subscription_id text UNIQUE,
  stripe_subscription_item_id text,
  stripe_price_id text,
  pending_stripe_price_id text,
  current_period_end timestamptz,
  cancel_at_period_end boolean NOT NULL DEFAULT false,
  selected_by text NOT NULL,
  selected_at timestamptz NOT NULL,
  last_provider_event_created_at timestamptz,
  last_provider_event_id text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, operation_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS billing_one_nonterminal_selection_per_tenant_idx
  ON tenant_private.billing_plan_selections (tenant_id)
  WHERE state NOT IN ('CANCELLED', 'FAILED', 'ROLLED_BACK');

CREATE TABLE IF NOT EXISTS axignal_global.stripe_webhook_receipts (
  provider_event_id text PRIMARY KEY,
  tenant_id uuid NOT NULL,
  selection_id uuid NOT NULL REFERENCES tenant_private.billing_plan_selections(selection_id),
  event_type text NOT NULL,
  event_created_at timestamptz NOT NULL,
  livemode boolean NOT NULL,
  provider_account_id text NOT NULL,
  payload_digest text NOT NULL CHECK (payload_digest ~ '^[0-9a-f]{64}$'),
  disposition text NOT NULL CHECK (disposition IN ('APPLIED', 'STALE', 'IGNORED')),
  received_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tenant_private.payment_ledger_entries (
  ledger_entry_id uuid PRIMARY KEY DEFAULT public.gen_random_uuid(),
  tenant_id uuid NOT NULL,
  selection_id uuid NOT NULL REFERENCES tenant_private.billing_plan_selections(selection_id),
  provider_event_id text,
  ledger_event_type text NOT NULL,
  plan_code text,
  amount_minor bigint CHECK (amount_minor IS NULL OR amount_minor >= 0),
  currency text CHECK (currency IS NULL OR currency ~ '^[A-Z]{3}$'),
  previous_state text,
  new_state text,
  payload_digest text CHECK (payload_digest IS NULL OR payload_digest ~ '^[0-9a-f]{64}$'),
  actor_subject text NOT NULL,
  occurred_at timestamptz NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (provider_event_id, ledger_event_type)
);

ALTER TABLE tenant_private.organisation_entitlements
  ADD COLUMN IF NOT EXISTS billing_selection_id uuid
  REFERENCES tenant_private.billing_plan_selections(selection_id);

CREATE UNIQUE INDEX IF NOT EXISTS organisation_paid_selection_idx
  ON tenant_private.organisation_entitlements (billing_selection_id)
  WHERE billing_selection_id IS NOT NULL;

CREATE OR REPLACE FUNCTION tenant_private.reject_billing_audit_mutation()
RETURNS trigger
LANGUAGE plpgsql
SET search_path TO pg_catalog
AS $$
BEGIN
  RAISE EXCEPTION 'AXIGNAL billing audit records are append-only';
END
$$;

DROP TRIGGER IF EXISTS payment_ledger_entries_immutable
  ON tenant_private.payment_ledger_entries;
CREATE TRIGGER payment_ledger_entries_immutable
BEFORE UPDATE OR DELETE ON tenant_private.payment_ledger_entries
FOR EACH ROW EXECUTE FUNCTION tenant_private.reject_billing_audit_mutation();

DROP TRIGGER IF EXISTS stripe_webhook_receipts_immutable
  ON axignal_global.stripe_webhook_receipts;
CREATE TRIGGER stripe_webhook_receipts_immutable
BEFORE UPDATE OR DELETE ON axignal_global.stripe_webhook_receipts
FOR EACH ROW EXECUTE FUNCTION tenant_private.reject_billing_audit_mutation();

ALTER TABLE tenant_private.billing_plan_selections ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.billing_plan_selections FORCE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.payment_ledger_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.payment_ledger_entries FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS billing_plan_selections_tenant_isolation
  ON tenant_private.billing_plan_selections;
CREATE POLICY billing_plan_selections_tenant_isolation
  ON tenant_private.billing_plan_selections
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

DROP POLICY IF EXISTS payment_ledger_entries_tenant_isolation
  ON tenant_private.payment_ledger_entries;
CREATE POLICY payment_ledger_entries_tenant_isolation
  ON tenant_private.payment_ledger_entries
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

CREATE OR REPLACE FUNCTION tenant_private.request_paid_plan_selection(
  p_operation_id text,
  p_plan_code text,
  p_provider_account_id text,
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.billing_plan_selections
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.current_tenant_id();
  v_existing tenant_private.billing_plan_selections%ROWTYPE;
  v_row tenant_private.billing_plan_selections%ROWTYPE;
BEGIN
  IF v_tenant_id IS NULL THEN RAISE EXCEPTION 'tenant_context_required'; END IF;
  IF p_operation_id IS NULL OR length(p_operation_id) < 8 THEN
    RAISE EXCEPTION 'billing_operation_id_required';
  END IF;
  IF p_plan_code NOT IN ('PROFESSIONAL_MONTHLY', 'TEAM_MONTHLY') THEN
    RAISE EXCEPTION 'unsupported_paid_plan';
  END IF;
  IF p_provider_account_id IS NULL OR btrim(p_provider_account_id) = '' THEN
    RAISE EXCEPTION 'provider_account_required';
  END IF;
  IF p_actor_subject IS NULL OR btrim(p_actor_subject) = '' THEN
    RAISE EXCEPTION 'actor_subject_required';
  END IF;

  SELECT * INTO v_existing
  FROM tenant_private.billing_plan_selections
  WHERE tenant_id = v_tenant_id AND operation_id = p_operation_id;
  IF FOUND THEN
    IF v_existing.plan_code <> p_plan_code
       OR v_existing.provider_account_id <> p_provider_account_id THEN
      RAISE EXCEPTION 'billing_operation_id_conflict';
    END IF;
    RETURN v_existing;
  END IF;

  IF EXISTS (
    SELECT 1 FROM tenant_private.organisation_entitlements
    WHERE tenant_id = v_tenant_id
      AND entitlement_kind = 'PAID_MONTHLY'
      AND state IN ('ACTIVE', 'SUSPENDED')
  ) THEN
    RAISE EXCEPTION 'paid_entitlement_already_exists';
  END IF;

  INSERT INTO tenant_private.billing_plan_selections (
    tenant_id, operation_id, provider_account_id, plan_code, state,
    selected_by, selected_at
  ) VALUES (
    v_tenant_id, p_operation_id, p_provider_account_id, p_plan_code,
    'SELECTED', p_actor_subject, p_now
  ) RETURNING * INTO v_row;

  INSERT INTO tenant_private.payment_ledger_entries (
    tenant_id, selection_id, ledger_event_type, plan_code,
    previous_state, new_state, actor_subject, occurred_at
  ) VALUES (
    v_tenant_id, v_row.selection_id, 'PAID_PLAN_EXPLICITLY_SELECTED', p_plan_code,
    NULL, 'SELECTED', p_actor_subject, p_now
  );
  RETURN v_row;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.mark_checkout_session_created(
  p_selection_id uuid,
  p_checkout_session_id text,
  p_price_id text,
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.billing_plan_selections
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.current_tenant_id();
  v_row tenant_private.billing_plan_selections%ROWTYPE;
BEGIN
  IF v_tenant_id IS NULL THEN RAISE EXCEPTION 'tenant_context_required'; END IF;
  SELECT * INTO v_row
  FROM tenant_private.billing_plan_selections
  WHERE tenant_id = v_tenant_id AND selection_id = p_selection_id
  FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'billing_selection_not_found'; END IF;
  IF v_row.state NOT IN ('SELECTED', 'CHECKOUT_CREATED') THEN
    RAISE EXCEPTION 'billing_selection_not_checkout_eligible';
  END IF;
  IF v_row.stripe_checkout_session_id IS NOT NULL
     AND v_row.stripe_checkout_session_id <> p_checkout_session_id THEN
    RAISE EXCEPTION 'checkout_session_conflict';
  END IF;
  UPDATE tenant_private.billing_plan_selections
  SET state = 'CHECKOUT_CREATED', stripe_checkout_session_id = p_checkout_session_id,
      stripe_price_id = p_price_id, updated_at = p_now
  WHERE selection_id = p_selection_id
  RETURNING * INTO v_row;
  RETURN v_row;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.request_paid_plan_upgrade(
  p_target_plan_code text,
  p_target_price_id text,
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.billing_plan_selections
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.current_tenant_id();
  v_row tenant_private.billing_plan_selections%ROWTYPE;
BEGIN
  IF v_tenant_id IS NULL THEN RAISE EXCEPTION 'tenant_context_required'; END IF;
  IF p_target_plan_code <> 'TEAM_MONTHLY' THEN RAISE EXCEPTION 'unsupported_upgrade'; END IF;
  SELECT * INTO v_row
  FROM tenant_private.billing_plan_selections
  WHERE tenant_id = v_tenant_id AND state = 'ACTIVE'
  FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'active_billing_subscription_required'; END IF;
  IF v_row.plan_code <> 'PROFESSIONAL_MONTHLY' THEN RAISE EXCEPTION 'upgrade_path_not_allowed'; END IF;
  UPDATE tenant_private.billing_plan_selections
  SET pending_plan_code = p_target_plan_code,
      pending_stripe_price_id = p_target_price_id,
      state = 'UPGRADE_PENDING', updated_at = p_now
  WHERE selection_id = v_row.selection_id
  RETURNING * INTO v_row;
  INSERT INTO tenant_private.payment_ledger_entries (
    tenant_id, selection_id, ledger_event_type, plan_code,
    previous_state, new_state, actor_subject, occurred_at
  ) VALUES (
    v_tenant_id, v_row.selection_id, 'PAID_UPGRADE_EXPLICITLY_REQUESTED',
    p_target_plan_code, 'ACTIVE', 'UPGRADE_PENDING', p_actor_subject, p_now
  );
  RETURN v_row;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.request_paid_cancellation(
  p_cancel_at_period_end boolean,
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.billing_plan_selections
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.current_tenant_id();
  v_row tenant_private.billing_plan_selections%ROWTYPE;
BEGIN
  IF v_tenant_id IS NULL THEN RAISE EXCEPTION 'tenant_context_required'; END IF;
  SELECT * INTO v_row
  FROM tenant_private.billing_plan_selections
  WHERE tenant_id = v_tenant_id
    AND state IN ('ACTIVE', 'CANCEL_AT_PERIOD_END', 'SUSPENDED')
  FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'active_billing_subscription_required'; END IF;
  UPDATE tenant_private.billing_plan_selections
  SET state = 'CANCEL_PENDING', cancel_at_period_end = p_cancel_at_period_end,
      updated_at = p_now
  WHERE selection_id = v_row.selection_id
  RETURNING * INTO v_row;
  INSERT INTO tenant_private.payment_ledger_entries (
    tenant_id, selection_id, ledger_event_type, plan_code,
    previous_state, new_state, actor_subject, occurred_at
  ) VALUES (
    v_tenant_id, v_row.selection_id,
    CASE WHEN p_cancel_at_period_end
      THEN 'PAID_CANCELLATION_AT_PERIOD_END_REQUESTED'
      ELSE 'PAID_IMMEDIATE_CANCELLATION_REQUESTED' END,
    v_row.plan_code, v_row.state, 'CANCEL_PENDING', p_actor_subject, p_now
  );
  RETURN v_row;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.release_billing_reservations(
  p_tenant_id uuid,
  p_entitlement_id uuid,
  p_now timestamptz
)
RETURNS bigint
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_released bigint := 0;
BEGIN
  SELECT COALESCE(sum(requested_tokens), 0) INTO v_released
  FROM tenant_private.ai_token_reservations
  WHERE tenant_id = p_tenant_id
    AND entitlement_id = p_entitlement_id
    AND state = 'RESERVED';

  UPDATE tenant_private.ai_token_reservations
  SET state = 'RELEASED', actual_tokens = 0, reconciled_at = p_now
  WHERE tenant_id = p_tenant_id
    AND entitlement_id = p_entitlement_id
    AND state = 'RESERVED';

  UPDATE tenant_private.organisation_entitlements
  SET token_budget_reserved = 0, updated_at = p_now
  WHERE entitlement_id = p_entitlement_id;
  RETURN v_released;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.apply_stripe_billing_event(
  p_event_id text,
  p_event_type text,
  p_event_created_at timestamptz,
  p_livemode boolean,
  p_payload_digest text,
  p_provider_account_id text,
  p_selection_id uuid,
  p_checkout_session_id text,
  p_customer_id text,
  p_subscription_id text,
  p_subscription_item_id text,
  p_price_id text,
  p_plan_code text,
  p_subscription_status text,
  p_current_period_end timestamptz,
  p_cancel_at_period_end boolean,
  p_amount_minor bigint,
  p_currency text,
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_existing axignal_global.stripe_webhook_receipts%ROWTYPE;
  v_row tenant_private.billing_plan_selections%ROWTYPE;
  v_paid tenant_private.organisation_entitlements%ROWTYPE;
  v_trial tenant_private.organisation_entitlements%ROWTYPE;
  v_previous_state text;
  v_new_state text;
  v_disposition text := 'APPLIED';
BEGIN
  IF p_livemode THEN RAISE EXCEPTION 'live_stripe_event_forbidden'; END IF;
  IF p_payload_digest !~ '^[0-9a-f]{64}$' THEN RAISE EXCEPTION 'payload_digest_invalid'; END IF;

  SELECT * INTO v_existing
  FROM axignal_global.stripe_webhook_receipts
  WHERE provider_event_id = p_event_id;
  IF FOUND THEN
    IF v_existing.payload_digest <> p_payload_digest THEN
      RAISE EXCEPTION 'stripe_event_id_payload_conflict';
    END IF;
    RETURN jsonb_build_object('disposition', 'DUPLICATE', 'selection_id', v_existing.selection_id);
  END IF;

  SELECT * INTO v_row
  FROM tenant_private.billing_plan_selections
  WHERE (p_selection_id IS NOT NULL AND selection_id = p_selection_id)
     OR (p_subscription_id IS NOT NULL AND stripe_subscription_id = p_subscription_id)
     OR (p_checkout_session_id IS NOT NULL AND stripe_checkout_session_id = p_checkout_session_id)
  ORDER BY created_at DESC
  LIMIT 1
  FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'billing_selection_not_found_for_event'; END IF;
  IF v_row.provider_account_id <> p_provider_account_id THEN
    RAISE EXCEPTION 'stripe_account_mismatch';
  END IF;

  v_previous_state := v_row.state;
  IF v_row.last_provider_event_created_at IS NOT NULL
     AND p_event_created_at < v_row.last_provider_event_created_at THEN
    v_disposition := 'STALE';
  ELSIF v_row.state IN ('CANCELLED', 'ROLLED_BACK')
     AND p_event_type IN ('customer.subscription.created', 'customer.subscription.updated') THEN
    v_disposition := 'STALE';
  ELSIF p_event_type = 'checkout.session.completed' THEN
    UPDATE tenant_private.billing_plan_selections
    SET state = 'CHECKOUT_COMPLETED',
        stripe_checkout_session_id = COALESCE(p_checkout_session_id, stripe_checkout_session_id),
        stripe_customer_id = COALESCE(p_customer_id, stripe_customer_id),
        stripe_subscription_id = COALESCE(p_subscription_id, stripe_subscription_id),
        last_provider_event_created_at = p_event_created_at,
        last_provider_event_id = p_event_id,
        updated_at = p_now
    WHERE selection_id = v_row.selection_id
    RETURNING * INTO v_row;
  ELSIF p_event_type IN ('customer.subscription.created', 'customer.subscription.updated') THEN
    IF p_subscription_status = 'trialing' THEN RAISE EXCEPTION 'stripe_trial_forbidden'; END IF;
    IF p_plan_code IS NULL THEN RAISE EXCEPTION 'stripe_plan_mapping_required'; END IF;
    IF v_row.pending_plan_code IS NOT NULL THEN
      IF p_plan_code <> v_row.pending_plan_code THEN RAISE EXCEPTION 'stripe_upgrade_plan_mismatch'; END IF;
    ELSIF p_plan_code <> v_row.plan_code THEN
      RAISE EXCEPTION 'stripe_selected_plan_mismatch';
    END IF;

    IF p_subscription_status IN ('active', 'past_due', 'unpaid') THEN
      IF p_subscription_status = 'active' THEN
        SELECT * INTO v_trial
        FROM tenant_private.organisation_entitlements
        WHERE tenant_id = v_row.tenant_id AND entitlement_kind = 'TRIAL' AND state = 'ACTIVE'
        FOR UPDATE;
        IF FOUND THEN
          PERFORM tenant_private.release_billing_reservations(
            v_row.tenant_id, v_trial.entitlement_id, p_now
          );
          UPDATE tenant_private.organisation_entitlements
          SET state = 'READ_ONLY', updated_at = p_now
          WHERE entitlement_id = v_trial.entitlement_id;
          INSERT INTO tenant_private.entitlement_events (
            tenant_id, entitlement_id, event_type, actor_subject, payload, occurred_at
          ) VALUES (
            v_row.tenant_id, v_trial.entitlement_id, 'TRIAL_REPLACED_BY_EXPLICIT_PAID_SELECTION',
            p_actor_subject, jsonb_build_object('selection_id', v_row.selection_id), p_now
          );
        END IF;

        SELECT * INTO v_paid
        FROM tenant_private.organisation_entitlements
        WHERE tenant_id = v_row.tenant_id AND entitlement_kind = 'PAID_MONTHLY'
        ORDER BY created_at DESC LIMIT 1 FOR UPDATE;
        IF FOUND THEN
          UPDATE tenant_private.organisation_entitlements
          SET plan_code = p_plan_code, state = 'ACTIVE', expires_at = NULL,
              unlimited_ai_tokens = true, token_budget_total = NULL,
              billing_selection_id = v_row.selection_id, updated_at = p_now
          WHERE entitlement_id = v_paid.entitlement_id
          RETURNING * INTO v_paid;
        ELSE
          INSERT INTO tenant_private.organisation_entitlements (
            tenant_id, entitlement_kind, plan_code, state, policy_version,
            starts_at, expires_at, unlimited_ai_tokens, token_budget_total,
            activated_by, billing_selection_id
          ) VALUES (
            v_row.tenant_id, 'PAID_MONTHLY', p_plan_code, 'ACTIVE',
            'ai-assistance-policy@0.1.0', p_now, NULL, true, NULL,
            p_actor_subject, v_row.selection_id
          ) RETURNING * INTO v_paid;
        END IF;
        UPDATE tenant_private.billing_plan_selections
        SET plan_code = p_plan_code, pending_plan_code = NULL,
            stripe_price_id = p_price_id, pending_stripe_price_id = NULL,
            stripe_customer_id = COALESCE(p_customer_id, stripe_customer_id),
            stripe_subscription_id = COALESCE(p_subscription_id, stripe_subscription_id),
            stripe_subscription_item_id = COALESCE(p_subscription_item_id, stripe_subscription_item_id),
            current_period_end = p_current_period_end,
            cancel_at_period_end = p_cancel_at_period_end,
            state = CASE WHEN p_cancel_at_period_end THEN 'CANCEL_AT_PERIOD_END' ELSE 'ACTIVE' END,
            last_provider_event_created_at = p_event_created_at,
            last_provider_event_id = p_event_id, updated_at = p_now
        WHERE selection_id = v_row.selection_id
        RETURNING * INTO v_row;
      ELSE
        SELECT * INTO v_paid
        FROM tenant_private.organisation_entitlements
        WHERE billing_selection_id = v_row.selection_id
        FOR UPDATE;
        IF FOUND THEN
          PERFORM tenant_private.release_billing_reservations(
            v_row.tenant_id, v_paid.entitlement_id, p_now
          );
          UPDATE tenant_private.organisation_entitlements
          SET state = 'SUSPENDED', updated_at = p_now
          WHERE entitlement_id = v_paid.entitlement_id;
        END IF;
        UPDATE tenant_private.billing_plan_selections
        SET state = 'SUSPENDED', current_period_end = p_current_period_end,
            last_provider_event_created_at = p_event_created_at,
            last_provider_event_id = p_event_id, updated_at = p_now
        WHERE selection_id = v_row.selection_id
        RETURNING * INTO v_row;
      END IF;
    ELSIF p_subscription_status = 'canceled' THEN
      p_event_type := 'customer.subscription.deleted';
    ELSE
      v_disposition := 'IGNORED';
    END IF;
  END IF;

  IF p_event_type = 'customer.subscription.deleted' THEN
    SELECT * INTO v_paid
    FROM tenant_private.organisation_entitlements
    WHERE billing_selection_id = v_row.selection_id
    FOR UPDATE;
    IF FOUND THEN
      PERFORM tenant_private.release_billing_reservations(
        v_row.tenant_id, v_paid.entitlement_id, p_now
      );
      UPDATE tenant_private.organisation_entitlements
      SET state = 'CANCELLED', updated_at = p_now
      WHERE entitlement_id = v_paid.entitlement_id;
    END IF;
    UPDATE tenant_private.billing_plan_selections
    SET state = 'CANCELLED', cancel_at_period_end = false,
        current_period_end = p_current_period_end,
        last_provider_event_created_at = p_event_created_at,
        last_provider_event_id = p_event_id, updated_at = p_now
    WHERE selection_id = v_row.selection_id
    RETURNING * INTO v_row;
  ELSIF p_event_type = 'invoice.payment_failed' THEN
    SELECT * INTO v_paid
    FROM tenant_private.organisation_entitlements
    WHERE billing_selection_id = v_row.selection_id
    FOR UPDATE;
    IF FOUND THEN
      PERFORM tenant_private.release_billing_reservations(
        v_row.tenant_id, v_paid.entitlement_id, p_now
      );
      UPDATE tenant_private.organisation_entitlements
      SET state = 'SUSPENDED', updated_at = p_now
      WHERE entitlement_id = v_paid.entitlement_id;
    END IF;
    UPDATE tenant_private.billing_plan_selections
    SET state = 'SUSPENDED', last_provider_event_created_at = p_event_created_at,
        last_provider_event_id = p_event_id, updated_at = p_now
    WHERE selection_id = v_row.selection_id
    RETURNING * INTO v_row;
  ELSIF p_event_type = 'checkout.session.expired' AND v_row.state <> 'ACTIVE' THEN
    UPDATE tenant_private.billing_plan_selections
    SET state = 'FAILED', last_provider_event_created_at = p_event_created_at,
        last_provider_event_id = p_event_id, updated_at = p_now
    WHERE selection_id = v_row.selection_id
    RETURNING * INTO v_row;
  END IF;

  v_new_state := v_row.state;
  INSERT INTO axignal_global.stripe_webhook_receipts (
    provider_event_id, tenant_id, selection_id, event_type, event_created_at,
    livemode, provider_account_id, payload_digest, disposition, received_at
  ) VALUES (
    p_event_id, v_row.tenant_id, v_row.selection_id, p_event_type,
    p_event_created_at, p_livemode, p_provider_account_id,
    p_payload_digest, v_disposition, p_now
  );
  INSERT INTO tenant_private.payment_ledger_entries (
    tenant_id, selection_id, provider_event_id, ledger_event_type, plan_code,
    amount_minor, currency, previous_state, new_state, payload_digest,
    actor_subject, occurred_at
  ) VALUES (
    v_row.tenant_id, v_row.selection_id, p_event_id,
    'STRIPE_' || upper(replace(p_event_type, '.', '_')),
    COALESCE(p_plan_code, v_row.plan_code), p_amount_minor,
    CASE WHEN p_currency IS NULL THEN NULL ELSE upper(p_currency) END,
    v_previous_state, v_new_state, p_payload_digest, p_actor_subject,
    p_event_created_at
  );
  RETURN jsonb_build_object('disposition', v_disposition, 'selection_id', v_row.selection_id,
                            'state', v_new_state);
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.rollback_paid_lifecycle(
  p_selection_id uuid,
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.billing_plan_selections
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_row tenant_private.billing_plan_selections%ROWTYPE;
  v_paid tenant_private.organisation_entitlements%ROWTYPE;
BEGIN
  SELECT * INTO v_row
  FROM tenant_private.billing_plan_selections
  WHERE selection_id = p_selection_id
  FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'billing_selection_not_found'; END IF;
  SELECT * INTO v_paid
  FROM tenant_private.organisation_entitlements
  WHERE billing_selection_id = p_selection_id
  FOR UPDATE;
  IF FOUND THEN
    PERFORM tenant_private.release_billing_reservations(v_row.tenant_id, v_paid.entitlement_id, p_now);
    UPDATE tenant_private.organisation_entitlements
    SET state = 'CANCELLED', updated_at = p_now
    WHERE entitlement_id = v_paid.entitlement_id;
  END IF;
  UPDATE tenant_private.billing_plan_selections
  SET state = 'ROLLED_BACK', cancel_at_period_end = false,
      pending_plan_code = NULL, pending_stripe_price_id = NULL, updated_at = p_now
  WHERE selection_id = p_selection_id
  RETURNING * INTO v_row;
  INSERT INTO tenant_private.payment_ledger_entries (
    tenant_id, selection_id, ledger_event_type, plan_code,
    previous_state, new_state, actor_subject, occurred_at
  ) VALUES (
    v_row.tenant_id, v_row.selection_id, 'PAID_LIFECYCLE_ROLLED_BACK',
    v_row.plan_code, NULL, 'ROLLED_BACK', p_actor_subject, p_now
  );
  RETURN v_row;
END
$$;

REVOKE ALL ON tenant_private.billing_plan_selections,
  tenant_private.payment_ledger_entries,
  axignal_global.stripe_webhook_receipts FROM PUBLIC;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON tenant_private.billing_plan_selections,
  tenant_private.payment_ledger_entries FROM axignal_app;

GRANT SELECT ON tenant_private.billing_plan_selections,
  tenant_private.payment_ledger_entries TO axignal_app;
GRANT EXECUTE ON FUNCTION tenant_private.request_paid_plan_selection(text, text, text, text, timestamptz)
  TO axignal_app;
GRANT EXECUTE ON FUNCTION tenant_private.mark_checkout_session_created(uuid, text, text, text, timestamptz)
  TO axignal_app;
GRANT EXECUTE ON FUNCTION tenant_private.request_paid_plan_upgrade(text, text, text, timestamptz)
  TO axignal_app;
GRANT EXECUTE ON FUNCTION tenant_private.request_paid_cancellation(boolean, text, timestamptz)
  TO axignal_app;

REVOKE ALL ON FUNCTION tenant_private.apply_stripe_billing_event(
  text, text, timestamptz, boolean, text, text, uuid, text, text, text,
  text, text, text, text, timestamptz, boolean, bigint, text, text, timestamptz
) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION tenant_private.apply_stripe_billing_event(
  text, text, timestamptz, boolean, text, text, uuid, text, text, text,
  text, text, text, text, timestamptz, boolean, bigint, text, text, timestamptz
) TO axignal_billing_worker;
REVOKE ALL ON FUNCTION tenant_private.rollback_paid_lifecycle(uuid, text, timestamptz)
  FROM PUBLIC;
GRANT EXECUTE ON FUNCTION tenant_private.rollback_paid_lifecycle(uuid, text, timestamptz)
  TO axignal_billing_worker;

CREATE INDEX IF NOT EXISTS billing_plan_selections_tenant_state_idx
  ON tenant_private.billing_plan_selections (tenant_id, state, updated_at DESC);
CREATE INDEX IF NOT EXISTS payment_ledger_tenant_time_idx
  ON tenant_private.payment_ledger_entries (tenant_id, occurred_at DESC);
