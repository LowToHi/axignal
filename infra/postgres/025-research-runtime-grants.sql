GRANT SELECT ON
  axignal_global.sources,
  axignal_global.evidence_objects,
  axignal_global.candidate_claims,
  axignal_global.admission_batches,
  axignal_global.canonical_claims,
  axignal_global.claim_state_events
TO axignal_app;

GRANT INSERT ON axignal_global.outbox_events TO axignal_app;
