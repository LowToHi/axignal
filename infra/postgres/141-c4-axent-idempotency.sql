-- AXIGNAL C4 AXENT durable idempotency and read adapter.
-- Extends the C3 tenant-governed conversation authority without creating a
-- second conversation store or granting direct table access to the app role.

CREATE TABLE IF NOT EXISTS tenant_private.axent_conversation_receipts (
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  request_id text NOT NULL CHECK (request_id ~ '^axent_req_[A-Za-z0-9_-]{8,120}$'),
  request_hash text NOT NULL CHECK (request_hash ~ '^sha256:[0-9a-f]{64}$'),
  conversation_id uuid NOT NULL REFERENCES tenant_private.axent_conversations(conversation_id) ON DELETE CASCADE,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id, request_id)
);

CREATE TABLE IF NOT EXISTS tenant_private.axent_message_receipts (
  tenant_id uuid NOT NULL REFERENCES tenant_private.workspace_lifecycle(tenant_id) ON DELETE CASCADE,
  conversation_id uuid NOT NULL REFERENCES tenant_private.axent_conversations(conversation_id) ON DELETE CASCADE,
  request_id text NOT NULL CHECK (request_id ~ '^axent_req_[A-Za-z0-9_-]{8,120}$'),
  request_hash text NOT NULL CHECK (request_hash ~ '^sha256:[0-9a-f]{64}$'),
  message_id uuid NOT NULL REFERENCES tenant_private.axent_messages(message_id) ON DELETE CASCADE,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id, conversation_id, request_id)
);

ALTER TABLE tenant_private.axent_conversation_receipts ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.axent_conversation_receipts FORCE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.axent_message_receipts ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_private.axent_message_receipts FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS axent_conversation_receipts_tenant_isolation
  ON tenant_private.axent_conversation_receipts;
CREATE POLICY axent_conversation_receipts_tenant_isolation
  ON tenant_private.axent_conversation_receipts
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

DROP POLICY IF EXISTS axent_message_receipts_tenant_isolation
  ON tenant_private.axent_message_receipts;
CREATE POLICY axent_message_receipts_tenant_isolation
  ON tenant_private.axent_message_receipts
  USING (tenant_id = tenant_private.current_tenant_id())
  WITH CHECK (tenant_id = tenant_private.current_tenant_id());

CREATE OR REPLACE FUNCTION tenant_private.create_axent_conversation_idempotent(
  p_request_id text,
  p_identity_subject text,
  p_title text,
  p_retention_class text,
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.axent_conversations
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.c3_require_active_workspace();
  v_request_hash text;
  v_receipt tenant_private.axent_conversation_receipts%ROWTYPE;
  v_conversation tenant_private.axent_conversations%ROWTYPE;
BEGIN
  IF p_request_id IS NULL OR p_request_id !~ '^axent_req_[A-Za-z0-9_-]{8,120}$' THEN
    RAISE EXCEPTION 'axent_request_id_invalid';
  END IF;
  v_request_hash := 'sha256:' || encode(
    public.digest(
      convert_to(
        concat_ws(E'\n', p_identity_subject, p_title, p_retention_class),
        'UTF8'
      ),
      'sha256'
    ),
    'hex'
  );
  PERFORM pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(v_tenant_id::text || ':' || p_request_id, 0)
  );

  SELECT * INTO v_receipt
  FROM tenant_private.axent_conversation_receipts
  WHERE tenant_id = v_tenant_id AND request_id = p_request_id;
  IF FOUND THEN
    IF v_receipt.request_hash <> v_request_hash THEN
      RAISE EXCEPTION 'axent_idempotency_conflict';
    END IF;
    SELECT * INTO v_conversation
    FROM tenant_private.axent_conversations
    WHERE tenant_id = v_tenant_id
      AND conversation_id = v_receipt.conversation_id
      AND identity_subject = p_identity_subject;
    IF NOT FOUND THEN RAISE EXCEPTION 'axent_conversation_not_found'; END IF;
    RETURN v_conversation;
  END IF;

  v_conversation := tenant_private.create_axent_conversation(
    p_identity_subject,
    p_title,
    p_retention_class,
    p_actor_subject,
    p_now
  );
  INSERT INTO tenant_private.axent_conversation_receipts (
    tenant_id, request_id, request_hash, conversation_id, created_at
  ) VALUES (
    v_tenant_id, p_request_id, v_request_hash,
    v_conversation.conversation_id, p_now
  );
  RETURN v_conversation;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.append_axent_message_idempotent(
  p_conversation_id uuid,
  p_request_id text,
  p_message_role text,
  p_content text,
  p_encryption_key text,
  p_actor_subject text,
  p_now timestamptz DEFAULT now()
)
RETURNS tenant_private.axent_messages
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
DECLARE
  v_tenant_id uuid := tenant_private.c3_require_active_workspace();
  v_request_hash text;
  v_receipt tenant_private.axent_message_receipts%ROWTYPE;
  v_message tenant_private.axent_messages%ROWTYPE;
BEGIN
  IF p_request_id IS NULL OR p_request_id !~ '^axent_req_[A-Za-z0-9_-]{8,120}$' THEN
    RAISE EXCEPTION 'axent_request_id_invalid';
  END IF;
  v_request_hash := 'sha256:' || encode(
    public.digest(
      convert_to(concat_ws(E'\n', p_message_role, p_content), 'UTF8'),
      'sha256'
    ),
    'hex'
  );
  PERFORM pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(
      v_tenant_id::text || ':' || p_conversation_id::text || ':' || p_request_id,
      0
    )
  );

  SELECT * INTO v_receipt
  FROM tenant_private.axent_message_receipts
  WHERE tenant_id = v_tenant_id
    AND conversation_id = p_conversation_id
    AND request_id = p_request_id;
  IF FOUND THEN
    IF v_receipt.request_hash <> v_request_hash THEN
      RAISE EXCEPTION 'axent_idempotency_conflict';
    END IF;
    SELECT * INTO v_message
    FROM tenant_private.axent_messages
    WHERE tenant_id = v_tenant_id
      AND conversation_id = p_conversation_id
      AND message_id = v_receipt.message_id;
    IF NOT FOUND THEN RAISE EXCEPTION 'axent_message_not_found'; END IF;
    RETURN v_message;
  END IF;

  v_message := tenant_private.append_axent_message(
    p_conversation_id,
    p_message_role,
    p_content,
    p_encryption_key,
    p_actor_subject,
    p_now
  );
  INSERT INTO tenant_private.axent_message_receipts (
    tenant_id, conversation_id, request_id, request_hash, message_id, created_at
  ) VALUES (
    v_tenant_id, p_conversation_id, p_request_id,
    v_request_hash, v_message.message_id, p_now
  );
  RETURN v_message;
END
$$;

CREATE OR REPLACE FUNCTION tenant_private.list_axent_conversations(
  p_identity_subject text,
  p_limit integer DEFAULT 50
)
RETURNS jsonb
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path TO pg_catalog
AS $$
  SELECT COALESCE(
    jsonb_agg(
      jsonb_build_object(
        'conversation_id', conversation.conversation_id,
        'title', conversation.title,
        'retention_class', conversation.retention_class,
        'retention_until', conversation.retention_until,
        'state', conversation.state,
        'message_count', (
          SELECT count(*)
          FROM tenant_private.axent_messages message
          WHERE message.tenant_id = conversation.tenant_id
            AND message.conversation_id = conversation.conversation_id
        ),
        'created_at', conversation.created_at,
        'updated_at', conversation.updated_at
      ) ORDER BY conversation.updated_at DESC, conversation.conversation_id
    ),
    '[]'::jsonb
  )
  FROM (
    SELECT *
    FROM tenant_private.axent_conversations
    WHERE tenant_id = tenant_private.c3_require_tenant()
      AND identity_subject = p_identity_subject
      AND state = 'ACTIVE'
    ORDER BY updated_at DESC, conversation_id
    LIMIT least(greatest(p_limit, 1), 50)
  ) conversation
$$;

REVOKE ALL ON tenant_private.axent_conversation_receipts,
  tenant_private.axent_message_receipts
FROM PUBLIC, axignal_app;

REVOKE ALL ON FUNCTION tenant_private.create_axent_conversation_idempotent(text, text, text, text, text, timestamptz) FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.append_axent_message_idempotent(uuid, text, text, text, text, text, timestamptz) FROM PUBLIC;
REVOKE ALL ON FUNCTION tenant_private.list_axent_conversations(text, integer) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION tenant_private.create_axent_conversation_idempotent(text, text, text, text, text, timestamptz),
  tenant_private.append_axent_message_idempotent(uuid, text, text, text, text, text, timestamptz),
  tenant_private.list_axent_conversations(text, integer)
TO axignal_app;

CREATE INDEX IF NOT EXISTS axent_conversation_receipts_conversation_idx
  ON tenant_private.axent_conversation_receipts (tenant_id, conversation_id);
CREATE INDEX IF NOT EXISTS axent_message_receipts_message_idx
  ON tenant_private.axent_message_receipts (tenant_id, conversation_id, message_id);
