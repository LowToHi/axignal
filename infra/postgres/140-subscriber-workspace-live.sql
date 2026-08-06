CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE UNIQUE INDEX IF NOT EXISTS research_runs_tenant_run_uidx
  ON tenant_private.research_runs (tenant_id, research_run_id);

CREATE TABLE IF NOT EXISTS tenant_private.subscriber_workspaces (
  workspace_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  research_run_id uuid NOT NULL,
  opportunity_id text NOT NULL,
  title text NOT NULL CHECK (char_length(title) BETWEEN 1 AND 300),
  state text NOT NULL DEFAULT 'ACTIVE' CHECK (state IN ('ACTIVE', 'CLOSED')),
  owner_subject text NOT NULL,
  revision bigint NOT NULL DEFAULT 1 CHECK (revision > 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, workspace_id),
  UNIQUE (tenant_id, research_run_id),
  FOREIGN KEY (tenant_id, research_run_id)
    REFERENCES tenant_private.research_runs (tenant_id, research_run_id)
    ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS tenant_private.subscriber_workspace_documents (
  document_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  workspace_id uuid NOT NULL,
  title text NOT NULL CHECK (char_length(title) BETWEEN 1 AND 300),
  body text NOT NULL CHECK (char_length(body) BETWEEN 1 AND 200000),
  version integer NOT NULL DEFAULT 1 CHECK (version > 0),
  status text NOT NULL DEFAULT 'DRAFT' CHECK (status IN ('DRAFT', 'READY')),
  created_by text NOT NULL,
  updated_by text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, workspace_id, document_id),
  FOREIGN KEY (tenant_id, workspace_id)
    REFERENCES tenant_private.subscriber_workspaces (tenant_id, workspace_id)
    ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS tenant_private.subscriber_workspace_exports (
  export_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  workspace_id uuid NOT NULL,
  document_id uuid,
  format text NOT NULL CHECK (format = 'MARKDOWN'),
  filename text NOT NULL CHECK (filename ~ '^[A-Za-z0-9._-]{1,180}[.]md$'),
  content text NOT NULL CHECK (char_length(content) BETWEEN 1 AND 300000),
  content_hash text NOT NULL CHECK (content_hash ~ '^sha256:[0-9a-f]{64}$'),
  created_by text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, workspace_id, export_id),
  FOREIGN KEY (tenant_id, workspace_id)
    REFERENCES tenant_private.subscriber_workspaces (tenant_id, workspace_id)
    ON DELETE RESTRICT,
  FOREIGN KEY (tenant_id, workspace_id, document_id)
    REFERENCES tenant_private.subscriber_workspace_documents (
      tenant_id,
      workspace_id,
      document_id
    )
    ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS tenant_private.subscriber_workspace_audit_events (
  audit_event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  workspace_id uuid,
  actor_subject text NOT NULL,
  event_type text NOT NULL CHECK (event_type IN (
    'WORKSPACE_CREATED',
    'WORKSPACE_OPENED',
    'DOCUMENT_CREATED',
    'DOCUMENT_UPDATED',
    'EXPORT_CREATED'
  )),
  object_type text NOT NULL,
  object_id uuid NOT NULL,
  details jsonb NOT NULL DEFAULT '{}'::jsonb,
  occurred_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (tenant_id, workspace_id)
    REFERENCES tenant_private.subscriber_workspaces (tenant_id, workspace_id)
    ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS subscriber_workspaces_tenant_updated_idx
  ON tenant_private.subscriber_workspaces (tenant_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS subscriber_workspace_documents_workspace_idx
  ON tenant_private.subscriber_workspace_documents (
    tenant_id,
    workspace_id,
    updated_at DESC
  );
CREATE INDEX IF NOT EXISTS subscriber_workspace_exports_workspace_idx
  ON tenant_private.subscriber_workspace_exports (
    tenant_id,
    workspace_id,
    created_at DESC
  );
CREATE INDEX IF NOT EXISTS subscriber_workspace_audit_idx
  ON tenant_private.subscriber_workspace_audit_events (
    tenant_id,
    occurred_at DESC
  );

ALTER TABLE tenant_private.subscriber_workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.subscriber_workspaces FORCE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.subscriber_workspace_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.subscriber_workspace_documents FORCE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.subscriber_workspace_exports ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.subscriber_workspace_exports FORCE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.subscriber_workspace_audit_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.subscriber_workspace_audit_events FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS subscriber_workspaces_tenant_policy
  ON tenant_private.subscriber_workspaces;
CREATE POLICY subscriber_workspaces_tenant_policy
  ON tenant_private.subscriber_workspaces
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

DROP POLICY IF EXISTS subscriber_workspace_documents_tenant_policy
  ON tenant_private.subscriber_workspace_documents;
CREATE POLICY subscriber_workspace_documents_tenant_policy
  ON tenant_private.subscriber_workspace_documents
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

DROP POLICY IF EXISTS subscriber_workspace_exports_tenant_policy
  ON tenant_private.subscriber_workspace_exports;
CREATE POLICY subscriber_workspace_exports_tenant_policy
  ON tenant_private.subscriber_workspace_exports
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

DROP POLICY IF EXISTS subscriber_workspace_audit_tenant_policy
  ON tenant_private.subscriber_workspace_audit_events;
CREATE POLICY subscriber_workspace_audit_tenant_policy
  ON tenant_private.subscriber_workspace_audit_events
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

CREATE OR REPLACE FUNCTION tenant_private.reject_subscriber_audit_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE EXCEPTION 'AXIGNAL subscriber workspace audit is append-only';
END
$$;

DROP TRIGGER IF EXISTS subscriber_workspace_audit_immutable
  ON tenant_private.subscriber_workspace_audit_events;
CREATE TRIGGER subscriber_workspace_audit_immutable
BEFORE UPDATE OR DELETE ON tenant_private.subscriber_workspace_audit_events
FOR EACH ROW EXECUTE FUNCTION tenant_private.reject_subscriber_audit_mutation();

GRANT SELECT, INSERT, UPDATE
  ON tenant_private.subscriber_workspaces TO axignal_app;
GRANT SELECT, INSERT, UPDATE
  ON tenant_private.subscriber_workspace_documents TO axignal_app;
GRANT SELECT, INSERT
  ON tenant_private.subscriber_workspace_exports TO axignal_app;
GRANT SELECT, INSERT
  ON tenant_private.subscriber_workspace_audit_events TO axignal_app;
REVOKE DELETE
  ON tenant_private.subscriber_workspaces FROM axignal_app;
REVOKE DELETE
  ON tenant_private.subscriber_workspace_documents FROM axignal_app;
REVOKE UPDATE, DELETE
  ON tenant_private.subscriber_workspace_exports FROM axignal_app;
REVOKE UPDATE, DELETE
  ON tenant_private.subscriber_workspace_audit_events FROM axignal_app;
