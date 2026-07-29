GRANT UPDATE (updated_at)
  ON axignal_global.candidate_claims
  TO axignal_ted_worker;

REVOKE UPDATE (
  fingerprint,
  opportunity_id,
  subject_id,
  predicate,
  object_value,
  statement,
  kind,
  state,
  evidence_ids,
  producer_type,
  producer_id,
  method_version,
  canonical_claim_id,
  rejection_reasons,
  relationship,
  model_version,
  prompt_version,
  extraction_confidence,
  assumptions,
  unknowns
) ON axignal_global.candidate_claims
FROM axignal_ted_worker;
