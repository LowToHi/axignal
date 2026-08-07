-- AXIGNAL Bid Workspace O01 durable spine (Prioridad 3).
--
-- The bid workspace journey (notice -> lots -> requirements -> criteria ->
-- documents -> amendments -> questions -> risks -> corporate evidence ->
-- tasks -> owners -> readiness -> review -> human approval -> handoff ->
-- outcome) with:
--   * versioned workspaces and requirements;
--   * official requirement vs inference vs recommendation distinction;
--   * amendment invalidation of affected requirements;
--   * append-only audit enforced BY THE DATABASE (no UPDATE/DELETE grants
--     on audit rows for any role);
--   * tenant isolation (forced RLS).
--
-- Tables:
--   tenant_private.bid_workspace_audit        append-only audit trail
--   tenant_private.bid_requirements           official/inference/recommendation
--   tenant_private.bid_requirement_versions   versioned requirements
--   tenant_private.bid_questions              clarification questions
--   tenant_private.bid_risks                  risks with mitigations
--   tenant_private.bid_tasks                  tasks with owners and state
--   tenant_private.bid_readiness              readiness checks per requirement
--   tenant_private.bid_approvals              human approvals (append-only)
--   tenant_private.bid_handoffs               handoff records (append-only)

-- ===========================================================================
-- 1. Requirements (current state) + versions (append-only history)
-- ===========================================================================

CREATE TABLE IF NOT EXISTS tenant_private.bid_requirements (
  requirement_id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  workspace_id uuid NOT NULL REFERENCES tenant_private.opportunity_workspaces(workspace_id) ON DELETE CASCADE,
  requirement_ref text NOT NULL,
  kind text NOT NULL CHECK (kind IN ('OFFICIAL', 'INFERENCE', 'RECOMMENDATION')),
  title text NOT NULL,
  description text NOT NULL DEFAULT '',
  source_notice_version integer,
  affected_by_amendment text,
  status text NOT NULL DEFAULT 'ACTIVE'
    CHECK (status IN ('ACTIVE', 'AMENDED', 'SUPERSEDED', 'REJECTED')),
  invalidated_by text,
  created_by text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, workspace_id, requirement_ref)
);

ALTER TABLE tenant_private.bid_requirements ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.bid_requirements FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS bid_requirements_tenant_isolation
  ON tenant_private.bid_requirements;
CREATE POLICY bid_requirements_tenant_isolation
  ON tenant_private.bid_requirements
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

CREATE TABLE IF NOT EXISTS tenant_private.bid_requirement_versions (
  version_id uuid PRIMARY KEY,
  requirement_id uuid NOT NULL REFERENCES tenant_private.bid_requirements(requirement_id) ON DELETE CASCADE,
  tenant_id uuid NOT NULL,
  version integer NOT NULL,
  title text NOT NULL,
  description text NOT NULL DEFAULT '',
  kind text NOT NULL,
  changed_by text NOT NULL,
  changed_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (requirement_id, version)
);

ALTER TABLE tenant_private.bid_requirement_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.bid_requirement_versions FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS bid_requirement_versions_tenant_isolation
  ON tenant_private.bid_requirement_versions;
CREATE POLICY bid_requirement_versions_tenant_isolation
  ON tenant_private.bid_requirement_versions
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

-- ===========================================================================
-- 2. Questions, risks, tasks, readiness
-- ===========================================================================

CREATE TABLE IF NOT EXISTS tenant_private.bid_questions (
  question_id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  workspace_id uuid NOT NULL REFERENCES tenant_private.opportunity_workspaces(workspace_id) ON DELETE CASCADE,
  question_ref text NOT NULL,
  question text NOT NULL,
  answer text,
  status text NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'ANSWERED', 'CLOSED')),
  asked_by text NOT NULL,
  asked_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, workspace_id, question_ref)
);

ALTER TABLE tenant_private.bid_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.bid_questions FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS bid_questions_tenant_isolation
  ON tenant_private.bid_questions;
CREATE POLICY bid_questions_tenant_isolation
  ON tenant_private.bid_questions
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

CREATE TABLE IF NOT EXISTS tenant_private.bid_risks (
  risk_id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  workspace_id uuid NOT NULL REFERENCES tenant_private.opportunity_workspaces(workspace_id) ON DELETE CASCADE,
  risk_ref text NOT NULL,
  description text NOT NULL,
  likelihood text NOT NULL CHECK (likelihood IN ('LOW', 'MEDIUM', 'HIGH')),
  impact text NOT NULL CHECK (impact IN ('LOW', 'MEDIUM', 'HIGH')),
  mitigation text NOT NULL DEFAULT '',
  status text NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'MITIGATED', 'ACCEPTED', 'CLOSED')),
  registered_by text NOT NULL,
  registered_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, workspace_id, risk_ref)
);

ALTER TABLE tenant_private.bid_risks ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.bid_risks FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS bid_risks_tenant_isolation
  ON tenant_private.bid_risks;
CREATE POLICY bid_risks_tenant_isolation
  ON tenant_private.bid_risks
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

CREATE TABLE IF NOT EXISTS tenant_private.bid_tasks (
  task_id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  workspace_id uuid NOT NULL REFERENCES tenant_private.opportunity_workspaces(workspace_id) ON DELETE CASCADE,
  task_ref text NOT NULL,
  requirement_id uuid REFERENCES tenant_private.bid_requirements(requirement_id),
  title text NOT NULL,
  owner text NOT NULL,
  due_at timestamptz,
  status text NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'IN_PROGRESS', 'DONE', 'BLOCKED', 'CANCELLED')),
  created_by text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, workspace_id, task_ref)
);

ALTER TABLE tenant_private.bid_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.bid_tasks FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS bid_tasks_tenant_isolation
  ON tenant_private.bid_tasks;
CREATE POLICY bid_tasks_tenant_isolation
  ON tenant_private.bid_tasks
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

CREATE TABLE IF NOT EXISTS tenant_private.bid_readiness (
  readiness_id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  workspace_id uuid NOT NULL REFERENCES tenant_private.opportunity_workspaces(workspace_id) ON DELETE CASCADE,
  requirement_id uuid NOT NULL REFERENCES tenant_private.bid_requirements(requirement_id) ON DELETE CASCADE,
  satisfied boolean NOT NULL DEFAULT false,
  evidence_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
  notes text NOT NULL DEFAULT '',
  updated_by text NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, workspace_id, requirement_id)
);

ALTER TABLE tenant_private.bid_readiness ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.bid_readiness FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS bid_readiness_tenant_isolation
  ON tenant_private.bid_readiness;
CREATE POLICY bid_readiness_tenant_isolation
  ON tenant_private.bid_readiness
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

-- ===========================================================================
-- 3. Append-only audit, approvals, handoffs
-- ===========================================================================

CREATE TABLE IF NOT EXISTS tenant_private.bid_workspace_audit (
  audit_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  workspace_id uuid NOT NULL,
  action text NOT NULL,
  actor text NOT NULL,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  occurred_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE tenant_private.bid_workspace_audit ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.bid_workspace_audit FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS bid_workspace_audit_tenant_isolation
  ON tenant_private.bid_workspace_audit;
CREATE POLICY bid_workspace_audit_tenant_isolation
  ON tenant_private.bid_workspace_audit
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

-- Append-only: no role may UPDATE or DELETE audit rows.
REVOKE UPDATE, DELETE ON tenant_private.bid_workspace_audit FROM axignal_app, axignal_worker;

CREATE TABLE IF NOT EXISTS tenant_private.bid_approvals (
  approval_id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  workspace_id uuid NOT NULL REFERENCES tenant_private.opportunity_workspaces(workspace_id) ON DELETE CASCADE,
  approval_ref text NOT NULL,
  decision text NOT NULL CHECK (decision IN ('APPROVED', 'REJECTED')),
  approved_by text NOT NULL,
  approved_at timestamptz NOT NULL DEFAULT now(),
  notes text NOT NULL DEFAULT '',
  UNIQUE (tenant_id, workspace_id, approval_ref)
);

ALTER TABLE tenant_private.bid_approvals ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.bid_approvals FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS bid_approvals_tenant_isolation
  ON tenant_private.bid_approvals;
CREATE POLICY bid_approvals_tenant_isolation
  ON tenant_private.bid_approvals
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

REVOKE UPDATE, DELETE ON tenant_private.bid_approvals FROM axignal_app, axignal_worker;

CREATE TABLE IF NOT EXISTS tenant_private.bid_handoffs (
  handoff_id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  workspace_id uuid NOT NULL REFERENCES tenant_private.opportunity_workspaces(workspace_id) ON DELETE CASCADE,
  handoff_ref text NOT NULL,
  target text NOT NULL,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  handed_off_by text NOT NULL,
  handed_off_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, workspace_id, handoff_ref)
);

ALTER TABLE tenant_private.bid_handoffs ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.bid_handoffs FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS bid_handoffs_tenant_isolation
  ON tenant_private.bid_handoffs;
CREATE POLICY bid_handoffs_tenant_isolation
  ON tenant_private.bid_handoffs
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

REVOKE UPDATE, DELETE ON tenant_private.bid_handoffs FROM axignal_app, axignal_worker;

-- Audit triggers: REQUIREMENTS, QUESTIONS, RISKS, TASKS, READINESS, APPROVALS.
-- One function per table: plpgsql resolves record fields statically, so the
-- shared generic function cannot reference fields absent from the table.

CREATE OR REPLACE FUNCTION tenant_private.bid_audit_req() RETURNS trigger AS $$
BEGIN
  INSERT INTO tenant_private.bid_workspace_audit (
    tenant_id, workspace_id, action, actor, payload
  ) VALUES (
    COALESCE(NEW.tenant_id, OLD.tenant_id),
    COALESCE(NEW.workspace_id, OLD.workspace_id),
    'bid_requirements.' || TG_OP,
    COALESCE(NEW.created_by, OLD.created_by, 'system'),
    jsonb_build_object('table', 'bid_requirements',
                       'id', COALESCE(NEW.requirement_id, OLD.requirement_id)::text)
  );
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION tenant_private.bid_audit_questions() RETURNS trigger AS $$
BEGIN
  INSERT INTO tenant_private.bid_workspace_audit (
    tenant_id, workspace_id, action, actor, payload
  ) VALUES (
    COALESCE(NEW.tenant_id, OLD.tenant_id),
    COALESCE(NEW.workspace_id, OLD.workspace_id),
    'bid_questions.' || TG_OP,
    COALESCE(NEW.asked_by, OLD.asked_by, 'system'),
    jsonb_build_object('table', 'bid_questions',
                       'id', COALESCE(NEW.question_id, OLD.question_id)::text)
  );
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION tenant_private.bid_audit_risks() RETURNS trigger AS $$
BEGIN
  INSERT INTO tenant_private.bid_workspace_audit (
    tenant_id, workspace_id, action, actor, payload
  ) VALUES (
    COALESCE(NEW.tenant_id, OLD.tenant_id),
    COALESCE(NEW.workspace_id, OLD.workspace_id),
    'bid_risks.' || TG_OP,
    COALESCE(NEW.registered_by, OLD.registered_by, 'system'),
    jsonb_build_object('table', 'bid_risks',
                       'id', COALESCE(NEW.risk_id, OLD.risk_id)::text)
  );
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION tenant_private.bid_audit_tasks() RETURNS trigger AS $$
BEGIN
  INSERT INTO tenant_private.bid_workspace_audit (
    tenant_id, workspace_id, action, actor, payload
  ) VALUES (
    COALESCE(NEW.tenant_id, OLD.tenant_id),
    COALESCE(NEW.workspace_id, OLD.workspace_id),
    'bid_tasks.' || TG_OP,
    COALESCE(NEW.created_by, OLD.created_by, 'system'),
    jsonb_build_object('table', 'bid_tasks',
                       'id', COALESCE(NEW.task_id, OLD.task_id)::text)
  );
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION tenant_private.bid_audit_readiness() RETURNS trigger AS $$
BEGIN
  INSERT INTO tenant_private.bid_workspace_audit (
    tenant_id, workspace_id, action, actor, payload
  ) VALUES (
    COALESCE(NEW.tenant_id, OLD.tenant_id),
    COALESCE(NEW.workspace_id, OLD.workspace_id),
    'bid_readiness.' || TG_OP,
    COALESCE(NEW.updated_by, OLD.updated_by, 'system'),
    jsonb_build_object('table', 'bid_readiness',
                       'id', COALESCE(NEW.readiness_id, OLD.readiness_id)::text)
  );
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION tenant_private.bid_audit_approvals() RETURNS trigger AS $$
BEGIN
  INSERT INTO tenant_private.bid_workspace_audit (
    tenant_id, workspace_id, action, actor, payload
  ) VALUES (
    COALESCE(NEW.tenant_id, OLD.tenant_id),
    COALESCE(NEW.workspace_id, OLD.workspace_id),
    'bid_approvals.' || TG_OP,
    COALESCE(NEW.approved_by, OLD.approved_by, 'system'),
    jsonb_build_object('table', 'bid_approvals',
                       'id', COALESCE(NEW.approval_id, OLD.approval_id)::text)
  );
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION tenant_private.bid_audit_handoffs() RETURNS trigger AS $$
BEGIN
  INSERT INTO tenant_private.bid_workspace_audit (
    tenant_id, workspace_id, action, actor, payload
  ) VALUES (
    COALESCE(NEW.tenant_id, OLD.tenant_id),
    COALESCE(NEW.workspace_id, OLD.workspace_id),
    'bid_handoffs.' || TG_OP,
    COALESCE(NEW.handed_off_by, OLD.handed_off_by, 'system'),
    jsonb_build_object('table', 'bid_handoffs',
                       'id', COALESCE(NEW.handoff_id, OLD.handoff_id)::text)
  );
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION tenant_private.bid_audit_req_versions() RETURNS trigger AS $$
BEGIN
  INSERT INTO tenant_private.bid_workspace_audit (
    tenant_id, workspace_id, action, actor, payload
  ) VALUES (
    COALESCE(NEW.tenant_id, OLD.tenant_id),
    (SELECT workspace_id FROM tenant_private.bid_requirements
     WHERE requirement_id = COALESCE(NEW.requirement_id, OLD.requirement_id)),
    'bid_requirement_versions.' || TG_OP,
    COALESCE(NEW.changed_by, OLD.changed_by, 'system'),
    jsonb_build_object('table', 'bid_requirement_versions',
                       'id', COALESCE(NEW.version_id, OLD.version_id)::text)
  );
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS bid_requirements_audit ON tenant_private.bid_requirements;
CREATE TRIGGER bid_requirements_audit
  AFTER INSERT OR UPDATE OR DELETE ON tenant_private.bid_requirements
  FOR EACH ROW EXECUTE FUNCTION tenant_private.bid_audit_req();

DROP TRIGGER IF EXISTS bid_questions_audit ON tenant_private.bid_questions;
CREATE TRIGGER bid_questions_audit
  AFTER INSERT OR UPDATE OR DELETE ON tenant_private.bid_questions
  FOR EACH ROW EXECUTE FUNCTION tenant_private.bid_audit_questions();

DROP TRIGGER IF EXISTS bid_risks_audit ON tenant_private.bid_risks;
CREATE TRIGGER bid_risks_audit
  AFTER INSERT OR UPDATE OR DELETE ON tenant_private.bid_risks
  FOR EACH ROW EXECUTE FUNCTION tenant_private.bid_audit_risks();

DROP TRIGGER IF EXISTS bid_tasks_audit ON tenant_private.bid_tasks;
CREATE TRIGGER bid_tasks_audit
  AFTER INSERT OR UPDATE OR DELETE ON tenant_private.bid_tasks
  FOR EACH ROW EXECUTE FUNCTION tenant_private.bid_audit_tasks();

DROP TRIGGER IF EXISTS bid_readiness_audit ON tenant_private.bid_readiness;
CREATE TRIGGER bid_readiness_audit
  AFTER INSERT OR UPDATE OR DELETE ON tenant_private.bid_readiness
  FOR EACH ROW EXECUTE FUNCTION tenant_private.bid_audit_readiness();

DROP TRIGGER IF EXISTS bid_approvals_audit ON tenant_private.bid_approvals;
CREATE TRIGGER bid_approvals_audit
  AFTER INSERT OR UPDATE OR DELETE ON tenant_private.bid_approvals
  FOR EACH ROW EXECUTE FUNCTION tenant_private.bid_audit_approvals();

DROP TRIGGER IF EXISTS bid_handoffs_audit ON tenant_private.bid_handoffs;
CREATE TRIGGER bid_handoffs_audit
  AFTER INSERT OR UPDATE OR DELETE ON tenant_private.bid_handoffs
  FOR EACH ROW EXECUTE FUNCTION tenant_private.bid_audit_handoffs();

DROP TRIGGER IF EXISTS bid_requirement_versions_audit ON tenant_private.bid_requirement_versions;
CREATE TRIGGER bid_requirement_versions_audit
  AFTER INSERT OR UPDATE OR DELETE ON tenant_private.bid_requirement_versions
  FOR EACH ROW EXECUTE FUNCTION tenant_private.bid_audit_req_versions();

GRANT SELECT, INSERT, UPDATE, DELETE ON
  tenant_private.bid_requirements,
  tenant_private.bid_requirement_versions,
  tenant_private.bid_questions,
  tenant_private.bid_risks,
  tenant_private.bid_tasks,
  tenant_private.bid_readiness
  TO axignal_worker;
GRANT SELECT, INSERT ON
  tenant_private.bid_workspace_audit,
  tenant_private.bid_approvals,
  tenant_private.bid_handoffs
  TO axignal_worker;
GRANT SELECT ON
  tenant_private.bid_requirements,
  tenant_private.bid_requirement_versions,
  tenant_private.bid_questions,
  tenant_private.bid_risks,
  tenant_private.bid_tasks,
  tenant_private.bid_readiness,
  tenant_private.bid_workspace_audit,
  tenant_private.bid_approvals,
  tenant_private.bid_handoffs
  TO axignal_app;
