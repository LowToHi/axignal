CREATE TABLE IF NOT EXISTS tenant_private.organisation_entitlements (
  entitlement_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  entitlement_kind text NOT NULL CHECK (entitlement_kind IN ('TRIAL', 'PAID_MONTHLY')),
  plan_code text NOT NULL,
  state text NOT NULL CHECK (state IN ('ACTIVE', 'READ_ONLY', 'SUSPENDED', 'CANCELLED')),
  policy_version text NOT NULL,
  starts_at timestamptz NOT NULL,
  expires_at timestamptz,
  unlimited_ai_tokens boolean NOT NULL,
  token_budget_total bigint,
  token_budget_reserved bigint NOT NULL DEFAULT 0 CHECK (token_budget_reserved >= 0),
  token_budget_consumed bigint NOT NULL DEFAULT 0 CHECK (token_budget_consumed >= 0),
  activated_by text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (
    (
      entitlement_kind = 'TRIAL'
      AND plan_code = 'TRIAL_7D'
      AND unlimited_ai_tokens = false
      AND token_budget_total = 1000000
      AND expires_at = starts_at + interval '7 days'
    ) OR (
      entitlement_kind = 'PAID_MONTHLY'
      AND unlimited_ai_tokens = true
      AND token_budget_total IS NULL
      AND expires_at IS NULL
    )
  ),
  CHECK (
    token_budget_total IS NULL
    OR token_budget_reserved + token_budget_consumed <= token_budget_total
  )
);

CREATE UNIQUE INDEX IF NOT EXISTS organisation_one_trial_ever_idx
  ON tenant_private.organisation_entitlements (tenant_id)
  WHERE entitlement_kind = 'TRIAL';

CREATE UNIQUE INDEX IF NOT EXISTS organisation_one_active_entitlement_idx
  ON tenant_private.organisation_entitlements (tenant_id)
  WHERE state = 'ACTIVE';

CREATE TABLE IF NOT EXISTS tenant_private.ai_token_reservations (
  reservation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  entitlement_id uuid NOT NULL REFERENCES tenant_private.organisation_entitlements(entitlement_id),
  operation_id text NOT NULL CHECK (length(operation_id) BETWEEN 8 AND 200),
  capability text NOT NULL CHECK (capability IN (
    'NAVIGATE_AXIGNAL',
    'READ_INVESTIGATION_CONTEXT',
    'UPDATE_INVESTIGATION_CONTEXT',
    'SEARCH_ADMITTED_AXIGNAL_DATA',
    'COMPARE_ADMITTED_AXIGNAL_DATA',
    'EXPLAIN_CLAIMS_AND_EVIDENCE',
    'SHOW_CONTRADICTIONS_AND_UNKNOWNS',
    'REQUEST_BOUNDED_RESEARCH_RUN',
    'READ_RESEARCH_RUN_PROGRESS',
    'ASSEMBLE_EVIDENCE_LINKED_DOSSIER',
    'GENERATE_GROUNDED_PDF_REPORT',
    'EXPLAIN_AXIGNAL_PRODUCT_AND_METHOD'
  )),
  requested_tokens bigint NOT NULL CHECK (requested_tokens > 0),
  actual_tokens bigint CHECK (actual_tokens >= 0 AND actual_tokens <= requested_tokens),
  state text NOT NULL DEFAULT 'RESERVED' CHECK (state IN ('RESERVED', 'RECONCILED', 'RELEASED')),
  reserved_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL,
  reconciled_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, operation_id)
);

CREATE TABLE IF NOT EXISTS tenant_private.entitlement_events (
  entitlement_event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  entitlement_id uuid REFERENCES tenant_private.organisation_entitlements(entitlement_id),
  reservation_id uuid REFERENCES tenant_private.ai_token_reservations(reservation_id),
  event_type text NOT NULL,
  actor_subject text NOT NULL,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  occurred_at timestamptz NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION tenant_private.reject_entitlement_event_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE EXCEPTION 'AXIGNAL entitlement events are append-only';
END
$$;

DROP TRIGGER IF EXISTS entitlement_events_immutable ON tenant_private.entitlement_events;
CREATE TRIGGER entitlement_events_immutable
BEFORE UPDATE OR DELETE ON tenant_private.entitlement_events
FOR EACH ROW EXECUTE FUNCTION tenant_private.reject_entitlement_event_mutation();

ALTER TABLE tenant_private.organisation_entitlements ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.organisation_entitlements FORCE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.ai_token_reservations ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.ai_token_reservations FORCE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.entitlement_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.entitlement_events FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS organisation_entitlements_tenant_isolation
  ON tenant_private.organisation_entitlements;
CREATE POLICY organisation_entitlements_tenant_isolation
  ON tenant_private.organisation_entitlements
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

DROP POLICY IF EXISTS ai_token_reservations_tenant_isolation
  ON tenant_private.ai_token_reservations;
CREATE POLICY ai_token_reservations_tenant_isolation
  ON tenant_private.ai_token_reservations
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

DROP POLICY IF EXISTS entitlement_events_tenant_isolation
  ON tenant_private.entitlement_events;
CREATE POLICY entitlement_events_tenant_isolation
  ON tenant_private.entitlement_events
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

CREATE OR REPLACE FUNCTION tenant_private.activate_controlled_trial(
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.organisation_entitlements
LANGUAGE plpgsql
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.current_tenant_id();
  v_row tenant_private.organisation_entitlements%ROWTYPE;
BEGIN
  IF v_tenant_id IS NULL THEN
    RAISE EXCEPTION 'tenant_context_required';
  END IF;
  IF p_actor_subject IS NULL OR btrim(p_actor_subject) = '' THEN
    RAISE EXCEPTION 'actor_subject_required';
  END IF;
  IF EXISTS (
    SELECT 1 FROM tenant_private.organisation_entitlements
    WHERE tenant_id = v_tenant_id AND entitlement_kind = 'TRIAL'
  ) THEN
    RAISE EXCEPTION 'trial_already_activated';
  END IF;

  INSERT INTO tenant_private.organisation_entitlements (
    tenant_id, entitlement_kind, plan_code, state, policy_version,
    starts_at, expires_at, unlimited_ai_tokens, token_budget_total, activated_by
  ) VALUES (
    v_tenant_id, 'TRIAL', 'TRIAL_7D', 'ACTIVE', 'ai-assistance-policy@0.1.0',
    p_now, p_now + interval '7 days', false, 1000000, p_actor_subject
  ) RETURNING * INTO v_row;

  INSERT INTO tenant_private.entitlement_events (
    tenant_id, entitlement_id, event_type, actor_subject, payload, occurred_at
  ) VALUES (
    v_tenant_id, v_row.entitlement_id, 'TRIAL_ACTIVATED', p_actor_subject,
    jsonb_build_object('duration_days', 7, 'token_budget_total', 1000000), p_now
  );
  RETURN v_row;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.reserve_ai_tokens(
  p_operation_id text,
  p_capability text,
  p_requested_tokens bigint,
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.ai_token_reservations
LANGUAGE plpgsql
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

  IF v_entitlement.entitlement_kind = 'TRIAL' AND v_entitlement.expires_at <= p_now THEN
    UPDATE tenant_private.organisation_entitlements
    SET state = 'READ_ONLY', updated_at = p_now
    WHERE entitlement_id = v_entitlement.entitlement_id;
    INSERT INTO tenant_private.entitlement_events (
      tenant_id, entitlement_id, event_type, actor_subject, payload, occurred_at
    ) VALUES (
      v_tenant_id, v_entitlement.entitlement_id, 'TRIAL_EXPIRED', p_actor_subject,
      jsonb_build_object('transition', 'READ_ONLY'), p_now
    );
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

CREATE OR REPLACE FUNCTION tenant_private.reconcile_ai_tokens(
  p_reservation_id uuid,
  p_actual_tokens bigint,
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.ai_token_reservations
LANGUAGE plpgsql
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.current_tenant_id();
  v_reservation tenant_private.ai_token_reservations%ROWTYPE;
BEGIN
  IF v_tenant_id IS NULL THEN RAISE EXCEPTION 'tenant_context_required'; END IF;

  SELECT * INTO v_reservation
  FROM tenant_private.ai_token_reservations
  WHERE tenant_id = v_tenant_id AND reservation_id = p_reservation_id
  FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'reservation_not_found'; END IF;
  IF p_actual_tokens < 0 OR p_actual_tokens > v_reservation.requested_tokens THEN
    RAISE EXCEPTION 'actual_tokens_outside_reservation';
  END IF;
  IF v_reservation.state = 'RECONCILED' THEN
    IF v_reservation.actual_tokens <> p_actual_tokens THEN
      RAISE EXCEPTION 'reconciliation_conflict';
    END IF;
    RETURN v_reservation;
  END IF;
  IF v_reservation.state <> 'RESERVED' THEN RAISE EXCEPTION 'reservation_not_active'; END IF;

  UPDATE tenant_private.organisation_entitlements
  SET token_budget_reserved = token_budget_reserved - v_reservation.requested_tokens,
      token_budget_consumed = token_budget_consumed + p_actual_tokens,
      updated_at = p_now
  WHERE entitlement_id = v_reservation.entitlement_id;

  UPDATE tenant_private.ai_token_reservations
  SET state = 'RECONCILED', actual_tokens = p_actual_tokens,
      reconciled_at = p_now
  WHERE reservation_id = p_reservation_id
  RETURNING * INTO v_reservation;

  INSERT INTO tenant_private.entitlement_events (
    tenant_id, entitlement_id, reservation_id, event_type, actor_subject, payload, occurred_at
  ) VALUES (
    v_tenant_id, v_reservation.entitlement_id, v_reservation.reservation_id,
    'TOKENS_RECONCILED', p_actor_subject,
    jsonb_build_object('requested_tokens', v_reservation.requested_tokens,
                       'actual_tokens', p_actual_tokens), p_now
  );
  RETURN v_reservation;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.release_ai_token_reservation(
  p_reservation_id uuid,
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.ai_token_reservations
LANGUAGE plpgsql
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.current_tenant_id();
  v_reservation tenant_private.ai_token_reservations%ROWTYPE;
BEGIN
  IF v_tenant_id IS NULL THEN RAISE EXCEPTION 'tenant_context_required'; END IF;
  SELECT * INTO v_reservation
  FROM tenant_private.ai_token_reservations
  WHERE tenant_id = v_tenant_id AND reservation_id = p_reservation_id
  FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'reservation_not_found'; END IF;
  IF v_reservation.state = 'RELEASED' THEN RETURN v_reservation; END IF;
  IF v_reservation.state <> 'RESERVED' THEN RAISE EXCEPTION 'reservation_not_active'; END IF;

  UPDATE tenant_private.organisation_entitlements
  SET token_budget_reserved = token_budget_reserved - v_reservation.requested_tokens,
      updated_at = p_now
  WHERE entitlement_id = v_reservation.entitlement_id;
  UPDATE tenant_private.ai_token_reservations
  SET state = 'RELEASED', actual_tokens = 0, reconciled_at = p_now
  WHERE reservation_id = p_reservation_id
  RETURNING * INTO v_reservation;
  INSERT INTO tenant_private.entitlement_events (
    tenant_id, entitlement_id, reservation_id, event_type, actor_subject, payload, occurred_at
  ) VALUES (
    v_tenant_id, v_reservation.entitlement_id, v_reservation.reservation_id,
    'TOKEN_RESERVATION_RELEASED', p_actor_subject, '{}'::jsonb, p_now
  );
  RETURN v_reservation;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.expire_current_trial(
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.organisation_entitlements
LANGUAGE plpgsql
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.current_tenant_id();
  v_row tenant_private.organisation_entitlements%ROWTYPE;
BEGIN
  IF v_tenant_id IS NULL THEN RAISE EXCEPTION 'tenant_context_required'; END IF;
  SELECT * INTO v_row
  FROM tenant_private.organisation_entitlements
  WHERE tenant_id = v_tenant_id AND entitlement_kind = 'TRIAL'
  FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'trial_not_found'; END IF;
  IF v_row.state = 'ACTIVE' AND v_row.expires_at <= p_now THEN
    UPDATE tenant_private.organisation_entitlements
    SET state = 'READ_ONLY', updated_at = p_now
    WHERE entitlement_id = v_row.entitlement_id
    RETURNING * INTO v_row;
    INSERT INTO tenant_private.entitlement_events (
      tenant_id, entitlement_id, event_type, actor_subject, payload, occurred_at
    ) VALUES (
      v_tenant_id, v_row.entitlement_id, 'TRIAL_EXPIRED', p_actor_subject,
      jsonb_build_object('transition', 'READ_ONLY'), p_now
    );
  END IF;
  RETURN v_row;
END
$$;

GRANT SELECT, INSERT ON tenant_private.organisation_entitlements,
  tenant_private.ai_token_reservations, tenant_private.entitlement_events TO axignal_app;
GRANT UPDATE (state, token_budget_reserved, token_budget_consumed, updated_at)
  ON tenant_private.organisation_entitlements TO axignal_app;
GRANT UPDATE (state, actual_tokens, reconciled_at)
  ON tenant_private.ai_token_reservations TO axignal_app;
GRANT EXECUTE ON FUNCTION tenant_private.activate_controlled_trial(text, timestamptz) TO axignal_app;
GRANT EXECUTE ON FUNCTION tenant_private.reserve_ai_tokens(text, text, bigint, text, timestamptz) TO axignal_app;
GRANT EXECUTE ON FUNCTION tenant_private.reconcile_ai_tokens(uuid, bigint, text, timestamptz) TO axignal_app;
GRANT EXECUTE ON FUNCTION tenant_private.release_ai_token_reservation(uuid, text, timestamptz) TO axignal_app;
GRANT EXECUTE ON FUNCTION tenant_private.expire_current_trial(text, timestamptz) TO axignal_app;

CREATE INDEX IF NOT EXISTS organisation_entitlements_tenant_state_idx
  ON tenant_private.organisation_entitlements (tenant_id, state, created_at DESC);
CREATE INDEX IF NOT EXISTS ai_token_reservations_tenant_state_idx
  ON tenant_private.ai_token_reservations (tenant_id, state, created_at DESC);
CREATE INDEX IF NOT EXISTS entitlement_events_tenant_time_idx
  ON tenant_private.entitlement_events (tenant_id, occurred_at DESC);
