CREATE SCHEMA IF NOT EXISTS evaluation;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'axignal_validation_runtime') THEN
    CREATE ROLE axignal_validation_runtime NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'axignal_validation_runtime_login') THEN
    CREATE ROLE axignal_validation_runtime_login LOGIN PASSWORD 'axignal_validation_runtime';
  ELSE
    ALTER ROLE axignal_validation_runtime_login LOGIN PASSWORD 'axignal_validation_runtime';
  END IF;
END
$$;

GRANT axignal_validation_runtime TO axignal_validation_runtime_login;
GRANT USAGE ON SCHEMA evaluation TO axignal_validation_runtime;

CREATE TABLE IF NOT EXISTS evaluation.validation_tasks (
  task_id text PRIMARY KEY,
  experiment_version text NOT NULL,
  language text NOT NULL CHECK (language IN ('en', 'es')),
  title text NOT NULL,
  content_hash text NOT NULL CHECK (content_hash ~ '^sha256:[0-9a-f]{64}$'),
  task_payload jsonb NOT NULL,
  frozen boolean NOT NULL DEFAULT true CHECK (frozen),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (experiment_version, content_hash)
);

CREATE TABLE IF NOT EXISTS evaluation.validation_sessions (
  validation_session_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  participant_id_hash text NOT NULL CHECK (
    participant_id_hash ~ '^sha256:[0-9a-f]{64}$'
  ),
  participant_profile text NOT NULL CHECK (
    participant_profile IN ('DOMAIN_EXPERT', 'ANALYST', 'DECISION_MAKER', 'OTHER_QUALIFIED')
  ),
  task_id text NOT NULL REFERENCES evaluation.validation_tasks(task_id),
  experiment_version text NOT NULL,
  condition text NOT NULL CHECK (condition IN ('AXIGNAL', 'CONTROL')),
  language text NOT NULL CHECK (language IN ('en', 'es')),
  state text NOT NULL DEFAULT 'STARTED' CHECK (
    state IN ('STARTED', 'COMPLETED', 'ABANDONED')
  ),
  outcome jsonb,
  response_hash text CHECK (
    response_hash IS NULL OR response_hash ~ '^sha256:[0-9a-f]{64}$'
  ),
  started_at timestamptz NOT NULL DEFAULT now(),
  completed_at timestamptz,
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, participant_id_hash, task_id, experiment_version)
);

CREATE INDEX IF NOT EXISTS validation_sessions_tenant_condition_idx
  ON evaluation.validation_sessions (tenant_id, condition, state, started_at);

CREATE TABLE IF NOT EXISTS evaluation.validation_events (
  validation_event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  validation_session_id uuid NOT NULL
    REFERENCES evaluation.validation_sessions(validation_session_id) ON DELETE CASCADE,
  tenant_id uuid NOT NULL,
  event_type text NOT NULL CHECK (
    event_type IN (
      'SESSION_STARTED',
      'TASK_OPENED',
      'SOURCE_OPENED',
      'EVIDENCE_INSPECTED',
      'CLAIM_INSPECTED',
      'TIMELINE_USED',
      'HUMAN_REVIEW_OPENED',
      'ANSWER_SUBMITTED',
      'SESSION_ABANDONED',
      'SESSION_COMPLETED'
    )
  ),
  idempotency_key text NOT NULL,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  occurred_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (validation_session_id, idempotency_key)
);

CREATE INDEX IF NOT EXISTS validation_events_session_idx
  ON evaluation.validation_events (validation_session_id, occurred_at);

CREATE TABLE IF NOT EXISTS evaluation.validation_responses (
  validation_response_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  validation_session_id uuid NOT NULL UNIQUE
    REFERENCES evaluation.validation_sessions(validation_session_id) ON DELETE CASCADE,
  tenant_id uuid NOT NULL,
  structured_response jsonb NOT NULL,
  response_hash text NOT NULL CHECK (response_hash ~ '^sha256:[0-9a-f]{64}$'),
  authority_layer_correct boolean NOT NULL,
  evidence_traceability boolean NOT NULL,
  unknowns_identified boolean NOT NULL,
  critical_error boolean NOT NULL,
  task_completed boolean NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION evaluation.block_validation_history_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE EXCEPTION 'AXIGNAL_VALIDATION_HISTORY_APPEND_ONLY';
END
$$;

DROP TRIGGER IF EXISTS validation_events_append_only
  ON evaluation.validation_events;
CREATE TRIGGER validation_events_append_only
BEFORE UPDATE OR DELETE ON evaluation.validation_events
FOR EACH ROW EXECUTE FUNCTION evaluation.block_validation_history_mutation();

DROP TRIGGER IF EXISTS validation_responses_append_only
  ON evaluation.validation_responses;
CREATE TRIGGER validation_responses_append_only
BEFORE UPDATE OR DELETE ON evaluation.validation_responses
FOR EACH ROW EXECUTE FUNCTION evaluation.block_validation_history_mutation();

ALTER TABLE evaluation.validation_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE evaluation.validation_sessions FORCE ROW LEVEL SECURITY;
ALTER TABLE evaluation.validation_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE evaluation.validation_events FORCE ROW LEVEL SECURITY;
ALTER TABLE evaluation.validation_responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE evaluation.validation_responses FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS validation_sessions_tenant_policy
  ON evaluation.validation_sessions;
CREATE POLICY validation_sessions_tenant_policy
  ON evaluation.validation_sessions
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

DROP POLICY IF EXISTS validation_events_tenant_policy
  ON evaluation.validation_events;
CREATE POLICY validation_events_tenant_policy
  ON evaluation.validation_events
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

DROP POLICY IF EXISTS validation_responses_tenant_policy
  ON evaluation.validation_responses;
CREATE POLICY validation_responses_tenant_policy
  ON evaluation.validation_responses
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

WITH frozen(task_id, experiment_version, language, title, payload) AS (
  VALUES
  (
    'F1-AUTHORITY-001', 'f1-qualified-user@0.1.0', 'en',
    'Distinguish canonical fact from proposal and context',
    jsonb_build_object(
      'prompt', 'Classify the highlighted statement and identify the evidence that supports it.',
      'statement', 'Russian real GDP growth was 2.3% in 2018.',
      'authority_layer', 'CANONICAL_CLAIM',
      'evidence', jsonb_build_array(
        jsonb_build_object('id','EV-WB-RUS-GDP-2018','title','World Bank Russia Economic Report 41','excerpt','Real GDP growth reached 2.3 percent in 2018.','source_state','ADMITTED')
      ),
      'required_evidence_ids', jsonb_build_array('EV-WB-RUS-GDP-2018'),
      'required_unknowns', jsonb_build_array('MOSCOW_MARKET_NOT_DEMONSTRATED'),
      'unknowns', jsonb_build_array(
        jsonb_build_object('id','MOSCOW_MARKET_NOT_DEMONSTRATED','label','The national report does not establish Moscow-specific market conditions.')
      ),
      'critical_error_layers', jsonb_build_array('MODEL_PROPOSAL'),
      'reference_answer', 'The statement is a canonical derived claim backed by the admitted World Bank evidence; it does not establish Moscow-specific conditions.'
    )
  ),
  (
    'F1-RIGHTS-002', 'f1-qualified-user@0.1.0', 'en',
    'Recognise a source blocked by rights',
    jsonb_build_object(
      'prompt', 'Decide whether the source may support a canonical claim and explain the blocking reason.',
      'statement', 'Bank of Russia statistics can be used commercially in this investigation.',
      'authority_layer', 'REJECTED_PROPOSAL',
      'evidence', jsonb_build_array(
        jsonb_build_object('id','EV-CBR-RIGHTS','title','Bank of Russia source registry record','excerpt','Commercial reuse and redistribution rights remain insufficiently explicit.','source_state','QUARANTINED')
      ),
      'required_evidence_ids', jsonb_build_array('EV-CBR-RIGHTS'),
      'required_unknowns', jsonb_build_array('COMMERCIAL_REUSE_RIGHTS_PENDING'),
      'unknowns', jsonb_build_array(
        jsonb_build_object('id','COMMERCIAL_REUSE_RIGHTS_PENDING','label','Commercial reuse rights require an independent legal review.')
      ),
      'critical_error_layers', jsonb_build_array('CANONICAL_CLAIM'),
      'reference_answer', 'The proposal must remain rejected because the source is quarantined and commercial reuse rights are unresolved.'
    )
  ),
  (
    'F1-CONTEXT-003', 'f1-qualified-user@0.1.0', 'en',
    'Interpret accepted non-canonical context',
    jsonb_build_object(
      'prompt', 'Classify the limitation and identify what it changes in the dossier.',
      'statement', 'The national report does not demonstrate Moscow-specific market conditions.',
      'authority_layer', 'HUMAN_REVIEW_CONTEXT',
      'evidence', jsonb_build_array(
        jsonb_build_object('id','EV-WB-SCOPE','title','World Bank report scope','excerpt','The report presents national-level Russian economic indicators.','source_state','ADMITTED')
      ),
      'required_evidence_ids', jsonb_build_array('EV-WB-SCOPE'),
      'required_unknowns', jsonb_build_array('LOCAL_SCOPE_UNRESOLVED'),
      'unknowns', jsonb_build_array(
        jsonb_build_object('id','LOCAL_SCOPE_UNRESOLVED','label','A Moscow-specific source has not been admitted.')
      ),
      'critical_error_layers', jsonb_build_array('CANONICAL_CLAIM'),
      'reference_answer', 'This is accepted human-review context, not a canonical claim. It constrains interpretation of the dossier.'
    )
  ),
  (
    'F1-CONTRADICTION-004', 'f1-qualified-user@0.1.0', 'en',
    'Interpret contradictory evidence',
    jsonb_build_object(
      'prompt', 'Identify the correct authority state when two admitted observations disagree.',
      'statement', 'The available evidence establishes one uncontested inflation value.',
      'authority_layer', 'CONTESTED',
      'evidence', jsonb_build_array(
        jsonb_build_object('id','EV-INF-A','title','Admitted observation A','excerpt','Inflation value A for the declared period.','source_state','ADMITTED'),
        jsonb_build_object('id','EV-INF-B','title','Admitted observation B','excerpt','A different inflation value for the same declared period.','source_state','ADMITTED')
      ),
      'required_evidence_ids', jsonb_build_array('EV-INF-A','EV-INF-B'),
      'required_unknowns', jsonb_build_array('CONTRADICTION_UNRESOLVED'),
      'unknowns', jsonb_build_array(
        jsonb_build_object('id','CONTRADICTION_UNRESOLVED','label','The contradiction has not been deterministically resolved.')
      ),
      'critical_error_layers', jsonb_build_array('CANONICAL_CLAIM'),
      'reference_answer', 'The claim remains contested until a deterministic resolution or stronger evidence is available.'
    )
  ),
  (
    'F1-TRACE-005', 'f1-qualified-user@0.1.0', 'en',
    'Reconstruct a decision from evidence',
    jsonb_build_object(
      'prompt', 'Select the evidence needed to reconstruct the admission decision.',
      'statement', 'The decision is reproducible from its bound evidence and policy version.',
      'authority_layer', 'DETERMINISTIC_DECISION',
      'evidence', jsonb_build_array(
        jsonb_build_object('id','EV-HASH-BINDING','title','Evidence binding record','excerpt','Candidate, evidence and policy hashes match the durable handoff.','source_state','ADMITTED'),
        jsonb_build_object('id','EV-POLICY-VERSION','title','Admission policy record','excerpt','The decision used the pinned policy version.','source_state','ADMITTED')
      ),
      'required_evidence_ids', jsonb_build_array('EV-HASH-BINDING','EV-POLICY-VERSION'),
      'required_unknowns', jsonb_build_array(),
      'unknowns', jsonb_build_array(),
      'critical_error_layers', jsonb_build_array('MODEL_PROPOSAL'),
      'reference_answer', 'The deterministic decision is reproducible from the evidence binding and pinned policy version.'
    )
  ),
  (
    'F1-TEMPORAL-006', 'f1-qualified-user@0.1.0', 'en',
    'Compare temporal states without collapsing periods',
    jsonb_build_object(
      'prompt', 'Classify the conclusion and select both period-specific observations.',
      'statement', 'The indicator changed between the two declared periods.',
      'authority_layer', 'DERIVED_COMPARISON',
      'evidence', jsonb_build_array(
        jsonb_build_object('id','EV-PERIOD-2018','title','2018 observation','excerpt','Observed value for 2018.','source_state','ADMITTED'),
        jsonb_build_object('id','EV-PERIOD-2019','title','2019 observation','excerpt','Observed value for 2019.','source_state','ADMITTED')
      ),
      'required_evidence_ids', jsonb_build_array('EV-PERIOD-2018','EV-PERIOD-2019'),
      'required_unknowns', jsonb_build_array('CAUSALITY_NOT_ESTABLISHED'),
      'unknowns', jsonb_build_array(
        jsonb_build_object('id','CAUSALITY_NOT_ESTABLISHED','label','The comparison does not establish why the change occurred.')
      ),
      'critical_error_layers', jsonb_build_array('CANONICAL_CAUSAL_CLAIM'),
      'reference_answer', 'The comparison is derived from two admitted period-specific observations and does not establish causality.'
    )
  )
)
INSERT INTO evaluation.validation_tasks (
  task_id, experiment_version, language, title, content_hash, task_payload, frozen
)
SELECT
  task_id,
  experiment_version,
  language,
  title,
  'sha256:' || encode(digest(payload::text, 'sha256'), 'hex'),
  payload,
  true
FROM frozen
ON CONFLICT (task_id) DO UPDATE SET
  experiment_version = EXCLUDED.experiment_version,
  language = EXCLUDED.language,
  title = EXCLUDED.title,
  content_hash = EXCLUDED.content_hash,
  task_payload = EXCLUDED.task_payload,
  frozen = true;

CREATE OR REPLACE FUNCTION evaluation.validation_condition(
  p_participant_hash text,
  p_task_id text,
  p_experiment_version text
)
RETURNS text
LANGUAGE sql
IMMUTABLE
AS $$
  SELECT CASE
    WHEN get_byte(digest(
      p_participant_hash || '|' || p_task_id || '|' || p_experiment_version,
      'sha256'
    ), 0) % 2 = 0 THEN 'AXIGNAL'
    ELSE 'CONTROL'
  END
$$;

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
    ),
    'events', COALESCE((
      SELECT jsonb_agg(to_jsonb(e) ORDER BY e.occurred_at, e.validation_event_id)
      FROM evaluation.validation_events e
      WHERE e.validation_session_id = s.validation_session_id
    ), '[]'::jsonb),
    'response', (
      SELECT to_jsonb(r)
      FROM evaluation.validation_responses r
      WHERE r.validation_session_id = s.validation_session_id
    )
  )
  FROM evaluation.validation_sessions s
  JOIN evaluation.validation_tasks t USING (task_id)
  WHERE s.validation_session_id = p_session_id
    AND s.tenant_id = tenant_private.current_tenant_id()
$$;

CREATE OR REPLACE FUNCTION evaluation.list_validation_tasks(p_language text DEFAULT NULL)
RETURNS SETOF jsonb
LANGUAGE sql
SECURITY DEFINER
SET search_path = pg_catalog, evaluation
AS $$
  SELECT jsonb_build_object(
    'task_id', t.task_id,
    'experiment_version', t.experiment_version,
    'language', t.language,
    'title', t.title,
    'content_hash', t.content_hash
  )
  FROM evaluation.validation_tasks t
  WHERE t.frozen
    AND (p_language IS NULL OR t.language = p_language)
  ORDER BY t.task_id
$$;

CREATE OR REPLACE FUNCTION evaluation.start_validation_session(
  p_tenant_id uuid,
  p_participant_hash text,
  p_participant_profile text,
  p_task_id text
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, evaluation
AS $$
DECLARE
  target_task evaluation.validation_tasks%ROWTYPE;
  target_session_id uuid;
  assigned_condition text;
BEGIN
  IF p_tenant_id IS NULL THEN
    RAISE EXCEPTION 'AXIGNAL_VALIDATION_TENANT_REQUIRED';
  END IF;
  IF p_participant_hash !~ '^sha256:[0-9a-f]{64}$' THEN
    RAISE EXCEPTION 'AXIGNAL_VALIDATION_PARTICIPANT_HASH_INVALID';
  END IF;
  IF p_participant_profile NOT IN (
    'DOMAIN_EXPERT', 'ANALYST', 'DECISION_MAKER', 'OTHER_QUALIFIED'
  ) THEN
    RAISE EXCEPTION 'AXIGNAL_VALIDATION_PROFILE_INVALID';
  END IF;

  SELECT * INTO target_task
  FROM evaluation.validation_tasks
  WHERE task_id = p_task_id AND frozen;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'AXIGNAL_VALIDATION_TASK_NOT_FOUND';
  END IF;

  assigned_condition := evaluation.validation_condition(
    p_participant_hash, target_task.task_id, target_task.experiment_version
  );

  INSERT INTO evaluation.validation_sessions (
    tenant_id,
    participant_id_hash,
    participant_profile,
    task_id,
    experiment_version,
    condition,
    language
  ) VALUES (
    p_tenant_id,
    p_participant_hash,
    p_participant_profile,
    target_task.task_id,
    target_task.experiment_version,
    assigned_condition,
    target_task.language
  )
  ON CONFLICT (tenant_id, participant_id_hash, task_id, experiment_version)
  DO UPDATE SET updated_at = evaluation.validation_sessions.updated_at
  RETURNING validation_session_id INTO target_session_id;

  INSERT INTO evaluation.validation_events (
    validation_session_id, tenant_id, event_type, idempotency_key, payload
  ) VALUES (
    target_session_id,
    p_tenant_id,
    'SESSION_STARTED',
    'session-started',
    jsonb_build_object('condition', assigned_condition, 'task_id', target_task.task_id)
  ) ON CONFLICT (validation_session_id, idempotency_key) DO NOTHING;

  PERFORM set_config('app.tenant_id', p_tenant_id::text, true);
  RETURN evaluation.validation_session_bundle(target_session_id);
END
$$;

CREATE OR REPLACE FUNCTION evaluation.append_validation_event(
  p_tenant_id uuid,
  p_session_id uuid,
  p_event_type text,
  p_idempotency_key text,
  p_payload jsonb DEFAULT '{}'::jsonb
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, evaluation
AS $$
DECLARE
  session_state text;
BEGIN
  SELECT state INTO session_state
  FROM evaluation.validation_sessions
  WHERE validation_session_id = p_session_id AND tenant_id = p_tenant_id;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'AXIGNAL_VALIDATION_SESSION_NOT_FOUND';
  END IF;
  IF session_state <> 'STARTED' THEN
    RAISE EXCEPTION 'AXIGNAL_VALIDATION_SESSION_NOT_OPEN';
  END IF;
  IF p_event_type NOT IN (
    'TASK_OPENED','SOURCE_OPENED','EVIDENCE_INSPECTED','CLAIM_INSPECTED',
    'TIMELINE_USED','HUMAN_REVIEW_OPENED'
  ) THEN
    RAISE EXCEPTION 'AXIGNAL_VALIDATION_EVENT_NOT_ALLOWED';
  END IF;
  IF p_idempotency_key IS NULL OR length(trim(p_idempotency_key)) < 3 THEN
    RAISE EXCEPTION 'AXIGNAL_VALIDATION_IDEMPOTENCY_KEY_REQUIRED';
  END IF;

  INSERT INTO evaluation.validation_events (
    validation_session_id, tenant_id, event_type, idempotency_key, payload
  ) VALUES (
    p_session_id, p_tenant_id, p_event_type, p_idempotency_key, COALESCE(p_payload,'{}')
  ) ON CONFLICT (validation_session_id, idempotency_key) DO NOTHING;

  PERFORM set_config('app.tenant_id', p_tenant_id::text, true);
  RETURN evaluation.validation_session_bundle(p_session_id);
END
$$;

CREATE OR REPLACE FUNCTION evaluation.complete_validation_session(
  p_tenant_id uuid,
  p_session_id uuid,
  p_authority_layer text,
  p_evidence_ids text[],
  p_unknown_ids text[],
  p_confidence integer,
  p_answer text
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, evaluation
AS $$
DECLARE
  target_session evaluation.validation_sessions%ROWTYPE;
  target_task evaluation.validation_tasks%ROWTYPE;
  response_payload jsonb;
  calculated_hash text;
  required_evidence text[];
  required_unknowns text[];
  critical_layers text[];
  authority_ok boolean;
  evidence_ok boolean;
  unknowns_ok boolean;
  critical_failure boolean;
  completed boolean;
BEGIN
  SELECT * INTO target_session
  FROM evaluation.validation_sessions
  WHERE validation_session_id = p_session_id AND tenant_id = p_tenant_id
  FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'AXIGNAL_VALIDATION_SESSION_NOT_FOUND';
  END IF;

  SELECT * INTO target_task
  FROM evaluation.validation_tasks
  WHERE task_id = target_session.task_id;

  response_payload := jsonb_build_object(
    'authority_layer', p_authority_layer,
    'evidence_ids', to_jsonb(COALESCE(p_evidence_ids, ARRAY[]::text[])),
    'unknown_ids', to_jsonb(COALESCE(p_unknown_ids, ARRAY[]::text[])),
    'confidence', p_confidence,
    'answer', COALESCE(p_answer, '')
  );
  calculated_hash := 'sha256:' || encode(digest(response_payload::text, 'sha256'), 'hex');

  IF target_session.state = 'COMPLETED' THEN
    IF target_session.response_hash <> calculated_hash THEN
      RAISE EXCEPTION 'AXIGNAL_VALIDATION_RESPONSE_IMMUTABLE';
    END IF;
    PERFORM set_config('app.tenant_id', p_tenant_id::text, true);
    RETURN evaluation.validation_session_bundle(p_session_id);
  END IF;
  IF target_session.state <> 'STARTED' THEN
    RAISE EXCEPTION 'AXIGNAL_VALIDATION_SESSION_NOT_OPEN';
  END IF;
  IF p_confidence < 0 OR p_confidence > 100 THEN
    RAISE EXCEPTION 'AXIGNAL_VALIDATION_CONFIDENCE_INVALID';
  END IF;

  SELECT COALESCE(array_agg(value), ARRAY[]::text[]) INTO required_evidence
  FROM jsonb_array_elements_text(target_task.task_payload->'required_evidence_ids');
  SELECT COALESCE(array_agg(value), ARRAY[]::text[]) INTO required_unknowns
  FROM jsonb_array_elements_text(target_task.task_payload->'required_unknowns');
  SELECT COALESCE(array_agg(value), ARRAY[]::text[]) INTO critical_layers
  FROM jsonb_array_elements_text(target_task.task_payload->'critical_error_layers');

  authority_ok := p_authority_layer = target_task.task_payload->>'authority_layer';
  evidence_ok := required_evidence <@ COALESCE(p_evidence_ids, ARRAY[]::text[]);
  unknowns_ok := required_unknowns <@ COALESCE(p_unknown_ids, ARRAY[]::text[]);
  critical_failure := p_authority_layer = ANY(critical_layers);
  completed := authority_ok AND evidence_ok AND unknowns_ok AND NOT critical_failure;

  INSERT INTO evaluation.validation_responses (
    validation_session_id,
    tenant_id,
    structured_response,
    response_hash,
    authority_layer_correct,
    evidence_traceability,
    unknowns_identified,
    critical_error,
    task_completed
  ) VALUES (
    p_session_id,
    p_tenant_id,
    response_payload,
    calculated_hash,
    authority_ok,
    evidence_ok,
    unknowns_ok,
    critical_failure,
    completed
  );

  UPDATE evaluation.validation_sessions
  SET state = 'COMPLETED',
      response_hash = calculated_hash,
      outcome = jsonb_build_object(
        'task_completed', completed,
        'authority_layer_correct', authority_ok,
        'evidence_traceability', evidence_ok,
        'unknowns_identified', unknowns_ok,
        'critical_error', critical_failure,
        'confidence', p_confidence
      ),
      completed_at = now(),
      updated_at = now()
  WHERE validation_session_id = p_session_id;

  INSERT INTO evaluation.validation_events (
    validation_session_id, tenant_id, event_type, idempotency_key, payload
  ) VALUES
    (p_session_id, p_tenant_id, 'ANSWER_SUBMITTED', 'answer-submitted',
      jsonb_build_object('response_hash', calculated_hash)),
    (p_session_id, p_tenant_id, 'SESSION_COMPLETED', 'session-completed',
      jsonb_build_object('task_completed', completed, 'critical_error', critical_failure));

  PERFORM set_config('app.tenant_id', p_tenant_id::text, true);
  RETURN evaluation.validation_session_bundle(p_session_id);
END
$$;

CREATE OR REPLACE FUNCTION evaluation.validation_metrics(p_tenant_id uuid)
RETURNS SETOF jsonb
LANGUAGE sql
SECURITY DEFINER
SET search_path = pg_catalog, evaluation
AS $$
  SELECT jsonb_build_object(
    'condition', s.condition,
    'sessions', count(*),
    'completed_sessions', count(*) FILTER (WHERE s.state = 'COMPLETED'),
    'task_completion_rate', COALESCE(avg((r.task_completed)::int), 0),
    'critical_error_rate', COALESCE(avg((r.critical_error)::int), 0),
    'evidence_traceability_rate', COALESCE(avg((r.evidence_traceability)::int), 0),
    'authority_layer_comprehension', COALESCE(avg((r.authority_layer_correct)::int), 0),
    'unknowns_identification_rate', COALESCE(avg((r.unknowns_identified)::int), 0)
  )
  FROM evaluation.validation_sessions s
  LEFT JOIN evaluation.validation_responses r USING (validation_session_id)
  WHERE s.tenant_id = p_tenant_id
  GROUP BY s.condition
  ORDER BY s.condition
$$;

REVOKE ALL ON ALL TABLES IN SCHEMA evaluation FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA evaluation FROM axignal_validation_runtime;
REVOKE ALL ON axignal_global.canonical_claims FROM axignal_validation_runtime;
REVOKE ALL ON axignal_global.evidence_objects FROM axignal_validation_runtime;
REVOKE ALL ON axignal_global.admission_decisions FROM axignal_validation_runtime;
REVOKE ALL ON tenant_private.research_runs FROM axignal_validation_runtime;

REVOKE ALL ON FUNCTION evaluation.list_validation_tasks(text) FROM PUBLIC;
REVOKE ALL ON FUNCTION evaluation.start_validation_session(uuid,text,text,text) FROM PUBLIC;
REVOKE ALL ON FUNCTION evaluation.validation_session_bundle(uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION evaluation.append_validation_event(uuid,uuid,text,text,jsonb) FROM PUBLIC;
REVOKE ALL ON FUNCTION evaluation.complete_validation_session(uuid,uuid,text,text[],text[],integer,text) FROM PUBLIC;
REVOKE ALL ON FUNCTION evaluation.validation_metrics(uuid) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION evaluation.list_validation_tasks(text)
  TO axignal_validation_runtime;
GRANT EXECUTE ON FUNCTION evaluation.start_validation_session(uuid,text,text,text)
  TO axignal_validation_runtime;
GRANT EXECUTE ON FUNCTION evaluation.validation_session_bundle(uuid)
  TO axignal_validation_runtime;
GRANT EXECUTE ON FUNCTION evaluation.append_validation_event(uuid,uuid,text,text,jsonb)
  TO axignal_validation_runtime;
GRANT EXECUTE ON FUNCTION evaluation.complete_validation_session(uuid,uuid,text,text[],text[],integer,text)
  TO axignal_validation_runtime;
GRANT EXECUTE ON FUNCTION evaluation.validation_metrics(uuid)
  TO axignal_validation_runtime;
