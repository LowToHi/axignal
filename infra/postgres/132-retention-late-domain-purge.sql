-- Reconcile terminal retention with tenant-scoped domains introduced after the
-- original 090 lifecycle migration. Identity and abuse-prevention authorities
-- remain separate; this migration removes the workspace's commercial and seat
-- subgraphs before deleting their entitlement parents.

CREATE OR REPLACE FUNCTION tenant_private.reject_membership_audit_mutation()
RETURNS trigger
LANGUAGE plpgsql
SET search_path TO pg_catalog
AS $$
BEGIN
  IF current_user = 'axignal'
     AND current_setting('app.retention_purge', true) = '1' THEN
    RETURN OLD;
  END IF;
  RAISE EXCEPTION 'membership_audit_events_are_append_only';
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.reject_billing_audit_mutation()
RETURNS trigger
LANGUAGE plpgsql
SET search_path TO pg_catalog
AS $$
BEGIN
  IF current_user = 'axignal'
     AND current_setting('app.retention_purge', true) = '1' THEN
    RETURN OLD;
  END IF;
  RAISE EXCEPTION 'AXIGNAL billing audit records are append-only';
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.purge_late_workspace_domains(
  p_tenant_id uuid
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
BEGIN
  IF current_user <> 'axignal'
     OR current_setting('app.retention_purge', true) IS DISTINCT FROM '1' THEN
    RAISE EXCEPTION 'retention_purge_authority_required';
  END IF;

  DELETE FROM tenant_private.membership_role_bindings
  WHERE tenant_id = p_tenant_id;
  DELETE FROM tenant_private.organisation_seat_allocations
  WHERE tenant_id = p_tenant_id;
  DELETE FROM tenant_private.membership_audit_events
  WHERE tenant_id = p_tenant_id;
  DELETE FROM tenant_private.organisation_invitations
  WHERE tenant_id = p_tenant_id;
  DELETE FROM tenant_private.organisation_memberships
  WHERE tenant_id = p_tenant_id;
  DELETE FROM tenant_private.organisation_seat_entitlements
  WHERE tenant_id = p_tenant_id;

  DELETE FROM axignal_global.stripe_webhook_receipts
  WHERE tenant_id = p_tenant_id;
  DELETE FROM tenant_private.payment_ledger_entries
  WHERE tenant_id = p_tenant_id;
END
$$;

REVOKE ALL ON FUNCTION tenant_private.purge_late_workspace_domains(uuid)
  FROM PUBLIC;

CREATE OR REPLACE FUNCTION tenant_private.purge_claimed_workspace(
  p_deletion_id uuid,
  p_worker_id text,
  p_now timestamptz DEFAULT now()
)
RETURNS axignal_global.deletion_tombstones
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_lifecycle tenant_private.workspace_lifecycle%ROWTYPE;
  v_tenant_id uuid;
  v_run_ids uuid[];
  v_handoff_ids uuid[];
  v_counts jsonb;
  v_tenant_hash text;
  v_digest text;
  v_tombstone axignal_global.deletion_tombstones%ROWTYPE;
BEGIN
  SELECT * INTO v_lifecycle
  FROM tenant_private.workspace_lifecycle
  WHERE deletion_id = p_deletion_id
  FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'deletion_not_found'; END IF;
  IF v_lifecycle.state <> 'PURGING'
     OR v_lifecycle.purge_lease_owner IS DISTINCT FROM p_worker_id
     OR v_lifecycle.purge_lease_expires_at <= p_now THEN
    RAISE EXCEPTION 'purge_lease_mismatch';
  END IF;

  v_tenant_id := v_lifecycle.tenant_id;
  SELECT COALESCE(array_agg(research_run_id), '{}'::uuid[]) INTO v_run_ids
  FROM tenant_private.research_runs WHERE tenant_id = v_tenant_id;
  SELECT COALESCE(array_agg(admission_handoff_id), '{}'::uuid[]) INTO v_handoff_ids
  FROM axignal_global.admission_handoffs WHERE tenant_id = v_tenant_id;

  SELECT jsonb_build_object(
    'research_runs', (SELECT count(*) FROM tenant_private.research_runs WHERE tenant_id = v_tenant_id),
    'dossiers', (SELECT count(*) FROM tenant_private.dossiers WHERE tenant_id = v_tenant_id),
    'knowledge_items', (SELECT count(*) FROM tenant_private.knowledge_items WHERE tenant_id = v_tenant_id),
    'intent_events', (SELECT count(*) FROM intent_intelligence.intent_events WHERE tenant_id = v_tenant_id),
    'human_review_cases', (SELECT count(*) FROM tenant_private.human_review_cases WHERE tenant_id = v_tenant_id),
    'entitlements', (SELECT count(*) FROM tenant_private.organisation_entitlements WHERE tenant_id = v_tenant_id),
    'token_reservations', (SELECT count(*) FROM tenant_private.ai_token_reservations WHERE tenant_id = v_tenant_id),
    'scheduled_jobs', (SELECT count(*) FROM axignal_global.scheduled_jobs WHERE tenant_id = v_tenant_id),
    'seat_entitlements', (SELECT count(*) FROM tenant_private.organisation_seat_entitlements WHERE tenant_id = v_tenant_id),
    'memberships', (SELECT count(*) FROM tenant_private.organisation_memberships WHERE tenant_id = v_tenant_id),
    'invitations', (SELECT count(*) FROM tenant_private.organisation_invitations WHERE tenant_id = v_tenant_id),
    'seat_allocations', (SELECT count(*) FROM tenant_private.organisation_seat_allocations WHERE tenant_id = v_tenant_id),
    'role_bindings', (SELECT count(*) FROM tenant_private.membership_role_bindings WHERE tenant_id = v_tenant_id),
    'membership_audit_events', (SELECT count(*) FROM tenant_private.membership_audit_events WHERE tenant_id = v_tenant_id),
    'billing_selections', (SELECT count(*) FROM tenant_private.billing_plan_selections WHERE tenant_id = v_tenant_id),
    'payment_ledger_entries', (SELECT count(*) FROM tenant_private.payment_ledger_entries WHERE tenant_id = v_tenant_id),
    'stripe_webhook_receipts', (SELECT count(*) FROM axignal_global.stripe_webhook_receipts WHERE tenant_id = v_tenant_id)
  ) INTO v_counts;

  PERFORM set_config('app.retention_purge', '1', true);

  DELETE FROM tenant_private.human_review_events WHERE tenant_id = v_tenant_id;
  DELETE FROM tenant_private.human_review_cases WHERE tenant_id = v_tenant_id;
  DELETE FROM axignal_global.admission_outbox_events
    WHERE aggregate_id = ANY(v_handoff_ids)
       OR payload->>'tenant_id' = v_tenant_id::text;
  DELETE FROM axignal_global.admission_decisions
    WHERE admission_handoff_id = ANY(v_handoff_ids);
  DELETE FROM axignal_global.admission_job_failures WHERE tenant_id = v_tenant_id;

  UPDATE tenant_private.research_runs
  SET admission_handoff_id = NULL, dossier_id = NULL
  WHERE tenant_id = v_tenant_id;
  DELETE FROM axignal_global.admission_handoffs WHERE tenant_id = v_tenant_id;
  DELETE FROM axignal_global.proposal_outbox_events
    WHERE aggregate_id = ANY(v_run_ids)
       OR payload->>'tenant_id' = v_tenant_id::text;
  DELETE FROM axignal_global.outbox_events
    WHERE aggregate_id = ANY(v_run_ids)
       OR payload->>'tenant_id' = v_tenant_id::text;
  DELETE FROM axignal_global.proposal_job_failures WHERE tenant_id = v_tenant_id;

  DELETE FROM axignal_global.scheduled_jobs WHERE tenant_id = v_tenant_id;
  DELETE FROM tenant_private.dossiers WHERE tenant_id = v_tenant_id;
  DELETE FROM tenant_private.research_evidence_links WHERE tenant_id = v_tenant_id;
  DELETE FROM tenant_private.knowledge_items WHERE tenant_id = v_tenant_id;
  DELETE FROM intent_intelligence.intent_events WHERE tenant_id = v_tenant_id;
  DELETE FROM tenant_private.research_runs WHERE tenant_id = v_tenant_id;

  DELETE FROM tenant_private.workspace_lifecycle_events WHERE tenant_id = v_tenant_id;
  DELETE FROM tenant_private.entitlement_events WHERE tenant_id = v_tenant_id;
  DELETE FROM tenant_private.ai_token_reservations WHERE tenant_id = v_tenant_id;
  PERFORM tenant_private.purge_late_workspace_domains(v_tenant_id);
  DELETE FROM tenant_private.organisation_entitlements WHERE tenant_id = v_tenant_id;
  DELETE FROM tenant_private.billing_plan_selections WHERE tenant_id = v_tenant_id;
  DELETE FROM tenant_private.workspace_lifecycle WHERE tenant_id = v_tenant_id;

  v_tenant_hash := 'sha256:' || encode(digest(v_tenant_id::text, 'sha256'), 'hex');
  v_digest := 'sha256:' || encode(
    digest(
      p_deletion_id::text || v_tenant_hash || v_counts::text || p_now::text,
      'sha256'
    ),
    'hex'
  );

  INSERT INTO axignal_global.deletion_tombstones (
    deletion_id, tenant_hash, policy_version, requested_at, completed_at,
    purged_object_counts, verification_digest
  ) VALUES (
    p_deletion_id, v_tenant_hash, v_lifecycle.policy_version,
    v_lifecycle.deletion_requested_at, p_now, v_counts, v_digest
  )
  ON CONFLICT (deletion_id) DO NOTHING
  RETURNING * INTO v_tombstone;

  IF v_tombstone.deletion_id IS NULL THEN
    SELECT * INTO v_tombstone
    FROM axignal_global.deletion_tombstones
    WHERE deletion_id = p_deletion_id;
  END IF;
  RETURN v_tombstone;
EXCEPTION WHEN OTHERS THEN
  UPDATE tenant_private.workspace_lifecycle
  SET state = 'PURGE_FAILED', reason_code = SQLSTATE || ':' || SQLERRM,
      purge_lease_owner = NULL, purge_lease_expires_at = NULL, updated_at = p_now
  WHERE deletion_id = p_deletion_id;
  RAISE;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.reapply_deletion_tombstone(
  p_tenant_id uuid,
  p_now timestamptz DEFAULT now()
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_hash text;
  v_deleted jsonb;
BEGIN
  v_tenant_hash := 'sha256:' || encode(digest(p_tenant_id::text, 'sha256'), 'hex');
  IF NOT EXISTS (
    SELECT 1 FROM axignal_global.deletion_tombstones WHERE tenant_hash = v_tenant_hash
  ) THEN
    RAISE EXCEPTION 'terminal_deletion_tombstone_not_found';
  END IF;

  PERFORM set_config('app.retention_purge', '1', true);
  SELECT jsonb_build_object(
    'restored_research_runs', (SELECT count(*) FROM tenant_private.research_runs WHERE tenant_id = p_tenant_id),
    'restored_knowledge_items', (SELECT count(*) FROM tenant_private.knowledge_items WHERE tenant_id = p_tenant_id),
    'restored_intent_events', (SELECT count(*) FROM intent_intelligence.intent_events WHERE tenant_id = p_tenant_id),
    'restored_seat_entitlements', (SELECT count(*) FROM tenant_private.organisation_seat_entitlements WHERE tenant_id = p_tenant_id),
    'restored_billing_selections', (SELECT count(*) FROM tenant_private.billing_plan_selections WHERE tenant_id = p_tenant_id)
  ) INTO v_deleted;

  DELETE FROM tenant_private.human_review_events WHERE tenant_id = p_tenant_id;
  DELETE FROM tenant_private.human_review_cases WHERE tenant_id = p_tenant_id;
  UPDATE tenant_private.research_runs
    SET admission_handoff_id = NULL, dossier_id = NULL WHERE tenant_id = p_tenant_id;
  DELETE FROM tenant_private.dossiers WHERE tenant_id = p_tenant_id;
  DELETE FROM tenant_private.research_evidence_links WHERE tenant_id = p_tenant_id;
  DELETE FROM tenant_private.knowledge_items WHERE tenant_id = p_tenant_id;
  DELETE FROM intent_intelligence.intent_events WHERE tenant_id = p_tenant_id;
  DELETE FROM tenant_private.research_runs WHERE tenant_id = p_tenant_id;
  DELETE FROM tenant_private.workspace_lifecycle_events WHERE tenant_id = p_tenant_id;
  DELETE FROM tenant_private.entitlement_events WHERE tenant_id = p_tenant_id;
  DELETE FROM tenant_private.ai_token_reservations WHERE tenant_id = p_tenant_id;
  PERFORM tenant_private.purge_late_workspace_domains(p_tenant_id);
  DELETE FROM tenant_private.organisation_entitlements WHERE tenant_id = p_tenant_id;
  DELETE FROM tenant_private.billing_plan_selections WHERE tenant_id = p_tenant_id;
  DELETE FROM tenant_private.workspace_lifecycle WHERE tenant_id = p_tenant_id;
  RETURN v_deleted || jsonb_build_object('reapplied_at', p_now);
END
$$;

REVOKE ALL ON FUNCTION tenant_private.purge_claimed_workspace(uuid, text, timestamptz)
  FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.reapply_deletion_tombstone(uuid, timestamptz)
  FROM PUBLIC;
GRANT EXECUTE ON FUNCTION tenant_private.purge_claimed_workspace(uuid, text, timestamptz),
  tenant_private.reapply_deletion_tombstone(uuid, timestamptz)
  TO axignal_retention_worker;
