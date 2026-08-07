-- AXIGNAL O01 continuous chain — persisted, versioned notices.
-- Prioridad 1: the pipeline materialises Notice -> Opportunity -> Pursuit ->
-- Bid Workspace from the TED worker; the test never invents opportunity ids.
--
-- tenant_private.opportunity_notices:
--   one row per (tenant, publication_number); every ingestion version is
--   stored with content hash, retrieval time, source reference and state.
--   Amendments produce a NEW version of the same publication number with a
--   different content hash; the previous version remains auditable.
--
-- axignal_global.notice_versions:
--   append-only version history (content hash per retrieval), shared across
--   tenants for dedup purposes; tenant link is via opportunity_notices.

CREATE TABLE IF NOT EXISTS axignal_global.notice_versions (
  version_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  publication_number text NOT NULL,
  source_id text NOT NULL,
  version integer NOT NULL,
  content_hash text NOT NULL,
  retrieved_at timestamptz NOT NULL,
  payload jsonb NOT NULL,
  UNIQUE (publication_number, source_id, version)
);

CREATE TABLE IF NOT EXISTS tenant_private.opportunity_notices (
  notice_id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  publication_number text NOT NULL,
  source_id text NOT NULL,
  current_version integer NOT NULL,
  current_content_hash text NOT NULL,
  first_retrieved_at timestamptz NOT NULL,
  last_retrieved_at timestamptz NOT NULL,
  last_version_id uuid NOT NULL REFERENCES axignal_global.notice_versions(version_id),
  notice_title jsonb NOT NULL DEFAULT '{}'::jsonb,
  buyer_name jsonb NOT NULL DEFAULT '{}'::jsonb,
  notice_type text,
  state text NOT NULL DEFAULT 'ACTIVE'
    CHECK (state IN ('ACTIVE', 'AMENDED', 'CANCELLED', 'QUARANTINED')),
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE (tenant_id, publication_number, source_id)
);

ALTER TABLE tenant_private.opportunity_notices ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.opportunity_notices FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS opportunity_notices_tenant_isolation
  ON tenant_private.opportunity_notices;
CREATE POLICY opportunity_notices_tenant_isolation
  ON tenant_private.opportunity_notices
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

-- The materialised Opportunity produced by the pipeline (not by tests).
CREATE TABLE IF NOT EXISTS tenant_private.opportunity_objects (
  opportunity_id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  opportunity_ref text NOT NULL,
  library_id text NOT NULL,
  notice_id uuid REFERENCES tenant_private.opportunity_notices(notice_id),
  publication_number text,
  version integer NOT NULL,
  content_hash text NOT NULL,
  source_id text NOT NULL,
  produced_by text NOT NULL,
  produced_at timestamptz NOT NULL DEFAULT now(),
  state text NOT NULL DEFAULT 'OPEN'
    CHECK (state IN ('OPEN', 'QUALIFIED', 'PURSUED', 'CLOSED', 'SUSPENDED')),
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE (tenant_id, opportunity_ref)
);

ALTER TABLE tenant_private.opportunity_objects ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.opportunity_objects FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS opportunity_objects_tenant_isolation
  ON tenant_private.opportunity_objects;
CREATE POLICY opportunity_objects_tenant_isolation
  ON tenant_private.opportunity_objects
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

GRANT SELECT, INSERT, UPDATE, DELETE ON
  tenant_private.opportunity_notices,
  tenant_private.opportunity_objects,
  axignal_global.notice_versions
  TO axignal_worker;
GRANT SELECT ON
  tenant_private.opportunity_notices,
  tenant_private.opportunity_objects,
  axignal_global.notice_versions
  TO axignal_app;
