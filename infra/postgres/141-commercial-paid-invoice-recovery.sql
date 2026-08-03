-- E2E-3 commercial round-trip hardening.
-- A signed, applied Stripe invoice.paid receipt may recover a suspended paid
-- entitlement. The transition is isolated to the billing worker and audited
-- separately; browser input can never invoke this function.

CREATE OR REPLACE FUNCTION tenant_private.recover_paid_lifecycle_from_invoice(
  p_selection_id uuid,
  p_provider_event_id text,
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.billing_plan_selections
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_receipt axignal_global.stripe_webhook_receipts%ROWTYPE;
  v_row tenant_private.billing_plan_selections%ROWTYPE;
  v_paid tenant_private.organisation_entitlements%ROWTYPE;
BEGIN
  IF p_selection_id IS NULL OR p_provider_event_id IS NULL THEN
    RAISE EXCEPTION 'paid_invoice_recovery_identity_required';
  END IF;
  IF p_actor_subject IS NULL OR btrim(p_actor_subject) = '' THEN
    RAISE EXCEPTION 'actor_subject_required';
  END IF;

  SELECT * INTO v_receipt
  FROM axignal_global.stripe_webhook_receipts
  WHERE provider_event_id = p_provider_event_id
    AND selection_id = p_selection_id
    AND event_type = 'invoice.paid'
    AND disposition = 'APPLIED'
    AND livemode = false;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'applied_test_invoice_paid_receipt_required';
  END IF;

  SELECT * INTO v_row
  FROM tenant_private.billing_plan_selections
  WHERE selection_id = p_selection_id
  FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'billing_selection_not_found'; END IF;

  IF v_row.state = 'ACTIVE' THEN
    RETURN v_row;
  END IF;
  IF v_row.state <> 'SUSPENDED' THEN
    RAISE EXCEPTION 'suspended_billing_selection_required';
  END IF;

  SELECT * INTO v_paid
  FROM tenant_private.organisation_entitlements
  WHERE billing_selection_id = p_selection_id
    AND entitlement_kind = 'PAID_MONTHLY'
  FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'paid_entitlement_not_found'; END IF;
  IF v_paid.state <> 'SUSPENDED' THEN
    RAISE EXCEPTION 'suspended_paid_entitlement_required';
  END IF;

  UPDATE tenant_private.organisation_entitlements
  SET state = 'ACTIVE', expires_at = NULL,
      unlimited_ai_tokens = true, token_budget_total = NULL,
      updated_at = p_now
  WHERE entitlement_id = v_paid.entitlement_id;

  UPDATE tenant_private.billing_plan_selections
  SET state = 'ACTIVE', cancel_at_period_end = false, updated_at = p_now
  WHERE selection_id = p_selection_id
  RETURNING * INTO v_row;

  INSERT INTO tenant_private.payment_ledger_entries (
    tenant_id, selection_id, provider_event_id, ledger_event_type, plan_code,
    previous_state, new_state, payload_digest, actor_subject, occurred_at
  ) VALUES (
    v_row.tenant_id, v_row.selection_id, p_provider_event_id,
    'STRIPE_INVOICE_PAID_RECOVERY', v_row.plan_code,
    'SUSPENDED', 'ACTIVE', v_receipt.payload_digest,
    p_actor_subject, v_receipt.event_created_at
  ) ON CONFLICT (provider_event_id, ledger_event_type) DO NOTHING;

  RETURN v_row;
END
$$;

REVOKE ALL ON FUNCTION tenant_private.recover_paid_lifecycle_from_invoice(
  uuid, text, text, timestamptz
) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION tenant_private.recover_paid_lifecycle_from_invoice(
  uuid, text, text, timestamptz
) TO axignal_billing_worker;
