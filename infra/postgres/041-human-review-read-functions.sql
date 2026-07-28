CREATE OR REPLACE FUNCTION tenant_private.human_review_case_bundle(
  requested_case_id uuid
)
RETURNS jsonb
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, axignal_global, tenant_private
AS $$
SELECT jsonb_build_object(
  'human_review_case_id', review_case.human_review_case_id,
  'tenant_id', review_case.tenant_id,
  'research_run_id', review_case.research_run_id,
  'admission_handoff_id', review_case.admission_handoff_id,
  'admission_decision_id', review_case.admission_decision_id,
  'candidate_claim_id', review_case.candidate_claim_id,
  'case_type', review_case.case_type,
  'state', review_case.state,
  'priority', review_case.priority,
  'assigned_reviewer_subject', review_case.assigned_reviewer_subject,
  'assigned_reviewer_email', review_case.assigned_reviewer_email,
  'opened_reason', review_case.opened_reason,
  'resolution', review_case.resolution,
  'resolution_reason_code', review_case.resolution_reason_code,
  'resolution_note', review_case.resolution_note,
  'created_at', review_case.created_at,
  'assigned_at', review_case.assigned_at,
  'resolved_at', review_case.resolved_at,
  'updated_at', review_case.updated_at,
  'deterministic_decision', jsonb_build_object(
    'outcome', decision.outcome,
    'policy_version', decision.policy_version,
    'gate_results', decision.gate_results,
    'rejection_reasons', decision.rejection_reasons,
    'canonical_claim_id', decision.canonical_claim_id
  ),
  'candidate_claim', jsonb_build_object(
    'statement', candidate.statement,
    'kind', candidate.kind,
    'state', candidate.state,
    'producer_type', candidate.producer_type,
    'producer_id', candidate.producer_id,
    'method_version', candidate.method_version,
    'assumptions', candidate.assumptions,
    'unknowns', candidate.unknowns,
    'canonical_claim_id', candidate.canonical_claim_id
  ),
  'source', CASE
    WHEN source.source_id IS NULL THEN NULL
    ELSE jsonb_build_object(
      'source_id', source.source_id,
      'name', source.name,
      'rights_status', source.rights_status,
      'license_id', source.license_id,
      'admission_state', source.admission_state,
      'kill_switch', source.kill_switch
    )
  END,
  'evidence', COALESCE((
    SELECT jsonb_agg(
      jsonb_build_object(
        'evidence_id', evidence.evidence_id,
        'title', evidence.title,
        'relationship', evidence.relationship,
        'source_id', evidence.source_id,
        'rights_status', evidence.rights_status,
        'fragment_id', evidence.payload->>'fragment_id',
        'quote_hash', evidence.payload->>'quote_hash',
        'text', evidence.payload->>'text'
      )
      ORDER BY evidence.created_at, evidence.evidence_id
    )
    FROM axignal_global.evidence_objects AS evidence
    WHERE evidence.evidence_id = ANY(candidate.evidence_ids)
  ), '[]'::jsonb),
  'events', COALESCE((
    SELECT jsonb_agg(
      to_jsonb(event)
      ORDER BY event.occurred_at, event.human_review_event_id
    )
    FROM tenant_private.human_review_events AS event
    WHERE event.human_review_case_id = review_case.human_review_case_id
  ), '[]'::jsonb)
)
FROM tenant_private.human_review_cases AS review_case
JOIN axignal_global.admission_decisions AS decision
  ON decision.admission_decision_id = review_case.admission_decision_id
JOIN axignal_global.candidate_claims AS candidate
  ON candidate.candidate_claim_id = review_case.candidate_claim_id
LEFT JOIN axignal_global.evidence_objects AS first_evidence
  ON first_evidence.evidence_id = candidate.evidence_ids[1]
LEFT JOIN axignal_global.sources AS source
  ON source.source_id = first_evidence.source_id
WHERE review_case.human_review_case_id = requested_case_id
  AND review_case.tenant_id = tenant_private.current_tenant_id();
$$;

CREATE OR REPLACE FUNCTION tenant_private.list_human_review_cases(
  requested_research_run_id uuid DEFAULT NULL
)
RETURNS SETOF jsonb
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, tenant_private
AS $$
SELECT tenant_private.human_review_case_bundle(review_case.human_review_case_id)
FROM tenant_private.human_review_cases AS review_case
WHERE review_case.tenant_id = tenant_private.current_tenant_id()
  AND (
    requested_research_run_id IS NULL
    OR review_case.research_run_id = requested_research_run_id
  )
ORDER BY
  CASE review_case.priority WHEN 'HIGH' THEN 0 WHEN 'NORMAL' THEN 1 ELSE 2 END,
  review_case.created_at,
  review_case.human_review_case_id;
$$;
