-- AX-GE2E-P25-T01 identity, passwordless authentication and trial-abuse governance.
-- Identity is global, sessions are opaque and revocable, and a trial belongs to a tenant/economic identity.
-- Browser-supplied tenant identifiers never become authority.

CREATE SCHEMA IF NOT EXISTS identity_private;
REVOKE ALL ON SCHEMA identity_private FROM PUBLIC;

CREATE TABLE IF NOT EXISTS identity_private.users (
  user_id uuid PRIMARY KEY DEFAULT public.gen_random_uuid(),
  subject text NOT NULL UNIQUE DEFAULT (
    'usr_' || replace(public.gen_random_uuid()::text, '-', '')
  ),
  email_normalized text NOT NULL UNIQUE CHECK (
    email_normalized = lower(btrim(email_normalized))
    AND position('@' IN email_normalized) > 1
  ),
  email_hmac text NOT NULL UNIQUE CHECK (email_hmac ~ '^[0-9a-f]{64}$'),
  email_identity_hmac text NOT NULL UNIQUE CHECK (
    email_identity_hmac ~ '^[0-9a-f]{64}$'
  ),
  webauthn_user_handle bytea NOT NULL UNIQUE DEFAULT public.gen_random_bytes(32),
  status text NOT NULL DEFAULT 'ACTIVE' CHECK (
    status IN ('ACTIVE', 'LOCKED', 'RECOVERY_ONLY', 'DELETED')
  ),
  email_verified_at timestamptz NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS identity_private.organisations (
  tenant_id uuid PRIMARY KEY DEFAULT public.gen_random_uuid(),
  status text NOT NULL DEFAULT 'ACTIVE' CHECK (
    status IN ('ACTIVE', 'SUSPENDED', 'DELETED')
  ),
  created_by_user_id uuid NOT NULL REFERENCES identity_private.users(user_id),
  primary_domain_hmac text NOT NULL CHECK (primary_domain_hmac ~ '^[0-9a-f]{64}$'),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS identity_private.user_organisations (
  user_id uuid NOT NULL REFERENCES identity_private.users(user_id),
  tenant_id uuid NOT NULL REFERENCES identity_private.organisations(tenant_id),
  state text NOT NULL DEFAULT 'ACTIVE' CHECK (
    state IN ('ACTIVE', 'SUSPENDED', 'REVOKED')
  ),
  relationship text NOT NULL CHECK (
    relationship IN ('OWNER', 'MEMBER', 'INVITED')
  ),
  created_at timestamptz NOT NULL DEFAULT now(),
  revoked_at timestamptz,
  PRIMARY KEY (user_id, tenant_id)
);

CREATE TABLE IF NOT EXISTS identity_private.email_challenges (
  email_challenge_id uuid PRIMARY KEY DEFAULT public.gen_random_uuid(),
  purpose text NOT NULL CHECK (purpose IN ('SIGNUP', 'EMAIL_CHANGE')),
  token_digest text NOT NULL UNIQUE CHECK (token_digest ~ '^[0-9a-f]{64}$'),
  email_normalized text NOT NULL,
  email_hmac text NOT NULL CHECK (email_hmac ~ '^[0-9a-f]{64}$'),
  email_identity_hmac text NOT NULL CHECK (
    email_identity_hmac ~ '^[0-9a-f]{64}$'
  ),
  domain_hmac text NOT NULL CHECK (domain_hmac ~ '^[0-9a-f]{64}$'),
  installation_hmac text NOT NULL CHECK (
    installation_hmac ~ '^[0-9a-f]{64}$'
  ),
  network_hmac text NOT NULL CHECK (network_hmac ~ '^[0-9a-f]{64}$'),
  disposable_domain boolean NOT NULL DEFAULT false,
  state text NOT NULL DEFAULT 'PENDING' CHECK (
    state IN ('PENDING', 'CONSUMED', 'EXPIRED', 'REVOKED')
  ),
  attempts integer NOT NULL DEFAULT 0 CHECK (attempts BETWEEN 0 AND 20),
  created_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL,
  consumed_at timestamptz,
  CHECK (expires_at > created_at)
);

CREATE UNIQUE INDEX IF NOT EXISTS identity_one_pending_signup_per_email_idx
  ON identity_private.email_challenges (email_identity_hmac, purpose)
  WHERE state = 'PENDING';

CREATE TABLE IF NOT EXISTS identity_private.bootstrap_tickets (
  bootstrap_ticket_id uuid PRIMARY KEY DEFAULT public.gen_random_uuid(),
  token_digest text NOT NULL UNIQUE CHECK (token_digest ~ '^[0-9a-f]{64}$'),
  user_id uuid NOT NULL REFERENCES identity_private.users(user_id),
  tenant_id uuid NOT NULL REFERENCES identity_private.organisations(tenant_id),
  purpose text NOT NULL CHECK (purpose IN ('PASSKEY_REGISTRATION', 'RECOVERY')),
  state text NOT NULL DEFAULT 'PENDING' CHECK (
    state IN ('PENDING', 'OPTIONS_ISSUED', 'CONSUMED', 'EXPIRED', 'REVOKED')
  ),
  created_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL,
  consumed_at timestamptz,
  CHECK (expires_at > created_at)
);

CREATE TABLE IF NOT EXISTS identity_private.webauthn_challenges (
  webauthn_challenge_id uuid PRIMARY KEY DEFAULT public.gen_random_uuid(),
  challenge_value text NOT NULL UNIQUE CHECK (
    challenge_value ~ '^[A-Za-z0-9_-]{20,}$'
  ),
  challenge_digest text NOT NULL UNIQUE CHECK (
    challenge_digest ~ '^[0-9a-f]{64}$'
  ),
  purpose text NOT NULL CHECK (
    purpose IN ('REGISTRATION', 'AUTHENTICATION', 'RECOVERY_REGISTRATION')
  ),
  user_id uuid REFERENCES identity_private.users(user_id),
  bootstrap_ticket_id uuid
    REFERENCES identity_private.bootstrap_tickets(bootstrap_ticket_id),
  rp_id text NOT NULL,
  expected_origin text NOT NULL,
  state text NOT NULL DEFAULT 'PENDING' CHECK (
    state IN ('PENDING', 'CONSUMED', 'EXPIRED', 'REVOKED')
  ),
  created_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL,
  consumed_at timestamptz,
  CHECK (expires_at > created_at)
);

CREATE TABLE IF NOT EXISTS identity_private.webauthn_credentials (
  authenticator_id uuid PRIMARY KEY DEFAULT public.gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES identity_private.users(user_id),
  credential_id text NOT NULL UNIQUE CHECK (
    credential_id ~ '^[A-Za-z0-9_-]{20,}$'
  ),
  credential_public_key bytea NOT NULL,
  sign_count bigint NOT NULL DEFAULT 0 CHECK (sign_count >= 0),
  transports text[] NOT NULL DEFAULT '{}',
  device_type text NOT NULL CHECK (
    device_type IN ('SINGLE_DEVICE', 'MULTI_DEVICE', 'UNKNOWN')
  ),
  backed_up boolean NOT NULL DEFAULT false,
  aaguid text,
  state text NOT NULL DEFAULT 'ACTIVE' CHECK (
    state IN ('ACTIVE', 'REVOKED', 'COMPROMISED')
  ),
  created_at timestamptz NOT NULL DEFAULT now(),
  last_used_at timestamptz,
  revoked_at timestamptz
);

CREATE TABLE IF NOT EXISTS identity_private.identity_sessions (
  session_id uuid PRIMARY KEY DEFAULT public.gen_random_uuid(),
  token_digest text NOT NULL UNIQUE CHECK (token_digest ~ '^[0-9a-f]{64}$'),
  user_id uuid NOT NULL REFERENCES identity_private.users(user_id),
  active_tenant_id uuid NOT NULL REFERENCES identity_private.organisations(tenant_id),
  auth_method text NOT NULL CHECK (
    auth_method IN ('PASSKEY', 'RECOVERY', 'PILOT_PASSWORD')
  ),
  assurance_level text NOT NULL CHECK (
    assurance_level IN ('AAL1', 'AAL2', 'RECOVERY_RESTRICTED')
  ),
  state text NOT NULL DEFAULT 'ACTIVE' CHECK (
    state IN ('ACTIVE', 'REVOKED', 'EXPIRED')
  ),
  installation_hmac text CHECK (installation_hmac ~ '^[0-9a-f]{64}$'),
  network_hmac text CHECK (network_hmac ~ '^[0-9a-f]{64}$'),
  user_agent_hmac text CHECK (user_agent_hmac ~ '^[0-9a-f]{64}$'),
  authenticated_at timestamptz NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  last_seen_at timestamptz NOT NULL,
  idle_expires_at timestamptz NOT NULL,
  absolute_expires_at timestamptz NOT NULL,
  step_up_valid_until timestamptz,
  revoked_at timestamptz,
  revoke_reason text,
  CHECK (idle_expires_at <= absolute_expires_at)
);

CREATE INDEX IF NOT EXISTS identity_sessions_user_active_idx
  ON identity_private.identity_sessions (user_id, state, absolute_expires_at);

CREATE TABLE IF NOT EXISTS identity_private.recovery_codes (
  recovery_code_id uuid PRIMARY KEY DEFAULT public.gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES identity_private.users(user_id),
  code_digest text NOT NULL UNIQUE CHECK (code_digest ~ '^[0-9a-f]{64}$'),
  state text NOT NULL DEFAULT 'ACTIVE' CHECK (
    state IN ('ACTIVE', 'CONSUMED', 'REVOKED')
  ),
  created_at timestamptz NOT NULL DEFAULT now(),
  consumed_at timestamptz
);

CREATE TABLE IF NOT EXISTS identity_private.identity_rate_limits (
  key_hmac text NOT NULL CHECK (key_hmac ~ '^[0-9a-f]{64}$'),
  route_key text NOT NULL,
  window_started_at timestamptz NOT NULL,
  request_count integer NOT NULL CHECK (request_count >= 0),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (key_hmac, route_key)
);

CREATE TABLE IF NOT EXISTS identity_private.security_events (
  security_event_id uuid PRIMARY KEY DEFAULT public.gen_random_uuid(),
  event_type text NOT NULL,
  user_id uuid REFERENCES identity_private.users(user_id),
  tenant_id uuid,
  session_id uuid,
  actor_subject text,
  decision text,
  reason_codes jsonb NOT NULL DEFAULT '[]'::jsonb,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  occurred_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS identity_private.trial_grants (
  trial_grant_id uuid PRIMARY KEY DEFAULT public.gen_random_uuid(),
  tenant_id uuid NOT NULL UNIQUE REFERENCES identity_private.organisations(tenant_id),
  requested_by_user_id uuid NOT NULL REFERENCES identity_private.users(user_id),
  state text NOT NULL CHECK (
    state IN (
      'ELIGIBILITY_PENDING', 'READY', 'ACTIVE', 'EXPIRED',
      'CONVERTED', 'SUSPENDED_ABUSE', 'REVOKED'
    )
  ),
  decision text NOT NULL CHECK (
    decision IN (
      'ALLOW', 'ALLOW_RESTRICTED', 'REUSE_EXISTING_TRIAL',
      'STEP_UP_REQUIRED', 'MANUAL_REVIEW', 'BLOCK_ABUSE'
    )
  ),
  risk_score integer NOT NULL CHECK (risk_score BETWEEN 0 AND 100),
  risk_policy_version text NOT NULL,
  reason_codes jsonb NOT NULL DEFAULT '[]'::jsonb,
  seat_capacity integer NOT NULL DEFAULT 2 CHECK (seat_capacity = 2),
  token_budget_ceiling bigint NOT NULL CHECK (
    token_budget_ceiling BETWEEN 1 AND 1000000
  ),
  cost_budget_microunits bigint NOT NULL CHECK (cost_budget_microunits > 0),
  cost_microunits_per_token integer NOT NULL DEFAULT 5 CHECK (
    cost_microunits_per_token BETWEEN 1 AND 1000
  ),
  max_concurrent_runs integer NOT NULL DEFAULT 1 CHECK (
    max_concurrent_runs BETWEEN 1 AND 4
  ),
  max_documents_per_run integer NOT NULL DEFAULT 25 CHECK (
    max_documents_per_run BETWEEN 1 AND 500
  ),
  bulk_export_allowed boolean NOT NULL DEFAULT false,
  private_connectors_allowed boolean NOT NULL DEFAULT false,
  prepared_at timestamptz NOT NULL DEFAULT now(),
  started_at timestamptz,
  expires_at timestamptz,
  converted_at timestamptz,
  suspended_at timestamptz,
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (
    (state = 'ACTIVE' AND started_at IS NOT NULL
      AND expires_at = started_at + interval '7 days')
    OR state <> 'ACTIVE'
  )
);

CREATE TABLE IF NOT EXISTS identity_private.trial_risk_decisions (
  risk_decision_id uuid PRIMARY KEY DEFAULT public.gen_random_uuid(),
  operation_id text NOT NULL UNIQUE,
  user_id uuid NOT NULL REFERENCES identity_private.users(user_id),
  tenant_id uuid NOT NULL REFERENCES identity_private.organisations(tenant_id),
  decision text NOT NULL,
  risk_score integer NOT NULL CHECK (risk_score BETWEEN 0 AND 100),
  reason_codes jsonb NOT NULL,
  policy_version text NOT NULL,
  evaluated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS identity_private.trial_subject_claims (
  trial_subject_claim_id uuid PRIMARY KEY DEFAULT public.gen_random_uuid(),
  trial_grant_id uuid NOT NULL REFERENCES identity_private.trial_grants(trial_grant_id),
  user_id uuid NOT NULL REFERENCES identity_private.users(user_id),
  tenant_id uuid NOT NULL REFERENCES identity_private.organisations(tenant_id),
  claim_type text NOT NULL CHECK (
    claim_type IN (
      'EMAIL_IDENTITY', 'VERIFIED_PHONE', 'PAYMENT_INSTRUMENT',
      'INSTALLATION', 'NETWORK_PREFIX', 'DOMAIN'
    )
  ),
  claim_hmac text NOT NULL CHECK (claim_hmac ~ '^[0-9a-f]{64}$'),
  strength text NOT NULL CHECK (strength IN ('STRONG', 'WEAK')),
  state text NOT NULL DEFAULT 'ACTIVE' CHECK (state IN ('ACTIVE', 'REVOKED')),
  created_at timestamptz NOT NULL DEFAULT now(),
  revoked_at timestamptz,
  UNIQUE (trial_grant_id, claim_type, claim_hmac)
);

CREATE UNIQUE INDEX IF NOT EXISTS trial_strong_claim_once_idx
  ON identity_private.trial_subject_claims (claim_type, claim_hmac)
  WHERE state = 'ACTIVE'
    AND claim_type IN ('EMAIL_IDENTITY', 'VERIFIED_PHONE', 'PAYMENT_INSTRUMENT');

CREATE INDEX IF NOT EXISTS trial_weak_claim_lookup_idx
  ON identity_private.trial_subject_claims (claim_type, claim_hmac, created_at)
  WHERE state = 'ACTIVE';

CREATE TABLE IF NOT EXISTS identity_private.trial_usage_accounts (
  trial_grant_id uuid PRIMARY KEY REFERENCES identity_private.trial_grants(trial_grant_id),
  tenant_id uuid NOT NULL UNIQUE REFERENCES identity_private.organisations(tenant_id),
  token_budget_total bigint NOT NULL,
  token_budget_reserved bigint NOT NULL DEFAULT 0 CHECK (token_budget_reserved >= 0),
  token_budget_consumed bigint NOT NULL DEFAULT 0 CHECK (token_budget_consumed >= 0),
  cost_budget_microunits bigint NOT NULL,
  cost_reserved_microunits bigint NOT NULL DEFAULT 0 CHECK (
    cost_reserved_microunits >= 0
  ),
  cost_consumed_microunits bigint NOT NULL DEFAULT 0 CHECK (
    cost_consumed_microunits >= 0
  ),
  active_runs integer NOT NULL DEFAULT 0 CHECK (active_runs >= 0),
  max_concurrent_runs integer NOT NULL DEFAULT 1,
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (token_budget_reserved + token_budget_consumed <= token_budget_total),
  CHECK (
    cost_reserved_microunits + cost_consumed_microunits
    <= cost_budget_microunits
  )
);

CREATE TABLE IF NOT EXISTS identity_private.trial_cost_reservations (
  trial_cost_reservation_id uuid PRIMARY KEY DEFAULT public.gen_random_uuid(),
  trial_grant_id uuid NOT NULL REFERENCES identity_private.trial_grants(trial_grant_id),
  tenant_id uuid NOT NULL,
  token_reservation_id uuid NOT NULL UNIQUE
    REFERENCES tenant_private.ai_token_reservations(reservation_id),
  requested_tokens bigint NOT NULL CHECK (requested_tokens > 0),
  actual_tokens bigint,
  requested_cost_microunits bigint NOT NULL CHECK (requested_cost_microunits > 0),
  actual_cost_microunits bigint,
  state text NOT NULL DEFAULT 'RESERVED' CHECK (
    state IN ('RESERVED', 'RECONCILED', 'RELEASED')
  ),
  created_at timestamptz NOT NULL DEFAULT now(),
  reconciled_at timestamptz
);

CREATE TABLE IF NOT EXISTS identity_private.trial_abuse_events (
  trial_abuse_event_id uuid PRIMARY KEY DEFAULT public.gen_random_uuid(),
  trial_grant_id uuid REFERENCES identity_private.trial_grants(trial_grant_id),
  user_id uuid REFERENCES identity_private.users(user_id),
  tenant_id uuid,
  event_type text NOT NULL,
  decision text,
  reason_codes jsonb NOT NULL DEFAULT '[]'::jsonb,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  occurred_at timestamptz NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION identity_private.reject_append_only_mutation()
RETURNS trigger
LANGUAGE plpgsql
SET search_path TO pg_catalog
AS $$
BEGIN
  RAISE EXCEPTION 'identity_append_only_ledger';
END
$$;

DROP TRIGGER IF EXISTS identity_security_events_immutable
  ON identity_private.security_events;
CREATE TRIGGER identity_security_events_immutable
BEFORE UPDATE OR DELETE ON identity_private.security_events
FOR EACH ROW EXECUTE FUNCTION identity_private.reject_append_only_mutation();

DROP TRIGGER IF EXISTS trial_risk_decisions_immutable
  ON identity_private.trial_risk_decisions;
CREATE TRIGGER trial_risk_decisions_immutable
BEFORE UPDATE OR DELETE ON identity_private.trial_risk_decisions
FOR EACH ROW EXECUTE FUNCTION identity_private.reject_append_only_mutation();

DROP TRIGGER IF EXISTS trial_abuse_events_immutable
  ON identity_private.trial_abuse_events;
CREATE TRIGGER trial_abuse_events_immutable
BEFORE UPDATE OR DELETE ON identity_private.trial_abuse_events
FOR EACH ROW EXECUTE FUNCTION identity_private.reject_append_only_mutation();

CREATE OR REPLACE FUNCTION identity_private.consume_rate_limit(
  p_key_hmac text,
  p_route_key text,
  p_limit integer,
  p_window_seconds integer,
  p_now timestamptz DEFAULT now()
)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_row identity_private.identity_rate_limits%ROWTYPE;
BEGIN
  IF p_key_hmac !~ '^[0-9a-f]{64}$' OR p_limit < 1
     OR p_window_seconds < 1 THEN
    RAISE EXCEPTION 'rate_limit_input_invalid';
  END IF;

  SELECT * INTO v_row
  FROM identity_private.identity_rate_limits
  WHERE key_hmac = p_key_hmac AND route_key = p_route_key
  FOR UPDATE;

  IF NOT FOUND THEN
    INSERT INTO identity_private.identity_rate_limits (
      key_hmac, route_key, window_started_at, request_count, updated_at
    ) VALUES (p_key_hmac, p_route_key, p_now, 1, p_now);
    RETURN true;
  END IF;

  IF v_row.window_started_at + make_interval(secs => p_window_seconds) <= p_now THEN
    UPDATE identity_private.identity_rate_limits
    SET window_started_at = p_now, request_count = 1, updated_at = p_now
    WHERE key_hmac = p_key_hmac AND route_key = p_route_key;
    RETURN true;
  END IF;

  IF v_row.request_count >= p_limit THEN
    RETURN false;
  END IF;

  UPDATE identity_private.identity_rate_limits
  SET request_count = request_count + 1, updated_at = p_now
  WHERE key_hmac = p_key_hmac AND route_key = p_route_key;
  RETURN true;
END
$$;
