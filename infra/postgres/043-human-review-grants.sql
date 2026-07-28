REVOKE ALL ON tenant_private.human_review_cases FROM axignal_human_reviewer;
REVOKE ALL ON tenant_private.human_review_events FROM axignal_human_reviewer;
REVOKE ALL ON axignal_global.canonical_claims FROM axignal_human_reviewer;
REVOKE ALL ON axignal_global.claim_state_events FROM axignal_human_reviewer;
REVOKE ALL ON axignal_global.admission_decisions FROM axignal_human_reviewer;
REVOKE ALL ON axignal_global.sources FROM axignal_human_reviewer;
REVOKE ALL ON axignal_global.source_objects FROM axignal_human_reviewer;
REVOKE ALL ON axignal_global.document_fragments FROM axignal_human_reviewer;
REVOKE ALL ON axignal_global.evidence_objects FROM axignal_human_reviewer;

REVOKE ALL ON FUNCTION tenant_private.human_review_case_bundle(uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.list_human_review_cases(uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.resolve_human_review_case(
  uuid, text, text, text, text, text
) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION tenant_private.human_review_case_bundle(uuid)
  TO axignal_human_reviewer;
GRANT EXECUTE ON FUNCTION tenant_private.list_human_review_cases(uuid)
  TO axignal_human_reviewer;
GRANT EXECUTE ON FUNCTION tenant_private.resolve_human_review_case(
  uuid, text, text, text, text, text
) TO axignal_human_reviewer;
