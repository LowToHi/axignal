-- AXENT customer support spine (Mandato AXENT — secciones 12-13).
--
-- Adapted from the historical reference branch (150/153/154) onto the
-- current schema: support conversations, messages, citations, verified
-- facts, cases, case events, tool invocations, actions, confirmations,
-- notifications, feedback, evaluations, incident links, knowledge
-- governance (documents, revisions, chunks). Tenant-scoped, forced RLS,
-- append-only ledgers.

CREATE UNIQUE INDEX IF NOT EXISTS support_messages_tenant_message_uidx
  ON tenant_private.axent_messages (tenant_id, message_id);

-- Tenant-aware uniqueness on conversations (composite FK target).
CREATE UNIQUE INDEX IF NOT EXISTS axent_conversations_tenant_conversation_uidx
  ON tenant_private.axent_conversations (tenant_id, conversation_id);

CREATE TABLE IF NOT EXISTS tenant_private.support_cases (
  case_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  conversation_id uuid NOT NULL,
  case_ref text NOT NULL,
  subject text NOT NULL,
  description text NOT NULL,
  status text NOT NULL DEFAULT 'OPEN' CHECK (status IN (
    'OPEN', 'INVESTIGATING', 'AWAITING_CUSTOMER', 'AWAITING_SYSTEM',
    'ESCALATED', 'RESOLVED', 'CLOSED', 'REOPENED'
  )),
  severity text NOT NULL DEFAULT 'S3' CHECK (severity IN ('S0', 'S1', 'S2', 'S3', 'S4')),
  priority text NOT NULL DEFAULT 'NORMAL' CHECK (priority IN ('LOW', 'NORMAL', 'HIGH', 'URGENT')),
  assigned_to text,
  resolution_code text,
  resolved_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, case_ref),
  FOREIGN KEY (tenant_id, conversation_id)
    REFERENCES tenant_private.axent_conversations (tenant_id, conversation_id) ON DELETE RESTRICT
);

-- Tenant-aware uniqueness on cases (composite FK targets).
CREATE UNIQUE INDEX IF NOT EXISTS support_cases_tenant_case_uidx
  ON tenant_private.support_cases (tenant_id, case_id);

CREATE TABLE IF NOT EXISTS tenant_private.support_case_events (
  event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  case_id uuid NOT NULL,
  event_type text NOT NULL,
  actor_subject text NOT NULL,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (tenant_id, case_id)
    REFERENCES tenant_private.support_cases (tenant_id, case_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tenant_private.support_incidents (
  incident_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  incident_ref text NOT NULL,
  fingerprint text NOT NULL,
  severity text NOT NULL DEFAULT 'S3' CHECK (severity IN ('S0', 'S1', 'S2', 'S3', 'S4')),
  status text NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'INVESTIGATING', 'RESOLVED', 'CLOSED')),
  summary text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, fingerprint)
);

-- Tenant-aware uniqueness on incidents (composite FK target).
CREATE UNIQUE INDEX IF NOT EXISTS support_incidents_tenant_incident_uidx
  ON tenant_private.support_incidents (tenant_id, incident_id);

CREATE TABLE IF NOT EXISTS tenant_private.support_incident_links (
  link_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  case_id uuid NOT NULL,
  incident_id uuid NOT NULL,
  linked_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (tenant_id, case_id)
    REFERENCES tenant_private.support_cases (tenant_id, case_id) ON DELETE CASCADE,
  FOREIGN KEY (tenant_id, incident_id)
    REFERENCES tenant_private.support_incidents (tenant_id, incident_id) ON DELETE CASCADE,
  UNIQUE (tenant_id, case_id, incident_id)
);

CREATE TABLE IF NOT EXISTS tenant_private.support_notifications (
  notification_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  case_id uuid NOT NULL,
  recipient_subject text NOT NULL,
  notification_type text NOT NULL,
  body text NOT NULL,
  read_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (tenant_id, case_id)
    REFERENCES tenant_private.support_cases (tenant_id, case_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tenant_private.support_feedback (
  feedback_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  case_id uuid NOT NULL,
  rating integer NOT NULL CHECK (rating BETWEEN 1 AND 5),
  comment text,
  created_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (tenant_id, case_id)
    REFERENCES tenant_private.support_cases (tenant_id, case_id) ON DELETE CASCADE
);

-- Knowledge governance: candidates -> review -> approval -> versioned
-- revision -> effective date -> retrieval eligibility.
CREATE TABLE IF NOT EXISTS axignal_global.knowledge_documents (
  knowledge_document_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title text NOT NULL,
  source_authority text NOT NULL,
  language text NOT NULL DEFAULT 'es',
  scope text NOT NULL DEFAULT 'PRODUCT',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS axignal_global.knowledge_revisions (
  revision_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id uuid NOT NULL REFERENCES axignal_global.knowledge_documents(knowledge_document_id) ON DELETE RESTRICT,
  version integer NOT NULL,
  content text NOT NULL,
  content_hash text NOT NULL CHECK (content_hash ~ '^sha256:[0-9a-f]{64}$'),
  status text NOT NULL DEFAULT 'CANDIDATE' CHECK (status IN (
    'CANDIDATE', 'APPROVED', 'SUPERSEDED', 'RETIRED'
  )),
  owner_subject text NOT NULL,
  reviewed_by text,
  effective_at timestamptz,
  retired_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (document_id, version)
);

CREATE TABLE IF NOT EXISTS axignal_global.knowledge_chunks (
  chunk_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  revision_id uuid NOT NULL REFERENCES axignal_global.knowledge_revisions(revision_id) ON DELETE RESTRICT,
  section_path text NOT NULL,
  content text NOT NULL,
  search_vector tsvector NOT NULL DEFAULT ''::tsvector,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS knowledge_chunks_search_idx
  ON axignal_global.knowledge_chunks USING gin (search_vector);
CREATE INDEX IF NOT EXISTS knowledge_revisions_document_idx
  ON axignal_global.knowledge_revisions (document_id, version DESC);

-- Append-only: knowledge revision CONTENT can never be mutated; status
-- transitions (CANDIDATE -> APPROVED -> SUPERSEDED/RETIRED) are the only
-- allowed mutations, performed by human authority.
CREATE OR REPLACE FUNCTION tenant_private.guard_knowledge_revision_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'knowledge revisions are append-only; create a new version';
  END IF;
  IF NEW.content IS DISTINCT FROM OLD.content
     OR NEW.content_hash IS DISTINCT FROM OLD.content_hash
     OR NEW.version IS DISTINCT FROM OLD.version THEN
    RAISE EXCEPTION 'knowledge revision content is immutable';
  END IF;
  RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS knowledge_revisions_immutable ON axignal_global.knowledge_revisions;
CREATE TRIGGER knowledge_revisions_immutable
BEFORE UPDATE OR DELETE ON axignal_global.knowledge_revisions
FOR EACH ROW EXECUTE FUNCTION tenant_private.guard_knowledge_revision_mutation();

-- RLS on tenant-scoped support tables.
DO $$
DECLARE
  rel text;
BEGIN
  FOREACH rel IN ARRAY ARRAY[
    'support_cases', 'support_case_events', 'support_incidents',
    'support_incident_links', 'support_notifications', 'support_feedback'
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
  tenant_private.support_cases,
  tenant_private.support_case_events,
  tenant_private.support_incidents,
  tenant_private.support_incident_links,
  tenant_private.support_notifications,
  tenant_private.support_feedback
  TO axignal_worker;
GRANT SELECT ON
  tenant_private.support_cases,
  tenant_private.support_case_events,
  tenant_private.support_incidents,
  tenant_private.support_incident_links,
  tenant_private.support_notifications,
  tenant_private.support_feedback
  TO axignal_app;
GRANT SELECT, INSERT, UPDATE ON
  axignal_global.knowledge_documents,
  axignal_global.knowledge_revisions,
  axignal_global.knowledge_chunks
  TO axignal_worker;
GRANT SELECT ON
  axignal_global.knowledge_documents,
  axignal_global.knowledge_revisions,
  axignal_global.knowledge_chunks
  TO axignal_app;
