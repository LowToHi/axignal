-- AX-GE2E-P26-T01 tender-alert double opt-in and delivery compensation.

CREATE OR REPLACE FUNCTION growth_private.confirm_tender_alert(
  p_confirmation_token_digest text,
  p_now timestamptz DEFAULT now()
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, growth_private
AS $$
DECLARE
  v_subscription growth_private.tender_alert_subscriptions%ROWTYPE;
BEGIN
  SELECT * INTO v_subscription
  FROM growth_private.tender_alert_subscriptions
  WHERE confirmation_token_digest = p_confirmation_token_digest
  FOR UPDATE;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'tender_alert_confirmation_not_found';
  END IF;
  IF v_subscription.state = 'SUPPRESSED' THEN
    RAISE EXCEPTION 'tender_alert_suppressed';
  END IF;
  IF v_subscription.state IN ('UNSUBSCRIBED', 'PAUSED') THEN
    RAISE EXCEPTION 'tender_alert_not_confirmable';
  END IF;

  UPDATE growth_private.tender_alert_subscriptions
  SET state = 'ACTIVE',
      confirmed_at = coalesce(confirmed_at, p_now),
      updated_at = p_now
  WHERE subscription_id = v_subscription.subscription_id;

  UPDATE growth_private.crm_contacts
  SET consent_status = 'OPTED_IN',
      lead_score = greatest(lead_score, 30),
      updated_at = p_now
  WHERE contact_id = v_subscription.contact_id;

  INSERT INTO growth_private.crm_activities (
    contact_id, activity_type, actor_subject, payload, occurred_at
  ) VALUES (
    v_subscription.contact_id,
    'TENDER_ALERT_CONFIRMED',
    'public',
    jsonb_build_object('subscription_id', v_subscription.subscription_id),
    p_now
  );

  RETURN jsonb_build_object(
    'subscription_id', v_subscription.subscription_id,
    'state', 'ACTIVE',
    'trial_created', false,
    'tenant_created', false
  );
END;
$$;

CREATE OR REPLACE FUNCTION growth_private.fail_tender_alert_delivery(
  p_subscription_id uuid,
  p_reason text,
  p_now timestamptz DEFAULT now()
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, growth_private
AS $$
DECLARE
  v_contact_id uuid;
BEGIN
  UPDATE growth_private.tender_alert_subscriptions
  SET state = 'SUPPRESSED', updated_at = p_now
  WHERE subscription_id = p_subscription_id
    AND state = 'PENDING_CONFIRMATION'
  RETURNING contact_id INTO v_contact_id;

  IF v_contact_id IS NULL THEN
    RAISE EXCEPTION 'tender_alert_not_pending';
  END IF;

  UPDATE growth_private.crm_contacts
  SET consent_status = 'SUPPRESSED',
      lifecycle_stage = 'SUPPRESSED',
      updated_at = p_now
  WHERE contact_id = v_contact_id
    AND NOT EXISTS (
      SELECT 1
      FROM growth_private.tender_alert_subscriptions s
      WHERE s.contact_id = v_contact_id
        AND s.state IN ('ACTIVE', 'PENDING_CONFIRMATION')
    );

  INSERT INTO growth_private.crm_activities (
    contact_id, activity_type, actor_subject, payload, occurred_at
  ) VALUES (
    v_contact_id,
    'TENDER_ALERT_DELIVERY_FAILED',
    'system',
    jsonb_build_object(
      'subscription_id', p_subscription_id,
      'reason', left(coalesce(p_reason, 'DELIVERY_FAILED'), 200)
    ),
    p_now
  );

  RETURN jsonb_build_object(
    'subscription_id', p_subscription_id,
    'state', 'SUPPRESSED'
  );
END;
$$;

CREATE OR REPLACE FUNCTION growth_private.unsubscribe_tender_alert(
  p_confirmation_token_digest text,
  p_now timestamptz DEFAULT now()
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, growth_private
AS $$
DECLARE
  v_subscription growth_private.tender_alert_subscriptions%ROWTYPE;
BEGIN
  SELECT * INTO v_subscription
  FROM growth_private.tender_alert_subscriptions
  WHERE confirmation_token_digest = p_confirmation_token_digest
  FOR UPDATE;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'tender_alert_not_found';
  END IF;

  UPDATE growth_private.tender_alert_subscriptions
  SET state = 'UNSUBSCRIBED', updated_at = p_now
  WHERE subscription_id = v_subscription.subscription_id;

  IF NOT EXISTS (
    SELECT 1 FROM growth_private.tender_alert_subscriptions s
    WHERE s.contact_id = v_subscription.contact_id AND s.state = 'ACTIVE'
  ) THEN
    UPDATE growth_private.crm_contacts
    SET consent_status = 'OPTED_OUT', updated_at = p_now
    WHERE contact_id = v_subscription.contact_id;
  END IF;

  INSERT INTO growth_private.crm_activities (
    contact_id, activity_type, actor_subject, payload, occurred_at
  ) VALUES (
    v_subscription.contact_id,
    'TENDER_ALERT_UNSUBSCRIBED',
    'public',
    jsonb_build_object('subscription_id', v_subscription.subscription_id),
    p_now
  );

  RETURN jsonb_build_object(
    'subscription_id', v_subscription.subscription_id,
    'state', 'UNSUBSCRIBED'
  );
END;
$$;

REVOKE ALL ON FUNCTION growth_private.confirm_tender_alert(text, timestamptz) FROM PUBLIC;
REVOKE ALL ON FUNCTION growth_private.fail_tender_alert_delivery(uuid, text, timestamptz) FROM PUBLIC;
REVOKE ALL ON FUNCTION growth_private.unsubscribe_tender_alert(text, timestamptz) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION growth_private.confirm_tender_alert(text, timestamptz) TO axignal_app;
GRANT EXECUTE ON FUNCTION growth_private.fail_tender_alert_delivery(uuid, text, timestamptz) TO axignal_app;
GRANT EXECUTE ON FUNCTION growth_private.unsubscribe_tender_alert(text, timestamptz) TO axignal_app;
