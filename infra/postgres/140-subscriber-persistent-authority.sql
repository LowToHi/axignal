-- AXIGNAL C3 persistent authority plane.
-- This migration replaces no product surface. It establishes the bounded,
-- tenant-isolated PostgreSQL authority consumed by the later C4 adapter.

CREATE TABLE IF NOT EXISTS tenant_private.subscriber_workspaces (
  workspace_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  opportunity_id text NOT NULL,
  title text NOT NULL,
  state text NOT NULL DEFAULT 'QUALIFYING' CHECK (state IN (
    'QUALIFYING', 'GO_REVIEW', 'PREPARING', 'SUBSCRIBER_APPROVED',
    'SUBMITTED_CONFIRMED', 'CLOSED'
  )),
  owner_subject text NOT NULL,
  deadline timestamptz NOT NULL,
  decision text NOT NULL DEFAULT 'UNDECIDED' CHECK (decision IN (
    'UNDECIDED', 'PURSUE', 'DO_NOT_PURSUE'
  )),
  package_status text NOT NULL DEFAULT 'NOT_STARTED' CHECK (package_status IN (
    'NOT_STARTED', 'READY', 'APPROVED'
  )),
  preflight_status text NOT NULL DEFAULT 'NOT_RUN' CHECK (preflight_status IN (
    'NOT_RUN', 'BLOCKED', 'READY'
  )),
  prepared_by text,
  prepared_revision bigint,
  approved_by text,
  approved_revision bigint,
  revision bigint NOT NULL DEFAULT 1 CHECK (revision > 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, opportunity_id),
  CHECK (approved_by IS NULL OR prepared_by IS DISTINCT FROM approved_by)
);

CREATE TABLE IF NOT EXISTS tenant_private.subscriber_requirements (
  requirement_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  workspace_id uuid NOT NULL REFERENCES tenant_private.subscriber_workspaces(workspace_id) ON DELETE CASCADE,
  title text NOT NULL,
  category text NOT NULL,
  status text NOT NULL DEFAULT 'UNKNOWN' CHECK (status IN (
    'UNKNOWN', 'MET', 'PARTIAL', 'BLOCKED', 'NOT_APPLICABLE'
  )),
  blocking boolean NOT NULL DEFAULT true,
  source_reference text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tenant_private.subscriber_evidence (
  evidence_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  workspace_id uuid NOT NULL REFERENCES tenant_private.subscriber_workspaces(workspace_id) ON DELETE CASCADE,
  requirement_id uuid REFERENCES tenant_private.subscriber_requirements(requirement_id) ON DELETE CASCADE,
  title text NOT NULL,
  evidence_type text NOT NULL CHECK (evidence_type IN (
    'SOURCE', 'SUBSCRIBER_DOCUMENT', 'CALCULATION'
  )),
  status text NOT NULL CHECK (status IN ('CANDIDATE', 'VERIFIED', 'EXPIRED', 'REJECTED')),
  source_reference text,
  content_hash text NOT NULL CHECK (content_hash ~ '^sha256:[0-9a-f]{64}$'),
  observed_at timestamptz NOT NULL,
  expires_at timestamptz,
  uploaded_by text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tenant_private.subscriber_amendments (
  amendment_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  workspace_id uuid NOT NULL REFERENCES tenant_private.subscriber_workspaces(workspace_id) ON DELETE CASCADE,
  title text NOT NULL,
  source_reference text NOT NULL,
  observed_at timestamptz NOT NULL,
  acknowledged boolean NOT NULL DEFAULT false,
  acknowledged_by text,
  acknowledged_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (
    (acknowledged = false AND acknowledged_by IS NULL AND acknowledged_at IS NULL)
    OR (acknowledged = true AND acknowledged_by IS NOT NULL AND acknowledged_at IS NOT NULL)
  )
);

CREATE TABLE IF NOT EXISTS tenant_private.subscriber_audit_events (
  event_sequence bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  audit_event_id uuid NOT NULL UNIQUE DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  workspace_id uuid,
  actor_subject text NOT NULL,
  event_type text NOT NULL CHECK (event_type IN (
    'WORKSPACE_CREATED',
    'DECISION_RECORDED',
    'REQUIREMENT_CREATED',
    'REQUIREMENT_UPDATED',
    'EVIDENCE_ATTACHED',
    'AMENDMENT_RECORDED',
    'AMENDMENT_ACKNOWLEDGED',
    'SUBMISSION_PREPARED',
    'SUBMISSION_APPROVED',
    'SUBMISSION_INVALIDATED'
  )),
  object_type text NOT NULL,
  object_id text NOT NULL,
  tenant_revision bigint NOT NULL CHECK (tenant_revision > 0),
  details jsonb NOT NULL DEFAULT '{}'::jsonb,
  occurred_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tenant_private.axent_conversations (
  conversation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  identity_subject text NOT NULL,
  title text NOT NULL,
  retention_class text NOT NULL CHECK (retention_class IN ('EPHEMERAL_30D', 'STANDARD_90D')),
  state text NOT NULL DEFAULT 'ACTIVE' CHECK (state IN ('ACTIVE', 'DELETION_REQUESTED')),
  retention_until timestamptz NOT NULL,
  deletion_requested_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (state <> 'DELETION_REQUESTED' OR deletion_requested_at IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS tenant_private.axent_messages (
  message_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  conversation_id uuid NOT NULL REFERENCES tenant_private.axent_conversations(conversation_id) ON DELETE CASCADE,
  ordinal integer NOT NULL CHECK (ordinal > 0),
  message_role text NOT NULL CHECK (message_role IN ('USER', 'ASSISTANT', 'SYSTEM')),
  ciphertext bytea NOT NULL,
  content_hash text NOT NULL CHECK (content_hash ~ '^sha256:[0-9a-f]{64}$'),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (conversation_id, ordinal)
);

CREATE TABLE IF NOT EXISTS tenant_private.axent_legal_holds (
  legal_hold_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  conversation_id uuid NOT NULL REFERENCES tenant_private.axent_conversations(conversation_id) ON DELETE CASCADE,
  reason text NOT NULL,
  placed_by text NOT NULL,
  placed_at timestamptz NOT NULL DEFAULT now(),
  released_by text,
  released_at timestamptz,
  CHECK (
    (released_by IS NULL AND released_at IS NULL)
    OR (released_by IS NOT NULL AND released_at IS NOT NULL)
  )
);

CREATE UNIQUE INDEX IF NOT EXISTS axent_one_active_hold_per_conversation
  ON tenant_private.axent_legal_holds (conversation_id)
  WHERE released_at IS NULL;

CREATE TABLE IF NOT EXISTS tenant_private.axent_audit_events (
  event_sequence bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  audit_event_id uuid NOT NULL UNIQUE DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  conversation_id uuid,
  actor_subject text NOT NULL,
  event_type text NOT NULL CHECK (event_type IN (
    'CONVERSATION_CREATED',
    'MESSAGE_APPENDED',
    'CONVERSATION_EXPORTED',
    'LEGAL_HOLD_PLACED',
    'LEGAL_HOLD_RELEASED',
    'DELETION_REQUESTED',
    'CONVERSATION_PURGED'
  )),
  details jsonb NOT NULL DEFAULT '{}'::jsonb,
  occurred_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS axignal_global.c3_terminal_purge_receipts (
  purge_receipt_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_hash text NOT NULL CHECK (tenant_hash ~ '^sha256:[0-9a-f]{64}$'),
  object_counts jsonb NOT NULL,
  verification_digest text NOT NULL CHECK (verification_digest ~ '^sha256:[0-9a-f]{64}$'),
  captured_at timestamptz NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION tenant_private.c3_append_only_guard()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF current_user = 'axignal'
     AND current_setting('app.retention_purge', true) = '1' THEN
    RETURN OLD;
  END IF;
  RAISE EXCEPTION 'AXIGNAL_C3_LEDGER_APPEND_ONLY';
END
$$;

DROP TRIGGER IF EXISTS subscriber_audit_events_immutable
  ON tenant_private.subscriber_audit_events;
CREATE TRIGGER subscriber_audit_events_immutable
BEFORE UPDATE OR DELETE ON tenant_private.subscriber_audit_events
FOR EACH ROW EXECUTE FUNCTION tenant_private.c3_append_only_guard();

DROP TRIGGER IF EXISTS axent_audit_events_immutable
  ON tenant_private.axent_audit_events;
CREATE TRIGGER axent_audit_events_immutable
BEFORE UPDATE OR DELETE ON tenant_private.axent_audit_events
FOR EACH ROW EXECUTE FUNCTION tenant_private.c3_append_only_guard();

CREATE OR REPLACE FUNCTION axignal_global.c3_purge_receipt_guard()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE EXCEPTION 'AXIGNAL_C3_PURGE_RECEIPTS_APPEND_ONLY';
END
$$;

DROP TRIGGER IF EXISTS c3_terminal_purge_receipts_immutable
  ON axignal_global.c3_terminal_purge_receipts;
CREATE TRIGGER c3_terminal_purge_receipts_immutable
BEFORE UPDATE OR DELETE ON axignal_global.c3_terminal_purge_receipts
FOR EACH ROW EXECUTE FUNCTION axignal_global.c3_purge_receipt_guard();

ALTER TABLE tenant_private.subscriber_workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.subscriber_workspaces FORCE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.subscriber_requirements ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.subscriber_requirements FORCE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.subscriber_evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.subscriber_evidence FORCE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.subscriber_amendments ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.subscriber_amendments FORCE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.subscriber_audit_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.subscriber_audit_events FORCE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.axent_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.axent_conversations FORCE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.axent_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.axent_messages FORCE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.axent_legal_holds ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.axent_legal_holds FORCE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.axent_audit_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.axent_audit_events FORCE ROW LEVEL SECURITY;

DO $$
DECLARE
  v_table text;
BEGIN
  FOREACH v_table IN ARRAY ARRAY[
    'subscriber_workspaces',
    'subscriber_requirements',
    'subscriber_evidence',
    'subscriber_amendments',
    'subscriber_audit_events',
    'axent_conversations',
    'axent_messages',
    'axent_legal_holds',
    'axent_audit_events'
  ]
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I_tenant_isolation ON tenant_private.%I', v_table, v_table);
    EXECUTE format(
      'CREATE POLICY %I_tenant_isolation ON tenant_private.%I USING (tenant_id = tenant_private.current_tenant_id()) WITH CHECK (tenant_id = tenant_private.current_tenant_id())',
      v_table,
      v_table
    );
  END LOOP;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.c3_require_tenant()
RETURNS uuid
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.current_tenant_id();
BEGIN
  IF v_tenant_id IS NULL THEN
    RAISE EXCEPTION 'tenant_context_required';
  END IF;
  RETURN v_tenant_id;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.c3_require_active_workspace()
RETURNS uuid
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.c3_require_tenant();
  v_state text;
BEGIN
  SELECT state INTO v_state
  FROM tenant_private.workspace_lifecycle
  WHERE tenant_id = v_tenant_id;
  IF v_state IS DISTINCT FROM 'ACTIVE' THEN
    RAISE EXCEPTION 'workspace_not_operational:%', COALESCE(v_state, 'MISSING');
  END IF;
  RETURN v_tenant_id;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.c3_append_workspace_event(
  p_workspace_id uuid,
  p_actor_subject text,
  p_event_type text,
  p_object_type text,
  p_object_id text,
  p_tenant_revision bigint,
  p_details jsonb DEFAULT '{}'::jsonb,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.subscriber_audit_events
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.c3_require_tenant();
  v_event tenant_private.subscriber_audit_events%ROWTYPE;
BEGIN
  IF p_actor_subject IS NULL OR btrim(p_actor_subject) = '' THEN
    RAISE EXCEPTION 'actor_subject_required';
  END IF;
  INSERT INTO tenant_private.subscriber_audit_events (
    tenant_id, workspace_id, actor_subject, event_type, object_type,
    object_id, tenant_revision, details, occurred_at
  ) VALUES (
    v_tenant_id, p_workspace_id, p_actor_subject, p_event_type,
    p_object_type, p_object_id, p_tenant_revision,
    COALESCE(p_details, '{}'::jsonb), p_now
  )
  RETURNING * INTO v_event;
  RETURN v_event;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.c3_touch_workspace(
  p_workspace_id uuid,
  p_actor_subject text,
  p_reason text,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.subscriber_workspaces
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.c3_require_active_workspace();
  v_before tenant_private.subscriber_workspaces%ROWTYPE;
  v_after tenant_private.subscriber_workspaces%ROWTYPE;
BEGIN
  SELECT * INTO v_before
  FROM tenant_private.subscriber_workspaces
  WHERE workspace_id = p_workspace_id AND tenant_id = v_tenant_id
  FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'subscriber_workspace_not_found'; END IF;

  UPDATE tenant_private.subscriber_workspaces
  SET revision = revision + 1,
      package_status = 'NOT_STARTED',
      preflight_status = 'NOT_RUN',
      prepared_by = NULL,
      prepared_revision = NULL,
      approved_by = NULL,
      approved_revision = NULL,
      updated_at = p_now
  WHERE workspace_id = p_workspace_id AND tenant_id = v_tenant_id
  RETURNING * INTO v_after;

  IF v_before.package_status <> 'NOT_STARTED' THEN
    PERFORM tenant_private.c3_append_workspace_event(
      p_workspace_id,
      p_actor_subject,
      'SUBMISSION_INVALIDATED',
      'workspace',
      p_workspace_id::text,
      v_after.revision,
      jsonb_build_object('reason', p_reason),
      p_now
    );
  END IF;
  RETURN v_after;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.create_subscriber_workspace(
  p_opportunity_id text,
  p_title text,
  p_deadline timestamptz,
  p_owner_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.subscriber_workspaces
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.c3_require_active_workspace();
  v_workspace tenant_private.subscriber_workspaces%ROWTYPE;
BEGIN
  IF p_opportunity_id IS NULL OR btrim(p_opportunity_id) = '' THEN
    RAISE EXCEPTION 'opportunity_id_required';
  END IF;
  IF p_title IS NULL OR btrim(p_title) = '' THEN
    RAISE EXCEPTION 'workspace_title_required';
  END IF;
  IF p_owner_subject IS NULL OR btrim(p_owner_subject) = '' THEN
    RAISE EXCEPTION 'owner_subject_required';
  END IF;
  IF p_deadline IS NULL THEN RAISE EXCEPTION 'deadline_required'; END IF;

  INSERT INTO tenant_private.subscriber_workspaces (
    tenant_id, opportunity_id, title, owner_subject, deadline, created_at, updated_at
  ) VALUES (
    v_tenant_id, p_opportunity_id, p_title, p_owner_subject, p_deadline, p_now, p_now
  )
  RETURNING * INTO v_workspace;

  PERFORM tenant_private.c3_append_workspace_event(
    v_workspace.workspace_id,
    p_owner_subject,
    'WORKSPACE_CREATED',
    'workspace',
    v_workspace.workspace_id::text,
    v_workspace.revision,
    jsonb_build_object('opportunity_id', p_opportunity_id, 'deadline', p_deadline),
    p_now
  );
  RETURN v_workspace;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.record_subscriber_decision(
  p_workspace_id uuid,
  p_decision text,
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.subscriber_workspaces
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.c3_require_active_workspace();
  v_workspace tenant_private.subscriber_workspaces%ROWTYPE;
BEGIN
  IF p_decision NOT IN ('PURSUE', 'DO_NOT_PURSUE') THEN
    RAISE EXCEPTION 'subscriber_decision_invalid';
  END IF;
  UPDATE tenant_private.subscriber_workspaces
  SET decision = p_decision,
      state = CASE WHEN p_decision = 'PURSUE' THEN 'PREPARING' ELSE 'CLOSED' END,
      revision = revision + 1,
      package_status = 'NOT_STARTED',
      preflight_status = 'NOT_RUN',
      prepared_by = NULL,
      prepared_revision = NULL,
      approved_by = NULL,
      approved_revision = NULL,
      updated_at = p_now
  WHERE workspace_id = p_workspace_id AND tenant_id = v_tenant_id
  RETURNING * INTO v_workspace;
  IF NOT FOUND THEN RAISE EXCEPTION 'subscriber_workspace_not_found'; END IF;

  PERFORM tenant_private.c3_append_workspace_event(
    p_workspace_id, p_actor_subject, 'DECISION_RECORDED',
    'qualification_decision', p_workspace_id::text, v_workspace.revision,
    jsonb_build_object('decision', p_decision), p_now
  );
  RETURN v_workspace;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.create_subscriber_requirement(
  p_workspace_id uuid,
  p_title text,
  p_category text,
  p_blocking boolean,
  p_source_reference text,
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.subscriber_requirements
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.c3_require_active_workspace();
  v_requirement tenant_private.subscriber_requirements%ROWTYPE;
  v_workspace tenant_private.subscriber_workspaces%ROWTYPE;
BEGIN
  PERFORM 1 FROM tenant_private.subscriber_workspaces
  WHERE workspace_id = p_workspace_id AND tenant_id = v_tenant_id;
  IF NOT FOUND THEN RAISE EXCEPTION 'subscriber_workspace_not_found'; END IF;

  INSERT INTO tenant_private.subscriber_requirements (
    tenant_id, workspace_id, title, category, blocking,
    source_reference, created_at, updated_at
  ) VALUES (
    v_tenant_id, p_workspace_id, p_title, p_category, p_blocking,
    p_source_reference, p_now, p_now
  )
  RETURNING * INTO v_requirement;

  v_workspace := tenant_private.c3_touch_workspace(
    p_workspace_id, p_actor_subject, 'REQUIREMENT_CREATED', p_now
  );
  PERFORM tenant_private.c3_append_workspace_event(
    p_workspace_id, p_actor_subject, 'REQUIREMENT_CREATED',
    'requirement', v_requirement.requirement_id::text, v_workspace.revision,
    jsonb_build_object('blocking', p_blocking, 'category', p_category), p_now
  );
  RETURN v_requirement;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.set_subscriber_requirement_status(
  p_requirement_id uuid,
  p_status text,
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.subscriber_requirements
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.c3_require_active_workspace();
  v_requirement tenant_private.subscriber_requirements%ROWTYPE;
  v_workspace tenant_private.subscriber_workspaces%ROWTYPE;
BEGIN
  IF p_status NOT IN ('UNKNOWN', 'MET', 'PARTIAL', 'BLOCKED', 'NOT_APPLICABLE') THEN
    RAISE EXCEPTION 'requirement_status_invalid';
  END IF;
  UPDATE tenant_private.subscriber_requirements
  SET status = p_status, updated_at = p_now
  WHERE requirement_id = p_requirement_id AND tenant_id = v_tenant_id
  RETURNING * INTO v_requirement;
  IF NOT FOUND THEN RAISE EXCEPTION 'subscriber_requirement_not_found'; END IF;

  v_workspace := tenant_private.c3_touch_workspace(
    v_requirement.workspace_id, p_actor_subject, 'REQUIREMENT_UPDATED', p_now
  );
  PERFORM tenant_private.c3_append_workspace_event(
    v_requirement.workspace_id, p_actor_subject, 'REQUIREMENT_UPDATED',
    'requirement', p_requirement_id::text, v_workspace.revision,
    jsonb_build_object('status', p_status), p_now
  );
  RETURN v_requirement;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.attach_subscriber_evidence(
  p_workspace_id uuid,
  p_requirement_id uuid,
  p_title text,
  p_evidence_type text,
  p_status text,
  p_source_reference text,
  p_content_hash text,
  p_observed_at timestamptz,
  p_expires_at timestamptz,
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.subscriber_evidence
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.c3_require_active_workspace();
  v_evidence tenant_private.subscriber_evidence%ROWTYPE;
  v_workspace tenant_private.subscriber_workspaces%ROWTYPE;
BEGIN
  IF p_evidence_type NOT IN ('SOURCE', 'SUBSCRIBER_DOCUMENT', 'CALCULATION') THEN
    RAISE EXCEPTION 'evidence_type_invalid';
  END IF;
  IF p_status NOT IN ('CANDIDATE', 'VERIFIED', 'EXPIRED', 'REJECTED') THEN
    RAISE EXCEPTION 'evidence_status_invalid';
  END IF;
  IF p_content_hash !~ '^sha256:[0-9a-f]{64}$' THEN
    RAISE EXCEPTION 'evidence_hash_invalid';
  END IF;
  PERFORM 1 FROM tenant_private.subscriber_requirements
  WHERE requirement_id = p_requirement_id
    AND workspace_id = p_workspace_id
    AND tenant_id = v_tenant_id;
  IF NOT FOUND THEN RAISE EXCEPTION 'subscriber_requirement_not_found'; END IF;

  INSERT INTO tenant_private.subscriber_evidence (
    tenant_id, workspace_id, requirement_id, title, evidence_type, status,
    source_reference, content_hash, observed_at, expires_at, uploaded_by, created_at
  ) VALUES (
    v_tenant_id, p_workspace_id, p_requirement_id, p_title, p_evidence_type,
    p_status, p_source_reference, p_content_hash, p_observed_at, p_expires_at,
    p_actor_subject, p_now
  )
  RETURNING * INTO v_evidence;

  v_workspace := tenant_private.c3_touch_workspace(
    p_workspace_id, p_actor_subject, 'EVIDENCE_ATTACHED', p_now
  );
  PERFORM tenant_private.c3_append_workspace_event(
    p_workspace_id, p_actor_subject, 'EVIDENCE_ATTACHED',
    'evidence', v_evidence.evidence_id::text, v_workspace.revision,
    jsonb_build_object('status', p_status, 'requirement_id', p_requirement_id), p_now
  );
  RETURN v_evidence;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.record_subscriber_amendment(
  p_workspace_id uuid,
  p_title text,
  p_source_reference text,
  p_observed_at timestamptz,
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.subscriber_amendments
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.c3_require_active_workspace();
  v_amendment tenant_private.subscriber_amendments%ROWTYPE;
  v_workspace tenant_private.subscriber_workspaces%ROWTYPE;
BEGIN
  PERFORM 1 FROM tenant_private.subscriber_workspaces
  WHERE workspace_id = p_workspace_id AND tenant_id = v_tenant_id;
  IF NOT FOUND THEN RAISE EXCEPTION 'subscriber_workspace_not_found'; END IF;

  INSERT INTO tenant_private.subscriber_amendments (
    tenant_id, workspace_id, title, source_reference, observed_at, created_at
  ) VALUES (
    v_tenant_id, p_workspace_id, p_title, p_source_reference, p_observed_at, p_now
  )
  RETURNING * INTO v_amendment;

  v_workspace := tenant_private.c3_touch_workspace(
    p_workspace_id, p_actor_subject, 'AMENDMENT_RECORDED', p_now
  );
  PERFORM tenant_private.c3_append_workspace_event(
    p_workspace_id, p_actor_subject, 'AMENDMENT_RECORDED',
    'amendment', v_amendment.amendment_id::text, v_workspace.revision,
    jsonb_build_object('source_reference', p_source_reference), p_now
  );
  RETURN v_amendment;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.acknowledge_subscriber_amendment(
  p_amendment_id uuid,
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.subscriber_amendments
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.c3_require_active_workspace();
  v_amendment tenant_private.subscriber_amendments%ROWTYPE;
  v_workspace tenant_private.subscriber_workspaces%ROWTYPE;
BEGIN
  UPDATE tenant_private.subscriber_amendments
  SET acknowledged = true,
      acknowledged_by = p_actor_subject,
      acknowledged_at = p_now
  WHERE amendment_id = p_amendment_id AND tenant_id = v_tenant_id
  RETURNING * INTO v_amendment;
  IF NOT FOUND THEN RAISE EXCEPTION 'subscriber_amendment_not_found'; END IF;

  v_workspace := tenant_private.c3_touch_workspace(
    v_amendment.workspace_id, p_actor_subject, 'AMENDMENT_ACKNOWLEDGED', p_now
  );
  PERFORM tenant_private.c3_append_workspace_event(
    v_amendment.workspace_id, p_actor_subject, 'AMENDMENT_ACKNOWLEDGED',
    'amendment', p_amendment_id::text, v_workspace.revision,
    '{}'::jsonb, p_now
  );
  RETURN v_amendment;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.subscriber_workspace_readiness(
  p_workspace_id uuid,
  p_as_of timestamptz DEFAULT now()
)
RETURNS jsonb
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.c3_require_tenant();
  v_workspace tenant_private.subscriber_workspaces%ROWTYPE;
  v_unresolved integer;
  v_missing_evidence integer;
  v_unacknowledged integer;
  v_evidence_sufficient boolean;
  v_submission_ready boolean;
BEGIN
  SELECT * INTO v_workspace
  FROM tenant_private.subscriber_workspaces
  WHERE workspace_id = p_workspace_id AND tenant_id = v_tenant_id;
  IF NOT FOUND THEN RAISE EXCEPTION 'subscriber_workspace_not_found'; END IF;

  SELECT count(*) INTO v_unresolved
  FROM tenant_private.subscriber_requirements
  WHERE tenant_id = v_tenant_id
    AND workspace_id = p_workspace_id
    AND blocking
    AND status NOT IN ('MET', 'NOT_APPLICABLE');

  SELECT count(*) INTO v_missing_evidence
  FROM tenant_private.subscriber_requirements requirement
  WHERE requirement.tenant_id = v_tenant_id
    AND requirement.workspace_id = p_workspace_id
    AND requirement.blocking
    AND requirement.status = 'MET'
    AND NOT EXISTS (
      SELECT 1
      FROM tenant_private.subscriber_evidence evidence
      WHERE evidence.tenant_id = v_tenant_id
        AND evidence.workspace_id = p_workspace_id
        AND evidence.requirement_id = requirement.requirement_id
        AND evidence.status = 'VERIFIED'
        AND (evidence.expires_at IS NULL OR evidence.expires_at > p_as_of)
    );

  SELECT count(*) INTO v_unacknowledged
  FROM tenant_private.subscriber_amendments
  WHERE tenant_id = v_tenant_id
    AND workspace_id = p_workspace_id
    AND acknowledged = false;

  v_evidence_sufficient := v_unresolved = 0 AND v_missing_evidence = 0;
  v_submission_ready :=
    v_workspace.decision = 'PURSUE'
    AND v_evidence_sufficient
    AND v_unacknowledged = 0
    AND v_workspace.package_status = 'APPROVED'
    AND v_workspace.preflight_status = 'READY'
    AND v_workspace.prepared_by IS NOT NULL
    AND v_workspace.approved_by IS NOT NULL
    AND v_workspace.prepared_by IS DISTINCT FROM v_workspace.approved_by
    AND v_workspace.approved_revision = v_workspace.revision;

  RETURN jsonb_build_object(
    'workspace_id', v_workspace.workspace_id,
    'tenant_revision', v_workspace.revision,
    'decision', v_workspace.decision,
    'unresolved_blocking_requirements', v_unresolved,
    'blocking_requirements_missing_verified_evidence', v_missing_evidence,
    'unacknowledged_amendments', v_unacknowledged,
    'evidence_sufficient', v_evidence_sufficient,
    'package_status', v_workspace.package_status,
    'preflight_status', v_workspace.preflight_status,
    'submission_ready', v_submission_ready,
    'as_of', p_as_of
  );
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.prepare_subscriber_submission(
  p_workspace_id uuid,
  p_actor_subject text,
  p_as_of timestamptz DEFAULT now()
)
RETURNS tenant_private.subscriber_workspaces
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.c3_require_active_workspace();
  v_readiness jsonb;
  v_workspace tenant_private.subscriber_workspaces%ROWTYPE;
BEGIN
  v_readiness := tenant_private.subscriber_workspace_readiness(p_workspace_id, p_as_of);
  IF (v_readiness->>'decision') <> 'PURSUE' THEN
    RAISE EXCEPTION 'submission_pursue_decision_required';
  END IF;
  IF NOT (v_readiness->>'evidence_sufficient')::boolean THEN
    RAISE EXCEPTION 'submission_evidence_insufficient';
  END IF;
  IF (v_readiness->>'unacknowledged_amendments')::integer <> 0 THEN
    RAISE EXCEPTION 'submission_amendment_acknowledgement_required';
  END IF;

  UPDATE tenant_private.subscriber_workspaces
  SET package_status = 'READY',
      preflight_status = 'READY',
      prepared_by = p_actor_subject,
      prepared_revision = revision + 1,
      approved_by = NULL,
      approved_revision = NULL,
      revision = revision + 1,
      updated_at = p_as_of
  WHERE workspace_id = p_workspace_id AND tenant_id = v_tenant_id
  RETURNING * INTO v_workspace;
  IF NOT FOUND THEN RAISE EXCEPTION 'subscriber_workspace_not_found'; END IF;

  PERFORM tenant_private.c3_append_workspace_event(
    p_workspace_id, p_actor_subject, 'SUBMISSION_PREPARED',
    'submission', p_workspace_id::text, v_workspace.revision,
    jsonb_build_object('prepared_revision', v_workspace.prepared_revision), p_as_of
  );
  RETURN v_workspace;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.approve_subscriber_submission(
  p_workspace_id uuid,
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.subscriber_workspaces
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.c3_require_active_workspace();
  v_workspace tenant_private.subscriber_workspaces%ROWTYPE;
BEGIN
  SELECT * INTO v_workspace
  FROM tenant_private.subscriber_workspaces
  WHERE workspace_id = p_workspace_id AND tenant_id = v_tenant_id
  FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'subscriber_workspace_not_found'; END IF;
  IF v_workspace.package_status <> 'READY'
     OR v_workspace.preflight_status <> 'READY'
     OR v_workspace.prepared_revision IS DISTINCT FROM v_workspace.revision THEN
    RAISE EXCEPTION 'submission_not_prepared_at_current_revision';
  END IF;
  IF v_workspace.prepared_by = p_actor_subject THEN
    RAISE EXCEPTION 'submission_separation_of_duties_required';
  END IF;

  UPDATE tenant_private.subscriber_workspaces
  SET package_status = 'APPROVED',
      state = 'SUBSCRIBER_APPROVED',
      approved_by = p_actor_subject,
      approved_revision = revision + 1,
      revision = revision + 1,
      updated_at = p_now
  WHERE workspace_id = p_workspace_id AND tenant_id = v_tenant_id
  RETURNING * INTO v_workspace;

  PERFORM tenant_private.c3_append_workspace_event(
    p_workspace_id, p_actor_subject, 'SUBMISSION_APPROVED',
    'submission', p_workspace_id::text, v_workspace.revision,
    jsonb_build_object('approved_revision', v_workspace.approved_revision), p_now
  );
  RETURN v_workspace;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.subscriber_workspace_summary(
  p_as_of timestamptz DEFAULT now()
)
RETURNS jsonb
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
  SELECT jsonb_build_object(
    'as_of', p_as_of,
    'workspaces', count(*),
    'active_workspaces', count(*) FILTER (WHERE state <> 'CLOSED'),
    'deadlines_next_30_days', count(*) FILTER (
      WHERE state <> 'CLOSED'
        AND deadline >= p_as_of
        AND deadline < p_as_of + interval '30 days'
    )
  )
  FROM tenant_private.subscriber_workspaces
  WHERE tenant_id = tenant_private.c3_require_tenant()
$$;

CREATE OR REPLACE FUNCTION tenant_private.subscriber_workspace_events(
  p_after_sequence bigint DEFAULT 0
)
RETURNS jsonb
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
  SELECT COALESCE(
    jsonb_agg(
      jsonb_build_object(
        'event_sequence', event_sequence,
        'audit_event_id', audit_event_id,
        'workspace_id', workspace_id,
        'actor_subject', actor_subject,
        'event_type', event_type,
        'object_type', object_type,
        'object_id', object_id,
        'tenant_revision', tenant_revision,
        'details', details,
        'occurred_at', occurred_at
      ) ORDER BY event_sequence
    ),
    '[]'::jsonb
  )
  FROM tenant_private.subscriber_audit_events
  WHERE tenant_id = tenant_private.c3_require_tenant()
    AND event_sequence > greatest(0, p_after_sequence)
$$;

CREATE OR REPLACE FUNCTION tenant_private.c3_append_axent_event(
  p_tenant_id uuid,
  p_conversation_id uuid,
  p_actor_subject text,
  p_event_type text,
  p_details jsonb DEFAULT '{}'::jsonb,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.axent_audit_events
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_event tenant_private.axent_audit_events%ROWTYPE;
BEGIN
  INSERT INTO tenant_private.axent_audit_events (
    tenant_id, conversation_id, actor_subject, event_type, details, occurred_at
  ) VALUES (
    p_tenant_id, p_conversation_id, p_actor_subject, p_event_type,
    COALESCE(p_details, '{}'::jsonb), p_now
  )
  RETURNING * INTO v_event;
  RETURN v_event;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.create_axent_conversation(
  p_identity_subject text,
  p_title text,
  p_retention_class text,
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.axent_conversations
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.c3_require_active_workspace();
  v_days integer;
  v_conversation tenant_private.axent_conversations%ROWTYPE;
BEGIN
  v_days := CASE p_retention_class
    WHEN 'EPHEMERAL_30D' THEN 30
    WHEN 'STANDARD_90D' THEN 90
    ELSE NULL
  END;
  IF v_days IS NULL THEN RAISE EXCEPTION 'axent_retention_class_invalid'; END IF;
  IF p_identity_subject IS NULL OR btrim(p_identity_subject) = '' THEN
    RAISE EXCEPTION 'identity_subject_required';
  END IF;

  INSERT INTO tenant_private.axent_conversations (
    tenant_id, identity_subject, title, retention_class, retention_until,
    created_at, updated_at
  ) VALUES (
    v_tenant_id, p_identity_subject, p_title, p_retention_class,
    p_now + make_interval(days => v_days), p_now, p_now
  )
  RETURNING * INTO v_conversation;

  PERFORM tenant_private.c3_append_axent_event(
    v_tenant_id, v_conversation.conversation_id, p_actor_subject,
    'CONVERSATION_CREATED',
    jsonb_build_object('retention_class', p_retention_class, 'retention_until', v_conversation.retention_until),
    p_now
  );
  RETURN v_conversation;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.append_axent_message(
  p_conversation_id uuid,
  p_message_role text,
  p_content text,
  p_encryption_key text,
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.axent_messages
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.c3_require_active_workspace();
  v_conversation tenant_private.axent_conversations%ROWTYPE;
  v_ordinal integer;
  v_message tenant_private.axent_messages%ROWTYPE;
BEGIN
  IF p_message_role NOT IN ('USER', 'ASSISTANT', 'SYSTEM') THEN
    RAISE EXCEPTION 'axent_message_role_invalid';
  END IF;
  IF p_content IS NULL OR btrim(p_content) = '' THEN
    RAISE EXCEPTION 'axent_message_content_required';
  END IF;
  IF p_encryption_key IS NULL OR octet_length(p_encryption_key) < 32 THEN
    RAISE EXCEPTION 'axent_encryption_key_invalid';
  END IF;

  SELECT * INTO v_conversation
  FROM tenant_private.axent_conversations
  WHERE conversation_id = p_conversation_id AND tenant_id = v_tenant_id
  FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'axent_conversation_not_found'; END IF;
  IF v_conversation.state <> 'ACTIVE' THEN
    RAISE EXCEPTION 'axent_conversation_not_active';
  END IF;

  SELECT COALESCE(max(ordinal), 0) + 1 INTO v_ordinal
  FROM tenant_private.axent_messages
  WHERE conversation_id = p_conversation_id AND tenant_id = v_tenant_id;

  INSERT INTO tenant_private.axent_messages (
    tenant_id, conversation_id, ordinal, message_role, ciphertext,
    content_hash, created_at
  ) VALUES (
    v_tenant_id,
    p_conversation_id,
    v_ordinal,
    p_message_role,
    pgp_sym_encrypt(p_content, p_encryption_key, 'cipher-algo=aes256,compress-algo=0'),
    'sha256:' || encode(digest(convert_to(p_content, 'UTF8'), 'sha256'), 'hex'),
    p_now
  )
  RETURNING * INTO v_message;

  UPDATE tenant_private.axent_conversations
  SET updated_at = p_now
  WHERE conversation_id = p_conversation_id AND tenant_id = v_tenant_id;

  PERFORM tenant_private.c3_append_axent_event(
    v_tenant_id, p_conversation_id, p_actor_subject, 'MESSAGE_APPENDED',
    jsonb_build_object(
      'message_id', v_message.message_id,
      'ordinal', v_message.ordinal,
      'message_role', v_message.message_role,
      'content_hash', v_message.content_hash
    ),
    p_now
  );
  RETURN v_message;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.export_axent_conversation(
  p_conversation_id uuid,
  p_encryption_key text,
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.c3_require_tenant();
  v_conversation tenant_private.axent_conversations%ROWTYPE;
  v_messages jsonb;
BEGIN
  IF p_encryption_key IS NULL OR octet_length(p_encryption_key) < 32 THEN
    RAISE EXCEPTION 'axent_encryption_key_invalid';
  END IF;
  SELECT * INTO v_conversation
  FROM tenant_private.axent_conversations
  WHERE conversation_id = p_conversation_id AND tenant_id = v_tenant_id;
  IF NOT FOUND THEN RAISE EXCEPTION 'axent_conversation_not_found'; END IF;

  SELECT COALESCE(
    jsonb_agg(
      jsonb_build_object(
        'message_id', message_id,
        'ordinal', ordinal,
        'role', message_role,
        'content', pgp_sym_decrypt(ciphertext, p_encryption_key),
        'content_hash', content_hash,
        'created_at', created_at
      ) ORDER BY ordinal
    ),
    '[]'::jsonb
  ) INTO v_messages
  FROM tenant_private.axent_messages
  WHERE conversation_id = p_conversation_id AND tenant_id = v_tenant_id;

  PERFORM tenant_private.c3_append_axent_event(
    v_tenant_id, p_conversation_id, p_actor_subject, 'CONVERSATION_EXPORTED',
    jsonb_build_object('message_count', jsonb_array_length(v_messages)), p_now
  );

  RETURN jsonb_build_object(
    'schema', 'axignal.axent-conversation-export.v1',
    'conversation_id', v_conversation.conversation_id,
    'tenant_id', v_tenant_id,
    'identity_subject', v_conversation.identity_subject,
    'title', v_conversation.title,
    'retention_class', v_conversation.retention_class,
    'retention_until', v_conversation.retention_until,
    'state', v_conversation.state,
    'messages', v_messages,
    'exported_at', p_now
  );
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.place_axent_legal_hold(
  p_conversation_id uuid,
  p_reason text,
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.axent_legal_holds
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.c3_require_tenant();
  v_hold tenant_private.axent_legal_holds%ROWTYPE;
BEGIN
  PERFORM 1 FROM tenant_private.axent_conversations
  WHERE conversation_id = p_conversation_id AND tenant_id = v_tenant_id;
  IF NOT FOUND THEN RAISE EXCEPTION 'axent_conversation_not_found'; END IF;
  IF p_reason IS NULL OR btrim(p_reason) = '' THEN
    RAISE EXCEPTION 'legal_hold_reason_required';
  END IF;

  INSERT INTO tenant_private.axent_legal_holds (
    tenant_id, conversation_id, reason, placed_by, placed_at
  ) VALUES (
    v_tenant_id, p_conversation_id, p_reason, p_actor_subject, p_now
  )
  RETURNING * INTO v_hold;

  PERFORM tenant_private.c3_append_axent_event(
    v_tenant_id, p_conversation_id, p_actor_subject, 'LEGAL_HOLD_PLACED',
    jsonb_build_object('legal_hold_id', v_hold.legal_hold_id, 'reason', p_reason), p_now
  );
  RETURN v_hold;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.release_axent_legal_hold(
  p_legal_hold_id uuid,
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.axent_legal_holds
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.c3_require_tenant();
  v_hold tenant_private.axent_legal_holds%ROWTYPE;
BEGIN
  UPDATE tenant_private.axent_legal_holds
  SET released_by = p_actor_subject, released_at = p_now
  WHERE legal_hold_id = p_legal_hold_id
    AND tenant_id = v_tenant_id
    AND released_at IS NULL
  RETURNING * INTO v_hold;
  IF NOT FOUND THEN RAISE EXCEPTION 'axent_active_legal_hold_not_found'; END IF;

  PERFORM tenant_private.c3_append_axent_event(
    v_tenant_id, v_hold.conversation_id, p_actor_subject, 'LEGAL_HOLD_RELEASED',
    jsonb_build_object('legal_hold_id', v_hold.legal_hold_id), p_now
  );
  RETURN v_hold;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.request_axent_conversation_deletion(
  p_conversation_id uuid,
  p_delete_after timestamptz,
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.axent_conversations
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.c3_require_tenant();
  v_conversation tenant_private.axent_conversations%ROWTYPE;
BEGIN
  IF p_delete_after IS NULL OR p_delete_after < p_now THEN
    RAISE EXCEPTION 'axent_deletion_deadline_invalid';
  END IF;
  UPDATE tenant_private.axent_conversations
  SET state = 'DELETION_REQUESTED',
      deletion_requested_at = p_now,
      retention_until = p_delete_after,
      updated_at = p_now
  WHERE conversation_id = p_conversation_id AND tenant_id = v_tenant_id
  RETURNING * INTO v_conversation;
  IF NOT FOUND THEN RAISE EXCEPTION 'axent_conversation_not_found'; END IF;

  PERFORM tenant_private.c3_append_axent_event(
    v_tenant_id, p_conversation_id, p_actor_subject, 'DELETION_REQUESTED',
    jsonb_build_object('delete_after', p_delete_after), p_now
  );
  RETURN v_conversation;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.purge_due_axent_conversations(
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS integer
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_conversation record;
  v_count integer := 0;
BEGIN
  IF p_actor_subject IS NULL OR btrim(p_actor_subject) = '' THEN
    RAISE EXCEPTION 'actor_subject_required';
  END IF;
  FOR v_conversation IN
    SELECT conversation_id, tenant_id
    FROM tenant_private.axent_conversations conversation
    WHERE conversation.retention_until <= p_now
      AND NOT EXISTS (
        SELECT 1
        FROM tenant_private.axent_legal_holds hold_row
        WHERE hold_row.conversation_id = conversation.conversation_id
          AND hold_row.released_at IS NULL
      )
    ORDER BY conversation.retention_until, conversation.conversation_id
    FOR UPDATE SKIP LOCKED
  LOOP
    PERFORM tenant_private.c3_append_axent_event(
      v_conversation.tenant_id,
      v_conversation.conversation_id,
      p_actor_subject,
      'CONVERSATION_PURGED',
      '{}'::jsonb,
      p_now
    );
    DELETE FROM tenant_private.axent_conversations
    WHERE conversation_id = v_conversation.conversation_id;
    v_count := v_count + 1;
  END LOOP;
  RETURN v_count;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.c3_capture_terminal_purge()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_counts jsonb;
  v_tenant_hash text;
  v_digest text;
BEGIN
  IF current_user <> 'axignal'
     OR current_setting('app.retention_purge', true) <> '1' THEN
    RAISE EXCEPTION 'C3_TERMINAL_PURGE_CONTEXT_REQUIRED';
  END IF;
  IF EXISTS (
    SELECT 1
    FROM tenant_private.axent_legal_holds
    WHERE tenant_id = OLD.tenant_id AND released_at IS NULL
  ) THEN
    RAISE EXCEPTION 'AXENT_LEGAL_HOLD_ACTIVE';
  END IF;

  SELECT jsonb_build_object(
    'subscriber_workspaces', (SELECT count(*) FROM tenant_private.subscriber_workspaces WHERE tenant_id = OLD.tenant_id),
    'subscriber_requirements', (SELECT count(*) FROM tenant_private.subscriber_requirements WHERE tenant_id = OLD.tenant_id),
    'subscriber_evidence', (SELECT count(*) FROM tenant_private.subscriber_evidence WHERE tenant_id = OLD.tenant_id),
    'subscriber_amendments', (SELECT count(*) FROM tenant_private.subscriber_amendments WHERE tenant_id = OLD.tenant_id),
    'subscriber_audit_events', (SELECT count(*) FROM tenant_private.subscriber_audit_events WHERE tenant_id = OLD.tenant_id),
    'axent_conversations', (SELECT count(*) FROM tenant_private.axent_conversations WHERE tenant_id = OLD.tenant_id),
    'axent_messages', (SELECT count(*) FROM tenant_private.axent_messages WHERE tenant_id = OLD.tenant_id),
    'axent_legal_holds', (SELECT count(*) FROM tenant_private.axent_legal_holds WHERE tenant_id = OLD.tenant_id),
    'axent_audit_events', (SELECT count(*) FROM tenant_private.axent_audit_events WHERE tenant_id = OLD.tenant_id)
  ) INTO v_counts;

  v_tenant_hash := 'sha256:' || encode(digest(OLD.tenant_id::text, 'sha256'), 'hex');
  v_digest := 'sha256:' || encode(
    digest(v_tenant_hash || v_counts::text || clock_timestamp()::text, 'sha256'),
    'hex'
  );
  INSERT INTO axignal_global.c3_terminal_purge_receipts (
    tenant_hash, object_counts, verification_digest
  ) VALUES (v_tenant_hash, v_counts, v_digest);
  RETURN OLD;
END
$$;

DROP TRIGGER IF EXISTS c3_workspace_terminal_purge_guard
  ON tenant_private.workspace_lifecycle;
CREATE TRIGGER c3_workspace_terminal_purge_guard
BEFORE DELETE ON tenant_private.workspace_lifecycle
FOR EACH ROW EXECUTE FUNCTION tenant_private.c3_capture_terminal_purge();

REVOKE ALL ON tenant_private.subscriber_workspaces,
  tenant_private.subscriber_requirements,
  tenant_private.subscriber_evidence,
  tenant_private.subscriber_amendments,
  tenant_private.subscriber_audit_events,
  tenant_private.axent_conversations,
  tenant_private.axent_messages,
  tenant_private.axent_legal_holds,
  tenant_private.axent_audit_events
FROM PUBLIC, axignal_app;

REVOKE ALL ON axignal_global.c3_terminal_purge_receipts FROM PUBLIC;
GRANT SELECT ON axignal_global.c3_terminal_purge_receipts
  TO axignal_retention_worker, axignal_operator;

REVOKE ALL ON FUNCTION tenant_private.c3_require_tenant() FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.c3_require_active_workspace() FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.c3_append_workspace_event(uuid, text, text, text, text, bigint, jsonb, timestamptz) FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.c3_touch_workspace(uuid, text, text, timestamptz) FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.c3_append_axent_event(uuid, uuid, text, text, jsonb, timestamptz) FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.c3_capture_terminal_purge() FROM PUBLIC;

REVOKE ALL ON FUNCTION tenant_private.create_subscriber_workspace(text, text, timestamptz, text, timestamptz) FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.record_subscriber_decision(uuid, text, text, timestamptz) FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.create_subscriber_requirement(uuid, text, text, boolean, text, text, timestamptz) FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.set_subscriber_requirement_status(uuid, text, text, timestamptz) FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.attach_subscriber_evidence(uuid, uuid, text, text, text, text, text, timestamptz, timestamptz, text, timestamptz) FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.record_subscriber_amendment(uuid, text, text, timestamptz, text, timestamptz) FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.acknowledge_subscriber_amendment(uuid, text, timestamptz) FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.subscriber_workspace_readiness(uuid, timestamptz) FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.prepare_subscriber_submission(uuid, text, timestamptz) FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.approve_subscriber_submission(uuid, text, timestamptz) FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.subscriber_workspace_summary(timestamptz) FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.subscriber_workspace_events(bigint) FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.create_axent_conversation(text, text, text, text, timestamptz) FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.append_axent_message(uuid, text, text, text, text, timestamptz) FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.export_axent_conversation(uuid, text, text, timestamptz) FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.place_axent_legal_hold(uuid, text, text, timestamptz) FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.release_axent_legal_hold(uuid, text, timestamptz) FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.request_axent_conversation_deletion(uuid, timestamptz, text, timestamptz) FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.purge_due_axent_conversations(text, timestamptz) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION tenant_private.create_subscriber_workspace(text, text, timestamptz, text, timestamptz),
  tenant_private.record_subscriber_decision(uuid, text, text, timestamptz),
  tenant_private.create_subscriber_requirement(uuid, text, text, boolean, text, text, timestamptz),
  tenant_private.set_subscriber_requirement_status(uuid, text, text, timestamptz),
  tenant_private.attach_subscriber_evidence(uuid, uuid, text, text, text, text, text, timestamptz, timestamptz, text, timestamptz),
  tenant_private.record_subscriber_amendment(uuid, text, text, timestamptz, text, timestamptz),
  tenant_private.acknowledge_subscriber_amendment(uuid, text, timestamptz),
  tenant_private.subscriber_workspace_readiness(uuid, timestamptz),
  tenant_private.prepare_subscriber_submission(uuid, text, timestamptz),
  tenant_private.approve_subscriber_submission(uuid, text, timestamptz),
  tenant_private.subscriber_workspace_summary(timestamptz),
  tenant_private.subscriber_workspace_events(bigint),
  tenant_private.create_axent_conversation(text, text, text, text, timestamptz),
  tenant_private.append_axent_message(uuid, text, text, text, text, timestamptz),
  tenant_private.export_axent_conversation(uuid, text, text, timestamptz),
  tenant_private.place_axent_legal_hold(uuid, text, text, timestamptz),
  tenant_private.release_axent_legal_hold(uuid, text, timestamptz),
  tenant_private.request_axent_conversation_deletion(uuid, timestamptz, text, timestamptz)
TO axignal_app;

GRANT EXECUTE ON FUNCTION tenant_private.purge_due_axent_conversations(text, timestamptz)
  TO axignal_retention_worker;

CREATE INDEX IF NOT EXISTS subscriber_workspaces_tenant_deadline_idx
  ON tenant_private.subscriber_workspaces (tenant_id, deadline, state);
CREATE INDEX IF NOT EXISTS subscriber_requirements_workspace_idx
  ON tenant_private.subscriber_requirements (tenant_id, workspace_id, blocking, status);
CREATE INDEX IF NOT EXISTS subscriber_evidence_requirement_idx
  ON tenant_private.subscriber_evidence (tenant_id, requirement_id, status, expires_at);
CREATE INDEX IF NOT EXISTS subscriber_amendments_workspace_idx
  ON tenant_private.subscriber_amendments (tenant_id, workspace_id, acknowledged);
CREATE INDEX IF NOT EXISTS subscriber_audit_events_tenant_sequence_idx
  ON tenant_private.subscriber_audit_events (tenant_id, event_sequence);
CREATE INDEX IF NOT EXISTS axent_conversations_retention_idx
  ON tenant_private.axent_conversations (retention_until, state);
CREATE INDEX IF NOT EXISTS axent_messages_conversation_idx
  ON tenant_private.axent_messages (tenant_id, conversation_id, ordinal);
CREATE INDEX IF NOT EXISTS axent_audit_events_tenant_sequence_idx
  ON tenant_private.axent_audit_events (tenant_id, event_sequence);
CREATE INDEX IF NOT EXISTS c3_terminal_purge_receipts_tenant_idx
  ON axignal_global.c3_terminal_purge_receipts (tenant_hash, captured_at DESC);
