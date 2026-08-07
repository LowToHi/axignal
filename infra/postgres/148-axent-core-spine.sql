-- AXENT core persistence (Mandato AXENT — sección 6.1).
--
-- Extends the existing axent_conversations/messages (140) with the
-- conversational-operational spine:
--
--   axent_message_citations     append-only, tenant-scoped
--   axent_verified_facts        grounded facts asserted by AXENT
--   axent_tool_invocations      append-only typed tool calls
--   axent_actions               append-only action ledger
--   axent_confirmations         consent tokens (preview + confirmation)
--   axent_notifications         contextual notifications
--   axent_feedback              user feedback on answers/actions
--   axent_evaluations           internal evaluations (never user-visible)
--
-- All tenant-scoped, forced RLS, tenant-aware FKs.

-- Tenant-aware uniqueness on the parent message table (needed by the
-- composite FKs below; idempotent).
CREATE UNIQUE INDEX IF NOT EXISTS axent_messages_tenant_message_uidx
  ON tenant_private.axent_messages (tenant_id, message_id);

CREATE TABLE IF NOT EXISTS tenant_private.axent_message_citations (
  citation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  message_id uuid NOT NULL,
  authority_type text NOT NULL CHECK (authority_type IN (
    'CANONICAL_CLAIM', 'EVIDENCE_OBJECT', 'SOURCE_OBJECT', 'NOTICE',
    'OPPORTUNITY', 'PURSUIT', 'WORKSPACE', 'REQUIREMENT', 'TASK',
    'OUTCOME', 'LEARNING', 'RESEARCH_RUN', 'KNOWLEDGE_REVISION',
    'ENTITLEMENT', 'SUBSCRIPTION', 'INCIDENT', 'AUDIT_EVENT'
  )),
  authority_id text NOT NULL,
  authority_version text NOT NULL,
  retrieved_at timestamptz NOT NULL DEFAULT now(),
  excerpt_hash text NOT NULL CHECK (excerpt_hash ~ '^sha256:[0-9a-f]{64}$'),
  FOREIGN KEY (tenant_id, message_id)
    REFERENCES tenant_private.axent_messages (tenant_id, message_id) ON DELETE CASCADE,
  UNIQUE (tenant_id, message_id, authority_type, authority_id, excerpt_hash)
);

CREATE TABLE IF NOT EXISTS tenant_private.axent_verified_facts (
  fact_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  conversation_id uuid NOT NULL REFERENCES tenant_private.axent_conversations(conversation_id) ON DELETE CASCADE,
  fact_type text NOT NULL CHECK (fact_type IN (
    'SOURCE_FACT', 'CANONICAL_CLAIM', 'INFERENCE', 'RECOMMENDATION',
    'UNKNOWN', 'CONTRADICTION'
  )),
  subject_type text NOT NULL,
  subject_id text NOT NULL,
  value_json jsonb NOT NULL,
  citation_ids uuid[] NOT NULL DEFAULT '{}'::uuid[],
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, conversation_id, subject_type, subject_id, fact_type)
);

CREATE TABLE IF NOT EXISTS tenant_private.axent_tool_invocations (
  invocation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  conversation_id uuid NOT NULL REFERENCES tenant_private.axent_conversations(conversation_id) ON DELETE CASCADE,
  tool_name text NOT NULL,
  tool_version text NOT NULL,
  parameters_hash text NOT NULL CHECK (parameters_hash ~ '^sha256:[0-9a-f]{64}$'),
  parameters_json jsonb NOT NULL,
  risk_class text NOT NULL CHECK (risk_class IN (
    'READ', 'LOW_RISK_REVERSIBLE', 'EXPLICIT_CONFIRMATION',
    'STEP_UP_REQUIRED', 'HUMAN_ONLY', 'DENY'
  )),
  state text NOT NULL DEFAULT 'PENDING' CHECK (state IN (
    'PENDING', 'CONFIRMATION_REQUIRED', 'APPROVED', 'EXECUTED',
    'FAILED', 'DENIED', 'CANCELLED'
  )),
  before_state_hash text,
  after_state_hash text,
  error_code text,
  executed_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Tenant-aware uniqueness on invocations (composite FK target).
CREATE UNIQUE INDEX IF NOT EXISTS axent_invocations_tenant_invocation_uidx
  ON tenant_private.axent_tool_invocations (tenant_id, invocation_id);

CREATE TABLE IF NOT EXISTS tenant_private.axent_actions (
  action_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  conversation_id uuid NOT NULL REFERENCES tenant_private.axent_conversations(conversation_id) ON DELETE CASCADE,
  invocation_id uuid NOT NULL,
  action_type text NOT NULL,
  object_type text NOT NULL,
  object_ref text NOT NULL,
  parameters_hash text NOT NULL CHECK (parameters_hash ~ '^sha256:[0-9a-f]{64}$'),
  receipt_json jsonb NOT NULL,
  outcome text NOT NULL CHECK (outcome IN ('SUCCESS', 'FAILED', 'DENIED', 'CANCELLED')),
  actor_subject text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (tenant_id, invocation_id)
    REFERENCES tenant_private.axent_tool_invocations (tenant_id, invocation_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS tenant_private.axent_confirmations (
  confirmation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  conversation_id uuid NOT NULL REFERENCES tenant_private.axent_conversations(conversation_id) ON DELETE CASCADE,
  invocation_id uuid NOT NULL REFERENCES tenant_private.axent_tool_invocations(invocation_id) ON DELETE CASCADE,
  action_type text NOT NULL,
  parameters_hash text NOT NULL CHECK (parameters_hash ~ '^sha256:[0-9a-f]{64}$'),
  before_state_hash text NOT NULL,
  state text NOT NULL DEFAULT 'PENDING' CHECK (state IN (
    'PENDING', 'CONFIRMED', 'REJECTED', 'EXPIRED', 'CANCELLED'
  )),
  issued_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL,
  confirmed_at timestamptz,
  confirmed_by text
);

CREATE TABLE IF NOT EXISTS tenant_private.axent_notifications (
  notification_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  recipient_subject text NOT NULL,
  notification_type text NOT NULL,
  title text NOT NULL,
  body text NOT NULL,
  route_path text,
  severity text NOT NULL DEFAULT 'INFO' CHECK (severity IN ('INFO', 'WARNING', 'CRITICAL')),
  read_at timestamptz,
  acknowledged_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tenant_private.axent_feedback (
  feedback_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  message_id uuid NOT NULL,
  rating integer NOT NULL CHECK (rating BETWEEN 1 AND 5),
  comment text,
  category text,
  created_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (tenant_id, message_id)
    REFERENCES tenant_private.axent_messages (tenant_id, message_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tenant_private.axent_evaluations (
  evaluation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  message_id uuid NOT NULL,
  grounded boolean NOT NULL,
  grounded_with_uncertainty boolean NOT NULL,
  cross_tenant_ok boolean NOT NULL,
  policy_violation text,
  notes text,
  created_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (tenant_id, message_id)
    REFERENCES tenant_private.axent_messages (tenant_id, message_id) ON DELETE CASCADE
);

-- Append-only guards ---------------------------------------------------------

CREATE OR REPLACE FUNCTION tenant_private.reject_axent_ledger_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'AXENT ledger is append-only';
END $$;

DROP TRIGGER IF EXISTS axent_citations_immutable ON tenant_private.axent_message_citations;
CREATE TRIGGER axent_citations_immutable
BEFORE UPDATE OR DELETE ON tenant_private.axent_message_citations
FOR EACH ROW EXECUTE FUNCTION tenant_private.reject_axent_ledger_mutation();

DROP TRIGGER IF EXISTS axent_actions_immutable ON tenant_private.axent_actions;
CREATE TRIGGER axent_actions_immutable
BEFORE UPDATE OR DELETE ON tenant_private.axent_actions
FOR EACH ROW EXECUTE FUNCTION tenant_private.reject_axent_ledger_mutation();

-- RLS ------------------------------------------------------------------------

DO $$
DECLARE
  rel text;
BEGIN
  FOREACH rel IN ARRAY ARRAY[
    'axent_message_citations', 'axent_verified_facts',
    'axent_tool_invocations', 'axent_actions', 'axent_confirmations',
    'axent_notifications', 'axent_feedback', 'axent_evaluations'
  ]
  LOOP
    EXECUTE format('ALTER TABLE tenant_private.%I ENABLE ROW LEVEL SECURITY', rel);
    EXECUTE format('ALTER TABLE tenant_private.%I FORCE ROW LEVEL SECURITY', rel);
    EXECUTE format('DROP POLICY IF EXISTS %I ON tenant_private.%I', rel || '_tenant_isolation', rel);
    EXECUTE format(
      'CREATE POLICY %I ON tenant_private.%I '
      'USING (tenant_id = tenant_private.current_tenant_id()) '
      'WITH CHECK (tenant_id = tenant_private.current_tenant_id())',
      rel || '_tenant_isolation', rel
    );
  END LOOP;
END $$;

GRANT SELECT, INSERT, UPDATE, DELETE ON
  tenant_private.axent_message_citations,
  tenant_private.axent_verified_facts,
  tenant_private.axent_tool_invocations,
  tenant_private.axent_actions,
  tenant_private.axent_confirmations,
  tenant_private.axent_notifications,
  tenant_private.axent_feedback,
  tenant_private.axent_evaluations
  TO axignal_worker;
GRANT SELECT ON
  tenant_private.axent_message_citations,
  tenant_private.axent_verified_facts,
  tenant_private.axent_tool_invocations,
  tenant_private.axent_actions,
  tenant_private.axent_confirmations,
  tenant_private.axent_notifications,
  tenant_private.axent_feedback,
  tenant_private.axent_evaluations
  TO axignal_app;
