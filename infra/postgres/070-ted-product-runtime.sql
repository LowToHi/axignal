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
  'TED Search API v3 · bounded non-personal projection',
  'INSTITUTIONAL_API',
  'https://api.ted.europa.eu/v3/notices/search',
  'PUBLIC_NO_AUTH',
  'COMMERCIAL_REUSE_WITH_ATTRIBUTION',
  'TED-LEGAL-NOTICE-REUSE',
  'Source: TED (Tenders Electronic Daily), Supplement to the Official Journal of the European Union. AXIGNAL selected and normalised the allowlisted fields; changes are indicated in the dossier methodology.',
  'https://ted.europa.eu/en/legal-notice',
  'https://docs.ted.europa.eu/api/latest/search.html',
  true,
  false,
  'ADMITTED',
  false,
  jsonb_build_object(
    'product_profile', 'ted-search-non-personal-projection@0.1.0',
    'allowed_hosts', jsonb_build_array('api.ted.europa.eu'),
    'allowed_path', '/v3/notices/search',
    'fixed_query', 'place-of-performance IN (LUX)',
    'allowed_fields', jsonb_build_array(
      'publication-number',
      'notice-title',
      'buyer-name',
      'notice-type'
    ),
    'prohibited_field_tokens', jsonb_build_array(
      'contact', 'email', 'person', 'phone', 'telephone'
    ),
    'max_api_requests', 1,
    'max_notices', 3,
    'max_response_bytes', 1048576,
    'max_model_calls', 0,
    'customer_display_allowed', true,
    'dossier_export_allowed', true,
    'api_redistribution_allowed', false,
    'bulk_redistribution_allowed', false,
    'model_training_allowed', false,
    'personal_contact_data_allowed', false
  ),
  '2026-07-29T14:49:00Z'
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
      'TED_PROCUREMENT'
    )
  );
