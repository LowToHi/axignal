CREATE OR REPLACE FUNCTION identity_private.complete_passkey_registration(
  p_challenge_digest text,
  p_bootstrap_ticket_digest text,
  p_credential_id text,
  p_public_key_hex text,
  p_sign_count bigint,
  p_transports text[],
  p_device_type text,
  p_backed_up boolean,
  p_aaguid text,
  p_session_token_digest text,
  p_installation_hmac text,
  p_network_hmac text,
  p_user_agent_hmac text,
  p_recovery_code_digests text[],
  p_idle_seconds integer,
  p_absolute_seconds integer,
  p_now timestamptz DEFAULT now()
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_challenge identity_private.webauthn_challenges%ROWTYPE;
  v_ticket identity_private.bootstrap_tickets%ROWTYPE;
  v_user identity_private.users%ROWTYPE;
  v_authenticator identity_private.webauthn_credentials%ROWTYPE;
  v_session identity_private.identity_sessions%ROWTYPE;
  v_digest text;
BEGIN
  SELECT * INTO v_challenge
  FROM identity_private.webauthn_challenges
  WHERE challenge_digest = p_challenge_digest
    AND purpose IN ('REGISTRATION', 'RECOVERY_REGISTRATION')
    AND state = 'PENDING'
  FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'webauthn_challenge_not_found'; END IF;
  IF v_challenge.expires_at <= p_now THEN RAISE EXCEPTION 'webauthn_challenge_expired'; END IF;

  SELECT * INTO v_ticket
  FROM identity_private.bootstrap_tickets
  WHERE token_digest = p_bootstrap_ticket_digest
    AND bootstrap_ticket_id = v_challenge.bootstrap_ticket_id
    AND state = 'OPTIONS_ISSUED'
  FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'bootstrap_ticket_not_found'; END IF;
  IF v_ticket.expires_at <= p_now THEN RAISE EXCEPTION 'bootstrap_ticket_expired'; END IF;

  SELECT * INTO v_user
  FROM identity_private.users
  WHERE user_id = v_ticket.user_id
  FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'identity_user_unavailable'; END IF;

  IF v_ticket.purpose = 'RECOVERY' THEN
    UPDATE identity_private.webauthn_credentials
    SET state = 'REVOKED', revoked_at = p_now
    WHERE user_id = v_user.user_id AND state = 'ACTIVE';
    UPDATE identity_private.identity_sessions
    SET state = 'REVOKED', revoked_at = p_now,
        revoke_reason = 'ACCOUNT_RECOVERY'
    WHERE user_id = v_user.user_id AND state = 'ACTIVE';
    UPDATE identity_private.users
    SET status = 'ACTIVE', updated_at = p_now
    WHERE user_id = v_user.user_id;
  END IF;

  INSERT INTO identity_private.webauthn_credentials (
    user_id, credential_id, credential_public_key, sign_count,
    transports, device_type, backed_up, aaguid, state, created_at
  ) VALUES (
    v_user.user_id, p_credential_id, decode(p_public_key_hex, 'hex'),
    p_sign_count, coalesce(p_transports, '{}'), p_device_type,
    p_backed_up, p_aaguid, 'ACTIVE', p_now
  ) RETURNING * INTO v_authenticator;

  DELETE FROM identity_private.recovery_codes
  WHERE user_id = v_user.user_id;

  FOREACH v_digest IN ARRAY p_recovery_code_digests LOOP
    IF v_digest !~ '^[0-9a-f]{64}$' THEN
      RAISE EXCEPTION 'recovery_code_digest_invalid';
    END IF;
    INSERT INTO identity_private.recovery_codes (
      user_id, code_digest, state, created_at
    ) VALUES (v_user.user_id, v_digest, 'ACTIVE', p_now);
  END LOOP;

  INSERT INTO identity_private.identity_sessions (
    token_digest, user_id, active_tenant_id, auth_method,
    assurance_level, state, installation_hmac, network_hmac,
    user_agent_hmac, authenticated_at, created_at, last_seen_at,
    idle_expires_at, absolute_expires_at, step_up_valid_until
  ) VALUES (
    p_session_token_digest, v_user.user_id, v_ticket.tenant_id,
    'PASSKEY', 'AAL2', 'ACTIVE', p_installation_hmac,
    p_network_hmac, p_user_agent_hmac, p_now, p_now, p_now,
    p_now + make_interval(secs => p_idle_seconds),
    p_now + make_interval(secs => p_absolute_seconds),
    p_now + interval '10 minutes'
  ) RETURNING * INTO v_session;

  UPDATE identity_private.webauthn_challenges
  SET state = 'CONSUMED', consumed_at = p_now
  WHERE webauthn_challenge_id = v_challenge.webauthn_challenge_id;
  UPDATE identity_private.bootstrap_tickets
  SET state = 'CONSUMED', consumed_at = p_now
  WHERE bootstrap_ticket_id = v_ticket.bootstrap_ticket_id;

  INSERT INTO identity_private.security_events (
    event_type, user_id, tenant_id, session_id, actor_subject,
    decision, metadata, occurred_at
  ) VALUES (
    'PASSKEY_BOUND', v_user.user_id, v_ticket.tenant_id,
    v_session.session_id, v_user.subject, 'ALLOW',
    jsonb_build_object(
      'authenticator_id', v_authenticator.authenticator_id,
      'recovery', v_ticket.purpose = 'RECOVERY'
    ), p_now
  );

  RETURN jsonb_build_object(
    'user_id', v_user.user_id,
    'subject', v_user.subject,
    'email', v_user.email_normalized,
    'tenant_id', v_ticket.tenant_id,
    'session_id', v_session.session_id,
    'authenticator_id', v_authenticator.authenticator_id,
    'assurance_level', v_session.assurance_level
  );
END
$$;

CREATE OR REPLACE FUNCTION identity_private.complete_passkey_authentication(
  p_challenge_digest text,
  p_credential_id text,
  p_new_sign_count bigint,
  p_session_token_digest text,
  p_installation_hmac text,
  p_network_hmac text,
  p_user_agent_hmac text,
  p_idle_seconds integer,
  p_absolute_seconds integer,
  p_now timestamptz DEFAULT now()
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_challenge identity_private.webauthn_challenges%ROWTYPE;
  v_authenticator identity_private.webauthn_credentials%ROWTYPE;
  v_user identity_private.users%ROWTYPE;
  v_tenant_id uuid;
  v_session identity_private.identity_sessions%ROWTYPE;
BEGIN
  SELECT * INTO v_challenge
  FROM identity_private.webauthn_challenges
  WHERE challenge_digest = p_challenge_digest
    AND purpose = 'AUTHENTICATION'
    AND state = 'PENDING'
  FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'webauthn_challenge_not_found'; END IF;
  IF v_challenge.expires_at <= p_now THEN RAISE EXCEPTION 'webauthn_challenge_expired'; END IF;

  SELECT * INTO v_authenticator
  FROM identity_private.webauthn_credentials
  WHERE credential_id = p_credential_id AND state = 'ACTIVE'
  FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'webauthn_credential_not_found'; END IF;
  IF p_new_sign_count < v_authenticator.sign_count THEN
    UPDATE identity_private.webauthn_credentials
    SET state = 'COMPROMISED', revoked_at = p_now
    WHERE authenticator_id = v_authenticator.authenticator_id;
    RAISE EXCEPTION 'webauthn_sign_count_regression';
  END IF;

  SELECT * INTO v_user
  FROM identity_private.users
  WHERE user_id = v_authenticator.user_id AND status = 'ACTIVE';
  IF NOT FOUND THEN RAISE EXCEPTION 'identity_user_unavailable'; END IF;

  SELECT tenant_id INTO v_tenant_id
  FROM identity_private.user_organisations
  WHERE user_id = v_user.user_id AND state = 'ACTIVE'
  ORDER BY (relationship = 'OWNER') DESC, created_at
  LIMIT 1;
  IF v_tenant_id IS NULL THEN RAISE EXCEPTION 'identity_tenant_unavailable'; END IF;

  UPDATE identity_private.webauthn_credentials
  SET sign_count = greatest(sign_count, p_new_sign_count),
      last_used_at = p_now
  WHERE authenticator_id = v_authenticator.authenticator_id;

  INSERT INTO identity_private.identity_sessions (
    token_digest, user_id, active_tenant_id, auth_method,
    assurance_level, state, installation_hmac, network_hmac,
    user_agent_hmac, authenticated_at, created_at, last_seen_at,
    idle_expires_at, absolute_expires_at, step_up_valid_until
  ) VALUES (
    p_session_token_digest, v_user.user_id, v_tenant_id,
    'PASSKEY', 'AAL2', 'ACTIVE', p_installation_hmac,
    p_network_hmac, p_user_agent_hmac, p_now, p_now, p_now,
    p_now + make_interval(secs => p_idle_seconds),
    p_now + make_interval(secs => p_absolute_seconds),
    p_now + interval '10 minutes'
  ) RETURNING * INTO v_session;

  UPDATE identity_private.webauthn_challenges
  SET state = 'CONSUMED', consumed_at = p_now
  WHERE webauthn_challenge_id = v_challenge.webauthn_challenge_id;

  INSERT INTO identity_private.security_events (
    event_type, user_id, tenant_id, session_id, actor_subject,
    decision, metadata, occurred_at
  ) VALUES (
    'LOGIN_SUCCEEDED', v_user.user_id, v_tenant_id,
    v_session.session_id, v_user.subject, 'ALLOW',
    jsonb_build_object('auth_method', 'PASSKEY'), p_now
  );

  RETURN jsonb_build_object(
    'user_id', v_user.user_id,
    'subject', v_user.subject,
    'email', v_user.email_normalized,
    'tenant_id', v_tenant_id,
    'session_id', v_session.session_id,
    'assurance_level', v_session.assurance_level
  );
END
$$;

CREATE OR REPLACE FUNCTION identity_private.resolve_identity_session(
  p_token_digest text,
  p_touch_interval_seconds integer,
  p_now timestamptz DEFAULT now()
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_session identity_private.identity_sessions%ROWTYPE;
  v_user identity_private.users%ROWTYPE;
  v_membership_id uuid;
  v_roles jsonb := '[]'::jsonb;
  v_grant_state text;
BEGIN
  SELECT * INTO v_session
  FROM identity_private.identity_sessions
  WHERE token_digest = p_token_digest
  FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'identity_session_not_found'; END IF;
  IF v_session.state <> 'ACTIVE'
     OR v_session.absolute_expires_at <= p_now
     OR v_session.idle_expires_at <= p_now THEN
    UPDATE identity_private.identity_sessions
    SET state = 'EXPIRED'
    WHERE session_id = v_session.session_id AND state = 'ACTIVE';
    RAISE EXCEPTION 'identity_session_expired';
  END IF;

  SELECT * INTO v_user
  FROM identity_private.users
  WHERE user_id = v_session.user_id AND status = 'ACTIVE';
  IF NOT FOUND THEN RAISE EXCEPTION 'identity_user_unavailable'; END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM identity_private.user_organisations
    WHERE user_id = v_user.user_id
      AND tenant_id = v_session.active_tenant_id
      AND state = 'ACTIVE'
  ) THEN
    RAISE EXCEPTION 'identity_tenant_membership_required';
  END IF;

  SELECT m.membership_id INTO v_membership_id
  FROM tenant_private.organisation_memberships m
  WHERE m.tenant_id = v_session.active_tenant_id
    AND m.principal_id = v_user.subject
    AND m.status = 'ACTIVE';

  IF v_membership_id IS NOT NULL THEN
    SELECT coalesce(jsonb_agg(rb.role_id ORDER BY rb.role_id), '[]'::jsonb)
    INTO v_roles
    FROM tenant_private.membership_role_bindings rb
    WHERE rb.tenant_id = v_session.active_tenant_id
      AND rb.membership_id = v_membership_id
      AND rb.state = 'ACTIVE';
  ELSE
    SELECT state INTO v_grant_state
    FROM identity_private.trial_grants
    WHERE tenant_id = v_session.active_tenant_id;
    IF v_grant_state NOT IN ('READY', 'ELIGIBILITY_PENDING') THEN
      RAISE EXCEPTION 'seat_membership_required';
    END IF;
  END IF;

  IF v_session.last_seen_at
     + make_interval(secs => p_touch_interval_seconds) <= p_now THEN
    UPDATE identity_private.identity_sessions
    SET last_seen_at = p_now,
        idle_expires_at = least(
          p_now + (idle_expires_at - last_seen_at),
          absolute_expires_at
        )
    WHERE session_id = v_session.session_id
    RETURNING * INTO v_session;
  END IF;

  RETURN jsonb_build_object(
    'session_id', v_session.session_id,
    'user_id', v_user.user_id,
    'subject', v_user.subject,
    'email', v_user.email_normalized,
    'tenant_id', v_session.active_tenant_id,
    'membership_id', v_membership_id,
    'roles', v_roles,
    'auth_method', v_session.auth_method,
    'assurance_level', v_session.assurance_level,
    'authenticated_at', v_session.authenticated_at,
    'step_up_valid_until', v_session.step_up_valid_until,
    'absolute_expires_at', v_session.absolute_expires_at
  );
END
$$;

CREATE OR REPLACE FUNCTION identity_private.revoke_identity_session(
  p_token_digest text,
  p_reason text,
  p_now timestamptz DEFAULT now()
)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_session identity_private.identity_sessions%ROWTYPE;
BEGIN
  UPDATE identity_private.identity_sessions
  SET state = 'REVOKED', revoked_at = p_now,
      revoke_reason = left(coalesce(p_reason, 'LOGOUT'), 200)
  WHERE token_digest = p_token_digest AND state = 'ACTIVE'
  RETURNING * INTO v_session;
  IF NOT FOUND THEN RETURN false; END IF;

  INSERT INTO identity_private.security_events (
    event_type, user_id, tenant_id, session_id, decision,
    metadata, occurred_at
  ) VALUES (
    'SESSION_REVOKED', v_session.user_id, v_session.active_tenant_id,
    v_session.session_id, 'ALLOW',
    jsonb_build_object('reason', p_reason), p_now
  );
  RETURN true;
END
$$;

CREATE OR REPLACE FUNCTION identity_private.begin_recovery(
  p_email_identity_hmac text,
  p_code_digest text,
  p_recovery_ticket_digest text,
  p_now timestamptz DEFAULT now()
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_user identity_private.users%ROWTYPE;
  v_code identity_private.recovery_codes%ROWTYPE;
  v_tenant_id uuid;
  v_ticket identity_private.bootstrap_tickets%ROWTYPE;
BEGIN
  SELECT * INTO v_user
  FROM identity_private.users
  WHERE email_identity_hmac = p_email_identity_hmac
    AND status IN ('ACTIVE', 'RECOVERY_ONLY')
  FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'recovery_credentials_invalid'; END IF;

  SELECT * INTO v_code
  FROM identity_private.recovery_codes
  WHERE user_id = v_user.user_id
    AND code_digest = p_code_digest
    AND state = 'ACTIVE'
  FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'recovery_credentials_invalid'; END IF;

  SELECT tenant_id INTO v_tenant_id
  FROM identity_private.user_organisations
  WHERE user_id = v_user.user_id AND state = 'ACTIVE'
  ORDER BY (relationship = 'OWNER') DESC, created_at
  LIMIT 1;
  IF v_tenant_id IS NULL THEN RAISE EXCEPTION 'identity_tenant_unavailable'; END IF;

  UPDATE identity_private.recovery_codes
  SET state = 'CONSUMED', consumed_at = p_now
  WHERE recovery_code_id = v_code.recovery_code_id;
  UPDATE identity_private.users
  SET status = 'RECOVERY_ONLY', updated_at = p_now
  WHERE user_id = v_user.user_id;
  UPDATE identity_private.identity_sessions
  SET state = 'REVOKED', revoked_at = p_now,
      revoke_reason = 'RECOVERY_STARTED'
  WHERE user_id = v_user.user_id AND state = 'ACTIVE';

  INSERT INTO identity_private.bootstrap_tickets (
    token_digest, user_id, tenant_id, purpose, state,
    created_at, expires_at
  ) VALUES (
    p_recovery_ticket_digest, v_user.user_id, v_tenant_id,
    'RECOVERY', 'PENDING', p_now, p_now + interval '10 minutes'
  ) RETURNING * INTO v_ticket;

  INSERT INTO identity_private.security_events (
    event_type, user_id, tenant_id, actor_subject,
    decision, metadata, occurred_at
  ) VALUES (
    'RECOVERY_STARTED', v_user.user_id, v_tenant_id,
    v_user.subject, 'ALLOW',
    jsonb_build_object('ticket_id', v_ticket.bootstrap_ticket_id), p_now
  );

  RETURN jsonb_build_object(
    'user_id', v_user.user_id,
    'subject', v_user.subject,
    'email', v_user.email_normalized,
    'tenant_id', v_tenant_id,
    'bootstrap_ticket_id', v_ticket.bootstrap_ticket_id
  );
END
$$;

CREATE OR REPLACE FUNCTION identity_private.trial_status_for_tenant(
  p_tenant_id uuid
)
RETURNS jsonb
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
  SELECT jsonb_build_object(
    'trial_grant_id', g.trial_grant_id,
    'tenant_id', g.tenant_id,
    'state', g.state,
    'decision', g.decision,
    'risk_score', g.risk_score,
    'reason_codes', g.reason_codes,
    'token_budget_ceiling', g.token_budget_ceiling,
    'cost_budget_microunits', g.cost_budget_microunits,
    'prepared_at', g.prepared_at,
    'started_at', g.started_at,
    'expires_at', g.expires_at
  )
  FROM identity_private.trial_grants g
  WHERE g.tenant_id = p_tenant_id
$$;

CREATE OR REPLACE FUNCTION identity_private.approve_trial_step_up(
  p_tenant_id uuid,
  p_user_id uuid,
  p_claim_type text,
  p_claim_hmac text,
  p_actor_subject text,
  p_full_token_budget bigint,
  p_full_cost_budget_microunits bigint,
  p_now timestamptz DEFAULT now()
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_grant identity_private.trial_grants%ROWTYPE;
BEGIN
  IF p_claim_type NOT IN ('VERIFIED_PHONE', 'PAYMENT_INSTRUMENT') THEN
    RAISE EXCEPTION 'trial_step_up_claim_invalid';
  END IF;
  IF p_claim_hmac !~ '^[0-9a-f]{64}$' THEN
    RAISE EXCEPTION 'trial_step_up_digest_invalid';
  END IF;

  SELECT * INTO v_grant
  FROM identity_private.trial_grants
  WHERE tenant_id = p_tenant_id
    AND requested_by_user_id = p_user_id
    AND state = 'ELIGIBILITY_PENDING'
  FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'trial_step_up_not_pending'; END IF;

  INSERT INTO identity_private.trial_subject_claims (
    trial_grant_id, user_id, tenant_id, claim_type,
    claim_hmac, strength, state, created_at
  ) VALUES (
    v_grant.trial_grant_id, p_user_id, p_tenant_id, p_claim_type,
    p_claim_hmac, 'STRONG', 'ACTIVE', p_now
  );

  UPDATE identity_private.trial_grants
  SET state = 'READY', decision = 'ALLOW',
      risk_score = least(risk_score, 20),
      reason_codes = reason_codes || jsonb_build_array('step_up_verified'),
      token_budget_ceiling = p_full_token_budget,
      cost_budget_microunits = p_full_cost_budget_microunits,
      updated_at = p_now
  WHERE trial_grant_id = v_grant.trial_grant_id
  RETURNING * INTO v_grant;

  INSERT INTO identity_private.trial_abuse_events (
    trial_grant_id, user_id, tenant_id, event_type,
    decision, reason_codes, metadata, occurred_at
  ) VALUES (
    v_grant.trial_grant_id, p_user_id, p_tenant_id,
    'TRIAL_STEP_UP_VERIFIED', 'ALLOW',
    jsonb_build_array('step_up_verified'),
    jsonb_build_object('claim_type', p_claim_type, 'actor', p_actor_subject),
    p_now
  );

  RETURN to_jsonb(v_grant);
END
$$;
