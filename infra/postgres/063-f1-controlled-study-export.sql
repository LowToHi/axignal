DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'axignal_validation_analyst') THEN
    CREATE ROLE axignal_validation_analyst NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'axignal_validation_analyst_login') THEN
    CREATE ROLE axignal_validation_analyst_login LOGIN PASSWORD 'axignal_validation_analyst';
  ELSE
    ALTER ROLE axignal_validation_analyst_login LOGIN PASSWORD 'axignal_validation_analyst';
  END IF;
END
$$;

GRANT axignal_validation_analyst TO axignal_validation_analyst_login;
GRANT USAGE ON SCHEMA evaluation TO axignal_validation_analyst;

CREATE OR REPLACE FUNCTION evaluation.export_validation_study(
  p_tenant_id uuid,
  p_experiment_version text
)
RETURNS SETOF jsonb
LANGUAGE sql
SECURITY DEFINER
SET search_path = pg_catalog, evaluation
AS $$
  SELECT jsonb_build_object(
    'study_id', 'AXIGNAL-F1-CONTROLLED-001',
    'protocol_version', '1.0.0',
    'session_id', s.validation_session_id,
    'participant_id_hash', s.participant_id_hash,
    'participant_profile', s.participant_profile,
    'task_id', s.task_id,
    'experiment_version', s.experiment_version,
    'condition', s.condition,
    'language', s.language,
    'state', s.state,
    'started_at', s.started_at,
    'completed_at', s.completed_at,
    'outcome', CASE
      WHEN r.validation_response_id IS NULL THEN NULL
      ELSE jsonb_build_object(
        'task_completed', r.task_completed,
        'critical_error', r.critical_error,
        'authority_layer_correct', r.authority_layer_correct,
        'evidence_traceability', r.evidence_traceability,
        'unknowns_identified', r.unknowns_identified,
        'confidence', s.outcome->'confidence'
      )
    END,
    'technical_pre_response_failure', false
  )
  FROM evaluation.validation_sessions s
  LEFT JOIN evaluation.validation_responses r
    ON r.validation_session_id = s.validation_session_id
  WHERE s.tenant_id = p_tenant_id
    AND s.experiment_version = p_experiment_version
  ORDER BY s.started_at, s.validation_session_id
$$;

REVOKE ALL ON FUNCTION evaluation.export_validation_study(uuid, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION evaluation.export_validation_study(uuid, text)
  TO axignal_validation_analyst;

REVOKE ALL ON ALL TABLES IN SCHEMA evaluation FROM axignal_validation_analyst;
REVOKE ALL ON ALL TABLES IN SCHEMA axignal_global FROM axignal_validation_analyst;
REVOKE ALL ON ALL TABLES IN SCHEMA tenant_private FROM axignal_validation_analyst;
