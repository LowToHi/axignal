-- Persist WebAuthn clone-signal containment before authentication is denied.
-- A raised exception inside the mutating transaction would roll the containment back.

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

  IF p_new_sign_count < v_authenticator.sign_count THEN
    UPDATE identity_private.webauthn_credentials
    SET state = 'COMPROMISED', revoked_at = p_now
    WHERE authenticator_id = v_authenticator.authenticator_id;

    UPDATE identity_private.identity_sessions
    SET state = 'REVOKED', revoked_at = p_now,
        revoke_reason = 'AUTHENTICATOR_CLONE_SIGNAL'
    WHERE user_id = v_user.user_id AND state = 'ACTIVE';

    UPDATE identity_private.webauthn_challenges
    SET state = 'CONSUMED', consumed_at = p_now
    WHERE webauthn_challenge_id = v_challenge.webauthn_challenge_id;

    INSERT INTO identity_private.security_events (
      event_type, user_id, tenant_id, actor_subject,
      decision, reason_codes, metadata, occurred_at
    ) VALUES (
      'LOGIN_BLOCKED', v_user.user_id, v_tenant_id,
      v_user.subject, 'BLOCK',
      jsonb_build_array('webauthn_sign_count_regression'),
      jsonb_build_object(
        'authenticator_id', v_authenticator.authenticator_id,
        'previous_sign_count', v_authenticator.sign_count,
        'supplied_sign_count', p_new_sign_count,
        'sessions_revoked', true
      ), p_now
    );

    RETURN jsonb_build_object(
      'decision', 'DENY',
      'reason', 'webauthn_sign_count_regression',
      'user_id', v_user.user_id,
      'tenant_id', v_tenant_id,
      'authenticator_id', v_authenticator.authenticator_id,
      'session_created', false
    );
  END IF;

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
    'decision', 'ALLOW',
    'user_id', v_user.user_id,
    'subject', v_user.subject,
    'email', v_user.email_normalized,
    'tenant_id', v_tenant_id,
    'session_id', v_session.session_id,
    'assurance_level', v_session.assurance_level,
    'session_created', true
  );
END
$$;

REVOKE ALL ON FUNCTION identity_private.complete_passkey_authentication(
  text, text, bigint, text, text, text, text, integer, integer, timestamptz
) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION identity_private.complete_passkey_authentication(
  text, text, bigint, text, text, text, text, integer, integer, timestamptz
) TO axignal_app;
