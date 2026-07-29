REVOKE UPDATE ON axignal_global.candidate_claims FROM axignal_ted_worker;

GRANT UPDATE (updated_at)
  ON axignal_global.candidate_claims
  TO axignal_ted_worker;
