CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS tenant_private.support_conversations (
  conversation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  workspace_id uuid,
  research_run_id uuid,
  opened_by_subject text NOT NULL,
  channel text NOT NULL DEFAULT 'WEB' CHECK (channel IN ('WEB','API','SYSTEM')),
  status text NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN','INVESTIGATING','AWAITING_CUSTOMER','AWAITING_SYSTEM','ESCALATED','RESOLVED','CLOSED')),
  intent text,
  priority text NOT NULL DEFAULT 'NORMAL' CHECK (priority IN ('LOW','NORMAL','HIGH','URGENT')),
  language text NOT NULL DEFAULT 'es',
  summary_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  last_message_at timestamptz,
  resolved_at timestamptz,
  resolution_code text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, conversation_id),
  FOREIGN KEY (tenant_id, workspace_id) REFERENCES tenant_private.subscriber_workspaces (tenant_id, workspace_id) ON DELETE RESTRICT,
  FOREIGN KEY (tenant_id, research_run_id) REFERENCES tenant_private.research_runs (tenant_id, research_run_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS tenant_private.support_messages (
  message_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  conversation_id uuid NOT NULL,
  author_type text NOT NULL CHECK (author_type IN ('USER','AXENT','HUMAN_AGENT','SYSTEM')),
  author_subject text,
  content text NOT NULL CHECK (char_length(content) BETWEEN 1 AND 100000),
  content_format text NOT NULL DEFAULT 'MARKDOWN' CHECK (content_format IN ('TEXT','MARKDOWN','STRUCTURED')),
  model_id text,
  prompt_policy_version text,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, conversation_id, message_id),
  FOREIGN KEY (tenant_id, conversation_id) REFERENCES tenant_private.support_conversations (tenant_id, conversation_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS tenant_private.support_message_citations (
  citation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  message_id uuid NOT NULL,
  authority_type text NOT NULL CHECK (authority_type IN ('KNOWLEDGE_REVISION','SUBSCRIPTION','ENTITLEMENT','RESEARCH_RUN','WORKSPACE','INVOICE','SOURCE_STATUS','INCIDENT','AUDIT_EVENT')),
  authority_id text NOT NULL,
  authority_version text NOT NULL,
  retrieved_at timestamptz NOT NULL DEFAULT now(),
  excerpt_hash text NOT NULL CHECK (excerpt_hash ~ '^sha256:[0-9a-f]{64}$'),
  FOREIGN KEY (tenant_id, message_id) REFERENCES tenant_private.support_messages (tenant_id, message_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS tenant_private.support_verified_facts (
  fact_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  conversation_id uuid NOT NULL,
  fact_type text NOT NULL,
  subject_type text NOT NULL,
  subject_id text NOT NULL,
  value_json jsonb NOT NULL,
  authority_source text NOT NULL,
  authority_version text NOT NULL,
  verified_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz,
  superseded_at timestamptz,
  FOREIGN KEY (tenant_id, conversation_id) REFERENCES tenant_private.support_conversations (tenant_id, conversation_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS tenant_private.support_cases (
  case_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  conversation_id uuid NOT NULL,
  case_type text NOT NULL CHECK (case_type IN ('HOW_TO','ACCOUNT_ACCESS','BILLING','SUBSCRIPTION','SEAT_MANAGEMENT','RESEARCH_RUN','SOURCE_DATA','ALERT','EXPORT','DOCUMENT','INTEGRATION','SECURITY','PRIVACY','LEGAL','BUG','SERVICE_INCIDENT','FEATURE_REQUEST')),
  severity text NOT NULL DEFAULT 'S3' CHECK (severity IN ('S0','S1','S2','S3','S4')),
  status text NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN','ACKNOWLEDGED','INVESTIGATING','AWAITING_CUSTOMER','RESOLVED','CLOSED')),
  owner_type text NOT NULL DEFAULT 'QUEUE' CHECK (owner_type IN ('QUEUE','HUMAN')),
  owner_subject text,
  service_area text NOT NULL,
  customer_impact text,
  system_impact text,
  resolution text,
  opened_at timestamptz NOT NULL DEFAULT now(),
  acknowledged_at timestamptz,
  resolved_at timestamptz,
  closed_at timestamptz,
  UNIQUE (tenant_id, case_id),
  FOREIGN KEY (tenant_id, conversation_id) REFERENCES tenant_private.support_conversations (tenant_id, conversation_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS tenant_private.support_tool_invocations (
  invocation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  conversation_id uuid NOT NULL,
  case_id uuid,
  tool_name text NOT NULL,
  tool_version text NOT NULL,
  requested_by_subject text NOT NULL,
  executed_as text NOT NULL DEFAULT 'AXENT_AGENT',
  input_redacted jsonb NOT NULL DEFAULT '{}'::jsonb,
  input_hash text NOT NULL CHECK (input_hash ~ '^sha256:[0-9a-f]{64}$'),
  decision text NOT NULL CHECK (decision IN ('ALLOW_READ','ALLOW','ALLOW_WITH_CONFIRMATION','REQUIRE_STEP_UP_AUTH','ESCALATE','DENY')),
  decision_reason jsonb NOT NULL DEFAULT '[]'::jsonb,
  result_status text NOT NULL CHECK (result_status IN ('PENDING','SUCCEEDED','FAILED','DENIED')),
  result_redacted jsonb NOT NULL DEFAULT '{}'::jsonb,
  started_at timestamptz NOT NULL DEFAULT now(),
  finished_at timestamptz,
  idempotency_key text,
  correlation_id text NOT NULL,
  UNIQUE (tenant_id, tool_name, idempotency_key),
  FOREIGN KEY (tenant_id, conversation_id) REFERENCES tenant_private.support_conversations (tenant_id, conversation_id) ON DELETE RESTRICT,
  FOREIGN KEY (tenant_id, case_id) REFERENCES tenant_private.support_cases (tenant_id, case_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS tenant_private.support_actions (
  action_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  conversation_id uuid NOT NULL,
  invocation_id uuid NOT NULL,
  action_type text NOT NULL,
  target_type text NOT NULL,
  target_id text NOT NULL,
  before_state_hash text,
  after_state_hash text,
  approval_mode text NOT NULL CHECK (approval_mode IN ('NONE','EXPLICIT_CONFIRMATION','STEP_UP_AUTH','HUMAN_AUTHORITY')),
  approved_by text,
  executed_at timestamptz NOT NULL DEFAULT now(),
  rollback_status text NOT NULL DEFAULT 'NOT_APPLICABLE' CHECK (rollback_status IN ('NOT_APPLICABLE','AVAILABLE','COMPLETED','FAILED')),
  FOREIGN KEY (tenant_id, conversation_id) REFERENCES tenant_private.support_conversations (tenant_id, conversation_id) ON DELETE RESTRICT,
  FOREIGN KEY (tenant_id, invocation_id) REFERENCES tenant_private.support_tool_invocations (tenant_id, invocation_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS axignal_global.knowledge_documents (
  knowledge_document_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  scope text NOT NULL CHECK (scope IN ('GLOBAL','PLAN','TENANT','INTERNAL')),
  tenant_id uuid,
  document_type text NOT NULL,
  slug text NOT NULL,
  title text NOT NULL,
  status text NOT NULL CHECK (status IN ('DRAFT','REVIEW','ACTIVE','RETIRED')),
  owner text NOT NULL,
  current_revision_id uuid,
  UNIQUE (scope, tenant_id, slug)
);

CREATE TABLE IF NOT EXISTS axignal_global.knowledge_revisions (
  revision_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id uuid NOT NULL REFERENCES axignal_global.knowledge_documents (knowledge_document_id) ON DELETE RESTRICT,
  version integer NOT NULL CHECK (version > 0),
  content text NOT NULL,
  content_hash text NOT NULL CHECK (content_hash ~ '^sha256:[0-9a-f]{64}$'),
  effective_from timestamptz NOT NULL,
  effective_until timestamptz,
  reviewed_by text,
  review_status text NOT NULL CHECK (review_status IN ('PENDING','APPROVED','REJECTED')),
  source_authority text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (document_id, version)
);

ALTER TABLE axignal_global.knowledge_documents
  ADD CONSTRAINT knowledge_current_revision_fk
  FOREIGN KEY (current_revision_id) REFERENCES axignal_global.knowledge_revisions (revision_id) DEFERRABLE INITIALLY DEFERRED;

CREATE TABLE IF NOT EXISTS axignal_global.knowledge_chunks (
  chunk_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  revision_id uuid NOT NULL REFERENCES axignal_global.knowledge_revisions (revision_id) ON DELETE RESTRICT,
  section_path text NOT NULL,
  content text NOT NULL,
  content_hash text NOT NULL CHECK (content_hash ~ '^sha256:[0-9a-f]{64}$'),
  embedding vector(1536),
  search_vector tsvector GENERATED ALWAYS AS (to_tsvector('simple', content)) STORED,
  language text NOT NULL,
  UNIQUE (revision_id, section_path, content_hash)
);

CREATE INDEX IF NOT EXISTS support_conversations_tenant_updated_idx ON tenant_private.support_conversations (tenant_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS support_messages_conversation_idx ON tenant_private.support_messages (tenant_id, conversation_id, created_at);
CREATE INDEX IF NOT EXISTS support_cases_status_idx ON tenant_private.support_cases (tenant_id, status, opened_at DESC);
CREATE INDEX IF NOT EXISTS knowledge_chunks_search_idx ON axignal_global.knowledge_chunks USING gin (search_vector);

DO $$
DECLARE rel regclass;
BEGIN
  FOREACH rel IN ARRAY ARRAY[
    'tenant_private.support_conversations'::regclass,
    'tenant_private.support_messages'::regclass,
    'tenant_private.support_message_citations'::regclass,
    'tenant_private.support_verified_facts'::regclass,
    'tenant_private.support_cases'::regclass,
    'tenant_private.support_tool_invocations'::regclass,
    'tenant_private.support_actions'::regclass
  ] LOOP
    EXECUTE format('ALTER TABLE %s ENABLE ROW LEVEL SECURITY', rel);
    EXECUTE format('ALTER TABLE %s FORCE ROW LEVEL SECURITY', rel);
  END LOOP;
END $$;

CREATE POLICY support_conversations_tenant_policy ON tenant_private.support_conversations USING (tenant_id = tenant_private.current_tenant_id()) WITH CHECK (tenant_id = tenant_private.current_tenant_id());
CREATE POLICY support_messages_tenant_policy ON tenant_private.support_messages USING (tenant_id = tenant_private.current_tenant_id()) WITH CHECK (tenant_id = tenant_private.current_tenant_id());
CREATE POLICY support_citations_tenant_policy ON tenant_private.support_message_citations USING (tenant_id = tenant_private.current_tenant_id()) WITH CHECK (tenant_id = tenant_private.current_tenant_id());
CREATE POLICY support_facts_tenant_policy ON tenant_private.support_verified_facts USING (tenant_id = tenant_private.current_tenant_id()) WITH CHECK (tenant_id = tenant_private.current_tenant_id());
CREATE POLICY support_cases_tenant_policy ON tenant_private.support_cases USING (tenant_id = tenant_private.current_tenant_id()) WITH CHECK (tenant_id = tenant_private.current_tenant_id());
CREATE POLICY support_invocations_tenant_policy ON tenant_private.support_tool_invocations USING (tenant_id = tenant_private.current_tenant_id()) WITH CHECK (tenant_id = tenant_private.current_tenant_id());
CREATE POLICY support_actions_tenant_policy ON tenant_private.support_actions USING (tenant_id = tenant_private.current_tenant_id()) WITH CHECK (tenant_id = tenant_private.current_tenant_id());

CREATE OR REPLACE FUNCTION tenant_private.reject_axent_ledger_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'AXENT support ledger is append-only';
END $$;

CREATE TRIGGER support_citations_immutable BEFORE UPDATE OR DELETE ON tenant_private.support_message_citations FOR EACH ROW EXECUTE FUNCTION tenant_private.reject_axent_ledger_mutation();
CREATE TRIGGER support_invocations_immutable BEFORE UPDATE OR DELETE ON tenant_private.support_tool_invocations FOR EACH ROW EXECUTE FUNCTION tenant_private.reject_axent_ledger_mutation();
CREATE TRIGGER support_actions_immutable BEFORE UPDATE OR DELETE ON tenant_private.support_actions FOR EACH ROW EXECUTE FUNCTION tenant_private.reject_axent_ledger_mutation();

GRANT SELECT, INSERT, UPDATE ON tenant_private.support_conversations, tenant_private.support_messages, tenant_private.support_verified_facts, tenant_private.support_cases TO axignal_app;
GRANT SELECT, INSERT ON tenant_private.support_message_citations, tenant_private.support_tool_invocations, tenant_private.support_actions TO axignal_app;
REVOKE DELETE ON tenant_private.support_conversations, tenant_private.support_messages, tenant_private.support_verified_facts, tenant_private.support_cases FROM axignal_app;
REVOKE UPDATE, DELETE ON tenant_private.support_message_citations, tenant_private.support_tool_invocations, tenant_private.support_actions FROM axignal_app;
GRANT SELECT ON axignal_global.knowledge_documents, axignal_global.knowledge_revisions, axignal_global.knowledge_chunks TO axignal_app;
