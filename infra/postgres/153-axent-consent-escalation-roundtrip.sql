CREATE TABLE IF NOT EXISTS tenant_private.support_confirmations (
  confirmation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  conversation_id uuid NOT NULL,
  requested_by_subject text NOT NULL,
  action_type text NOT NULL,
  parameters_hash text NOT NULL CHECK (parameters_hash ~ '^sha256:[0-9a-f]{64}$'),
  before_state_hash text NOT NULL CHECK (before_state_hash ~ '^sha256:[0-9a-f]{64}$'),
  token_hash text NOT NULL CHECK (token_hash ~ '^sha256:[0-9a-f]{64}$'),
  assurance_level text NOT NULL,
  expires_at timestamptz NOT NULL,
  consumed_at timestamptz,
  consumed_by_invocation_id uuid,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, confirmation_id),
  UNIQUE (tenant_id, token_hash),
  FOREIGN KEY (tenant_id, conversation_id)
    REFERENCES tenant_private.support_conversations (tenant_id, conversation_id)
    ON DELETE RESTRICT,
  FOREIGN KEY (tenant_id, consumed_by_invocation_id)
    REFERENCES tenant_private.support_tool_invocations (tenant_id, invocation_id)
    ON DELETE RESTRICT,
  CHECK (expires_at > created_at),
  CHECK ((consumed_at IS NULL) = (consumed_by_invocation_id IS NULL))
);

CREATE TABLE IF NOT EXISTS tenant_private.support_case_events (
  event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  case_id uuid NOT NULL,
  event_type text NOT NULL CHECK (event_type IN (
    'OPENED','ACKNOWLEDGED','ASSIGNED','INVESTIGATING','AWAITING_CUSTOMER',
    'CUSTOMER_REPLIED','RESOLVED','REOPENED','CLOSED','NOTIFICATION_SENT'
  )),
  actor_type text NOT NULL CHECK (actor_type IN ('USER','AXENT','HUMAN_AGENT','SYSTEM')),
  actor_subject text,
  payload_redacted jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (tenant_id, case_id)
    REFERENCES tenant_private.support_cases (tenant_id, case_id)
    ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS tenant_private.support_notifications (
  notification_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  case_id uuid NOT NULL,
  conversation_id uuid NOT NULL,
  recipient_subject text NOT NULL,
  notification_type text NOT NULL CHECK (notification_type IN (
    'CASE_ACKNOWLEDGED','CASE_ASSIGNED','CASE_RESOLVED','CASE_REOPENED','ACTION_RECEIPT'
  )),
  payload_redacted jsonb NOT NULL DEFAULT '{}'::jsonb,
  delivery_state text NOT NULL DEFAULT 'PENDING' CHECK (delivery_state IN (
    'PENDING','DELIVERED','FAILED'
  )),
  delivered_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (tenant_id, case_id)
    REFERENCES tenant_private.support_cases (tenant_id, case_id)
    ON DELETE RESTRICT,
  FOREIGN KEY (tenant_id, conversation_id)
    REFERENCES tenant_private.support_conversations (tenant_id, conversation_id)
    ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS support_confirmations_expiry_idx
  ON tenant_private.support_confirmations (tenant_id, expires_at)
  WHERE consumed_at IS NULL;
CREATE INDEX IF NOT EXISTS support_case_events_case_idx
  ON tenant_private.support_case_events (tenant_id, case_id, created_at);
CREATE INDEX IF NOT EXISTS support_notifications_delivery_idx
  ON tenant_private.support_notifications (tenant_id, delivery_state, created_at);

ALTER TABLE tenant_private.support_confirmations ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.support_confirmations FORCE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.support_case_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.support_case_events FORCE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.support_notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.support_notifications FORCE ROW LEVEL SECURITY;

CREATE POLICY support_confirmations_tenant_policy
  ON tenant_private.support_confirmations
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());
CREATE POLICY support_case_events_tenant_policy
  ON tenant_private.support_case_events
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());
CREATE POLICY support_notifications_tenant_policy
  ON tenant_private.support_notifications
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

CREATE OR REPLACE FUNCTION tenant_private.reject_axent_case_event_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'AXENT case event ledger is append-only';
END $$;

DROP TRIGGER IF EXISTS support_case_events_immutable
  ON tenant_private.support_case_events;
CREATE TRIGGER support_case_events_immutable
BEFORE UPDATE OR DELETE ON tenant_private.support_case_events
FOR EACH ROW EXECUTE FUNCTION tenant_private.reject_axent_case_event_mutation();

GRANT SELECT, INSERT, UPDATE ON tenant_private.support_confirmations TO axignal_app;
GRANT SELECT, INSERT ON tenant_private.support_case_events TO axignal_app;
GRANT SELECT, INSERT, UPDATE ON tenant_private.support_notifications TO axignal_app;
REVOKE DELETE ON tenant_private.support_confirmations,
  tenant_private.support_case_events,
  tenant_private.support_notifications FROM axignal_app;
REVOKE UPDATE ON tenant_private.support_case_events FROM axignal_app;
