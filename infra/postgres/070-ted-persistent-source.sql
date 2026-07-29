DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'axignal_ted_worker') THEN
    CREATE ROLE axignal_ted_worker LOGIN PASSWORD 'axignal_ted_worker';
  ELSE
    ALTER ROLE axignal_ted_worker LOGIN PASSWORD 'axignal_ted_worker';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'axignal_ted_admission_runtime') THEN
    CREATE ROLE axignal_ted_admission_runtime LOGIN PASSWORD 'axignal_ted_admission_runtime';
  ELSE
    ALTER ROLE axignal_ted_admission_runtime LOGIN PASSWORD 'axignal_ted_admission_runtime';
  END IF;
END
$$;

GRANT USAGE ON SCHEMA axignal_global, tenant_private TO
  axignal_ted_worker,
  axignal_ted_admission_runtime;

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
  'src_ted_search_api_v3',
  'TED Search API v3 and official eForms XML notices — non-personal derived profile',
  'INSTITUTIONAL_API',
  'https://api.ted.europa.eu/v3/notices/search',
  'PUBLIC_NO_AUTH',
  'COMMERCIAL_REUSE_WITH_ATTRIBUTION',
  'CC0-1.0+2011/833/EU-DERIVED-NON-PERSONAL',
  'Source: TED, Publications Office of the European Union. AXIGNAL stores and redistributes only a minimised non-personal derived projection, identifies modifications and preserves notice lineage.',
  'https://ted.europa.eu/en/legal-notice',
  'https://docs.ted.europa.eu/api/latest/search.html',
  true,
  true,
  'ADMITTED',
  false,
  jsonb_build_object(
    'product_profile_id', 'ted-eforms-non-personal@1.0.0',
    'rights_scope', 'DERIVED_NON_PERSONAL_ONLY',
    'search_endpoint', 'https://api.ted.europa.eu/v3/notices/search',
    'xml_url_template', 'https://ted.europa.eu/en/notice/{publication_number}/xml',
    'allowed_hosts', jsonb_build_array('api.ted.europa.eu', 'ted.europa.eu'),
    'max_notices_per_run', 4,
    'max_xml_bytes_per_notice', 2097152,
    'parser_profile', 'ted-eforms-procurement-lifecycle@0.1.0',
    'supported_sdk_release', '1.14.2',
    'supported_customization_id', 'eforms-sdk-1.14',
    'supported_notice_subtypes', jsonb_build_array('16', '29'),
    'raw_xml_persistence', false,
    'raw_xml_redistribution', false,
    'derived_non_personal_redistribution', true,
    'personal_values_persistence', false,
    'model_training', false,
    'automatic_predicates', jsonb_build_array(
      'procurement_notice_type',
      'procurement_procedure_type',
      'procurement_contract_nature',
      'procurement_cpv_code',
      'procurement_place_of_performance_nuts',
      'procurement_estimated_value',
      'procurement_lot_identifier',
      'procurement_submission_deadline',
      'procurement_eu_funding_indicator',
      'procurement_notice_lifecycle_kind',
      'procurement_changed_notice_reference',
      'procurement_change_reason_code',
      'procurement_result_lot_identifier',
      'procurement_winner_selection_status',
      'procurement_tenders_received_count',
      'procurement_awarded_value',
      'procurement_award_date'
    ),
    'excluded_predicates', jsonb_build_array(
      'procurement_buyer_official_name',
      'procurement_buyer_identifier',
      'procurement_winner_official_name',
      'procurement_winner_organisation_ref',
      'procurement_contract_identifier'
    ),
    'attribution_required', true,
    'kill_switch_conditions', jsonb_build_array(
      'rights_change',
      'personal_value_leakage',
      'unknown_parser_profile',
      'lineage_failure',
      'hash_mismatch',
      'attribution_failure'
    )
  ),
  '2026-07-29T11:35:00Z'
)
ON CONFLICT (source_id) DO UPDATE SET
  name = EXCLUDED.name,
  source_type = EXCLUDED.source_type,
  base_url = EXCLUDED.base_url,
  access_mode = EXCLUDED.access_mode,
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
  DROP CONSTRAINT IF EXISTS research_runs_job_kind_check;
ALTER TABLE tenant_private.research_runs
  ADD CONSTRAINT research_runs_job_kind_check CHECK (
    job_kind IN (
      'STRUCTURED_SOURCE_OBSERVATION',
      'DOCUMENT_PROPOSAL',
      'PROCUREMENT_TED'
    )
  );

CREATE TABLE IF NOT EXISTS axignal_global.procurement_notice_versions (
  procurement_notice_version_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_object_id uuid NOT NULL UNIQUE
    REFERENCES axignal_global.source_objects(source_object_id),
  source_id text NOT NULL REFERENCES axignal_global.sources(source_id),
  publication_number text NOT NULL CHECK (
    publication_number ~ '^[0-9]{1,8}-[0-9]{4}$'
  ),
  notice_reference text NOT NULL UNIQUE CHECK (
    notice_reference ~ '^[0-9a-fA-F-]{36}-[0-9]{2}$'
  ),
  procedure_identifier text NOT NULL,
  lifecycle_kind text NOT NULL CHECK (
    lifecycle_kind IN (
      'COMPETITION_INITIAL',
      'COMPETITION_CORRECTION',
      'NOTICE_CANCELLATION',
      'PROCEDURE_RESULT'
    )
  ),
  previous_notice_reference text,
  issue_date date NOT NULL,
  raw_content_hash text NOT NULL CHECK (
    raw_content_hash ~ '^sha256:[0-9a-f]{64}$'
  ),
  parser_profile text NOT NULL,
  sanitised_payload jsonb NOT NULL,
  personal_field_element_count integer NOT NULL DEFAULT 0 CHECK (
    personal_field_element_count >= 0
  ),
  raw_xml_persisted boolean NOT NULL DEFAULT false CHECK (raw_xml_persisted = false),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (publication_number, raw_content_hash)
);

CREATE INDEX IF NOT EXISTS procurement_notice_versions_procedure_idx
  ON axignal_global.procurement_notice_versions (
    procedure_identifier,
    issue_date,
    notice_reference
  );

CREATE TABLE IF NOT EXISTS axignal_global.procurement_retrieval_outbox_events (
  procurement_retrieval_outbox_event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  aggregate_id uuid NOT NULL,
  event_type text NOT NULL CHECK (
    event_type IN (
      'research.procurement.requested',
      'research.procurement.proposed',
      'research.procurement.completed'
    )
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

CREATE INDEX IF NOT EXISTS procurement_retrieval_outbox_pending_idx
  ON axignal_global.procurement_retrieval_outbox_events (available_at, created_at)
  WHERE status = 'PENDING';

CREATE TABLE IF NOT EXISTS axignal_global.procurement_admission_outbox_events (
  procurement_admission_outbox_event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  aggregate_id uuid NOT NULL,
  event_type text NOT NULL CHECK (
    event_type IN (
      'admission.procurement.requested',
      'admission.procurement.decided'
    )
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

CREATE INDEX IF NOT EXISTS procurement_admission_outbox_pending_idx
  ON axignal_global.procurement_admission_outbox_events (available_at, created_at)
  WHERE status = 'PENDING';

CREATE TABLE IF NOT EXISTS axignal_global.procurement_job_failures (
  procurement_job_failure_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  stage text NOT NULL CHECK (stage IN ('RETRIEVAL', 'ADMISSION')),
  tenant_id uuid NOT NULL,
  research_run_id uuid NOT NULL,
  admission_handoff_id uuid,
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
  IF NEW.package->>'pipeline_version' = 'ted-persistent-source@0.1.0' THEN
    INSERT INTO axignal_global.procurement_admission_outbox_events (
      aggregate_id,
      event_type,
      payload
    ) VALUES (
      NEW.admission_handoff_id,
      'admission.procurement.requested',
      jsonb_build_object(
        'schema_version', 1,
        'job_kind', 'PROCUREMENT_ADMISSION_REVIEW',
        'admission_handoff_id', NEW.admission_handoff_id::text,
        'research_run_id', NEW.research_run_id::text,
        'tenant_id', NEW.tenant_id::text,
        'expected_package_hash', NEW.package_hash,
        'policy_version', 'ted-procurement-observed@1.0.0',
        'publication_numbers', NEW.package->'publication_numbers'
      )
    );
  ELSE
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
  END IF;
  RETURN NEW;
END
$$;

GRANT SELECT, INSERT, UPDATE ON
  axignal_global.procurement_retrieval_outbox_events
TO axignal_app;

GRANT SELECT ON axignal_global.sources TO axignal_ted_worker;
GRANT SELECT, INSERT ON
  axignal_global.source_objects,
  axignal_global.procurement_notice_versions,
  axignal_global.evidence_objects,
  axignal_global.candidate_claims,
  axignal_global.admission_handoffs,
  axignal_global.procurement_job_failures
TO axignal_ted_worker;
GRANT SELECT, UPDATE ON
  axignal_global.procurement_retrieval_outbox_events
TO axignal_ted_worker;
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
) ON tenant_private.research_runs TO axignal_ted_worker;
GRANT SELECT, INSERT ON
  tenant_private.dossiers,
  tenant_private.research_evidence_links
TO axignal_ted_worker;

REVOKE ALL PRIVILEGES ON
  axignal_global.admission_batches,
  axignal_global.admission_decisions,
  axignal_global.canonical_claims,
  axignal_global.claim_state_events
FROM axignal_ted_worker;

GRANT SELECT ON
  axignal_global.sources,
  axignal_global.source_objects,
  axignal_global.procurement_notice_versions,
  axignal_global.evidence_objects,
  axignal_global.candidate_claims,
  axignal_global.admission_handoffs,
  axignal_global.admission_batches,
  axignal_global.admission_decisions,
  axignal_global.canonical_claims,
  axignal_global.claim_state_events,
  axignal_global.procurement_admission_outbox_events
TO axignal_ted_admission_runtime;

GRANT INSERT ON
  axignal_global.admission_batches,
  axignal_global.admission_decisions,
  axignal_global.canonical_claims,
  axignal_global.claim_state_events,
  axignal_global.procurement_job_failures
TO axignal_ted_admission_runtime;
GRANT UPDATE (state, canonical_claim_id, rejection_reasons, updated_at)
  ON axignal_global.candidate_claims TO axignal_ted_admission_runtime;
GRANT UPDATE (state, consumed_at)
  ON axignal_global.admission_handoffs TO axignal_ted_admission_runtime;
GRANT UPDATE (state, decision_summary, decided_at)
  ON axignal_global.admission_batches TO axignal_ted_admission_runtime;
GRANT UPDATE (status, attempts, published_at, last_error, available_at)
  ON axignal_global.procurement_admission_outbox_events
  TO axignal_ted_admission_runtime;
GRANT SELECT ON tenant_private.research_runs, tenant_private.dossiers
  TO axignal_ted_admission_runtime;
GRANT UPDATE (
  state,
  actual_usage,
  canonical_claim_ids,
  admission_batch_id,
  error_code,
  error_detail,
  updated_at
) ON tenant_private.research_runs TO axignal_ted_admission_runtime;
GRANT UPDATE (status) ON tenant_private.dossiers TO axignal_ted_admission_runtime;

REVOKE INSERT, UPDATE, DELETE ON
  axignal_global.sources,
  axignal_global.source_objects,
  axignal_global.procurement_notice_versions,
  axignal_global.evidence_objects
FROM axignal_ted_admission_runtime;
