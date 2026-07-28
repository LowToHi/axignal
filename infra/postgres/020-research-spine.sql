CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS axignal_global;
CREATE SCHEMA IF NOT EXISTS tenant_private;
CREATE SCHEMA IF NOT EXISTS intent_intelligence;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'axignal_app') THEN
    CREATE ROLE axignal_app NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'axignal_worker') THEN
    CREATE ROLE axignal_worker NOLOGIN;
  END IF;
END
$$;

GRANT axignal_app, axignal_worker TO axignal;
GRANT USAGE ON SCHEMA axignal_global, tenant_private, intent_intelligence TO axignal_app, axignal_worker;

CREATE OR REPLACE FUNCTION tenant_private.current_tenant_id()
RETURNS uuid
LANGUAGE sql
STABLE
AS $$
  SELECT NULLIF(current_setting('app.tenant_id', true), '')::uuid
$$;

CREATE TABLE IF NOT EXISTS axignal_global.sources (
  source_id text PRIMARY KEY,
  name text NOT NULL,
  source_type text NOT NULL CHECK (source_type IN ('INSTITUTIONAL_API', 'INSTITUTIONAL_WEB', 'COMMERCIAL_API')),
  base_url text NOT NULL,
  access_mode text NOT NULL CHECK (access_mode IN ('PUBLIC_NO_AUTH', 'PUBLIC_WITH_KEY', 'CONTRACTUAL')),
  rights_status text NOT NULL CHECK (rights_status IN ('COMMERCIAL_REUSE_WITH_ATTRIBUTION', 'INTERNAL_EVALUATION_ONLY', 'RIGHTS_PENDING', 'REJECTED')),
  license_id text,
  attribution_text text,
  terms_url text NOT NULL,
  dataset_url text,
  commercial_use boolean NOT NULL DEFAULT false,
  redistribution boolean NOT NULL DEFAULT false,
  admission_state text NOT NULL CHECK (admission_state IN ('ADMITTED', 'QUARANTINED', 'REJECTED')),
  kill_switch boolean NOT NULL DEFAULT true,
  config jsonb NOT NULL DEFAULT '{}'::jsonb,
  last_reviewed_at timestamptz NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

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
  'world-bank-wdi',
  'World Bank World Development Indicators',
  'INSTITUTIONAL_API',
  'https://api.worldbank.org/v2',
  'PUBLIC_NO_AUTH',
  'COMMERCIAL_REUSE_WITH_ATTRIBUTION',
  'CC-BY-4.0',
  'World Bank Open Data — World Development Indicators; changes and derived interpretation by AXIGNAL.',
  'https://www.worldbank.org/ext/en/legal/terms-conditions/datasets',
  'https://data.worldbank.org/indicator/FP.CPI.TOTL.ZG?locations=RU',
  true,
  true,
  'ADMITTED',
  false,
  jsonb_build_object(
    'allowed_hosts', jsonb_build_array('api.worldbank.org'),
    'country', 'RUS',
    'indicators', jsonb_build_array('FP.CPI.TOTL.ZG'),
    'max_response_bytes', 524288,
    'timeout_seconds', 10,
    'attribution_required', true
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
  'bank-of-russia-statistics',
  'Bank of Russia Statistics API',
  'INSTITUTIONAL_API',
  'https://cbr.ru/statistics/data-service',
  'PUBLIC_NO_AUTH',
  'RIGHTS_PENDING',
  NULL,
  'Bank of Russia attribution would be required if a later rights review admits this source.',
  'https://cbr.ru/eng/user_agreement/',
  'https://cbr.ru/statistics/data-service/apidocumentation/',
  false,
  false,
  'QUARANTINED',
  true,
  jsonb_build_object(
    'reason', 'Commercial reuse and redistribution rights are not sufficiently explicit for AXIGNAL production use.',
    'network_access_allowed', false
  ),
  '2026-07-27T00:00:00Z'
)
ON CONFLICT (source_id) DO UPDATE SET
  rights_status = EXCLUDED.rights_status,
  admission_state = EXCLUDED.admission_state,
  kill_switch = EXCLUDED.kill_switch,
  config = EXCLUDED.config,
  last_reviewed_at = EXCLUDED.last_reviewed_at,
  updated_at = now();

CREATE TABLE IF NOT EXISTS axignal_global.source_objects (
  source_object_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_id text NOT NULL REFERENCES axignal_global.sources(source_id),
  retrieval_key text NOT NULL UNIQUE,
  request_url text NOT NULL,
  retrieved_at timestamptz NOT NULL,
  source_updated_at timestamptz,
  http_status integer NOT NULL CHECK (http_status BETWEEN 100 AND 599),
  content_type text NOT NULL,
  content_hash text NOT NULL CHECK (content_hash ~ '^sha256:[0-9a-f]{64}$'),
  raw_payload jsonb NOT NULL,
  rights_snapshot jsonb NOT NULL,
  lineage jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (source_id, content_hash)
);

CREATE TABLE IF NOT EXISTS axignal_global.evidence_objects (
  evidence_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_object_id uuid NOT NULL REFERENCES axignal_global.source_objects(source_object_id),
  source_id text NOT NULL REFERENCES axignal_global.sources(source_id),
  evidence_key text NOT NULL UNIQUE,
  title text NOT NULL,
  relationship text NOT NULL CHECK (relationship IN ('SUPPORT', 'CONTRADICT', 'UNKNOWN', 'CONTEXT')),
  subject_id text NOT NULL,
  predicate text NOT NULL,
  observed_at timestamptz NOT NULL,
  valid_from timestamptz,
  valid_to timestamptz,
  numeric_value numeric,
  unit text,
  payload jsonb NOT NULL,
  content_hash text NOT NULL CHECK (content_hash ~ '^sha256:[0-9a-f]{64}$'),
  rights_status text NOT NULL,
  provisional boolean NOT NULL DEFAULT true,
  embedding vector,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS axignal_global.candidate_claims (
  candidate_claim_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  fingerprint text NOT NULL UNIQUE CHECK (fingerprint ~ '^sha256:[0-9a-f]{64}$'),
  opportunity_id text NOT NULL,
  subject_id text NOT NULL,
  predicate text NOT NULL,
  object_value jsonb NOT NULL,
  statement text NOT NULL,
  kind text NOT NULL CHECK (kind IN ('FACT', 'INFERENCE', 'PREDICTION', 'CONTRADICTION')),
  state text NOT NULL CHECK (state IN ('PROPOSED', 'ADMISSION_QUEUED', 'ADMITTED', 'REJECTED')),
  evidence_ids uuid[] NOT NULL CHECK (cardinality(evidence_ids) > 0),
  producer_type text NOT NULL CHECK (producer_type IN ('DETERMINISTIC_PARSER', 'LOCAL_MODEL', 'EXTERNAL_MODEL')),
  producer_id text NOT NULL,
  method_version text NOT NULL,
  tenant_scope text NOT NULL DEFAULT 'GLOBAL' CHECK (tenant_scope = 'GLOBAL'),
  canonical_claim_id uuid,
  rejection_reasons jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS axignal_global.admission_batches (
  admission_batch_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  policy_version text NOT NULL,
  state text NOT NULL CHECK (state IN ('PENDING', 'DECIDED', 'FAILED')),
  candidate_claim_ids uuid[] NOT NULL,
  decision_summary jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  decided_at timestamptz
);

CREATE TABLE IF NOT EXISTS axignal_global.canonical_claims (
  canonical_claim_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  fingerprint text NOT NULL UNIQUE CHECK (fingerprint ~ '^sha256:[0-9a-f]{64}$'),
  subject_id text NOT NULL,
  predicate text NOT NULL,
  object_value jsonb NOT NULL,
  statement text NOT NULL,
  evidence_ids uuid[] NOT NULL CHECK (cardinality(evidence_ids) > 0),
  valid_from timestamptz,
  valid_to timestamptz,
  observed_at timestamptz NOT NULL,
  epistemic_class text NOT NULL CHECK (epistemic_class IN ('OBSERVED_FACT', 'DERIVED_FACT')),
  state text NOT NULL DEFAULT 'ADMITTED' CHECK (state = 'ADMITTED'),
  admitted_by text NOT NULL CHECK (admitted_by = 'DETERMINISTIC_RUNTIME'),
  admission_batch_id uuid NOT NULL REFERENCES axignal_global.admission_batches(admission_batch_id),
  admitted_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE axignal_global.candidate_claims
  DROP CONSTRAINT IF EXISTS candidate_claims_canonical_claim_id_fkey;
ALTER TABLE axignal_global.candidate_claims
  ADD CONSTRAINT candidate_claims_canonical_claim_id_fkey
  FOREIGN KEY (canonical_claim_id) REFERENCES axignal_global.canonical_claims(canonical_claim_id);

CREATE TABLE IF NOT EXISTS axignal_global.claim_state_events (
  claim_state_event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  canonical_claim_id uuid NOT NULL REFERENCES axignal_global.canonical_claims(canonical_claim_id),
  from_state text,
  to_state text NOT NULL,
  reason text NOT NULL,
  admission_batch_id uuid REFERENCES axignal_global.admission_batches(admission_batch_id),
  occurred_at timestamptz NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION axignal_global.reject_ledger_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE EXCEPTION 'AXIGNAL canonical ledger rows are append-only';
END
$$;

DROP TRIGGER IF EXISTS canonical_claims_immutable ON axignal_global.canonical_claims;
CREATE TRIGGER canonical_claims_immutable
BEFORE UPDATE OR DELETE ON axignal_global.canonical_claims
FOR EACH ROW EXECUTE FUNCTION axignal_global.reject_ledger_mutation();

DROP TRIGGER IF EXISTS claim_state_events_immutable ON axignal_global.claim_state_events;
CREATE TRIGGER claim_state_events_immutable
BEFORE UPDATE OR DELETE ON axignal_global.claim_state_events
FOR EACH ROW EXECUTE FUNCTION axignal_global.reject_ledger_mutation();

CREATE TABLE IF NOT EXISTS axignal_global.outbox_events (
  outbox_event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  aggregate_type text NOT NULL,
  aggregate_id uuid NOT NULL,
  event_type text NOT NULL,
  payload jsonb NOT NULL,
  status text NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'PUBLISHED', 'FAILED')),
  attempts integer NOT NULL DEFAULT 0 CHECK (attempts >= 0),
  available_at timestamptz NOT NULL DEFAULT now(),
  published_at timestamptz,
  last_error text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS outbox_pending_idx
  ON axignal_global.outbox_events (available_at, created_at)
  WHERE status = 'PENDING';

CREATE TABLE IF NOT EXISTS tenant_private.research_runs (
  research_run_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  context_id text NOT NULL,
  opportunity_id text NOT NULL,
  question text NOT NULL,
  state text NOT NULL CHECK (state IN ('QUEUED', 'RETRIEVING', 'PROPOSING', 'ADMISSION_PENDING', 'COMPLETED', 'FAILED')),
  private_knowledge_authorised boolean NOT NULL DEFAULT false,
  source_plan jsonb NOT NULL,
  budgets jsonb NOT NULL,
  actual_usage jsonb NOT NULL DEFAULT '{}'::jsonb,
  evidence_ids uuid[] NOT NULL DEFAULT '{}'::uuid[],
  candidate_claim_ids uuid[] NOT NULL DEFAULT '{}'::uuid[],
  canonical_claim_ids uuid[] NOT NULL DEFAULT '{}'::uuid[],
  dossier_id uuid,
  admission_batch_id uuid REFERENCES axignal_global.admission_batches(admission_batch_id),
  error_code text,
  error_detail text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tenant_private.dossiers (
  dossier_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  research_run_id uuid NOT NULL REFERENCES tenant_private.research_runs(research_run_id) ON DELETE CASCADE,
  status text NOT NULL CHECK (status IN ('TRACEABLE_PROVISIONAL', 'TRACEABLE_WITH_ADMITTED_FACTS')),
  title text NOT NULL,
  summary text NOT NULL,
  sections jsonb NOT NULL,
  attribution jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE tenant_private.research_runs
  DROP CONSTRAINT IF EXISTS research_runs_dossier_id_fkey;
ALTER TABLE tenant_private.research_runs
  ADD CONSTRAINT research_runs_dossier_id_fkey
  FOREIGN KEY (dossier_id) REFERENCES tenant_private.dossiers(dossier_id);

CREATE TABLE IF NOT EXISTS tenant_private.research_evidence_links (
  tenant_id uuid NOT NULL,
  research_run_id uuid NOT NULL REFERENCES tenant_private.research_runs(research_run_id) ON DELETE CASCADE,
  evidence_id uuid NOT NULL REFERENCES axignal_global.evidence_objects(evidence_id),
  visibility text NOT NULL CHECK (visibility IN ('GLOBAL_PUBLIC', 'TENANT_PRIVATE')),
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (research_run_id, evidence_id)
);

CREATE TABLE IF NOT EXISTS tenant_private.knowledge_items (
  knowledge_item_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  item_type text NOT NULL CHECK (item_type IN ('NOTE', 'DOCUMENT', 'TRAIL', 'WATCHLIST', 'PRIVATE_CLAIM')),
  title text NOT NULL,
  body text NOT NULL,
  source_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  content_hash text NOT NULL CHECK (content_hash ~ '^sha256:[0-9a-f]{64}$'),
  embedding vector,
  retention_until timestamptz,
  deleted_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, content_hash)
);

CREATE TABLE IF NOT EXISTS intent_intelligence.intent_events (
  intent_event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  event_type text NOT NULL,
  subject_key text NOT NULL,
  payload jsonb NOT NULL,
  occurred_at timestamptz NOT NULL,
  expires_at timestamptz NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS intent_intelligence.knowledge_tides (
  knowledge_tide_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  cohort_key text NOT NULL,
  subject_key text NOT NULL,
  window_start timestamptz NOT NULL,
  window_end timestamptz NOT NULL,
  distinct_tenant_count integer NOT NULL CHECK (distinct_tenant_count >= 0),
  signal_strength numeric NOT NULL,
  privacy_threshold_met boolean NOT NULL,
  manipulation_status text NOT NULL CHECK (manipulation_status IN ('CLEAR', 'SUSPECTED', 'BLOCKED')),
  research_candidate_only boolean NOT NULL DEFAULT true CHECK (research_candidate_only),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (cohort_key, subject_key, window_start, window_end)
);

ALTER TABLE tenant_private.research_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.research_runs FORCE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.dossiers ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.dossiers FORCE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.research_evidence_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.research_evidence_links FORCE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.knowledge_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.knowledge_items FORCE ROW LEVEL SECURITY;
ALTER TABLE intent_intelligence.intent_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE intent_intelligence.intent_events FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS research_runs_tenant_isolation ON tenant_private.research_runs;
CREATE POLICY research_runs_tenant_isolation ON tenant_private.research_runs
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

DROP POLICY IF EXISTS dossiers_tenant_isolation ON tenant_private.dossiers;
CREATE POLICY dossiers_tenant_isolation ON tenant_private.dossiers
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

DROP POLICY IF EXISTS research_evidence_links_tenant_isolation ON tenant_private.research_evidence_links;
CREATE POLICY research_evidence_links_tenant_isolation ON tenant_private.research_evidence_links
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

DROP POLICY IF EXISTS knowledge_items_tenant_isolation ON tenant_private.knowledge_items;
CREATE POLICY knowledge_items_tenant_isolation ON tenant_private.knowledge_items
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

DROP POLICY IF EXISTS intent_events_tenant_isolation ON intent_intelligence.intent_events;
CREATE POLICY intent_events_tenant_isolation ON intent_intelligence.intent_events
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

GRANT SELECT ON axignal_global.sources, axignal_global.canonical_claims, axignal_global.claim_state_events TO axignal_app;
GRANT SELECT, INSERT ON tenant_private.research_runs, tenant_private.dossiers, tenant_private.research_evidence_links, tenant_private.knowledge_items TO axignal_app;
GRANT UPDATE (state, actual_usage, evidence_ids, candidate_claim_ids, canonical_claim_ids, dossier_id, admission_batch_id, error_code, error_detail, updated_at)
  ON tenant_private.research_runs TO axignal_app;
GRANT SELECT, INSERT ON intent_intelligence.intent_events TO axignal_app;
GRANT SELECT ON intent_intelligence.knowledge_tides TO axignal_app;

GRANT SELECT, INSERT, UPDATE ON axignal_global.source_objects, axignal_global.evidence_objects, axignal_global.candidate_claims,
  axignal_global.admission_batches, axignal_global.outbox_events TO axignal_worker;
GRANT SELECT, INSERT ON axignal_global.canonical_claims, axignal_global.claim_state_events TO axignal_worker;
GRANT SELECT ON axignal_global.sources TO axignal_worker;
GRANT SELECT, INSERT, UPDATE ON tenant_private.research_runs, tenant_private.dossiers, tenant_private.research_evidence_links TO axignal_worker;
GRANT SELECT ON tenant_private.knowledge_items TO axignal_worker;
GRANT SELECT, INSERT, UPDATE ON intent_intelligence.knowledge_tides TO axignal_worker;

CREATE INDEX IF NOT EXISTS research_runs_tenant_created_idx
  ON tenant_private.research_runs (tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS evidence_subject_predicate_idx
  ON axignal_global.evidence_objects (subject_id, predicate, observed_at DESC);
CREATE INDEX IF NOT EXISTS canonical_claim_subject_predicate_idx
  ON axignal_global.canonical_claims (subject_id, predicate, observed_at DESC);
CREATE INDEX IF NOT EXISTS candidate_claim_state_idx
  ON axignal_global.candidate_claims (state, created_at);
CREATE INDEX IF NOT EXISTS tenant_knowledge_created_idx
  ON tenant_private.knowledge_items (tenant_id, created_at DESC)
  WHERE deleted_at IS NULL;
