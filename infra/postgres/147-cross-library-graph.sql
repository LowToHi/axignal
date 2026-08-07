-- AXIGNAL persistent cross-library graph (Prioridad 5).
--
-- Nodes, edges, timeline events, contradictions and causal hypotheses
-- persisted tenant-scoped (forced RLS). Relations keep evidence refs and
-- provenance; hypotheses are NEVER canonical (separate table, flagged
-- non-canonical). Suspension of a source invalidates its edges via
-- status=QUARANTINED.

CREATE TABLE IF NOT EXISTS tenant_private.cross_library_nodes (
  node_id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  node_ref text NOT NULL,
  library_id text NOT NULL,
  entity_type text NOT NULL,
  label text NOT NULL,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, node_ref)
);

ALTER TABLE tenant_private.cross_library_nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.cross_library_nodes FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS cross_library_nodes_tenant_isolation
  ON tenant_private.cross_library_nodes;
CREATE POLICY cross_library_nodes_tenant_isolation
  ON tenant_private.cross_library_nodes
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

CREATE TABLE IF NOT EXISTS tenant_private.cross_library_edges (
  edge_id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  from_ref text NOT NULL,
  to_ref text NOT NULL,
  relation text NOT NULL,
  evidence_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
  status text NOT NULL DEFAULT 'ACTIVE'
    CHECK (status IN ('ACTIVE', 'QUARANTINED', 'SUPERSEDED')),
  source_id text,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, from_ref, to_ref, relation)
);

ALTER TABLE tenant_private.cross_library_edges ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.cross_library_edges FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS cross_library_edges_tenant_isolation
  ON tenant_private.cross_library_edges;
CREATE POLICY cross_library_edges_tenant_isolation
  ON tenant_private.cross_library_edges
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

CREATE TABLE IF NOT EXISTS tenant_private.cross_library_timeline (
  event_id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  node_ref text NOT NULL,
  occurred_at timestamptz NOT NULL,
  event_type text NOT NULL,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE tenant_private.cross_library_timeline ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.cross_library_timeline FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS cross_library_timeline_tenant_isolation
  ON tenant_private.cross_library_timeline;
CREATE POLICY cross_library_timeline_tenant_isolation
  ON tenant_private.cross_library_timeline
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

-- Contradictions: explicit, never silently resolved.
CREATE TABLE IF NOT EXISTS tenant_private.cross_library_contradictions (
  contradiction_id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  claim_a_ref text NOT NULL,
  claim_b_ref text NOT NULL,
  description text NOT NULL,
  status text NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'RESOLVED', 'ACCEPTED')),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, claim_a_ref, claim_b_ref)
);

ALTER TABLE tenant_private.cross_library_contradictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.cross_library_contradictions FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS cross_library_contradictions_tenant_isolation
  ON tenant_private.cross_library_contradictions;
CREATE POLICY cross_library_contradictions_tenant_isolation
  ON tenant_private.cross_library_contradictions
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

-- Causal hypotheses: NEVER canonical (enforced by table separation and
-- the API layer refusing to admit them).
CREATE TABLE IF NOT EXISTS tenant_private.cross_library_hypotheses (
  hypothesis_id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  hypothesis_ref text NOT NULL,
  cause_ref text NOT NULL,
  effect_ref text NOT NULL,
  description text NOT NULL,
  confidence text NOT NULL DEFAULT 'LOW' CHECK (confidence IN ('LOW', 'MEDIUM', 'HIGH')),
  status text NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'DISMISSED', 'ELEVATED')),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, hypothesis_ref)
);

ALTER TABLE tenant_private.cross_library_hypotheses ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.cross_library_hypotheses FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS cross_library_hypotheses_tenant_isolation
  ON tenant_private.cross_library_hypotheses;
CREATE POLICY cross_library_hypotheses_tenant_isolation
  ON tenant_private.cross_library_hypotheses
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

GRANT SELECT, INSERT, UPDATE, DELETE ON
  tenant_private.cross_library_nodes,
  tenant_private.cross_library_edges,
  tenant_private.cross_library_timeline,
  tenant_private.cross_library_contradictions,
  tenant_private.cross_library_hypotheses
  TO axignal_worker;
GRANT SELECT ON
  tenant_private.cross_library_nodes,
  tenant_private.cross_library_edges,
  tenant_private.cross_library_timeline,
  tenant_private.cross_library_contradictions,
  tenant_private.cross_library_hypotheses
  TO axignal_app;
