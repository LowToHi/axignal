CREATE OR REPLACE FUNCTION identity_private.begin_email_challenge(
  p_purpose text,
  p_token_digest text,
  p_email_normalized text,
  p_email_hmac text,
  p_email_identity_hmac text,
  p_domain_hmac text,
  p_installation_hmac text,
  p_network_hmac text,
  p_disposable_domain boolean,
  p_expires_at timestamptz,
  p_now timestamptz DEFAULT now()
)
RETURNS identity_private.email_challenges
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_row identity_private.email_challenges%ROWTYPE;
BEGIN
  IF p_purpose NOT IN ('SIGNUP', 'EMAIL_CHANGE') THEN
    RAISE EXCEPTION 'email_challenge_purpose_invalid';
  END IF;
  IF p_token_digest !~ '^[0-9a-f]{64}$'
     OR p_email_hmac !~ '^[0-9a-f]{64}$'
     OR p_email_identity_hmac !~ '^[0-9a-f]{64}$'
     OR p_domain_hmac !~ '^[0-9a-f]{64}$'
     OR p_installation_hmac !~ '^[0-9a-f]{64}$'
     OR p_network_hmac !~ '^[0-9a-f]{64}$' THEN
    RAISE EXCEPTION 'email_challenge_digest_invalid';
  END IF;
  IF p_expires_at <= p_now OR p_expires_at > p_now + interval '30 minutes' THEN
    RAISE EXCEPTION 'email_challenge_expiry_invalid';
  END IF;

  UPDATE identity_private.email_challenges
  SET state = 'REVOKED'
  WHERE email_identity_hmac = p_email_identity_hmac
    AND purpose = p_purpose
    AND state = 'PENDING';

  INSERT INTO identity_private.email_challenges (
    purpose, token_digest, email_normalized, email_hmac,
    email_identity_hmac, domain_hmac, installation_hmac,
    network_hmac, disposable_domain, state, created_at, expires_at
  ) VALUES (
    p_purpose, p_token_digest, lower(btrim(p_email_normalized)),
    p_email_hmac, p_email_identity_hmac, p_domain_hmac,
    p_installation_hmac, p_network_hmac, p_disposable_domain,
    'PENDING', p_now, p_expires_at
  ) RETURNING * INTO v_row;

  RETURN v_row;
END
$$;

CREATE OR REPLACE FUNCTION identity_private.consume_signup_challenge(
  p_token_digest text,
  p_registration_ticket_digest text,
  p_operation_id text,
  p_full_token_budget bigint,
  p_restricted_token_budget bigint,
  p_full_cost_budget_microunits bigint,
  p_restricted_cost_budget_microunits bigint,
  p_now timestamptz DEFAULT now()
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_challenge identity_private.email_challenges%ROWTYPE;
  v_user identity_private.users%ROWTYPE;
  v_tenant_id uuid;
  v_existing_tenant uuid;
  v_grant identity_private.trial_grants%ROWTYPE;
  v_decision text := 'ALLOW';
  v_score integer := 0;
  v_reasons jsonb := '[]'::jsonb;
  v_installation_trials integer := 0;
  v_network_signups integer := 0;
  v_domain_trials integer := 0;
  v_ticket identity_private.bootstrap_tickets%ROWTYPE;
BEGIN
  IF p_registration_ticket_digest !~ '^[0-9a-f]{64}$' THEN
    RAISE EXCEPTION 'registration_ticket_digest_invalid';
  END IF;

  SELECT * INTO v_challenge
  FROM identity_private.email_challenges
  WHERE token_digest = p_token_digest
    AND purpose = 'SIGNUP'
    AND state = 'PENDING'
  FOR UPDATE;

  IF NOT FOUND THEN RAISE EXCEPTION 'email_challenge_not_found'; END IF;
  IF v_challenge.expires_at <= p_now THEN
    UPDATE identity_private.email_challenges
    SET state = 'EXPIRED'
    WHERE email_challenge_id = v_challenge.email_challenge_id;
    RAISE EXCEPTION 'email_challenge_expired';
  END IF;

  SELECT * INTO v_user
  FROM identity_private.users
  WHERE email_identity_hmac = v_challenge.email_identity_hmac
     OR email_normalized = v_challenge.email_normalized
  FOR UPDATE;

  IF NOT FOUND THEN
    INSERT INTO identity_private.users (
      email_normalized, email_hmac, email_identity_hmac,
      status, email_verified_at, created_at, updated_at
    ) VALUES (
      v_challenge.email_normalized, v_challenge.email_hmac,
      v_challenge.email_identity_hmac, 'ACTIVE', p_now, p_now, p_now
    ) RETURNING * INTO v_user;
  ELSE
    UPDATE identity_private.users
    SET email_verified_at = p_now, updated_at = p_now
    WHERE user_id = v_user.user_id
    RETURNING * INTO v_user;
  END IF;

  SELECT c.tenant_id INTO v_existing_tenant
  FROM identity_private.trial_subject_claims c
  JOIN identity_private.trial_grants g
    ON g.trial_grant_id = c.trial_grant_id
  WHERE c.claim_type = 'EMAIL_IDENTITY'
    AND c.claim_hmac = v_challenge.email_identity_hmac
    AND c.state = 'ACTIVE'
    AND g.state IN (
      'READY', 'ACTIVE', 'EXPIRED', 'CONVERTED',
      'SUSPENDED_ABUSE', 'REVOKED', 'ELIGIBILITY_PENDING'
    )
  ORDER BY g.prepared_at
  LIMIT 1;

  IF v_existing_tenant IS NOT NULL THEN
    v_tenant_id := v_existing_tenant;
    v_decision := 'REUSE_EXISTING_TRIAL';
    v_score := 100;
    v_reasons := jsonb_build_array('strong_email_identity_already_claimed');
  ELSE
    SELECT count(*) INTO v_installation_trials
    FROM identity_private.trial_subject_claims c
    JOIN identity_private.trial_grants g
      ON g.trial_grant_id = c.trial_grant_id
    WHERE c.claim_type = 'INSTALLATION'
      AND c.claim_hmac = v_challenge.installation_hmac
      AND c.state = 'ACTIVE'
      AND g.state <> 'REVOKED';

    SELECT count(*) INTO v_network_signups
    FROM identity_private.email_challenges
    WHERE network_hmac = v_challenge.network_hmac
      AND created_at >= p_now - interval '1 hour';

    SELECT count(*) INTO v_domain_trials
    FROM identity_private.trial_subject_claims c
    JOIN identity_private.trial_grants g
      ON g.trial_grant_id = c.trial_grant_id
    WHERE c.claim_type = 'DOMAIN'
      AND c.claim_hmac = v_challenge.domain_hmac
      AND c.state = 'ACTIVE'
      AND g.prepared_at >= p_now - interval '24 hours';

    IF v_challenge.disposable_domain THEN
      v_decision := 'STEP_UP_REQUIRED';
      v_score := 75;
      v_reasons := v_reasons || jsonb_build_array('disposable_email_domain');
    END IF;
    IF v_installation_trials > 0 THEN
      v_decision := 'STEP_UP_REQUIRED';
      v_score := greatest(v_score, 70);
      v_reasons := v_reasons || jsonb_build_array('installation_seen_on_prior_trial');
    END IF;
    IF v_network_signups >= 5 THEN
      v_decision := 'STEP_UP_REQUIRED';
      v_score := greatest(v_score, 65);
      v_reasons := v_reasons || jsonb_build_array('signup_velocity_network');
    END IF;
    IF v_domain_trials >= 3 AND v_decision = 'ALLOW' THEN
      v_decision := 'MANUAL_REVIEW';
      v_score := greatest(v_score, 60);
      v_reasons := v_reasons || jsonb_build_array('multiple_new_tenants_same_domain');
    END IF;

    INSERT INTO identity_private.organisations (
      created_by_user_id, primary_domain_hmac, status, created_at, updated_at
    ) VALUES (
      v_user.user_id, v_challenge.domain_hmac, 'ACTIVE', p_now, p_now
    ) RETURNING tenant_id INTO v_tenant_id;

    INSERT INTO identity_private.trial_grants (
      tenant_id, requested_by_user_id, state, decision,
      risk_score, risk_policy_version, reason_codes,
      token_budget_ceiling, cost_budget_microunits,
      prepared_at, updated_at
    ) VALUES (
      v_tenant_id, v_user.user_id,
      CASE WHEN v_decision IN ('ALLOW', 'ALLOW_RESTRICTED')
        THEN 'READY' ELSE 'ELIGIBILITY_PENDING' END,
      v_decision, v_score, 'trial-risk-policy@1.0.0', v_reasons,
      CASE WHEN v_decision = 'ALLOW_RESTRICTED'
        THEN p_restricted_token_budget ELSE p_full_token_budget END,
      CASE WHEN v_decision = 'ALLOW_RESTRICTED'
        THEN p_restricted_cost_budget_microunits
        ELSE p_full_cost_budget_microunits END,
      p_now, p_now
    ) RETURNING * INTO v_grant;

    INSERT INTO identity_private.trial_subject_claims (
      trial_grant_id, user_id, tenant_id, claim_type,
      claim_hmac, strength, state, created_at
    ) VALUES
      (
        v_grant.trial_grant_id, v_user.user_id, v_tenant_id,
        'EMAIL_IDENTITY', v_challenge.email_identity_hmac,
        'STRONG', 'ACTIVE', p_now
      ),
      (
        v_grant.trial_grant_id, v_user.user_id, v_tenant_id,
        'INSTALLATION', v_challenge.installation_hmac,
        'WEAK', 'ACTIVE', p_now
      ),
      (
        v_grant.trial_grant_id, v_user.user_id, v_tenant_id,
        'NETWORK_PREFIX', v_challenge.network_hmac,
        'WEAK', 'ACTIVE', p_now
      ),
      (
        v_grant.trial_grant_id, v_user.user_id, v_tenant_id,
        'DOMAIN', v_challenge.domain_hmac,
        'WEAK', 'ACTIVE', p_now
      );

    INSERT INTO identity_private.trial_risk_decisions (
      operation_id, user_id, tenant_id, decision, risk_score,
      reason_codes, policy_version, evaluated_at
    ) VALUES (
      p_operation_id, v_user.user_id, v_tenant_id, v_decision,
      v_score, v_reasons, 'trial-risk-policy@1.0.0', p_now
    );
  END IF;

  INSERT INTO identity_private.user_organisations (
    user_id, tenant_id, state, relationship, created_at
  ) VALUES (
    v_user.user_id, v_tenant_id, 'ACTIVE', 'OWNER', p_now
  )
  ON CONFLICT (user_id, tenant_id) DO UPDATE SET
    state = 'ACTIVE',
    revoked_at = NULL;

  INSERT INTO identity_private.bootstrap_tickets (
    token_digest, user_id, tenant_id, purpose, state,
    created_at, expires_at
  ) VALUES (
    p_registration_ticket_digest, v_user.user_id, v_tenant_id,
    'PASSKEY_REGISTRATION', 'PENDING', p_now, p_now + interval '10 minutes'
  ) RETURNING * INTO v_ticket;

  UPDATE identity_private.email_challenges
  SET state = 'CONSUMED', consumed_at = p_now, attempts = attempts + 1
  WHERE email_challenge_id = v_challenge.email_challenge_id;

  INSERT INTO identity_private.security_events (
    event_type, user_id, tenant_id, actor_subject,
    decision, reason_codes, metadata, occurred_at
  ) VALUES (
    'EMAIL_VERIFIED', v_user.user_id, v_tenant_id, v_user.subject,
    v_decision, v_reasons,
    jsonb_build_object('purpose', 'SIGNUP'), p_now
  );

  RETURN jsonb_build_object(
    'user_id', v_user.user_id,
    'subject', v_user.subject,
    'email', v_user.email_normalized,
    'webauthn_user_handle_hex', encode(v_user.webauthn_user_handle, 'hex'),
    'tenant_id', v_tenant_id,
    'decision', v_decision,
    'risk_score', v_score,
    'reason_codes', v_reasons,
    'bootstrap_ticket_id', v_ticket.bootstrap_ticket_id
  );
END
$$;

CREATE OR REPLACE FUNCTION identity_private.resolve_bootstrap_ticket(
  p_token_digest text,
  p_purpose text,
  p_now timestamptz DEFAULT now()
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_ticket identity_private.bootstrap_tickets%ROWTYPE;
  v_user identity_private.users%ROWTYPE;
BEGIN
  SELECT * INTO v_ticket
  FROM identity_private.bootstrap_tickets
  WHERE token_digest = p_token_digest
    AND purpose = p_purpose
    AND state IN ('PENDING', 'OPTIONS_ISSUED')
  FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'bootstrap_ticket_not_found'; END IF;
  IF v_ticket.expires_at <= p_now THEN
    UPDATE identity_private.bootstrap_tickets
    SET state = 'EXPIRED'
    WHERE bootstrap_ticket_id = v_ticket.bootstrap_ticket_id;
    RAISE EXCEPTION 'bootstrap_ticket_expired';
  END IF;

  SELECT * INTO v_user
  FROM identity_private.users
  WHERE user_id = v_ticket.user_id AND status IN ('ACTIVE', 'RECOVERY_ONLY');
  IF NOT FOUND THEN RAISE EXCEPTION 'identity_user_unavailable'; END IF;

  UPDATE identity_private.bootstrap_tickets
  SET state = 'OPTIONS_ISSUED'
  WHERE bootstrap_ticket_id = v_ticket.bootstrap_ticket_id;

  RETURN jsonb_build_object(
    'bootstrap_ticket_id', v_ticket.bootstrap_ticket_id,
    'user_id', v_user.user_id,
    'subject', v_user.subject,
    'email', v_user.email_normalized,
    'webauthn_user_handle_hex', encode(v_user.webauthn_user_handle, 'hex'),
    'tenant_id', v_ticket.tenant_id,
    'purpose', v_ticket.purpose
  );
END
$$;

CREATE OR REPLACE FUNCTION identity_private.create_webauthn_challenge(
  p_challenge_value text,
  p_challenge_digest text,
  p_purpose text,
  p_user_id uuid,
  p_bootstrap_ticket_id uuid,
  p_rp_id text,
  p_expected_origin text,
  p_expires_at timestamptz,
  p_now timestamptz DEFAULT now()
)
RETURNS identity_private.webauthn_challenges
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_row identity_private.webauthn_challenges%ROWTYPE;
BEGIN
  IF p_challenge_digest !~ '^[0-9a-f]{64}$'
     OR p_expires_at <= p_now
     OR p_expires_at > p_now + interval '30 minutes' THEN
    RAISE EXCEPTION 'webauthn_challenge_invalid';
  END IF;
  IF p_purpose NOT IN ('REGISTRATION', 'AUTHENTICATION', 'RECOVERY_REGISTRATION') THEN
    RAISE EXCEPTION 'webauthn_purpose_invalid';
  END IF;

  INSERT INTO identity_private.webauthn_challenges (
    challenge_value, challenge_digest, purpose, user_id,
    bootstrap_ticket_id, rp_id, expected_origin,
    state, created_at, expires_at
  ) VALUES (
    p_challenge_value, p_challenge_digest, p_purpose, p_user_id,
    p_bootstrap_ticket_id, p_rp_id, p_expected_origin,
    'PENDING', p_now, p_expires_at
  ) RETURNING * INTO v_row;
  RETURN v_row;
END
$$;

CREATE OR REPLACE FUNCTION identity_private.pending_webauthn_challenge(
  p_challenge_digest text,
  p_purpose text,
  p_now timestamptz DEFAULT now()
)
RETURNS jsonb
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_row identity_private.webauthn_challenges%ROWTYPE;
BEGIN
  SELECT * INTO v_row
  FROM identity_private.webauthn_challenges
  WHERE challenge_digest = p_challenge_digest
    AND purpose = p_purpose
    AND state = 'PENDING';
  IF NOT FOUND THEN RAISE EXCEPTION 'webauthn_challenge_not_found'; END IF;
  IF v_row.expires_at <= p_now THEN RAISE EXCEPTION 'webauthn_challenge_expired'; END IF;
  RETURN to_jsonb(v_row);
END
$$;

CREATE OR REPLACE FUNCTION identity_private.credential_for_authentication(
  p_credential_id text
)
RETURNS jsonb
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
  SELECT jsonb_build_object(
    'authenticator_id', c.authenticator_id,
    'credential_id', c.credential_id,
    'credential_public_key_hex', encode(c.credential_public_key, 'hex'),
    'sign_count', c.sign_count,
    'transports', to_jsonb(c.transports),
    'user_id', u.user_id,
    'subject', u.subject,
    'email', u.email_normalized,
    'webauthn_user_handle_hex', encode(u.webauthn_user_handle, 'hex')
  )
  FROM identity_private.webauthn_credentials c
  JOIN identity_private.users u ON u.user_id = c.user_id
  WHERE c.credential_id = p_credential_id
    AND c.state = 'ACTIVE'
    AND u.status = 'ACTIVE'
$$;
