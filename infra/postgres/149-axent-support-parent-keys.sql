CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS tenant_private.support_conversations (
  conversation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  workspace_id uuid,
  research_run_id uuid,
  opened_by_subject text NOT NULL,
  channel text NOT NULL DEFAULT 'WEB'
    CHECK (channel IN ('WEB', 'API', 'SYSTEM')),
  status text NOT NULL DEFAULT 'OPEN'
    CHECK (status IN (
      'OPEN', 'INVESTIGATING', 'AWAITING_CUSTOMER', 'AWAITING_SYSTEM',
      'ESCALATED', 'RESOLVED', 'CLOSED'
    )),
  intent text,
  priority text NOT NULL DEFAULT 'NORMAL'
    CHECK (priority IN ('LOW', 'NORMAL', 'HIGH', 'URGENT')),
  language text NOT NULL DEFAULT 'es',
  summary_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  last_message_at timestamptz,
  resolved_at timestamptz,
  resolution_code text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, conversation_id),
  FOREIGN KEY (tenant_id, workspace_id)
    REFERENCES tenant_private.subscriber_workspaces (tenant_id, workspace_id)
    ON DELETE RESTRICT,
  FOREIGN KEY (tenant_id, research_run_id)
    REFERENCES tenant_private.research_runs (tenant_id, research_run_id)
    ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS tenant_private.support_messages (
  message_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  conversation_id uuid NOT NULL,
  author_type text NOT NULL
    CHECK (author_type IN ('USER', 'AXENT', 'HUMAN_AGENT', 'SYSTEM')),
  author_subject text,
  content text NOT NULL CHECK (char_length(content) BETWEEN 1 AND 100000),
  content_format text NOT NULL DEFAULT 'MARKDOWN'
    CHECK (content_format IN ('TEXT', 'MARKDOWN', 'STRUCTURED')),
  model_id text,
  prompt_policy_version text,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, message_id),
  UNIQUE (tenant_id, conversation_id, message_id),
  FOREIGN KEY (tenant_id, conversation_id)
    REFERENCES tenant_private.support_conversations (tenant_id, conversation_id)
    ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS tenant_private.support_cases (
  case_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  conversation_id uuid NOT NULL,
  case_type text NOT NULL CHECK (case_type IN (
    'HOW_TO', 'ACCOUNT_ACCESS', 'BILLING', 'SUBSCRIPTION',
    'SEAT_MANAGEMENT', 'RESEARCH_RUN', 'SOURCE_DATA', 'ALERT',
    'EXPORT', 'DOCUMENT', 'INTEGRATION', 'SECURITY', 'PRIVACY',
    'LEGAL', 'BUG', 'SERVICE_INCIDENT', 'FEATURE_REQUEST'
  )),
  severity text NOT NULL DEFAULT 'S3'
    CHECK (severity IN ('S0', 'S1', 'S2', 'S3', 'S4')),
  status text NOT NULL DEFAULT 'OPEN'
    CHECK (status IN (
      'OPEN', 'ACKNOWLEDGED', 'INVESTIGATING',
      'AWAITING_CUSTOMER', 'RESOLVED', 'CLOSED'
    )),
  owner_type text NOT NULL DEFAULT 'QUEUE'
    CHECK (owner_type IN ('QUEUE', 'HUMAN')),
  owner_subject text,
  service_area text NOT NULL,
  customer_impact text,
  system_impact text,
  resolution text,
  opened_at timestamptz NOT NULL DEFAULT now(),
  acknowledged_at timestamptz,
  resolved_at timestamptz,
  closed_at timestamptz,
  UNIQUE (tenant_id, case_id),
  FOREIGN KEY (tenant_id, conversation_id)
    REFERENCES tenant_private.support_conversations (tenant_id, conversation_id)
    ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS tenant_private.support_tool_invocations (
  invocation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL,
  conversation_id uuid NOT NULL,
  case_id uuid,
  tool_name text NOT NULL,
  tool_version text NOT NULL,
  requested_by_subject text NOT NULL,
  executed_as text NOT NULL DEFAULT 'AXENT_AGENT',
  input_redacted jsonb NOT NULL DEFAULT '{}'::jsonb,
  input_hash text NOT NULL CHECK (input_hash ~ '^sha256:[0-9a-f]{64}$'),
  decision text NOT NULL CHECK (decision IN (
    'ALLOW_READ', 'ALLOW', 'ALLOW_WITH_CONFIRMATION',
    'REQUIRE_STEP_UP_AUTH', 'ESCALATE', 'DENY'
  )),
  decision_reason jsonb NOT NULL DEFAULT '[]'::jsonb,
  result_status text NOT NULL
    CHECK (result_status IN ('PENDING', 'SUCCEEDED', 'FAILED', 'DENIED')),
  result_redacted jsonb NOT NULL DEFAULT '{}'::jsonb,
  started_at timestamptz NOT NULL DEFAULT now(),
  finished_at timestamptz,
  idempotency_key text,
  correlation_id text NOT NULL,
  UNIQUE (tenant_id, invocation_id),
  UNIQUE (tenant_id, tool_name, idempotency_key),
  FOREIGN KEY (tenant_id, conversation_id)
    REFERENCES tenant_private.support_conversations (tenant_id, conversation_id)
    ON DELETE RESTRICT,
  FOREIGN KEY (tenant_id, case_id)
    REFERENCES tenant_private.support_cases (tenant_id, case_id)
    ON DELETE RESTRICT
);
