-- AXIGNAL executable library objects (Prioridad 4).
-- Tenant-scoped canonical objects for O02-O09 vertical slices,
-- produced by the ingestion pipeline from frozen official-style fixtures.

CREATE TABLE IF NOT EXISTS tenant_private.library_objects (
  object_id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  library_id text NOT NULL CHECK (library_id ~ '^O0[2-9]$'),
  source_id text NOT NULL,
  content_hash text NOT NULL,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, library_id, source_id)
);

ALTER TABLE tenant_private.library_objects ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.library_objects FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS library_objects_tenant_isolation
  ON tenant_private.library_objects;
CREATE POLICY library_objects_tenant_isolation
  ON tenant_private.library_objects
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

GRANT SELECT, INSERT, UPDATE, DELETE ON tenant_private.library_objects TO axignal_worker;
GRANT SELECT ON tenant_private.library_objects TO axignal_app;

-- Technical fixture sources (non-commercial: COMMERCIAL_ADMISSION remains
-- BLOCKED_EXTERNAL until Legal/Privacy authorisation). Registered here
-- because only the migration role may insert into axignal_global.sources.
INSERT INTO axignal_global.sources (
  source_id, name, source_type, access_mode, base_url,
  rights_status, commercial_use, redistribution, kill_switch,
  license_id, attribution_text, terms_url, dataset_url,
  admission_state, config, last_reviewed_at
) VALUES
  ('src_cordis_grants_v1', 'Fixture O02 Grants', 'INSTITUTIONAL_API', 'PUBLIC_NO_AUTH', 'fixture://o02_grants_fixture.json',
   'COMMERCIAL_REUSE_WITH_ATTRIBUTION', false, false, false,
   'fixture-internal', 'Versioned internal fixture (official-style data)',
   'fixture://o02_grants_fixture.json#terms', NULL, 'ADMITTED',
   '{"fixture":"o02_grants_fixture.json","library_id":"O02","commercial_admission":"BLOCKED_EXTERNAL"}',
   now()),
  ('src_eurlex_regulation_v1', 'Fixture O03 Regulation', 'INSTITUTIONAL_API', 'PUBLIC_NO_AUTH', 'fixture://o03_regulation_fixture.json',
   'COMMERCIAL_REUSE_WITH_ATTRIBUTION', false, false, false,
   'fixture-internal', 'Versioned internal fixture (official-style data)',
   'fixture://o03_regulation_fixture.json#terms', NULL, 'ADMITTED',
   '{"fixture":"o03_regulation_fixture.json","library_id":"O03","commercial_admission":"BLOCKED_EXTERNAL"}',
   now()),
  ('src_o04_o09_fixture_v1', 'Fixture O04-O09', 'INSTITUTIONAL_API', 'PUBLIC_NO_AUTH', 'fixture://o04_o09_fixture.json',
   'COMMERCIAL_REUSE_WITH_ATTRIBUTION', false, false, false,
   'fixture-internal', 'Versioned internal fixture (official-style data)',
   'fixture://o04_o09_fixture.json#terms', NULL, 'ADMITTED',
   '{"fixture":"o04_o09_fixture.json","libraries":["O04","O05","O06","O07","O08","O09"],"commercial_admission":"BLOCKED_EXTERNAL"}',
   now())
ON CONFLICT (source_id) DO NOTHING;
