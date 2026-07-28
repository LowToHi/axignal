DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_roles WHERE rolname = 'axignal_admission_runtime_login'
  ) THEN
    CREATE ROLE axignal_admission_runtime_login
      LOGIN PASSWORD 'axignal_admission_runtime';
  ELSE
    ALTER ROLE axignal_admission_runtime_login
      LOGIN PASSWORD 'axignal_admission_runtime';
  END IF;
END
$$;

GRANT axignal_admission_runtime TO axignal_admission_runtime_login;

ALTER TABLE axignal_global.candidate_claims
  DROP CONSTRAINT IF EXISTS candidate_claims_state_check;
ALTER TABLE axignal_global.candidate_claims
  ADD CONSTRAINT candidate_claims_state_check CHECK (
    state IN (
      'PROPOSED',
      'ADMISSION_QUEUED',
      'ADMITTED',
      'REJECTED',
      'CONTESTED',
      'HUMAN_REVIEW_REQUIRED'
    )
  );

ALTER TABLE axignal_global.admission_handoffs
  DROP CONSTRAINT IF EXISTS admission_handoffs_state_check;
ALTER TABLE axignal_global.admission_handoffs
  ADD CONSTRAINT admission_handoffs_state_check CHECK (
    state IN (
      'PENDING',
      'CONSUMED',
      'REJECTED',
      'QUARANTINED',
      'HUMAN_REVIEW_REQUIRED'
    )
  );

ALTER TABLE tenant_private.research_runs
  DROP CONSTRAINT IF EXISTS research_runs_state_check;
ALTER TABLE tenant_private.research_runs
  ADD CONSTRAINT research_runs_state_check CHECK (
    state IN (
      'QUEUED',
      'RETRIEVING',
      'DOCUMENT_PARSING',
      'SECURITY_SCANNING',
      'PROPOSING',
      'EVIDENCE_BINDING',
      'ADMISSION_PENDING',
      'HANDOFF_PENDING',
      'ADMISSION_REVIEWING',
      'COMPLETED',
      'COMPLETED_PROVISIONAL',
      'HUMAN_REVIEW_REQUIRED',
      'CONTESTED',
      'QUARANTINED',
      'FAILED'
    )
  );

CREATE TABLE IF NOT EXISTS axignal_global.admission_outbox_events (
  admission_outbox_event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  aggregate_id uuid NOT NULL,
  event_type text NOT NULL CHECK (
    event_type IN ('admission.handoff.requested', 'admission.handoff.decided')
  ),
  payload jsonb NOT NULL,
  status text NOT NULL DEFAULT 'PENDING' CHECK (
    status IN ('PENDING', 'PUBLISHED', 'FAILED')
  ),
  attempts integer NOT NULL DEFAULT 0 CHECK (attempts >= 0),
  available_at timestamptz NOT NULL DEFAULT now(),
  published_at timestamptz,
  last_error text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS admission_outbox_pending_idx
  ON axignal_global.admission_outbox_events (available_at, created_at)
  WHERE status = 'PENDING';

CREATE TABLE IF NOT EXISTS axignal_global.admission_decisions (
  admission_decision_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  admission_batch_id uuid NOT NULL
    REFERENCES axignal_global.admission_batches(admission_batch_id),
  admission_handoff_id uuid NOT NULL
    REFERENCES axignal_global.admission_handoffs(admission_handoff_id),
  candidate_claim_id uuid NOT NULL
    REFERENCES axignal_global.candidate_claims(candidate_claim_id),
  outcome text NOT NULL CHECK (
    outcome IN (
      'ADMITTED_REDERIVED',
      'REJECTED',
      'QUARANTINED',
      'CONTESTED',
      'HUMAN_REVIEW_REQUIRED',
      'DUPLICATE',
      'SUPERSEDED'
    )
  ),
  policy_version text NOT NULL,
  gate_results jsonb NOT NULL,
  rejection_reasons jsonb NOT NULL DEFAULT '[]'::jsonb,
  canonical_claim_id uuid
    REFERENCES axignal_global.canonical_claims(canonical_claim_id),
  rederived_fingerprint text CHECK (
    rederived_fingerprint IS NULL
    OR rederived_fingerprint ~ '^sha256:[0-9a-f]{64}$'
  ),
  human_review_required boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (admission_handoff_id, candidate_claim_id)
);

CREATE INDEX IF NOT EXISTS admission_decisions_handoff_idx
  ON axignal_global.admission_decisions (admission_handoff_id, created_at);

CREATE TABLE IF NOT EXISTS axignal_global.admission_job_failures (
  admission_job_failure_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  research_run_id uuid NOT NULL,
  admission_handoff_id uuid NOT NULL,
  job_payload jsonb NOT NULL,
  error_code text NOT NULL,
  error_detail text NOT NULL,
  quarantined boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION axignal_global.enqueue_admission_handoff()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, axignal_global
AS $$
BEGIN
  INSERT INTO axignal_global.admission_outbox_events (
    aggregate_id,
    event_type,
    payload
  ) VALUES (
    NEW.admission_handoff_id,
    'admission.handoff.requested',
    jsonb_build_object(
      'schema_version', 1,
      'job_kind', 'ADMISSION_REVIEW',
      'admission_handoff_id', NEW.admission_handoff_id::text,
      'research_run_id', NEW.research_run_id::text,
      'tenant_id', NEW.tenant_id::text,
      'expected_package_hash', NEW.package_hash,
      'policy_version', 'document-observed-fact@0.1.0'
    )
  );
  RETURN NEW;
END
$$;

DROP TRIGGER IF EXISTS admission_handoff_enqueue ON axignal_global.admission_handoffs;
CREATE TRIGGER admission_handoff_enqueue
AFTER INSERT ON axignal_global.admission_handoffs
FOR EACH ROW EXECUTE FUNCTION axignal_global.enqueue_admission_handoff();

GRANT SELECT, UPDATE ON axignal_global.admission_outbox_events TO axignal_app;

GRANT SELECT ON
  axignal_global.sources,
  axignal_global.source_objects,
  axignal_global.document_fragments,
  axignal_global.evidence_objects,
  axignal_global.candidate_claims,
  axignal_global.admission_handoffs,
  axignal_global.admission_batches,
  axignal_global.canonical_claims,
  axignal_global.claim_state_events,
  axignal_global.admission_decisions
TO axignal_admission_runtime;

GRANT INSERT ON
  axignal_global.admission_batches,
  axignal_global.canonical_claims,
  axignal_global.claim_state_events,
  axignal_global.admission_decisions,
  axignal_global.admission_job_failures
TO axignal_admission_runtime;

GRANT UPDATE (state, canonical_claim_id, rejection_reasons, updated_at)
  ON axignal_global.candidate_claims TO axignal_admission_runtime;
GRANT UPDATE (state, consumed_at)
  ON axignal_global.admission_handoffs TO axignal_admission_runtime;
GRANT UPDATE (state, decision_summary, decided_at)
  ON axignal_global.admission_batches TO axignal_admission_runtime;

GRANT SELECT ON tenant_private.research_runs, tenant_private.dossiers
  TO axignal_admission_runtime;
GRANT UPDATE (
  state,
  actual_usage,
  canonical_claim_ids,
  admission_batch_id,
  error_code,
  error_detail,
  updated_at
) ON tenant_private.research_runs TO axignal_admission_runtime;
GRANT UPDATE (status) ON tenant_private.dossiers TO axignal_admission_runtime;

REVOKE INSERT, UPDATE, DELETE ON
  axignal_global.sources,
  axignal_global.source_objects,
  axignal_global.document_fragments,
  axignal_global.evidence_objects
FROM axignal_admission_runtime;

REVOKE ALL PRIVILEGES ON axignal_global.proposal_outbox_events
  FROM axignal_admission_runtime;
