CREATE TABLE IF NOT EXISTS tenant_private.support_feedback (
  feedback_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  conversation_id uuid NOT NULL,
  message_id uuid,
  submitted_by_subject text NOT NULL,
  rating smallint NOT NULL CHECK (rating BETWEEN 1 AND 5),
  resolution_helpful boolean,
  comment_redacted text,
  created_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (tenant_id, conversation_id)
    REFERENCES tenant_private.support_conversations (tenant_id, conversation_id)
    ON DELETE RESTRICT,
  FOREIGN KEY (tenant_id, message_id)
    REFERENCES tenant_private.support_messages (tenant_id, message_id)
    ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS tenant_private.support_evaluations (
  evaluation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  conversation_id uuid NOT NULL,
  evaluator_type text NOT NULL CHECK (evaluator_type IN ('AUTOMATED','HUMAN')),
  evaluator_subject text,
  policy_version text NOT NULL,
  grounded boolean NOT NULL,
  citation_valid boolean NOT NULL,
  correct_resolution boolean,
  escalation_correct boolean,
  security_violation boolean NOT NULL DEFAULT false,
  score numeric(5,4) CHECK (score BETWEEN 0 AND 1),
  evidence_redacted jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (tenant_id, conversation_id)
    REFERENCES tenant_private.support_conversations (tenant_id, conversation_id)
    ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS tenant_private.support_incident_links (
  incident_link_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  case_id uuid NOT NULL,
  incident_id text NOT NULL,
  incident_authority text NOT NULL,
  linked_by_subject text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, case_id, incident_id),
  FOREIGN KEY (tenant_id, case_id)
    REFERENCES tenant_private.support_cases (tenant_id, case_id)
    ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS support_feedback_conversation_idx
  ON tenant_private.support_feedback (tenant_id, conversation_id, created_at);
CREATE INDEX IF NOT EXISTS support_evaluations_conversation_idx
  ON tenant_private.support_evaluations (tenant_id, conversation_id, created_at);
CREATE INDEX IF NOT EXISTS support_incident_links_case_idx
  ON tenant_private.support_incident_links (tenant_id, case_id, created_at);

ALTER TABLE tenant_private.support_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.support_feedback FORCE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.support_evaluations ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.support_evaluations FORCE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.support_incident_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.support_incident_links FORCE ROW LEVEL SECURITY;

CREATE POLICY support_feedback_tenant_policy
  ON tenant_private.support_feedback
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());
CREATE POLICY support_evaluations_tenant_policy
  ON tenant_private.support_evaluations
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());
CREATE POLICY support_incident_links_tenant_policy
  ON tenant_private.support_incident_links
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

CREATE OR REPLACE FUNCTION tenant_private.reject_axent_evidence_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'AXENT evaluation evidence is append-only';
END $$;

CREATE TRIGGER support_feedback_immutable
BEFORE UPDATE OR DELETE ON tenant_private.support_feedback
FOR EACH ROW EXECUTE FUNCTION tenant_private.reject_axent_evidence_mutation();
CREATE TRIGGER support_evaluations_immutable
BEFORE UPDATE OR DELETE ON tenant_private.support_evaluations
FOR EACH ROW EXECUTE FUNCTION tenant_private.reject_axent_evidence_mutation();
CREATE TRIGGER support_incident_links_immutable
BEFORE UPDATE OR DELETE ON tenant_private.support_incident_links
FOR EACH ROW EXECUTE FUNCTION tenant_private.reject_axent_evidence_mutation();

CREATE OR REPLACE VIEW tenant_private.axent_support_metrics
WITH (security_invoker = true) AS
SELECT
  tenant_id,
  count(DISTINCT conversation_id) AS conversations_total,
  count(DISTINCT conversation_id) FILTER (
    WHERE status IN ('RESOLVED','CLOSED')
  ) AS conversations_resolved,
  count(DISTINCT conversation_id) FILTER (
    WHERE status = 'ESCALATED'
  ) AS conversations_escalated,
  percentile_cont(0.5) WITHIN GROUP (
    ORDER BY EXTRACT(EPOCH FROM (resolved_at - created_at))
  ) FILTER (WHERE resolved_at IS NOT NULL) AS median_resolution_seconds
FROM tenant_private.support_conversations
GROUP BY tenant_id;

GRANT SELECT, INSERT ON tenant_private.support_feedback TO axignal_app;
GRANT SELECT, INSERT ON tenant_private.support_evaluations TO axignal_app;
GRANT SELECT, INSERT ON tenant_private.support_incident_links TO axignal_app;
GRANT SELECT ON tenant_private.axent_support_metrics TO axignal_app;
REVOKE UPDATE, DELETE ON tenant_private.support_feedback,
  tenant_private.support_evaluations,
  tenant_private.support_incident_links FROM axignal_app;
