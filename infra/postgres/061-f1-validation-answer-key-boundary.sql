CREATE OR REPLACE FUNCTION evaluation.validation_session_bundle(p_session_id uuid)
RETURNS jsonb
LANGUAGE sql
SECURITY DEFINER
SET search_path = pg_catalog, evaluation
AS $$
  SELECT jsonb_build_object(
    'session', to_jsonb(s),
    'task', jsonb_build_object(
      'task_id', t.task_id,
      'title', t.title,
      'language', t.language,
      'content_hash', t.content_hash,
      'payload', t.task_payload
        - 'authority_layer'
        - 'required_evidence_ids'
        - 'required_unknowns'
        - 'critical_error_layers'
        - 'reference_answer'
    ),
    'events', COALESCE((
      SELECT jsonb_agg(to_jsonb(e) ORDER BY e.occurred_at, e.validation_event_id)
      FROM evaluation.validation_events e
      WHERE e.validation_session_id = s.validation_session_id
    ), '[]'::jsonb),
    'response', (
      SELECT jsonb_build_object(
        'authority_layer_correct', r.authority_layer_correct,
        'evidence_traceability', r.evidence_traceability,
        'unknowns_identified', r.unknowns_identified,
        'critical_error', r.critical_error,
        'task_completed', r.task_completed,
        'created_at', r.created_at
      )
      FROM evaluation.validation_responses r
      WHERE r.validation_session_id = s.validation_session_id
    )
  )
  FROM evaluation.validation_sessions s
  JOIN evaluation.validation_tasks t USING (task_id)
  WHERE s.validation_session_id = p_session_id
    AND s.tenant_id = tenant_private.current_tenant_id()
$$;

REVOKE ALL ON FUNCTION evaluation.validation_session_bundle(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION evaluation.validation_session_bundle(uuid)
  TO axignal_validation_runtime;
