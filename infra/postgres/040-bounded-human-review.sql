DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'axignal_human_reviewer') THEN
    CREATE ROLE axignal_human_reviewer NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'axignal_human_reviewer_login') THEN
    CREATE ROLE axignal_human_reviewer_login LOGIN PASSWORD 'axignal_human_reviewer';
  ELSE
    ALTER ROLE axignal_human_reviewer_login LOGIN PASSWORD 'axignal_human_reviewer';
  END IF;
END
$$;

GRANT axignal_human_reviewer TO axignal_human_reviewer_login;
GRANT USAGE ON SCHEMA tenant_private TO axignal_human_reviewer;

ALTER TABLE tenant_private.dossiers
  ADD COLUMN IF NOT EXISTS human_review_context jsonb NOT NULL DEFAULT '[]'::jsonb;

CREATE TABLE IF NOT EXISTS tenant_private.human_review_cases (
  human_review_case_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  research_run_id uuid NOT NULL
    REFERENCES tenant_private.research_runs(research_run_id) ON DELETE CASCADE,
  admission_handoff_id uuid NOT NULL
    REFERENCES axignal_global.admission_handoffs(admission_handoff_id),
  admission_decision_id uuid NOT NULL UNIQUE
    REFERENCES axignal_global.admission_decisions(admission_decision_id),
  candidate_claim_id uuid NOT NULL
    REFERENCES axignal_global.candidate_claims(candidate_claim_id),
  case_type text NOT NULL CHECK (
    case_type IN ('HUMAN_REVIEW_REQUIRED', 'CONTESTED')
  ),
  state text NOT NULL DEFAULT 'OPEN' CHECK (
    state IN (
      'OPEN',
      'IN_REVIEW',
      'MORE_EVIDENCE_REQUIRED',
      'RESOLVED',
      'CANCELLED'
    )
  ),
  priority text NOT NULL DEFAULT 'NORMAL' CHECK (
    priority IN ('LOW', 'NORMAL', 'HIGH')
  ),
  assigned_reviewer_subject text,
  assigned_reviewer_email text,
  opened_reason text NOT NULL,
  resolution text CHECK (
    resolution IS NULL OR resolution IN (
      'ACCEPT_AS_CONTEXT',
      'REJECT_PROPOSAL',
      'CONFIRM_CONTESTED',
      'RETURN_TO_DETERMINISTIC_REVIEW',
      'MARK_OUT_OF_SCOPE'
    )
  ),
  resolution_reason_code text,
  resolution_note text,
  created_at timestamptz NOT NULL DEFAULT now(),
  assigned_at timestamptz,
  resolved_at timestamptz,
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS human_review_cases_tenant_run_idx
  ON tenant_private.human_review_cases (tenant_id, research_run_id, created_at);

CREATE TABLE IF NOT EXISTS tenant_private.human_review_events (
  human_review_event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  human_review_case_id uuid NOT NULL
    REFERENCES tenant_private.human_review_cases(human_review_case_id),
  tenant_id uuid NOT NULL,
  event_type text NOT NULL CHECK (
    event_type IN (
      'CASE_OPENED',
      'CASE_ASSIGNED',
      'REVIEW_STARTED',
      'EVIDENCE_REQUESTED',
      'RESOLUTION_RECORDED',
      'CASE_CLOSED'
    )
  ),
  actor_subject text,
  actor_email text,
  reason_code text,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  occurred_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS human_review_events_case_idx
  ON tenant_private.human_review_events (
    human_review_case_id,
    occurred_at,
    human_review_event_id
  );

ALTER TABLE tenant_private.human_review_cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.human_review_cases FORCE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.human_review_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.human_review_events FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS human_review_cases_tenant_isolation
  ON tenant_private.human_review_cases;
CREATE POLICY human_review_cases_tenant_isolation
  ON tenant_private.human_review_cases
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

DROP POLICY IF EXISTS human_review_events_tenant_isolation
  ON tenant_private.human_review_events;
CREATE POLICY human_review_events_tenant_isolation
  ON tenant_private.human_review_events
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

CREATE OR REPLACE FUNCTION tenant_private.reject_human_review_event_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE EXCEPTION 'AXIGNAL_HUMAN_REVIEW_EVENTS_APPEND_ONLY';
END
$$;

DROP TRIGGER IF EXISTS human_review_events_immutable
  ON tenant_private.human_review_events;
CREATE TRIGGER human_review_events_immutable
BEFORE UPDATE OR DELETE ON tenant_private.human_review_events
FOR EACH ROW EXECUTE FUNCTION tenant_private.reject_human_review_event_mutation();

CREATE OR REPLACE FUNCTION tenant_private.open_human_review_case()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, axignal_global, tenant_private
AS $$
DECLARE
  handoff axignal_global.admission_handoffs%ROWTYPE;
  case_id uuid;
BEGIN
  IF NEW.outcome NOT IN ('HUMAN_REVIEW_REQUIRED', 'CONTESTED') THEN
    RETURN NEW;
  END IF;

  SELECT * INTO handoff
  FROM axignal_global.admission_handoffs
  WHERE admission_handoff_id = NEW.admission_handoff_id;

  IF handoff.admission_handoff_id IS NULL THEN
    RAISE EXCEPTION 'HUMAN_REVIEW_HANDOFF_NOT_FOUND';
  END IF;

  INSERT INTO tenant_private.human_review_cases (
    tenant_id,
    research_run_id,
    admission_handoff_id,
    admission_decision_id,
    candidate_claim_id,
    case_type,
    priority,
    opened_reason
  ) VALUES (
    handoff.tenant_id,
    handoff.research_run_id,
    handoff.admission_handoff_id,
    NEW.admission_decision_id,
    NEW.candidate_claim_id,
    NEW.outcome,
    CASE WHEN NEW.outcome = 'CONTESTED' THEN 'HIGH' ELSE 'NORMAL' END,
    COALESCE(NEW.rejection_reasons->>0, lower(NEW.outcome))
  )
  ON CONFLICT (admission_decision_id) DO NOTHING
  RETURNING human_review_case_id INTO case_id;

  IF case_id IS NOT NULL THEN
    INSERT INTO tenant_private.human_review_events (
      human_review_case_id,
      tenant_id,
      event_type,
      reason_code,
      payload
    ) VALUES (
      case_id,
      handoff.tenant_id,
      'CASE_OPENED',
      COALESCE(NEW.rejection_reasons->>0, lower(NEW.outcome)),
      jsonb_build_object(
        'admission_decision_id', NEW.admission_decision_id,
        'candidate_claim_id', NEW.candidate_claim_id,
        'deterministic_outcome', NEW.outcome,
        'policy_version', NEW.policy_version
      )
    );
  END IF;

  RETURN NEW;
END
$$;

DROP TRIGGER IF EXISTS admission_decision_opens_human_review
  ON axignal_global.admission_decisions;
CREATE TRIGGER admission_decision_opens_human_review
AFTER INSERT ON axignal_global.admission_decisions
FOR EACH ROW EXECUTE FUNCTION tenant_private.open_human_review_case();

INSERT INTO tenant_private.human_review_cases (
  tenant_id,
  research_run_id,
  admission_handoff_id,
  admission_decision_id,
  candidate_claim_id,
  case_type,
  priority,
  opened_reason
)
SELECT
  handoff.tenant_id,
  handoff.research_run_id,
  handoff.admission_handoff_id,
  decision.admission_decision_id,
  decision.candidate_claim_id,
  decision.outcome,
  CASE WHEN decision.outcome = 'CONTESTED' THEN 'HIGH' ELSE 'NORMAL' END,
  COALESCE(decision.rejection_reasons->>0, lower(decision.outcome))
FROM axignal_global.admission_decisions AS decision
JOIN axignal_global.admission_handoffs AS handoff
  USING (admission_handoff_id)
WHERE decision.outcome IN ('HUMAN_REVIEW_REQUIRED', 'CONTESTED')
ON CONFLICT (admission_decision_id) DO NOTHING;

INSERT INTO tenant_private.human_review_events (
  human_review_case_id,
  tenant_id,
  event_type,
  reason_code,
  payload
)
SELECT
  review_case.human_review_case_id,
  review_case.tenant_id,
  'CASE_OPENED',
  review_case.opened_reason,
  jsonb_build_object(
    'admission_decision_id', review_case.admission_decision_id,
    'candidate_claim_id', review_case.candidate_claim_id,
    'backfilled', true
  )
FROM tenant_private.human_review_cases AS review_case
WHERE NOT EXISTS (
  SELECT 1
  FROM tenant_private.human_review_events AS event
  WHERE event.human_review_case_id = review_case.human_review_case_id
    AND event.event_type = 'CASE_OPENED'
);

