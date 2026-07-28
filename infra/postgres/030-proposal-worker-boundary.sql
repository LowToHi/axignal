DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'axignal_proposal_worker') THEN
    CREATE ROLE axignal_proposal_worker LOGIN PASSWORD 'axignal_proposal_worker';
  ELSE
    ALTER ROLE axignal_proposal_worker LOGIN PASSWORD 'axignal_proposal_worker';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'axignal_admission_runtime') THEN
    CREATE ROLE axignal_admission_runtime NOLOGIN;
  END IF;
END
$$;

GRANT axignal_admission_runtime TO axignal;
GRANT USAGE ON SCHEMA axignal_global, tenant_private TO
  axignal_proposal_worker,
  axignal_admission_runtime;

INSERT INTO axignal_global.sources (
  source_id,
  name,
  source_type,
  base_url,
  access_mode,
  rights_status,
  license_id,
  attribution_text,
  terms_url,
  dataset_url,
  commercial_use,
  redistribution,
  admission_state,
  kill_switch,
  config,
  last_reviewed_at
) VALUES (
  'world-bank-rer41',
  'World Bank Russia Economic Report 41',
  'INSTITUTIONAL_WEB',
  'https://documents.worldbank.org',
  'PUBLIC_NO_AUTH',
  'COMMERCIAL_REUSE_WITH_ATTRIBUTION',
  'CC-BY-4.0',
  'Adapted from World Bank, Russia Economic Report 41; lineage preserved by AXIGNAL.',
  'https://www.worldbank.org/en/about/legal/terms-and-conditions',
  'https://documents.worldbank.org/en/publication/documents-reports/documentdetail/332081560895493011',
  true,
  true,
  'ADMITTED',
  false,
  jsonb_build_object(
    'document_id', 'doc_world_bank_rer41',
    'allowed_hosts', jsonb_build_array('documents.worldbank.org'),
    'max_documents', 1,
    'max_model_calls', 1,
    'fixture_only', true
  ),
  '2026-07-27T00:00:00Z'
)
ON CONFLICT (source_id) DO UPDATE SET
  rights_status = EXCLUDED.rights_status,
  license_id = EXCLUDED.license_id,
  attribution_text = EXCLUDED.attribution_text,
  terms_url = EXCLUDED.terms_url,
  dataset_url = EXCLUDED.dataset_url,
  commercial_use = EXCLUDED.commercial_use,
  redistribution = EXCLUDED.redistribution,
  admission_state = EXCLUDED.admission_state,
  kill_switch = EXCLUDED.kill_switch,
  config = EXCLUDED.config,
  last_reviewed_at = EXCLUDED.last_reviewed_at,
  updated_at = now();

ALTER TABLE tenant_private.research_runs
  ADD COLUMN IF NOT EXISTS job_kind text NOT NULL DEFAULT 'STRUCTURED_SOURCE_OBSERVATION';
ALTER TABLE tenant_private.research_runs
  ADD COLUMN IF NOT EXISTS document_id text;
ALTER TABLE tenant_private.research_runs
  ADD COLUMN IF NOT EXISTS admission_handoff_id uuid;

ALTER TABLE tenant_private.research_runs
  DROP CONSTRAINT IF EXISTS research_runs_job_kind_check;
ALTER TABLE tenant_private.research_runs
  ADD CONSTRAINT research_runs_job_kind_check CHECK (
    job_kind IN ('STRUCTURED_SOURCE_OBSERVATION', 'DOCUMENT_PROPOSAL')
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
      'COMPLETED',
      'COMPLETED_PROVISIONAL',
      'QUARANTINED',
      'FAILED'
    )
  );

ALTER TABLE axignal_global.candidate_claims
  DROP CONSTRAINT IF EXISTS candidate_claims_kind_check;
ALTER TABLE axignal_global.candidate_claims
  ADD CONSTRAINT candidate_claims_kind_check CHECK (
    kind IN (
      'FACT',
      'INFERENCE',
      'PREDICTION',
      'FORECAST',
      'LIMITATION',
      'CONTRADICTION'
    )
  );
ALTER TABLE axignal_global.candidate_claims
  ADD COLUMN IF NOT EXISTS relationship text;
ALTER TABLE axignal_global.candidate_claims
  ADD COLUMN IF NOT EXISTS model_version text;
ALTER TABLE axignal_global.candidate_claims
  ADD COLUMN IF NOT EXISTS prompt_version text;
ALTER TABLE axignal_global.candidate_claims
  ADD COLUMN IF NOT EXISTS extraction_confidence numeric;
ALTER TABLE axignal_global.candidate_claims
  ADD COLUMN IF NOT EXISTS assumptions jsonb NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE axignal_global.candidate_claims
  ADD COLUMN IF NOT EXISTS unknowns jsonb NOT NULL DEFAULT '[]'::jsonb;

CREATE TABLE IF NOT EXISTS axignal_global.document_fragments (
  fragment_id text PRIMARY KEY,
  source_object_id uuid NOT NULL REFERENCES axignal_global.source_objects(source_object_id),
  document_id text NOT NULL,
  ordinal integer NOT NULL CHECK (ordinal >= 0),
  start_char integer NOT NULL CHECK (start_char >= 0),
  end_char integer NOT NULL CHECK (end_char > start_char),
  text_content text NOT NULL,
  content_hash text NOT NULL CHECK (content_hash ~ '^sha256:[0-9a-f]{64}$'),
  parser_version text NOT NULL,
  security_scan_state text NOT NULL CHECK (security_scan_state IN ('CLEAR', 'QUARANTINED')),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (document_id, ordinal),
  UNIQUE (document_id, content_hash)
);

CREATE TABLE IF NOT EXISTS axignal_global.admission_handoffs (
  admission_handoff_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  research_run_id uuid NOT NULL REFERENCES tenant_private.research_runs(research_run_id) ON DELETE CASCADE,
  state text NOT NULL DEFAULT 'PENDING' CHECK (state IN ('PENDING', 'CONSUMED', 'REJECTED', 'QUARANTINED')),
  candidate_claim_ids uuid[] NOT NULL CHECK (cardinality(candidate_claim_ids) > 0),
  package jsonb NOT NULL,
  package_hash text NOT NULL UNIQUE CHECK (package_hash ~ '^sha256:[0-9a-f]{64}$'),
  created_at timestamptz NOT NULL DEFAULT now(),
  consumed_at timestamptz
);

ALTER TABLE tenant_private.research_runs
  DROP CONSTRAINT IF EXISTS research_runs_admission_handoff_id_fkey;
ALTER TABLE tenant_private.research_runs
  ADD CONSTRAINT research_runs_admission_handoff_id_fkey
  FOREIGN KEY (admission_handoff_id)
  REFERENCES axignal_global.admission_handoffs(admission_handoff_id);

CREATE TABLE IF NOT EXISTS axignal_global.proposal_outbox_events (
  proposal_outbox_event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  aggregate_id uuid NOT NULL,
  event_type text NOT NULL CHECK (
    event_type IN ('research.document_proposal.requested', 'research.document_proposal.completed')
  ),
  payload jsonb NOT NULL,
  status text NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'PUBLISHED', 'FAILED')),
  attempts integer NOT NULL DEFAULT 0 CHECK (attempts >= 0),
  available_at timestamptz NOT NULL DEFAULT now(),
  published_at timestamptz,
  last_error text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS proposal_outbox_pending_idx
  ON axignal_global.proposal_outbox_events (available_at, created_at)
  WHERE status = 'PENDING';

CREATE TABLE IF NOT EXISTS axignal_global.proposal_job_failures (
  proposal_job_failure_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  research_run_id uuid NOT NULL,
  job_payload jsonb NOT NULL,
  error_code text NOT NULL,
  error_detail text NOT NULL,
  quarantined boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS dossiers_one_per_research_run_idx
  ON tenant_private.dossiers (research_run_id);
CREATE INDEX IF NOT EXISTS document_fragments_document_idx
  ON axignal_global.document_fragments (document_id, ordinal);
CREATE INDEX IF NOT EXISTS admission_handoffs_state_idx
  ON axignal_global.admission_handoffs (state, created_at);

GRANT SELECT, INSERT, UPDATE ON axignal_global.proposal_outbox_events TO axignal_app;

GRANT SELECT ON axignal_global.sources TO axignal_proposal_worker;
GRANT SELECT, INSERT ON
  axignal_global.source_objects,
  axignal_global.document_fragments,
  axignal_global.evidence_objects,
  axignal_global.candidate_claims,
  axignal_global.admission_handoffs,
  axignal_global.proposal_job_failures,
  axignal_global.outbox_events
TO axignal_proposal_worker;
GRANT SELECT ON axignal_global.proposal_outbox_events TO axignal_proposal_worker;
GRANT SELECT, UPDATE (
  state,
  actual_usage,
  evidence_ids,
  candidate_claim_ids,
  canonical_claim_ids,
  dossier_id,
  admission_handoff_id,
  error_code,
  error_detail,
  updated_at
) ON tenant_private.research_runs TO axignal_proposal_worker;
GRANT SELECT, INSERT ON
  tenant_private.dossiers,
  tenant_private.research_evidence_links
TO axignal_proposal_worker;

REVOKE ALL PRIVILEGES ON axignal_global.canonical_claims FROM axignal_proposal_worker;
REVOKE ALL PRIVILEGES ON axignal_global.claim_state_events FROM axignal_proposal_worker;
REVOKE ALL PRIVILEGES ON axignal_global.admission_batches FROM axignal_proposal_worker;

GRANT SELECT ON
  axignal_global.sources,
  axignal_global.source_objects,
  axignal_global.document_fragments,
  axignal_global.evidence_objects,
  axignal_global.candidate_claims,
  axignal_global.admission_handoffs
TO axignal_admission_runtime;
GRANT INSERT ON
  axignal_global.admission_batches,
  axignal_global.canonical_claims,
  axignal_global.claim_state_events
TO axignal_admission_runtime;
GRANT UPDATE (state, canonical_claim_id, rejection_reasons, updated_at)
  ON axignal_global.candidate_claims TO axignal_admission_runtime;
GRANT UPDATE (state, consumed_at)
  ON axignal_global.admission_handoffs TO axignal_admission_runtime;
