-- AX-F9-T15 trial retention, suspension and terminal deletion lifecycle.
-- Customer-facing retention duration remains unapproved; callers must provide a
-- versioned retention deadline and all runtime entry points remain feature-gated.

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'axignal_retention_worker') THEN
    CREATE ROLE axignal_retention_worker NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'axignal_operator') THEN
    CREATE ROLE axignal_operator NOLOGIN;
  END IF;
END
$$;

GRANT axignal_retention_worker, axignal_operator TO axignal;
GRANT USAGE ON SCHEMA tenant_private, intent_intelligence, axignal_global
  TO axignal_retention_worker;
GRANT USAGE ON SCHEMA tenant_private, axignal_global TO axignal_operator;

CREATE TABLE IF NOT EXISTS tenant_private.workspace_lifecycle (
  tenant_id uuid PRIMARY KEY,
  deletion_id uuid UNIQUE,
  state text NOT NULL CHECK (state IN (
    'ACTIVE',
    'READ_ONLY',
    'SUSPENDED',
    'DELETION_REQUESTED',
    'RETENTION_HOLD',
    'PURGE_QUEUED',
    'PURGING',
    'PURGE_FAILED'
  )),
  policy_version text NOT NULL,
  reason_code text,
  deletion_requested_at timestamptz,
  retention_until timestamptz,
  purge_lease_owner text,
  purge_lease_expires_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (
    state NOT IN ('DELETION_REQUESTED', 'RETENTION_HOLD', 'PURGE_QUEUED', 'PURGING', 'PURGE_FAILED')
    OR (deletion_id IS NOT NULL AND deletion_requested_at IS NOT NULL AND retention_until IS NOT NULL)
  )
);

CREATE TABLE IF NOT EXISTS tenant_private.workspace_lifecycle_events (
  workspace_lifecycle_event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  deletion_id uuid,
  event_type text NOT NULL,
  actor_subject text NOT NULL,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  occurred_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS axignal_global.deletion_tombstones (
  deletion_id uuid PRIMARY KEY,
  tenant_hash text NOT NULL UNIQUE CHECK (tenant_hash ~ '^sha256:[0-9a-f]{64}$'),
  policy_version text NOT NULL,
  requested_at timestamptz NOT NULL,
  completed_at timestamptz NOT NULL,
  purged_object_counts jsonb NOT NULL,
  verification_digest text NOT NULL CHECK (verification_digest ~ '^sha256:[0-9a-f]{64}$')
);

CREATE OR REPLACE FUNCTION tenant_private.retention_mutation_guard()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF current_user = 'axignal'
     AND current_setting('app.retention_purge', true) = '1' THEN
    RETURN OLD;
  END IF;
  RAISE EXCEPTION 'AXIGNAL_RETENTION_HISTORY_APPEND_ONLY';
END
$$;

DROP TRIGGER IF EXISTS workspace_lifecycle_events_immutable
  ON tenant_private.workspace_lifecycle_events;
CREATE TRIGGER workspace_lifecycle_events_immutable
BEFORE UPDATE OR DELETE ON tenant_private.workspace_lifecycle_events
FOR EACH ROW EXECUTE FUNCTION tenant_private.retention_mutation_guard();

CREATE OR REPLACE FUNCTION axignal_global.deletion_tombstone_guard()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE EXCEPTION 'AXIGNAL_DELETION_TOMBSTONES_APPEND_ONLY';
END
$$;

DROP TRIGGER IF EXISTS deletion_tombstones_immutable
  ON axignal_global.deletion_tombstones;
CREATE TRIGGER deletion_tombstones_immutable
BEFORE UPDATE OR DELETE ON axignal_global.deletion_tombstones
FOR EACH ROW EXECUTE FUNCTION axignal_global.deletion_tombstone_guard();

-- Existing append-only histories may be removed only inside the terminal purge
-- function, where current_user is the database owner and a transaction-local
-- purge marker has been set. Application roles cannot satisfy both conditions.
CREATE OR REPLACE FUNCTION tenant_private.reject_entitlement_event_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF current_user = 'axignal'
     AND current_setting('app.retention_purge', true) = '1' THEN
    RETURN OLD;
  END IF;
  RAISE EXCEPTION 'AXIGNAL entitlement events are append-only';
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.reject_human_review_event_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF current_user = 'axignal'
     AND current_setting('app.retention_purge', true) = '1' THEN
    RETURN OLD;
  END IF;
  RAISE EXCEPTION 'AXIGNAL_HUMAN_REVIEW_EVENTS_APPEND_ONLY';
END
$$;

CREATE OR REPLACE FUNCTION axignal_global.reject_scheduler_event_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF current_user = 'axignal'
     AND current_setting('app.retention_purge', true) = '1' THEN
    RETURN OLD;
  END IF;
  RAISE EXCEPTION 'AXIGNAL_SCHEDULER_EVENTS_APPEND_ONLY';
END
$$;

ALTER TABLE tenant_private.workspace_lifecycle ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.workspace_lifecycle FORCE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.workspace_lifecycle_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.workspace_lifecycle_events FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS workspace_lifecycle_tenant_isolation
  ON tenant_private.workspace_lifecycle;
CREATE POLICY workspace_lifecycle_tenant_isolation
  ON tenant_private.workspace_lifecycle
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

DROP POLICY IF EXISTS workspace_lifecycle_events_tenant_isolation
  ON tenant_private.workspace_lifecycle_events;
CREATE POLICY workspace_lifecycle_events_tenant_isolation
  ON tenant_private.workspace_lifecycle_events
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

CREATE OR REPLACE FUNCTION tenant_private.reject_terminally_deleted_tenant()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM axignal_global.deletion_tombstones
    WHERE tenant_hash = 'sha256:' || encode(digest(NEW.tenant_id::text, 'sha256'), 'hex')
  ) THEN
    RAISE EXCEPTION 'workspace_terminally_deleted';
  END IF;
  RETURN NEW;
END
$$;

DROP TRIGGER IF EXISTS organisation_entitlement_terminal_deletion_guard
  ON tenant_private.organisation_entitlements;
CREATE TRIGGER organisation_entitlement_terminal_deletion_guard
BEFORE INSERT ON tenant_private.organisation_entitlements
FOR EACH ROW EXECUTE FUNCTION tenant_private.reject_terminally_deleted_tenant();

DROP TRIGGER IF EXISTS research_run_terminal_deletion_guard
  ON tenant_private.research_runs;
CREATE TRIGGER research_run_terminal_deletion_guard
BEFORE INSERT ON tenant_private.research_runs
FOR EACH ROW EXECUTE FUNCTION tenant_private.reject_terminally_deleted_tenant();

CREATE OR REPLACE FUNCTION tenant_private.sync_workspace_lifecycle_from_entitlement()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_state text;
BEGIN
  v_state := CASE NEW.state
    WHEN 'ACTIVE' THEN 'ACTIVE'
    WHEN 'READ_ONLY' THEN 'READ_ONLY'
    WHEN 'SUSPENDED' THEN 'SUSPENDED'
    ELSE NULL
  END;
  IF v_state IS NULL THEN
    RETURN NEW;
  END IF;

  INSERT INTO tenant_private.workspace_lifecycle (
    tenant_id, state, policy_version, reason_code, created_at, updated_at
  ) VALUES (
    NEW.tenant_id, v_state, 'trial-retention@0.1.0',
    CASE WHEN v_state = 'READ_ONLY' THEN 'ENTITLEMENT_EXPIRED' ELSE NULL END,
    NEW.created_at, NEW.updated_at
  )
  ON CONFLICT (tenant_id) DO UPDATE SET
    state = CASE
      WHEN tenant_private.workspace_lifecycle.state IN (
        'DELETION_REQUESTED', 'RETENTION_HOLD', 'PURGE_QUEUED', 'PURGING', 'PURGE_FAILED'
      ) THEN tenant_private.workspace_lifecycle.state
      ELSE EXCLUDED.state
    END,
    reason_code = CASE
      WHEN tenant_private.workspace_lifecycle.state IN (
        'DELETION_REQUESTED', 'RETENTION_HOLD', 'PURGE_QUEUED', 'PURGING', 'PURGE_FAILED'
      ) THEN tenant_private.workspace_lifecycle.reason_code
      ELSE EXCLUDED.reason_code
    END,
    updated_at = EXCLUDED.updated_at;
  RETURN NEW;
END
$$;

DROP TRIGGER IF EXISTS entitlement_syncs_workspace_lifecycle
  ON tenant_private.organisation_entitlements;
CREATE TRIGGER entitlement_syncs_workspace_lifecycle
AFTER INSERT OR UPDATE OF state ON tenant_private.organisation_entitlements
FOR EACH ROW EXECUTE FUNCTION tenant_private.sync_workspace_lifecycle_from_entitlement();

CREATE OR REPLACE FUNCTION tenant_private.assert_workspace_accepts_execution()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_state text;
BEGIN
  SELECT state INTO v_state
  FROM tenant_private.workspace_lifecycle
  WHERE tenant_id = NEW.tenant_id;

  IF v_state IS NOT NULL AND v_state <> 'ACTIVE' THEN
    RAISE EXCEPTION 'workspace_not_operational:%', v_state;
  END IF;
  RETURN NEW;
END
$$;

DROP TRIGGER IF EXISTS research_run_workspace_execution_guard
  ON tenant_private.research_runs;
CREATE TRIGGER research_run_workspace_execution_guard
BEFORE INSERT ON tenant_private.research_runs
FOR EACH ROW EXECUTE FUNCTION tenant_private.assert_workspace_accepts_execution();

DROP TRIGGER IF EXISTS ai_reservation_workspace_execution_guard
  ON tenant_private.ai_token_reservations;
CREATE TRIGGER ai_reservation_workspace_execution_guard
BEFORE INSERT ON tenant_private.ai_token_reservations
FOR EACH ROW EXECUTE FUNCTION tenant_private.assert_workspace_accepts_execution();

CREATE OR REPLACE FUNCTION tenant_private.request_workspace_deletion(
  p_actor_subject text,
  p_retention_until timestamptz,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.workspace_lifecycle
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.current_tenant_id();
  v_row tenant_private.workspace_lifecycle%ROWTYPE;
BEGIN
  IF v_tenant_id IS NULL THEN RAISE EXCEPTION 'tenant_context_required'; END IF;
  IF p_actor_subject IS NULL OR btrim(p_actor_subject) = '' THEN
    RAISE EXCEPTION 'actor_subject_required';
  END IF;
  IF p_retention_until IS NULL OR p_retention_until < p_now THEN
    RAISE EXCEPTION 'retention_deadline_invalid';
  END IF;

  SELECT * INTO v_row
  FROM tenant_private.workspace_lifecycle
  WHERE tenant_id = v_tenant_id
  FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'workspace_lifecycle_not_found'; END IF;

  IF v_row.state IN ('DELETION_REQUESTED', 'RETENTION_HOLD', 'PURGE_QUEUED', 'PURGING') THEN
    RETURN v_row;
  END IF;
  IF v_row.state = 'PURGE_FAILED' THEN
    RAISE EXCEPTION 'workspace_purge_requires_operator_review';
  END IF;

  WITH released AS (
    UPDATE tenant_private.ai_token_reservations
    SET state = 'RELEASED', actual_tokens = 0, reconciled_at = p_now
    WHERE tenant_id = v_tenant_id AND state = 'RESERVED'
    RETURNING entitlement_id, requested_tokens
  ), totals AS (
    SELECT entitlement_id, sum(requested_tokens)::bigint AS released_tokens
    FROM released GROUP BY entitlement_id
  )
  UPDATE tenant_private.organisation_entitlements AS entitlement
  SET token_budget_reserved = greatest(
        0, entitlement.token_budget_reserved - totals.released_tokens
      ),
      updated_at = p_now
  FROM totals
  WHERE entitlement.entitlement_id = totals.entitlement_id;

  UPDATE tenant_private.organisation_entitlements
  SET state = 'SUSPENDED', updated_at = p_now
  WHERE tenant_id = v_tenant_id AND state IN ('ACTIVE', 'READ_ONLY');

  UPDATE tenant_private.workspace_lifecycle
  SET deletion_id = COALESCE(deletion_id, gen_random_uuid()),
      state = 'DELETION_REQUESTED',
      reason_code = 'USER_REQUESTED_DELETION',
      deletion_requested_at = COALESCE(deletion_requested_at, p_now),
      retention_until = p_retention_until,
      purge_lease_owner = NULL,
      purge_lease_expires_at = NULL,
      updated_at = p_now
  WHERE tenant_id = v_tenant_id
  RETURNING * INTO v_row;

  INSERT INTO tenant_private.workspace_lifecycle_events (
    tenant_id, deletion_id, event_type, actor_subject, payload, occurred_at
  ) VALUES (
    v_tenant_id, v_row.deletion_id, 'DELETION_REQUESTED', p_actor_subject,
    jsonb_build_object(
      'policy_version', v_row.policy_version,
      'retention_until', v_row.retention_until,
      'silent_conversion', false
    ),
    p_now
  );
  RETURN v_row;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.operator_suspend_workspace(
  p_tenant_id uuid,
  p_reason_code text,
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.workspace_lifecycle
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_row tenant_private.workspace_lifecycle%ROWTYPE;
BEGIN
  IF p_tenant_id IS NULL THEN RAISE EXCEPTION 'tenant_id_required'; END IF;
  IF p_reason_code IS NULL OR btrim(p_reason_code) = '' THEN
    RAISE EXCEPTION 'suspension_reason_required';
  END IF;

  UPDATE tenant_private.organisation_entitlements
  SET state = 'SUSPENDED', updated_at = p_now
  WHERE tenant_id = p_tenant_id AND state IN ('ACTIVE', 'READ_ONLY');

  UPDATE tenant_private.workspace_lifecycle
  SET state = 'SUSPENDED', reason_code = p_reason_code, updated_at = p_now
  WHERE tenant_id = p_tenant_id
    AND state IN ('ACTIVE', 'READ_ONLY', 'SUSPENDED')
  RETURNING * INTO v_row;
  IF NOT FOUND THEN RAISE EXCEPTION 'workspace_not_suspendable'; END IF;

  INSERT INTO tenant_private.workspace_lifecycle_events (
    tenant_id, event_type, actor_subject, payload, occurred_at
  ) VALUES (
    p_tenant_id, 'WORKSPACE_SUSPENDED', p_actor_subject,
    jsonb_build_object('reason_code', p_reason_code), p_now
  );
  RETURN v_row;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.queue_due_workspace_purges(
  p_now timestamptz DEFAULT now()
)
RETURNS integer
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_count integer;
BEGIN
  WITH queued AS (
    UPDATE tenant_private.workspace_lifecycle
    SET state = 'PURGE_QUEUED', updated_at = p_now
    WHERE state = 'DELETION_REQUESTED'
      AND retention_until <= p_now
    RETURNING tenant_id, deletion_id
  )
  SELECT count(*) INTO v_count FROM queued;
  RETURN v_count;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.claim_workspace_purge(
  p_worker_id text,
  p_now timestamptz DEFAULT now(),
  p_lease_seconds integer DEFAULT 60
)
RETURNS TABLE (deletion_id uuid, tenant_id uuid, policy_version text)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_row tenant_private.workspace_lifecycle%ROWTYPE;
BEGIN
  IF p_worker_id IS NULL OR length(btrim(p_worker_id)) < 3 THEN
    RAISE EXCEPTION 'worker_id_required';
  END IF;

  SELECT * INTO v_row
  FROM tenant_private.workspace_lifecycle
  WHERE state = 'PURGE_QUEUED'
     OR (
       state = 'PURGING'
       AND purge_lease_expires_at IS NOT NULL
       AND purge_lease_expires_at <= p_now
     )
  ORDER BY retention_until, updated_at
  FOR UPDATE SKIP LOCKED
  LIMIT 1;

  IF NOT FOUND THEN RETURN; END IF;

  UPDATE tenant_private.workspace_lifecycle
  SET state = 'PURGING',
      purge_lease_owner = p_worker_id,
      purge_lease_expires_at = p_now + make_interval(secs => greatest(1, p_lease_seconds)),
      updated_at = p_now
  WHERE tenant_private.workspace_lifecycle.tenant_id = v_row.tenant_id;

  RETURN QUERY SELECT v_row.deletion_id, v_row.tenant_id, v_row.policy_version;
END
$$;

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
    'scheduled_jobs', (SELECT count(*) FROM axignal_global.scheduled_jobs WHERE tenant_id = v_tenant_id)
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
  DELETE FROM tenant_private.organisation_entitlements WHERE tenant_id = v_tenant_id;
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
    'restored_intent_events', (SELECT count(*) FROM intent_intelligence.intent_events WHERE tenant_id = p_tenant_id)
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
  DELETE FROM tenant_private.organisation_entitlements WHERE tenant_id = p_tenant_id;
  DELETE FROM tenant_private.workspace_lifecycle WHERE tenant_id = p_tenant_id;
  RETURN v_deleted || jsonb_build_object('reapplied_at', p_now);
END
$$;

REVOKE ALL ON tenant_private.workspace_lifecycle,
  tenant_private.workspace_lifecycle_events FROM PUBLIC;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON tenant_private.workspace_lifecycle,
  tenant_private.workspace_lifecycle_events FROM axignal_app;
GRANT SELECT ON tenant_private.workspace_lifecycle TO axignal_app;

REVOKE ALL ON axignal_global.deletion_tombstones FROM PUBLIC;
GRANT SELECT ON axignal_global.deletion_tombstones TO axignal_retention_worker;

REVOKE ALL ON FUNCTION tenant_private.request_workspace_deletion(text, timestamptz, timestamptz)
  FROM PUBLIC;
GRANT EXECUTE ON FUNCTION tenant_private.request_workspace_deletion(text, timestamptz, timestamptz)
  TO axignal_app;

REVOKE ALL ON FUNCTION tenant_private.operator_suspend_workspace(uuid, text, text, timestamptz)
  FROM PUBLIC;
GRANT EXECUTE ON FUNCTION tenant_private.operator_suspend_workspace(uuid, text, text, timestamptz)
  TO axignal_operator;

REVOKE ALL ON FUNCTION tenant_private.queue_due_workspace_purges(timestamptz)
  FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.claim_workspace_purge(text, timestamptz, integer)
  FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.purge_claimed_workspace(uuid, text, timestamptz)
  FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.reapply_deletion_tombstone(uuid, timestamptz)
  FROM PUBLIC;
GRANT EXECUTE ON FUNCTION tenant_private.queue_due_workspace_purges(timestamptz),
  tenant_private.claim_workspace_purge(text, timestamptz, integer),
  tenant_private.purge_claimed_workspace(uuid, text, timestamptz),
  tenant_private.reapply_deletion_tombstone(uuid, timestamptz)
  TO axignal_retention_worker;

CREATE INDEX IF NOT EXISTS workspace_lifecycle_state_retention_idx
  ON tenant_private.workspace_lifecycle (state, retention_until, updated_at);
CREATE INDEX IF NOT EXISTS workspace_lifecycle_events_tenant_time_idx
  ON tenant_private.workspace_lifecycle_events (tenant_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS deletion_tombstones_completed_idx
  ON axignal_global.deletion_tombstones (completed_at DESC);
