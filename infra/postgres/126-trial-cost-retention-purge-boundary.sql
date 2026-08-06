-- Trial cost reservations are subordinate accounting records for a token
-- reservation. Application roles cannot delete token reservations directly;
-- the only deletion path is the authorised terminal retention purge. Cascade
-- therefore closes the dependency without weakening append-only runtime use.

ALTER TABLE identity_private.trial_cost_reservations
  DROP CONSTRAINT IF EXISTS trial_cost_reservations_token_reservation_id_fkey;

ALTER TABLE identity_private.trial_cost_reservations
  ADD CONSTRAINT trial_cost_reservations_token_reservation_id_fkey
  FOREIGN KEY (token_reservation_id)
  REFERENCES tenant_private.ai_token_reservations(reservation_id)
  ON DELETE CASCADE;
