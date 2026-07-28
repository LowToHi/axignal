CREATE OR REPLACE FUNCTION tenant_private.resolve_human_review_case(
  requested_case_id uuid,
  reviewer_subject text,
  reviewer_email text,
  requested_action text,
  requested_reason_code text,
  requested_note text DEFAULT NULL
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, axignal_global, tenant_private
AS $$
DECLARE
  review_case tenant_private.human_review_cases%ROWTYPE;
  decision axignal_global.admission_decisions%ROWTYPE;
  source axignal_global.sources%ROWTYPE;
  required_gate text;
  allowed_actions constant text[] := ARRAY[
    'ACCEPT_AS_CONTEXT',
    'REJECT_PROPOSAL',
    'CONFIRM_CONTESTED',
    'REQUEST_MORE_EVIDENCE',
    'RETURN_TO_DETERMINISTIC_REVIEW',
    'MARK_OUT_OF_SCOPE'
  ];
BEGIN
  IF requested_action <> ALL(allowed_actions) THEN
    RAISE EXCEPTION 'HUMAN_REVIEW_ACTION_INVALID';
  END IF;

  SELECT * INTO review_case
  FROM tenant_private.human_review_cases
  WHERE human_review_case_id = requested_case_id
    AND tenant_id = tenant_private.current_tenant_id()
  FOR UPDATE;

  IF review_case.human_review_case_id IS NULL THEN
    RAISE EXCEPTION 'HUMAN_REVIEW_CASE_NOT_FOUND';
  END IF;
  IF review_case.state = 'CANCELLED' THEN
    RAISE EXCEPTION 'HUMAN_REVIEW_CASE_CANCELLED';
  END IF;
  IF review_case.state = 'RESOLVED' THEN
    IF review_case.resolution = requested_action
      AND review_case.resolution_reason_code = requested_reason_code
      AND review_case.resolution_note IS NOT DISTINCT FROM requested_note
    THEN
      RETURN tenant_private.human_review_case_bundle(requested_case_id);
    END IF;
    RAISE EXCEPTION 'HUMAN_REVIEW_CASE_ALREADY_RESOLVED';
  END IF;
  IF review_case.assigned_reviewer_subject IS NOT NULL
    AND review_case.assigned_reviewer_subject <> reviewer_subject
  THEN
    RAISE EXCEPTION 'HUMAN_REVIEW_CASE_ASSIGNED_TO_ANOTHER_REVIEWER';
  END IF;

  SELECT * INTO decision
  FROM axignal_global.admission_decisions
  WHERE admission_decision_id = review_case.admission_decision_id;

  SELECT admitted_source.* INTO source
  FROM axignal_global.candidate_claims AS candidate
  JOIN axignal_global.evidence_objects AS evidence
    ON evidence.evidence_id = candidate.evidence_ids[1]
  JOIN axignal_global.sources AS admitted_source
    ON admitted_source.source_id = evidence.source_id
  WHERE candidate.candidate_claim_id = review_case.candidate_claim_id;

  IF requested_action IN ('ACCEPT_AS_CONTEXT', 'RETURN_TO_DETERMINISTIC_REVIEW') THEN
    FOREACH required_gate IN ARRAY ARRAY[
      'HANDOFF_SCHEMA_VALID',
      'PACKAGE_HASH_VALID',
      'SOURCE_STILL_ADMITTED',
      'SOURCE_KILL_SWITCH_OFF',
      'RIGHTS_STILL_VALID',
      'RAW_OBJECT_HASH_VALID',
      'PRODUCER_AUTHORITY_SEPARATED',
      'POLICY_VERSION_PINNED'
    ]
    LOOP
      IF COALESCE((decision.gate_results->>required_gate)::boolean, false) IS NOT TRUE THEN
        RAISE EXCEPTION 'HUMAN_REVIEW_NON_BYPASSABLE_GATE_FAILED:%', required_gate;
      END IF;
    END LOOP;

    IF source.source_id IS NULL
      OR source.admission_state <> 'ADMITTED'
      OR source.kill_switch
      OR NOT source.commercial_use
      OR NOT source.redistribution
    THEN
      RAISE EXCEPTION 'HUMAN_REVIEW_NON_BYPASSABLE_GATE_FAILED:CURRENT_SOURCE';
    END IF;

    IF EXISTS (
      SELECT 1
      FROM axignal_global.candidate_claims AS candidate
      JOIN axignal_global.evidence_objects AS evidence
        ON evidence.evidence_id = ANY(candidate.evidence_ids)
      LEFT JOIN axignal_global.document_fragments AS fragment
        ON fragment.fragment_id = evidence.payload->>'fragment_id'
      WHERE candidate.candidate_claim_id = review_case.candidate_claim_id
        AND (
          evidence.source_id <> source.source_id
          OR evidence.rights_status <> source.rights_status
          OR fragment.fragment_id IS NULL
          OR evidence.payload->>'quote_hash' <> fragment.content_hash
          OR evidence.payload->>'text' <> fragment.text_content
        )
    ) THEN
      RAISE EXCEPTION 'HUMAN_REVIEW_NON_BYPASSABLE_GATE_FAILED:EVIDENCE_BINDING';
    END IF;
  END IF;

  IF review_case.assigned_reviewer_subject IS NULL THEN
    UPDATE tenant_private.human_review_cases
    SET assigned_reviewer_subject = reviewer_subject,
        assigned_reviewer_email = reviewer_email,
        assigned_at = now(),
        state = 'IN_REVIEW',
        updated_at = now()
    WHERE human_review_case_id = requested_case_id;

    INSERT INTO tenant_private.human_review_events (
      human_review_case_id,
      tenant_id,
      event_type,
      actor_subject,
      actor_email,
      reason_code
    ) VALUES
      (
        requested_case_id,
        review_case.tenant_id,
        'CASE_ASSIGNED',
        reviewer_subject,
        reviewer_email,
        requested_reason_code
      ),
      (
        requested_case_id,
        review_case.tenant_id,
        'REVIEW_STARTED',
        reviewer_subject,
        reviewer_email,
        requested_reason_code
      );
  END IF;

  IF requested_action = 'REQUEST_MORE_EVIDENCE' THEN
    IF review_case.state = 'MORE_EVIDENCE_REQUIRED'
      AND EXISTS (
        SELECT 1
        FROM tenant_private.human_review_events
        WHERE human_review_case_id = requested_case_id
          AND event_type = 'EVIDENCE_REQUESTED'
          AND actor_subject = reviewer_subject
          AND reason_code = requested_reason_code
          AND payload->>'note' IS NOT DISTINCT FROM requested_note
      )
    THEN
      RETURN tenant_private.human_review_case_bundle(requested_case_id);
    END IF;

    UPDATE tenant_private.human_review_cases
    SET state = 'MORE_EVIDENCE_REQUIRED',
        updated_at = now()
    WHERE human_review_case_id = requested_case_id;

    INSERT INTO tenant_private.human_review_events (
      human_review_case_id,
      tenant_id,
      event_type,
      actor_subject,
      actor_email,
      reason_code,
      payload
    ) VALUES (
      requested_case_id,
      review_case.tenant_id,
      'EVIDENCE_REQUESTED',
      reviewer_subject,
      reviewer_email,
      requested_reason_code,
      jsonb_build_object('note', requested_note)
    );

    RETURN tenant_private.human_review_case_bundle(requested_case_id);
  END IF;

  UPDATE tenant_private.human_review_cases
  SET state = 'RESOLVED',
      resolution = requested_action,
      resolution_reason_code = requested_reason_code,
      resolution_note = requested_note,
      resolved_at = now(),
      updated_at = now()
  WHERE human_review_case_id = requested_case_id;

  IF current_setting('axignal.test_fail_after_case_update', true) = 'on' THEN
    RAISE EXCEPTION 'TEST_FAILPOINT_AFTER_HUMAN_REVIEW_CASE_UPDATE';
  END IF;

  IF requested_action = 'ACCEPT_AS_CONTEXT' THEN
    UPDATE tenant_private.dossiers
    SET human_review_context = human_review_context || jsonb_build_array(
      jsonb_build_object(
        'human_review_case_id', requested_case_id,
        'candidate_claim_id', review_case.candidate_claim_id,
        'resolution', requested_action,
        'reason_code', requested_reason_code,
        'note', requested_note,
        'reviewer_subject', reviewer_subject,
        'reviewer_email', reviewer_email,
        'reviewed_at', now()
      )
    )
    WHERE research_run_id = review_case.research_run_id
      AND tenant_id = review_case.tenant_id;
  END IF;

  INSERT INTO tenant_private.human_review_events (
    human_review_case_id,
    tenant_id,
    event_type,
    actor_subject,
    actor_email,
    reason_code,
    payload
  ) VALUES
    (
      requested_case_id,
      review_case.tenant_id,
      'RESOLUTION_RECORDED',
      reviewer_subject,
      reviewer_email,
      requested_reason_code,
      jsonb_build_object(
        'resolution', requested_action,
        'note', requested_note
      )
    ),
    (
      requested_case_id,
      review_case.tenant_id,
      'CASE_CLOSED',
      reviewer_subject,
      reviewer_email,
      requested_reason_code,
      jsonb_build_object('resolution', requested_action)
    );

  RETURN tenant_private.human_review_case_bundle(requested_case_id);
END
$$;

