-- AX-GE2E-P21-T02 end-to-end seat governance.
-- Flat-tier commercial packages are materialised as tenant-scoped seat capacity.
-- Stripe bills one package unit; AXIGNAL allocates, reserves and revokes seats.

CREATE TABLE IF NOT EXISTS axignal_global.seat_plan_policies (
  plan_code text PRIMARY KEY,
  billing_model text NOT NULL CHECK (billing_model = 'FLAT_TIER'),
  seat_capacity integer NOT NULL CHECK (seat_capacity BETWEEN 1 AND 10000),
  policy_version text NOT NULL,
  state text NOT NULL CHECK (state IN ('CANDIDATE', 'ACTIVE', 'RETIRED')),
  created_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO axignal_global.seat_plan_policies (
  plan_code, billing_model, seat_capacity, policy_version, state
) VALUES
  ('TRIAL_7D', 'FLAT_TIER', 2, 'seat-governance-policy@0.1.0', 'CANDIDATE'),
  ('PROFESSIONAL_MONTHLY', 'FLAT_TIER', 3, 'seat-governance-policy@0.1.0', 'CANDIDATE'),
  ('TEAM_MONTHLY', 'FLAT_TIER', 15, 'seat-governance-policy@0.1.0', 'CANDIDATE')
ON CONFLICT (plan_code) DO UPDATE SET
  billing_model = EXCLUDED.billing_model,
  seat_capacity = EXCLUDED.seat_capacity,
  policy_version = EXCLUDED.policy_version,
  state = EXCLUDED.state;

CREATE TABLE IF NOT EXISTS tenant_private.organisation_seat_entitlements (
  seat_entitlement_id uuid PRIMARY KEY DEFAULT public.gen_random_uuid(),
  tenant_id uuid NOT NULL UNIQUE,
  source_entitlement_id uuid NOT NULL UNIQUE
    REFERENCES tenant_private.organisation_entitlements(entitlement_id),
  source_billing_selection_id uuid
    REFERENCES tenant_private.billing_plan_selections(selection_id),
  plan_code text NOT NULL REFERENCES axignal_global.seat_plan_policies(plan_code),
  billing_model text NOT NULL CHECK (billing_model = 'FLAT_TIER'),
  seat_capacity integer NOT NULL CHECK (seat_capacity > 0),
  state text NOT NULL CHECK (state IN ('ACTIVE', 'READ_ONLY', 'SUSPENDED', 'CANCELLED')),
  policy_version text NOT NULL,
  valid_from timestamptz NOT NULL,
  valid_until timestamptz,
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tenant_private.organisation_memberships (
  membership_id uuid PRIMARY KEY DEFAULT public.gen_random_uuid(),
  tenant_id uuid NOT NULL,
  principal_id text NOT NULL CHECK (length(principal_id) BETWEEN 3 AND 200),
  email_normalized text NOT NULL CHECK (
    email_normalized = lower(btrim(email_normalized))
    AND position('@' IN email_normalized) > 1
  ),
  status text NOT NULL CHECK (status IN (
    'ACTIVE', 'SUSPENDED', 'REVOKED', 'EXPIRED'
  )),
  workspace_scope jsonb NOT NULL DEFAULT '["*"]'::jsonb,
  invited_by text NOT NULL,
  joined_at timestamptz NOT NULL,
  suspended_at timestamptz,
  revoked_at timestamptz,
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, principal_id),
  UNIQUE (tenant_id, email_normalized)
);

CREATE TABLE IF NOT EXISTS tenant_private.organisation_invitations (
  invitation_id uuid PRIMARY KEY DEFAULT public.gen_random_uuid(),
  tenant_id uuid NOT NULL,
  operation_id text NOT NULL CHECK (length(operation_id) BETWEEN 8 AND 200),
  email_normalized text NOT NULL CHECK (
    email_normalized = lower(btrim(email_normalized))
    AND position('@' IN email_normalized) > 1
  ),
  requested_role_id text NOT NULL CHECK (requested_role_id IN (
    'ORG_ADMIN', 'B2G_MANAGER', 'RESEARCH_OPERATOR', 'BID_REVIEWER',
    'VIEWER', 'BILLING_ADMIN', 'AUDITOR'
  )),
  token_digest text NOT NULL CHECK (token_digest ~ '^[0-9a-f]{64}$'),
  status text NOT NULL CHECK (status IN (
    'PENDING', 'ACCEPTED', 'EXPIRED', 'REVOKED', 'DELIVERY_FAILED'
  )),
  invited_by text NOT NULL,
  invited_at timestamptz NOT NULL,
  expires_at timestamptz NOT NULL,
  accepted_at timestamptz,
  revoked_at timestamptz,
  delivery_provider text NOT NULL CHECK (delivery_provider IN ('TEST', 'SMTP')),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, operation_id),
  UNIQUE (tenant_id, token_digest)
);

CREATE UNIQUE INDEX IF NOT EXISTS organisation_one_pending_invitation_per_email_idx
  ON tenant_private.organisation_invitations (tenant_id, email_normalized)
  WHERE status = 'PENDING';

CREATE TABLE IF NOT EXISTS tenant_private.organisation_seat_allocations (
  seat_allocation_id uuid PRIMARY KEY DEFAULT public.gen_random_uuid(),
  tenant_id uuid NOT NULL,
  seat_entitlement_id uuid NOT NULL
    REFERENCES tenant_private.organisation_seat_entitlements(seat_entitlement_id),
  membership_id uuid REFERENCES tenant_private.organisation_memberships(membership_id),
  invitation_id uuid REFERENCES tenant_private.organisation_invitations(invitation_id),
  state text NOT NULL CHECK (state IN ('RESERVED', 'ACTIVE', 'RELEASED')),
  reserved_at timestamptz NOT NULL,
  activated_at timestamptz,
  released_at timestamptz,
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (
    (state = 'RESERVED' AND invitation_id IS NOT NULL AND membership_id IS NULL)
    OR (state = 'ACTIVE' AND membership_id IS NOT NULL AND invitation_id IS NULL)
    OR state = 'RELEASED'
  )
);

CREATE UNIQUE INDEX IF NOT EXISTS organisation_active_allocation_per_membership_idx
  ON tenant_private.organisation_seat_allocations (tenant_id, membership_id)
  WHERE membership_id IS NOT NULL AND state = 'ACTIVE';

CREATE UNIQUE INDEX IF NOT EXISTS organisation_reserved_allocation_per_invitation_idx
  ON tenant_private.organisation_seat_allocations (tenant_id, invitation_id)
  WHERE invitation_id IS NOT NULL AND state = 'RESERVED';

CREATE TABLE IF NOT EXISTS tenant_private.membership_role_bindings (
  role_binding_id uuid PRIMARY KEY DEFAULT public.gen_random_uuid(),
  tenant_id uuid NOT NULL,
  membership_id uuid NOT NULL
    REFERENCES tenant_private.organisation_memberships(membership_id),
  role_id text NOT NULL CHECK (role_id IN (
    'ORG_OWNER', 'ORG_ADMIN', 'B2G_MANAGER', 'RESEARCH_OPERATOR',
    'BID_REVIEWER', 'VIEWER', 'BILLING_ADMIN', 'AUDITOR'
  )),
  state text NOT NULL CHECK (state IN ('ACTIVE', 'REVOKED')),
  granted_by text NOT NULL,
  granted_at timestamptz NOT NULL,
  revoked_at timestamptz,
  UNIQUE (tenant_id, membership_id, role_id)
);

CREATE TABLE IF NOT EXISTS tenant_private.membership_audit_events (
  audit_event_id uuid PRIMARY KEY DEFAULT public.gen_random_uuid(),
  tenant_id uuid NOT NULL,
  event_type text NOT NULL,
  actor_subject text NOT NULL,
  membership_id uuid,
  invitation_id uuid,
  seat_allocation_id uuid,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  occurred_at timestamptz NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION tenant_private.reject_membership_audit_mutation()
RETURNS trigger
LANGUAGE plpgsql
SET search_path TO pg_catalog
AS $$
BEGIN
  RAISE EXCEPTION 'membership_audit_events_are_append_only';
END
$$;

DROP TRIGGER IF EXISTS membership_audit_events_immutable
  ON tenant_private.membership_audit_events;
CREATE TRIGGER membership_audit_events_immutable
BEFORE UPDATE OR DELETE ON tenant_private.membership_audit_events
FOR EACH ROW EXECUTE FUNCTION tenant_private.reject_membership_audit_mutation();

ALTER TABLE tenant_private.organisation_seat_entitlements ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.organisation_seat_entitlements FORCE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.organisation_memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.organisation_memberships FORCE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.organisation_invitations ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.organisation_invitations FORCE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.organisation_seat_allocations ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.organisation_seat_allocations FORCE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.membership_role_bindings ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.membership_role_bindings FORCE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.membership_audit_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.membership_audit_events FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS seat_entitlements_tenant_isolation
  ON tenant_private.organisation_seat_entitlements;
CREATE POLICY seat_entitlements_tenant_isolation
  ON tenant_private.organisation_seat_entitlements
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

DROP POLICY IF EXISTS memberships_tenant_isolation
  ON tenant_private.organisation_memberships;
CREATE POLICY memberships_tenant_isolation
  ON tenant_private.organisation_memberships
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

DROP POLICY IF EXISTS invitations_tenant_isolation
  ON tenant_private.organisation_invitations;
CREATE POLICY invitations_tenant_isolation
  ON tenant_private.organisation_invitations
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

DROP POLICY IF EXISTS seat_allocations_tenant_isolation
  ON tenant_private.organisation_seat_allocations;
CREATE POLICY seat_allocations_tenant_isolation
  ON tenant_private.organisation_seat_allocations
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

DROP POLICY IF EXISTS role_bindings_tenant_isolation
  ON tenant_private.membership_role_bindings;
CREATE POLICY role_bindings_tenant_isolation
  ON tenant_private.membership_role_bindings
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

DROP POLICY IF EXISTS membership_audit_tenant_isolation
  ON tenant_private.membership_audit_events;
CREATE POLICY membership_audit_tenant_isolation
  ON tenant_private.membership_audit_events
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

CREATE OR REPLACE FUNCTION tenant_private.seat_actor_is_admin(
  p_principal_id text
)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
  SELECT EXISTS (
    SELECT 1
    FROM tenant_private.organisation_memberships m
    JOIN tenant_private.membership_role_bindings rb
      ON rb.tenant_id = m.tenant_id
     AND rb.membership_id = m.membership_id
     AND rb.state = 'ACTIVE'
    WHERE m.tenant_id = tenant_private.current_tenant_id()
      AND m.principal_id = p_principal_id
      AND m.status = 'ACTIVE'
      AND rb.role_id IN ('ORG_OWNER', 'ORG_ADMIN')
  )
$$;

CREATE OR REPLACE FUNCTION tenant_private.expire_pending_seat_invitations(
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS integer
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.current_tenant_id();
  v_count integer := 0;
BEGIN
  IF v_tenant_id IS NULL THEN RAISE EXCEPTION 'tenant_context_required'; END IF;

  WITH expired AS (
    UPDATE tenant_private.organisation_invitations
    SET status = 'EXPIRED', updated_at = p_now
    WHERE tenant_id = v_tenant_id
      AND status = 'PENDING'
      AND expires_at <= p_now
    RETURNING invitation_id
  ), released AS (
    UPDATE tenant_private.organisation_seat_allocations a
    SET state = 'RELEASED', released_at = p_now, updated_at = p_now
    FROM expired e
    WHERE a.tenant_id = v_tenant_id
      AND a.invitation_id = e.invitation_id
      AND a.state = 'RESERVED'
    RETURNING a.invitation_id, a.seat_allocation_id
  )
  INSERT INTO tenant_private.membership_audit_events (
    tenant_id, event_type, actor_subject, invitation_id,
    seat_allocation_id, payload, occurred_at
  )
  SELECT v_tenant_id, 'SEAT_INVITATION_EXPIRED', p_actor_subject,
         invitation_id, seat_allocation_id, '{}'::jsonb, p_now
  FROM released;

  GET DIAGNOSTICS v_count = ROW_COUNT;
  RETURN v_count;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.sync_seat_entitlement_from_product()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_policy axignal_global.seat_plan_policies%ROWTYPE;
  v_state text;
  v_allocated integer;
BEGIN
  SELECT * INTO v_policy
  FROM axignal_global.seat_plan_policies
  WHERE plan_code = NEW.plan_code AND state IN ('CANDIDATE', 'ACTIVE');

  IF NOT FOUND THEN
    RETURN NEW;
  END IF;

  v_state := CASE NEW.state
    WHEN 'ACTIVE' THEN 'ACTIVE'
    WHEN 'READ_ONLY' THEN 'READ_ONLY'
    WHEN 'SUSPENDED' THEN 'SUSPENDED'
    ELSE 'CANCELLED'
  END;

  SELECT count(*) INTO v_allocated
  FROM tenant_private.organisation_seat_allocations
  WHERE tenant_id = NEW.tenant_id
    AND state IN ('RESERVED', 'ACTIVE');

  IF v_state = 'ACTIVE' AND v_allocated > v_policy.seat_capacity THEN
    RAISE EXCEPTION 'seat_downgrade_capacity_conflict';
  END IF;

  INSERT INTO tenant_private.organisation_seat_entitlements (
    tenant_id, source_entitlement_id, source_billing_selection_id,
    plan_code, billing_model, seat_capacity, state, policy_version,
    valid_from, valid_until, updated_at
  ) VALUES (
    NEW.tenant_id, NEW.entitlement_id, NEW.billing_selection_id,
    NEW.plan_code, v_policy.billing_model, v_policy.seat_capacity, v_state,
    v_policy.policy_version, NEW.starts_at, NEW.expires_at, now()
  )
  ON CONFLICT (tenant_id) DO UPDATE SET
    source_entitlement_id = EXCLUDED.source_entitlement_id,
    source_billing_selection_id = EXCLUDED.source_billing_selection_id,
    plan_code = EXCLUDED.plan_code,
    billing_model = EXCLUDED.billing_model,
    seat_capacity = EXCLUDED.seat_capacity,
    state = EXCLUDED.state,
    policy_version = EXCLUDED.policy_version,
    valid_from = EXCLUDED.valid_from,
    valid_until = EXCLUDED.valid_until,
    updated_at = EXCLUDED.updated_at;

  IF v_state <> 'ACTIVE' THEN
    UPDATE tenant_private.organisation_invitations
    SET status = 'REVOKED', revoked_at = now(), updated_at = now()
    WHERE tenant_id = NEW.tenant_id AND status = 'PENDING';

    UPDATE tenant_private.organisation_seat_allocations
    SET state = 'RELEASED', released_at = now(), updated_at = now()
    WHERE tenant_id = NEW.tenant_id AND state = 'RESERVED';
  END IF;
  RETURN NEW;
END
$$;

DROP TRIGGER IF EXISTS organisation_entitlement_seat_sync
  ON tenant_private.organisation_entitlements;
CREATE TRIGGER organisation_entitlement_seat_sync
AFTER INSERT OR UPDATE OF plan_code, state, billing_selection_id, expires_at
ON tenant_private.organisation_entitlements
FOR EACH ROW EXECUTE FUNCTION tenant_private.sync_seat_entitlement_from_product();

CREATE OR REPLACE FUNCTION tenant_private.bootstrap_organisation_owner(
  p_principal_id text,
  p_email text,
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.organisation_memberships
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.current_tenant_id();
  v_seat tenant_private.organisation_seat_entitlements%ROWTYPE;
  v_member tenant_private.organisation_memberships%ROWTYPE;
  v_allocation tenant_private.organisation_seat_allocations%ROWTYPE;
  v_email text := lower(btrim(p_email));
BEGIN
  IF v_tenant_id IS NULL THEN RAISE EXCEPTION 'tenant_context_required'; END IF;
  IF p_principal_id IS NULL OR btrim(p_principal_id) = '' THEN
    RAISE EXCEPTION 'principal_required';
  END IF;
  IF position('@' IN v_email) <= 1 THEN RAISE EXCEPTION 'email_invalid'; END IF;

  SELECT * INTO v_member
  FROM tenant_private.organisation_memberships
  WHERE tenant_id = v_tenant_id AND principal_id = p_principal_id;
  IF FOUND THEN RETURN v_member; END IF;

  SELECT * INTO v_seat
  FROM tenant_private.organisation_seat_entitlements
  WHERE tenant_id = v_tenant_id
  FOR UPDATE;
  IF NOT FOUND OR v_seat.state <> 'ACTIVE' THEN
    RAISE EXCEPTION 'active_seat_entitlement_required';
  END IF;

  IF EXISTS (
    SELECT 1 FROM tenant_private.organisation_memberships
    WHERE tenant_id = v_tenant_id AND status = 'ACTIVE'
  ) THEN
    RAISE EXCEPTION 'owner_bootstrap_closed';
  END IF;

  INSERT INTO tenant_private.organisation_memberships (
    tenant_id, principal_id, email_normalized, status, invited_by, joined_at
  ) VALUES (
    v_tenant_id, p_principal_id, v_email, 'ACTIVE', p_actor_subject, p_now
  ) RETURNING * INTO v_member;

  INSERT INTO tenant_private.organisation_seat_allocations (
    tenant_id, seat_entitlement_id, membership_id, state,
    reserved_at, activated_at
  ) VALUES (
    v_tenant_id, v_seat.seat_entitlement_id, v_member.membership_id,
    'ACTIVE', p_now, p_now
  ) RETURNING * INTO v_allocation;

  INSERT INTO tenant_private.membership_role_bindings (
    tenant_id, membership_id, role_id, state, granted_by, granted_at
  ) VALUES (
    v_tenant_id, v_member.membership_id, 'ORG_OWNER',
    'ACTIVE', p_actor_subject, p_now
  );

  INSERT INTO tenant_private.membership_audit_events (
    tenant_id, event_type, actor_subject, membership_id,
    seat_allocation_id, payload, occurred_at
  ) VALUES (
    v_tenant_id, 'ORGANISATION_OWNER_BOOTSTRAPPED', p_actor_subject,
    v_member.membership_id, v_allocation.seat_allocation_id,
    jsonb_build_object('plan_code', v_seat.plan_code), p_now
  );
  RETURN v_member;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.reserve_seat_invitation(
  p_operation_id text,
  p_email text,
  p_role_id text,
  p_token_digest text,
  p_delivery_provider text,
  p_invited_by text,
  p_expires_at timestamptz,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.organisation_invitations
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.current_tenant_id();
  v_seat tenant_private.organisation_seat_entitlements%ROWTYPE;
  v_invitation tenant_private.organisation_invitations%ROWTYPE;
  v_email text := lower(btrim(p_email));
  v_occupied integer;
BEGIN
  IF v_tenant_id IS NULL THEN RAISE EXCEPTION 'tenant_context_required'; END IF;
  IF NOT tenant_private.seat_actor_is_admin(p_invited_by) THEN
    RAISE EXCEPTION 'membership_admin_required';
  END IF;
  IF p_role_id NOT IN (
    'ORG_ADMIN', 'B2G_MANAGER', 'RESEARCH_OPERATOR', 'BID_REVIEWER',
    'VIEWER', 'BILLING_ADMIN', 'AUDITOR'
  ) THEN RAISE EXCEPTION 'seat_role_invalid'; END IF;
  IF p_token_digest !~ '^[0-9a-f]{64}$' THEN
    RAISE EXCEPTION 'invitation_token_digest_invalid';
  END IF;
  IF p_expires_at <= p_now OR p_expires_at > p_now + interval '14 days' THEN
    RAISE EXCEPTION 'invitation_expiry_invalid';
  END IF;
  IF position('@' IN v_email) <= 1 THEN RAISE EXCEPTION 'email_invalid'; END IF;

  SELECT * INTO v_invitation
  FROM tenant_private.organisation_invitations
  WHERE tenant_id = v_tenant_id AND operation_id = p_operation_id;
  IF FOUND THEN
    IF v_invitation.email_normalized <> v_email
       OR v_invitation.requested_role_id <> p_role_id THEN
      RAISE EXCEPTION 'seat_operation_id_conflict';
    END IF;
    RETURN v_invitation;
  END IF;

  PERFORM tenant_private.expire_pending_seat_invitations(p_invited_by, p_now);

  SELECT * INTO v_seat
  FROM tenant_private.organisation_seat_entitlements
  WHERE tenant_id = v_tenant_id
  FOR UPDATE;
  IF NOT FOUND OR v_seat.state <> 'ACTIVE' THEN
    RAISE EXCEPTION 'active_seat_entitlement_required';
  END IF;

  IF EXISTS (
    SELECT 1 FROM tenant_private.organisation_memberships
    WHERE tenant_id = v_tenant_id
      AND email_normalized = v_email
      AND status IN ('ACTIVE', 'SUSPENDED')
  ) THEN RAISE EXCEPTION 'membership_email_already_exists'; END IF;

  IF EXISTS (
    SELECT 1 FROM tenant_private.organisation_invitations
    WHERE tenant_id = v_tenant_id
      AND email_normalized = v_email
      AND status = 'PENDING'
  ) THEN RAISE EXCEPTION 'pending_invitation_already_exists'; END IF;

  SELECT count(*) INTO v_occupied
  FROM tenant_private.organisation_seat_allocations
  WHERE tenant_id = v_tenant_id AND state IN ('RESERVED', 'ACTIVE');

  IF v_occupied >= v_seat.seat_capacity THEN
    RAISE EXCEPTION 'seat_capacity_exhausted';
  END IF;

  INSERT INTO tenant_private.organisation_invitations (
    tenant_id, operation_id, email_normalized, requested_role_id,
    token_digest, status, invited_by, invited_at, expires_at, delivery_provider
  ) VALUES (
    v_tenant_id, p_operation_id, v_email, p_role_id, p_token_digest,
    'PENDING', p_invited_by, p_now, p_expires_at, p_delivery_provider
  ) RETURNING * INTO v_invitation;

  INSERT INTO tenant_private.organisation_seat_allocations (
    tenant_id, seat_entitlement_id, invitation_id, state, reserved_at
  ) VALUES (
    v_tenant_id, v_seat.seat_entitlement_id,
    v_invitation.invitation_id, 'RESERVED', p_now
  );

  INSERT INTO tenant_private.membership_audit_events (
    tenant_id, event_type, actor_subject, invitation_id, payload, occurred_at
  ) VALUES (
    v_tenant_id, 'SEAT_INVITATION_RESERVED', p_invited_by,
    v_invitation.invitation_id,
    jsonb_build_object('email', v_email, 'role_id', p_role_id), p_now
  );
  RETURN v_invitation;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.accept_seat_invitation(
  p_token_digest text,
  p_principal_id text,
  p_email text,
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.organisation_memberships
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.current_tenant_id();
  v_invitation tenant_private.organisation_invitations%ROWTYPE;
  v_member tenant_private.organisation_memberships%ROWTYPE;
  v_allocation tenant_private.organisation_seat_allocations%ROWTYPE;
  v_email text := lower(btrim(p_email));
BEGIN
  IF v_tenant_id IS NULL THEN RAISE EXCEPTION 'tenant_context_required'; END IF;

  SELECT * INTO v_invitation
  FROM tenant_private.organisation_invitations
  WHERE tenant_id = v_tenant_id
    AND token_digest = p_token_digest
    AND status = 'PENDING'
  FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'seat_invitation_not_found'; END IF;

  IF v_invitation.expires_at <= p_now THEN
    UPDATE tenant_private.organisation_invitations
    SET status = 'EXPIRED', updated_at = p_now
    WHERE invitation_id = v_invitation.invitation_id;
    UPDATE tenant_private.organisation_seat_allocations
    SET state = 'RELEASED', released_at = p_now, updated_at = p_now
    WHERE invitation_id = v_invitation.invitation_id AND state = 'RESERVED';
    RAISE EXCEPTION 'seat_invitation_expired';
  END IF;
  IF v_invitation.email_normalized <> v_email THEN
    RAISE EXCEPTION 'seat_invitation_email_mismatch';
  END IF;

  IF EXISTS (
    SELECT 1 FROM tenant_private.organisation_memberships
    WHERE tenant_id = v_tenant_id
      AND (principal_id = p_principal_id OR email_normalized = v_email)
      AND status IN ('ACTIVE', 'SUSPENDED')
  ) THEN RAISE EXCEPTION 'membership_already_exists'; END IF;

  INSERT INTO tenant_private.organisation_memberships (
    tenant_id, principal_id, email_normalized, status,
    invited_by, joined_at
  ) VALUES (
    v_tenant_id, p_principal_id, v_email, 'ACTIVE',
    v_invitation.invited_by, p_now
  ) RETURNING * INTO v_member;

  UPDATE tenant_private.organisation_seat_allocations
  SET membership_id = v_member.membership_id,
      invitation_id = NULL,
      state = 'ACTIVE',
      activated_at = p_now,
      updated_at = p_now
  WHERE tenant_id = v_tenant_id
    AND invitation_id = v_invitation.invitation_id
    AND state = 'RESERVED'
  RETURNING * INTO v_allocation;
  IF NOT FOUND THEN RAISE EXCEPTION 'reserved_seat_allocation_not_found'; END IF;

  INSERT INTO tenant_private.membership_role_bindings (
    tenant_id, membership_id, role_id, state, granted_by, granted_at
  ) VALUES (
    v_tenant_id, v_member.membership_id, v_invitation.requested_role_id,
    'ACTIVE', v_invitation.invited_by, p_now
  );

  UPDATE tenant_private.organisation_invitations
  SET status = 'ACCEPTED', accepted_at = p_now, updated_at = p_now
  WHERE invitation_id = v_invitation.invitation_id;

  INSERT INTO tenant_private.membership_audit_events (
    tenant_id, event_type, actor_subject, membership_id,
    invitation_id, seat_allocation_id, payload, occurred_at
  ) VALUES (
    v_tenant_id, 'SEAT_INVITATION_ACCEPTED', p_actor_subject,
    v_member.membership_id, v_invitation.invitation_id,
    v_allocation.seat_allocation_id,
    jsonb_build_object('role_id', v_invitation.requested_role_id), p_now
  );
  RETURN v_member;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.revoke_seat_invitation(
  p_invitation_id uuid,
  p_actor_subject text,
  p_reason text,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.organisation_invitations
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.current_tenant_id();
  v_invitation tenant_private.organisation_invitations%ROWTYPE;
BEGIN
  IF v_tenant_id IS NULL THEN RAISE EXCEPTION 'tenant_context_required'; END IF;
  IF NOT tenant_private.seat_actor_is_admin(p_actor_subject) THEN
    RAISE EXCEPTION 'membership_admin_required';
  END IF;

  SELECT * INTO v_invitation
  FROM tenant_private.organisation_invitations
  WHERE tenant_id = v_tenant_id AND invitation_id = p_invitation_id
  FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'seat_invitation_not_found'; END IF;
  IF v_invitation.status <> 'PENDING' THEN RETURN v_invitation; END IF;

  UPDATE tenant_private.organisation_invitations
  SET status = CASE WHEN p_reason = 'DELIVERY_FAILED'
                    THEN 'DELIVERY_FAILED' ELSE 'REVOKED' END,
      revoked_at = p_now, updated_at = p_now
  WHERE invitation_id = p_invitation_id
  RETURNING * INTO v_invitation;

  UPDATE tenant_private.organisation_seat_allocations
  SET state = 'RELEASED', released_at = p_now, updated_at = p_now
  WHERE tenant_id = v_tenant_id
    AND invitation_id = p_invitation_id
    AND state = 'RESERVED';

  INSERT INTO tenant_private.membership_audit_events (
    tenant_id, event_type, actor_subject, invitation_id, payload, occurred_at
  ) VALUES (
    v_tenant_id,
    CASE WHEN p_reason = 'DELIVERY_FAILED'
      THEN 'SEAT_INVITATION_DELIVERY_FAILED'
      ELSE 'SEAT_INVITATION_REVOKED' END,
    p_actor_subject, p_invitation_id,
    jsonb_build_object('reason', left(coalesce(p_reason, ''), 200)), p_now
  );
  RETURN v_invitation;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.revoke_organisation_membership(
  p_membership_id uuid,
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.organisation_memberships
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.current_tenant_id();
  v_member tenant_private.organisation_memberships%ROWTYPE;
  v_is_owner boolean;
  v_owner_count integer;
BEGIN
  IF v_tenant_id IS NULL THEN RAISE EXCEPTION 'tenant_context_required'; END IF;
  IF NOT tenant_private.seat_actor_is_admin(p_actor_subject) THEN
    RAISE EXCEPTION 'membership_admin_required';
  END IF;

  SELECT * INTO v_member
  FROM tenant_private.organisation_memberships
  WHERE tenant_id = v_tenant_id AND membership_id = p_membership_id
  FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'membership_not_found'; END IF;
  IF v_member.status = 'REVOKED' THEN RETURN v_member; END IF;

  SELECT EXISTS (
    SELECT 1 FROM tenant_private.membership_role_bindings
    WHERE tenant_id = v_tenant_id
      AND membership_id = p_membership_id
      AND role_id = 'ORG_OWNER'
      AND state = 'ACTIVE'
  ) INTO v_is_owner;

  IF v_is_owner THEN
    SELECT count(*) INTO v_owner_count
    FROM tenant_private.organisation_memberships m
    JOIN tenant_private.membership_role_bindings rb
      ON rb.tenant_id = m.tenant_id AND rb.membership_id = m.membership_id
    WHERE m.tenant_id = v_tenant_id
      AND m.status = 'ACTIVE'
      AND rb.role_id = 'ORG_OWNER'
      AND rb.state = 'ACTIVE';
    IF v_owner_count <= 1 THEN RAISE EXCEPTION 'last_owner_revocation_forbidden'; END IF;
  END IF;

  UPDATE tenant_private.organisation_memberships
  SET status = 'REVOKED', revoked_at = p_now, updated_at = p_now
  WHERE membership_id = p_membership_id
  RETURNING * INTO v_member;

  UPDATE tenant_private.membership_role_bindings
  SET state = 'REVOKED', revoked_at = p_now
  WHERE tenant_id = v_tenant_id
    AND membership_id = p_membership_id
    AND state = 'ACTIVE';

  UPDATE tenant_private.organisation_seat_allocations
  SET state = 'RELEASED', released_at = p_now, updated_at = p_now
  WHERE tenant_id = v_tenant_id
    AND membership_id = p_membership_id
    AND state = 'ACTIVE';

  INSERT INTO tenant_private.membership_audit_events (
    tenant_id, event_type, actor_subject, membership_id, payload, occurred_at
  ) VALUES (
    v_tenant_id, 'MEMBERSHIP_REVOKED', p_actor_subject,
    p_membership_id, '{}'::jsonb, p_now
  );
  RETURN v_member;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.change_organisation_membership_role(
  p_membership_id uuid,
  p_role_id text,
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.organisation_memberships
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.current_tenant_id();
  v_member tenant_private.organisation_memberships%ROWTYPE;
  v_current_owner boolean;
  v_owner_count integer;
BEGIN
  IF v_tenant_id IS NULL THEN RAISE EXCEPTION 'tenant_context_required'; END IF;
  IF NOT tenant_private.seat_actor_is_admin(p_actor_subject) THEN
    RAISE EXCEPTION 'membership_admin_required';
  END IF;
  IF p_role_id NOT IN (
    'ORG_OWNER', 'ORG_ADMIN', 'B2G_MANAGER', 'RESEARCH_OPERATOR',
    'BID_REVIEWER', 'VIEWER', 'BILLING_ADMIN', 'AUDITOR'
  ) THEN RAISE EXCEPTION 'seat_role_invalid'; END IF;

  SELECT * INTO v_member
  FROM tenant_private.organisation_memberships
  WHERE tenant_id = v_tenant_id
    AND membership_id = p_membership_id
    AND status = 'ACTIVE'
  FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'active_membership_required'; END IF;

  SELECT EXISTS (
    SELECT 1 FROM tenant_private.membership_role_bindings
    WHERE tenant_id = v_tenant_id
      AND membership_id = p_membership_id
      AND role_id = 'ORG_OWNER'
      AND state = 'ACTIVE'
  ) INTO v_current_owner;

  IF v_current_owner AND p_role_id <> 'ORG_OWNER' THEN
    SELECT count(*) INTO v_owner_count
    FROM tenant_private.organisation_memberships m
    JOIN tenant_private.membership_role_bindings rb
      ON rb.tenant_id = m.tenant_id AND rb.membership_id = m.membership_id
    WHERE m.tenant_id = v_tenant_id
      AND m.status = 'ACTIVE'
      AND rb.role_id = 'ORG_OWNER'
      AND rb.state = 'ACTIVE';
    IF v_owner_count <= 1 THEN RAISE EXCEPTION 'last_owner_role_change_forbidden'; END IF;
  END IF;

  UPDATE tenant_private.membership_role_bindings
  SET state = 'REVOKED', revoked_at = p_now
  WHERE tenant_id = v_tenant_id
    AND membership_id = p_membership_id
    AND state = 'ACTIVE';

  INSERT INTO tenant_private.membership_role_bindings (
    tenant_id, membership_id, role_id, state, granted_by, granted_at
  ) VALUES (
    v_tenant_id, p_membership_id, p_role_id, 'ACTIVE',
    p_actor_subject, p_now
  )
  ON CONFLICT (tenant_id, membership_id, role_id) DO UPDATE SET
    state = 'ACTIVE', granted_by = EXCLUDED.granted_by,
    granted_at = EXCLUDED.granted_at, revoked_at = NULL;

  INSERT INTO tenant_private.membership_audit_events (
    tenant_id, event_type, actor_subject, membership_id, payload, occurred_at
  ) VALUES (
    v_tenant_id, 'MEMBERSHIP_ROLE_CHANGED', p_actor_subject,
    p_membership_id, jsonb_build_object('role_id', p_role_id), p_now
  );
  RETURN v_member;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.seat_access_decision(
  p_principal_id text,
  p_write boolean,
  p_now timestamptz DEFAULT now()
)
RETURNS jsonb
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.current_tenant_id();
  v_member tenant_private.organisation_memberships%ROWTYPE;
  v_seat tenant_private.organisation_seat_entitlements%ROWTYPE;
  v_roles jsonb;
BEGIN
  IF v_tenant_id IS NULL THEN
    RETURN jsonb_build_object('decision', 'DENY', 'reason', 'tenant_context_required');
  END IF;

  SELECT * INTO v_member
  FROM tenant_private.organisation_memberships
  WHERE tenant_id = v_tenant_id
    AND principal_id = p_principal_id
    AND status = 'ACTIVE';
  IF NOT FOUND THEN
    RETURN jsonb_build_object('decision', 'DENY', 'reason', 'seat_membership_required');
  END IF;

  SELECT * INTO v_seat
  FROM tenant_private.organisation_seat_entitlements
  WHERE tenant_id = v_tenant_id;
  IF NOT FOUND THEN
    RETURN jsonb_build_object('decision', 'DENY', 'reason', 'seat_entitlement_required');
  END IF;

  IF v_seat.valid_until IS NOT NULL AND v_seat.valid_until <= p_now THEN
    RETURN jsonb_build_object('decision', 'DENY', 'reason', 'seat_entitlement_expired');
  END IF;
  IF v_seat.state IN ('SUSPENDED', 'CANCELLED') THEN
    RETURN jsonb_build_object('decision', 'DENY', 'reason', 'seat_entitlement_inactive');
  END IF;
  IF p_write AND v_seat.state <> 'ACTIVE' THEN
    RETURN jsonb_build_object('decision', 'DENY', 'reason', 'seat_entitlement_read_only');
  END IF;

  SELECT coalesce(jsonb_agg(role_id ORDER BY role_id), '[]'::jsonb) INTO v_roles
  FROM tenant_private.membership_role_bindings
  WHERE tenant_id = v_tenant_id
    AND membership_id = v_member.membership_id
    AND state = 'ACTIVE';

  RETURN jsonb_build_object(
    'decision', 'ALLOW',
    'reason', CASE WHEN v_seat.state = 'READ_ONLY'
                   THEN 'read_only_membership' ELSE 'active_membership' END,
    'membership_id', v_member.membership_id,
    'seat_state', v_seat.state,
    'plan_code', v_seat.plan_code,
    'roles', v_roles
  );
END
$$;

INSERT INTO tenant_private.organisation_seat_entitlements (
  tenant_id, source_entitlement_id, source_billing_selection_id,
  plan_code, billing_model, seat_capacity, state, policy_version,
  valid_from, valid_until, updated_at
)
SELECT
  e.tenant_id, e.entitlement_id, e.billing_selection_id,
  e.plan_code, p.billing_model, p.seat_capacity,
  CASE e.state
    WHEN 'ACTIVE' THEN 'ACTIVE'
    WHEN 'READ_ONLY' THEN 'READ_ONLY'
    WHEN 'SUSPENDED' THEN 'SUSPENDED'
    ELSE 'CANCELLED'
  END,
  p.policy_version, e.starts_at, e.expires_at, now()
FROM tenant_private.organisation_entitlements e
JOIN axignal_global.seat_plan_policies p ON p.plan_code = e.plan_code
ON CONFLICT (tenant_id) DO NOTHING;

GRANT SELECT ON axignal_global.seat_plan_policies TO axignal_app;
GRANT SELECT ON
  tenant_private.organisation_seat_entitlements,
  tenant_private.organisation_memberships,
  tenant_private.organisation_invitations,
  tenant_private.organisation_seat_allocations,
  tenant_private.membership_role_bindings,
  tenant_private.membership_audit_events
TO axignal_app;

REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON
  tenant_private.organisation_seat_entitlements,
  tenant_private.organisation_memberships,
  tenant_private.organisation_invitations,
  tenant_private.organisation_seat_allocations,
  tenant_private.membership_role_bindings,
  tenant_private.membership_audit_events
FROM axignal_app;

REVOKE ALL ON FUNCTION tenant_private.seat_actor_is_admin(text) FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.expire_pending_seat_invitations(text, timestamptz) FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.bootstrap_organisation_owner(text, text, text, timestamptz) FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.reserve_seat_invitation(text, text, text, text, text, text, timestamptz, timestamptz) FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.accept_seat_invitation(text, text, text, text, timestamptz) FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.revoke_seat_invitation(uuid, text, text, timestamptz) FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.revoke_organisation_membership(uuid, text, timestamptz) FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.change_organisation_membership_role(uuid, text, text, timestamptz) FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.seat_access_decision(text, boolean, timestamptz) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION tenant_private.expire_pending_seat_invitations(text, timestamptz) TO axignal_app;
GRANT EXECUTE ON FUNCTION tenant_private.bootstrap_organisation_owner(text, text, text, timestamptz) TO axignal_app;
GRANT EXECUTE ON FUNCTION tenant_private.reserve_seat_invitation(text, text, text, text, text, text, timestamptz, timestamptz) TO axignal_app;
GRANT EXECUTE ON FUNCTION tenant_private.accept_seat_invitation(text, text, text, text, timestamptz) TO axignal_app;
GRANT EXECUTE ON FUNCTION tenant_private.revoke_seat_invitation(uuid, text, text, timestamptz) TO axignal_app;
GRANT EXECUTE ON FUNCTION tenant_private.revoke_organisation_membership(uuid, text, timestamptz) TO axignal_app;
GRANT EXECUTE ON FUNCTION tenant_private.change_organisation_membership_role(uuid, text, text, timestamptz) TO axignal_app;
GRANT EXECUTE ON FUNCTION tenant_private.seat_access_decision(text, boolean, timestamptz) TO axignal_app;
